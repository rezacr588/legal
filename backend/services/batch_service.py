"""
Batch Generation Service - Handles background batch generation logic.
Extracted from api_server.py for better separation of concerns.
"""
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import json

from config import (
    MAX_BATCH_TIMEOUT,
    MAX_MODEL_SWITCHES,
    MAX_SAMPLE_RETRIES,
    SAMPLE_TYPE_CYCLE,
    TOPICS,
    PROVIDERS
)
from models import db
from models.batch import BatchHistory
from services.generation_service import GenerationService
from services.llm_service import LLMProviderFactory
from services.sse_service import get_sse_service
from utils.circuit_breaker import CircuitBreaker
from services.data_service import DataService


class BatchService:
    """
    Service class for managing batch generation operations.
    Handles background workers, progress tracking, and database persistence.
    """

    # Class-level shared state (persists across all instances)
    _active_batches: Dict = {}  # In-memory batch state shared across all instances
    _batch_lock = threading.Lock()  # Shared lock for thread-safe access
    _parquet_lock = threading.Lock()  # Shared lock for parquet writes

    def __init__(self):
        """Initialize batch service (uses class-level shared state)."""
        self.generation_service = GenerationService()

    @property
    def active_batches(self):
        """Access shared active_batches dictionary"""
        return BatchService._active_batches

    @property
    def batch_lock(self):
        """Access shared batch_lock"""
        return BatchService._batch_lock

    @property
    def parquet_lock(self):
        """Access shared parquet_lock"""
        return BatchService._parquet_lock

    def create_batch_state(self, batch_id: str, provider: str, model: str, total: int = 0) -> Dict:
        """Create initial batch state object."""
        return {
            'running': True,
            'progress': 0,
            'total': total,
            'current_sample': None,
            'current_provider': provider,
            'current_model': model,
            'errors': [],
            'batch_id': batch_id,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'samples_generated': 0,
            'total_tokens': 0,
            'model_switches': [],
            'provider_switches': [],
            'failed_models_by_provider': {provider: []},
            'consecutive_failures': 0,
            'skipped_topics': [],
            'circuit_breaker_summary': {}
        }

    def start_batch(self, target_count: int, provider: str = 'auto', model: str = None,
                    topic_filter: Optional[str] = None, difficulty_filter: Optional[str] = None,
                    reasoning_instruction: Optional[str] = None, sample_type_filter: str = 'balance',
                    smart_mode: bool = True):
        """
        Start a new batch generation job in background thread.

        Args:
            target_count: Target total sample count
            provider: LLM provider name ('auto' for intelligent provider selection)
            model: Model name (None for provider's best model)
            topic_filter: Optional topic filter (None = auto-balance all topics)
            difficulty_filter: Optional difficulty filter (None = auto-balance)
            reasoning_instruction: Optional custom reasoning requirements
            sample_type_filter: Sample type filter ('balance' = auto-balance types)
            smart_mode: Enable intelligent provider failover and auto-balancing

        Returns:
            Dict with success status and batch info
        """
        # Calculate samples needed from database
        data_service = DataService()
        current_count = data_service.count()
        samples_needed = target_count - current_count

        if samples_needed <= 0:
            return {
                'success': False,
                'error': f'Target already met: {current_count} samples exist, target is {target_count}'
            }

        # Smart mode: Auto-select best available provider
        if smart_mode and (provider == 'auto' or not provider):
            provider = self._select_best_provider()
            print(f"🤖 Smart mode: Selected provider '{provider}'")

        # Smart mode: Use provider's champion model if not specified
        if not model and provider in PROVIDERS:
            model = PROVIDERS[provider].get('champion_model') or PROVIDERS[provider]['default_model']
            print(f"🤖 Smart mode: Using model '{model}'")

        # Generate unique batch ID
        batch_id = f"batch_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        # Create batch state
        with self.batch_lock:
            batch_state = self.create_batch_state(batch_id, provider, model, samples_needed)
            batch_state.update({
                'topic_filter': topic_filter,
                'difficulty_filter': difficulty_filter,
                'reasoning_instruction': reasoning_instruction,
                'sample_type_filter': sample_type_filter or 'balance',
                'smart_mode': smart_mode,
                'provider_failures': {},  # Track failures per provider
                'available_providers': [p for p in PROVIDERS.keys() if PROVIDERS[p]['enabled']],
                'tried_models_by_provider': {provider: [model]}  # Mark initial model as tried
            })
            self.active_batches[batch_id] = batch_state

        # Save to database
        self._save_batch_to_db(batch_state)

        # Get Flask app instance to pass to worker thread
        from flask import current_app
        app = current_app._get_current_object()

        # Start background worker thread
        thread = threading.Thread(
            target=self._batch_worker,
            args=(batch_id, target_count, provider, model, app)
        )
        thread.daemon = True
        thread.start()

        return {
            'success': True,
            'batch_id': batch_id,
            'samples_needed': samples_needed,
            'smart_mode': smart_mode,
            'initial_provider': provider,
            'initial_model': model
        }

    def _select_best_provider(self) -> str:
        """
        Intelligently select the best available provider based on:
        - Availability (enabled)
        - Rate limits
        - Recent failures
        - Performance

        Uses database-driven configuration with fallback to config.py.
        """
        # Try database first
        try:
            from models import Provider
            from flask import current_app

            with current_app.app_context():
                # Priority order: Cerebras (fastest) → Mistral (high quality) → Google → Groq → Ollama
                priority_order = ['cerebras', 'mistral', 'google', 'groq', 'ollama']

                for provider_id in priority_order:
                    provider = Provider.query.filter_by(id=provider_id, enabled=True).first()
                    if provider:
                        print(f"🔍 Database: Selected provider '{provider_id}' (RPM: {provider.requests_per_minute})")
                        return provider_id

                # Fallback to first enabled provider in database
                first_enabled = Provider.query.filter_by(enabled=True).first()
                if first_enabled:
                    print(f"🔍 Database: Selected provider '{first_enabled.id}' (fallback)")
                    return first_enabled.id
        except Exception as e:
            print(f"⚠️  Database provider selection failed, using config.py: {e}")

        # Fallback to config.py
        priority_order = ['cerebras', 'mistral', 'google', 'groq', 'ollama']

        for provider_id in priority_order:
            if provider_id in PROVIDERS and PROVIDERS[provider_id].get('enabled', False):
                print(f"🔍 Config: Selected provider '{provider_id}'")
                return provider_id

        # Fallback to first enabled provider
        for provider_id, config in PROVIDERS.items():
            if config.get('enabled', False):
                print(f"🔍 Config: Selected provider '{provider_id}' (fallback)")
                return provider_id

        return 'groq'  # Final fallback

    def _should_switch_provider(self, error: str, current_provider: str, batch_state: Dict) -> bool:
        """
        Determine if we should switch providers based on error type.

        Args:
            error: Error message from failed generation
            current_provider: Current provider being used
            batch_state: Current batch state

        Returns:
            bool: True if should switch providers
        """
        if not error:
            return False

        error_lower = str(error).lower()

        # Rate limit errors - immediate switch
        if any(keyword in error_lower for keyword in ['rate limit', 'rate_limit', '429', 'too many requests']):
            print(f"⚠️  Rate limit detected on {current_provider}")
            return True

        # Model unavailable errors
        if any(keyword in error_lower for keyword in ['model_unavailable', 'model not found', 'invalid model']):
            print(f"⚠️  Model unavailable on {current_provider}")
            return True

        # Authentication/API key errors
        if any(keyword in error_lower for keyword in ['authentication', 'api key', 'unauthorized', '401', '403']):
            print(f"⚠️  Authentication issue on {current_provider}")
            return True

        # Consecutive failures threshold (switch after 5 consecutive failures)
        if batch_state.get('consecutive_failures', 0) >= 5:
            print(f"⚠️  Too many consecutive failures ({batch_state['consecutive_failures']}) on {current_provider}")
            return True

        return False

    def _get_next_model_for_provider(self, provider: str, batch_state: Dict) -> Optional[str]:
        """
        Get the next untried model for a provider.
        Cycles through available models to maximize success chances.

        Args:
            provider: Provider ID
            batch_state: Current batch state

        Returns:
            str: Model name to try next, or None if all models exhausted
        """
        # Initialize tried_models tracking if not exists
        if 'tried_models_by_provider' not in batch_state:
            batch_state['tried_models_by_provider'] = {}

        if provider not in batch_state['tried_models_by_provider']:
            batch_state['tried_models_by_provider'][provider] = []

        tried_models = batch_state['tried_models_by_provider'][provider]

        # Get fallback order from provider instance (DRY - don't repeat provider logic)
        try:
            from services.llm_service import LLMProviderFactory
            # Use database-driven configuration
            provider_instance = LLMProviderFactory.get_provider(provider, use_db=True)
            available_models = provider_instance.get_fallback_order()
        except Exception as e:
            print(f"⚠️  Error getting fallback order for {provider}: {e}")
            # Fallback to champion/default model from config
            return PROVIDERS[provider].get('champion_model') or PROVIDERS[provider]['default_model']

        # Find next untried model
        for model in available_models:
            if model not in tried_models:
                # Mark this model as tried
                tried_models.append(model)
                print(f"🔄 Trying next model on {provider}: {model} ({len(tried_models)}/{len(available_models)} models tried)")
                return model

        # All models tried on this provider
        print(f"❌ All {len(available_models)} models exhausted on {provider}")
        return None

    def _has_more_models(self, provider: str, batch_state: Dict) -> bool:
        """
        Check if provider has more untried models.

        Args:
            provider: Provider ID
            batch_state: Current batch state

        Returns:
            bool: True if there are more models to try
        """
        if 'tried_models_by_provider' not in batch_state:
            return True

        if provider not in batch_state['tried_models_by_provider']:
            return True

        tried_models = batch_state['tried_models_by_provider'][provider]

        # Get fallback order from provider instance (DRY - centralized logic)
        try:
            from services.llm_service import LLMProviderFactory
            # Use database-driven configuration
            provider_instance = LLMProviderFactory.get_provider(provider, use_db=True)
            available_models = provider_instance.get_fallback_order()
        except Exception as e:
            print(f"⚠️  Error getting fallback order for {provider}: {e}")
            return False  # If we can't get models, assume none available

        # Check if there are untried models
        return len(tried_models) < len(available_models)

    def _switch_to_next_provider(self, current_provider: str, batch_state: Dict) -> Optional[str]:
        """
        Switch to the next available provider.

        Args:
            current_provider: Provider to switch away from
            batch_state: Current batch state

        Returns:
            str: Next provider to use, or None if all providers exhausted
        """
        available_providers = batch_state.get('available_providers', [])
        provider_failures = batch_state.get('provider_failures', {})

        # Record failure for current provider
        if current_provider not in provider_failures:
            provider_failures[current_provider] = 0
        provider_failures[current_provider] += 1

        # Check if all available providers have been tried and failed
        all_providers_failed = all(
            provider_id in provider_failures and provider_failures[provider_id] > 0
            for provider_id in available_providers
        )

        if all_providers_failed:
            print(f"❌ All providers exhausted! Failures: {provider_failures}")
            # Check if all failures are rate limits
            if provider_failures[current_provider] < 3:
                # Give each provider a few tries before giving up completely
                print(f"⏳ Will retry providers (attempt {provider_failures[current_provider]}/3)")
            else:
                print(f"🛑 Stopping batch - all providers have been tried multiple times")
                return None

        # Remove current provider from available list
        remaining_providers = [p for p in available_providers if p != current_provider]

        if not remaining_providers:
            # Reset to try all providers again with backoff
            remaining_providers = available_providers

        # Priority order for switching
        priority_order = ['cerebras', 'mistral', 'google', 'groq', 'ollama']

        # Try providers in priority order
        for provider_id in priority_order:
            if provider_id in remaining_providers:
                return provider_id

        # Fallback to first remaining provider
        return remaining_providers[0] if remaining_providers else None

    def stop_batch(self, batch_id: Optional[str] = None):
        """
        Stop batch generation(s).
        Handles both in-memory batches and database-only stuck batches.

        Args:
            batch_id: Specific batch to stop, or None to stop all

        Returns:
            Dict with stop status
        """
        stopped_batches = []

        with self.batch_lock:
            if batch_id:
                # Stop specific batch - check in-memory first
                if batch_id in self.active_batches:
                    batch_state = self.active_batches[batch_id]
                    if batch_state['running']:
                        batch_state['running'] = False
                        batch_state['completed_at'] = datetime.now().isoformat()
                        stopped_batches.append(batch_id)
                        # Save to database
                        self._save_batch_to_db(batch_state)
                else:
                    # Not in memory - check database for stuck batch
                    from flask import current_app
                    with current_app.app_context():
                        db_batch = BatchHistory.query.filter_by(batch_id=batch_id).first()
                        if db_batch and db_batch.status == 'running':
                            # Found stuck batch in database - stop it
                            db_batch.status = 'stopped'
                            db_batch.completed_at = datetime.now().isoformat()
                            db.session.commit()
                            stopped_batches.append(batch_id)
                            print(f"✅ Stopped stuck batch {batch_id} from database (not in memory)")
                        else:
                            return {'success': False, 'error': f'Batch {batch_id} not found or already stopped'}
            else:
                # Stop all running batches (in-memory)
                for bid, batch_state in self.active_batches.items():
                    if batch_state.get('running', False):
                        batch_state['running'] = False
                        batch_state['completed_at'] = datetime.now().isoformat()
                        stopped_batches.append(bid)
                        # Save to database
                        self._save_batch_to_db(batch_state)

        if len(stopped_batches) > 0:
            return {'success': True, 'stopped_batches': stopped_batches, 'count': len(stopped_batches)}
        else:
            return {'success': False, 'error': 'Batch not found or already stopped'}

    def get_batch_status(self, batch_id: Optional[str] = None):
        """Get status of specific batch or all batches."""
        with self.batch_lock:
            if batch_id:
                return self.active_batches.get(batch_id)
            else:
                return {
                    'batches': self.active_batches,
                    'count': len(self.active_batches)
                }

    def _batch_worker(self, batch_id: str, target_count: int, provider: str, model: str, app):
        """
        Background worker for batch generation.
        This is the main batch generation loop extracted from api_server.py.

        Args:
            batch_id: Unique batch identifier
            target_count: Target total sample count
            provider: LLM provider name
            model: Model name
            app: Flask app instance for app_context

        NOTE: This is a simplified version. Full implementation should include:
        - Complete error handling and model switching logic
        - Provider failover
        - Rate limiting with proper tracking
        - All the logic from api_server.py lines 376-759
        """
        # Wrap entire worker in try-except to catch and log any errors
        try:
            # Run within Flask application context for database access
            with app.app_context():
                # SSE broadcast is handled by the routes layer, not here
                # We just update the batch state which routes can poll

                with self.batch_lock:
                    if batch_id not in self.active_batches:
                        print(f"❌ Batch {batch_id} not found in active_batches")
                        return
                    batch_state = self.active_batches[batch_id]

                # Get rate limits from database
                rate_limits = LLMProviderFactory.get_rate_limits(provider, use_db=True)
                requests_per_minute = rate_limits['requests_per_minute']
                request_delay = 60 / requests_per_minute

                # Initialize circuit breaker
                circuit_breaker = CircuitBreaker()

                # Load existing dataset from database (not parquet)
                data_service = DataService()
                current_count = data_service.count()
                samples_needed = target_count - current_count

                # Get filters
                topic_filter = batch_state.get('topic_filter')
                difficulty_filter = batch_state.get('difficulty_filter')
                reasoning_instruction = batch_state.get('reasoning_instruction')
                sample_type_filter = batch_state.get('sample_type_filter', 'case_analysis')

                # Prepare topic cycle
                if topic_filter:
                    filtered_topics = [t for t in TOPICS if f"{t[0]} - {t[1]}" == topic_filter]
                    if not filtered_topics:
                        filtered_topics = TOPICS
                else:
                    filtered_topics = TOPICS

                topic_cycle = filtered_topics * ((samples_needed // len(filtered_topics)) + 10)

                generated_samples = []
                minute_start = time.time()
                minute_requests = 0
                minute_tokens = 0
                batch_start_time = time.time()
                iteration = 0
                max_iterations = samples_needed * 3

                # Main generation loop
                while batch_state['samples_generated'] < samples_needed and iteration < max_iterations:
                    # Check for manual stop
                    if not batch_state['running']:
                        break

                    # Check timeout
                    elapsed_time = time.time() - batch_start_time
                    if elapsed_time > MAX_BATCH_TIMEOUT:
                        batch_state['errors'].append({
                            'error': f"Batch timed out after {int(elapsed_time/60)} minutes",
                            'timeout': True
                        })
                        batch_state['running'] = False
                        break

                    # Get current topic
                    topic_index = iteration % len(topic_cycle)
                    practice_area, topic, original_difficulty = topic_cycle[topic_index]
                    topic_key = f"{practice_area} - {topic}"
                    difficulty = difficulty_filter if difficulty_filter else original_difficulty

                    # Circuit breaker check
                    if circuit_breaker.is_open(topic_key):
                        if topic_key not in batch_state['skipped_topics']:
                            batch_state['skipped_topics'].append(topic_key)
                        iteration += 1
                        continue

                    # Determine sample type
                    if sample_type_filter == 'balance':
                        sample_type_index = iteration % len(SAMPLE_TYPE_CYCLE)
                        current_sample_type = SAMPLE_TYPE_CYCLE[sample_type_index]
                    else:
                        current_sample_type = sample_type_filter

                    # Rate limiting
                    elapsed_minute = time.time() - minute_start
                    if elapsed_minute < 60 and minute_requests >= requests_per_minute:
                        wait_time = 60 - elapsed_minute
                        time.sleep(wait_time)
                        minute_start = time.time()
                        minute_tokens = 0
                        minute_requests = 0
                    elif elapsed_minute >= 60:
                        minute_start = time.time()
                        minute_tokens = 0
                        minute_requests = 0

                    batch_state['current_sample'] = topic_key

                    # Generate sample with retries
                    sample_success = False
                    sample_retries = 0

                    while not sample_success and sample_retries < MAX_SAMPLE_RETRIES:
                        sample, tokens_used, elapsed, error = self.generation_service.generate_single_sample(
                            practice_area, topic, difficulty,
                            current_count + batch_state['samples_generated'] + 1,
                            provider, model, reasoning_instruction, batch_id, current_sample_type
                        )

                        if sample:
                            generated_samples.append(sample)
                            batch_state['samples_generated'] += 1
                            batch_state['total_tokens'] += tokens_used
                            batch_state['consecutive_failures'] = 0
                            minute_tokens += tokens_used
                            minute_requests += 1
                            sample_success = True

                            circuit_breaker.record_success(topic_key)

                            # Auto-save to database every sample
                            if generated_samples:
                                data_service.add_bulk(generated_samples)
                                generated_samples = []
                            batch_state['circuit_breaker_summary'] = circuit_breaker.get_summary()

                            # Broadcast real-time update to SSE subscribers
                            sse_service = get_sse_service()
                            sse_service.broadcast_batch_update(batch_id=batch_id, batch_data=batch_state)

                        else:
                            # Handle failure
                            sample_retries += 1
                            batch_state['consecutive_failures'] += 1
                            circuit_breaker.record_failure(topic_key, error)

                            # Smart provider failover logic
                            if batch_state.get('smart_mode', False):
                                should_switch = self._should_switch_provider(error, provider, batch_state)

                                if should_switch:
                                    # STRATEGY: Try all models on current provider FIRST, then switch providers

                                    # Check if current provider has more untried models
                                    if self._has_more_models(provider, batch_state):
                                        # Try next model on SAME provider
                                        new_model = self._get_next_model_for_provider(provider, batch_state)

                                        if new_model:
                                            model = new_model
                                            batch_state['current_model'] = model
                                            batch_state['model_switches'].append({
                                                'from': batch_state.get('last_model', model),
                                                'to': model,
                                                'provider': provider,
                                                'reason': error,
                                                'at_sample': batch_state['samples_generated']
                                            })
                                            batch_state['last_model'] = model

                                            # Reset failure counters
                                            batch_state['consecutive_failures'] = 0
                                            sample_retries = 0

                                            print(f"✅ Switched to next model on {provider}: {model}")
                                            continue  # Try with new model immediately

                                    # All models exhausted on current provider - switch to next provider
                                    print(f"⚠️  All models tried on {provider}, switching providers...")
                                    new_provider = self._switch_to_next_provider(provider, batch_state)

                                    # Check if all providers are exhausted
                                    if new_provider is None:
                                        print(f"🛑 All providers exhausted - stopping batch")
                                        batch_state['running'] = False
                                        batch_state['completed_at'] = datetime.now().isoformat()
                                        batch_state['errors'].append({
                                            'error': 'All providers and models exhausted',
                                            'provider_failures': batch_state.get('provider_failures', {}),
                                            'timestamp': datetime.now().isoformat()
                                        })
                                        # Save to database
                                        self._save_batch_to_db(batch_state)

                                        # Broadcast error state to SSE subscribers
                                        sse_service = get_sse_service()
                                        sse_service.broadcast_batch_update(batch_id=batch_id, batch_data=batch_state)

                                        break  # Exit the sample generation loop

                                    if new_provider != provider:
                                        print(f"🔄 Provider failover: {provider} → {new_provider} (reason: {error})")
                                        provider = new_provider

                                        # Get first model for new provider
                                        model = self._get_next_model_for_provider(provider, batch_state)

                                        if model is None:
                                            # Shouldn't happen, but handle gracefully
                                            print(f"❌ No models available for {provider}")
                                            continue

                                        # Update batch state
                                        batch_state['current_provider'] = provider
                                        batch_state['current_model'] = model
                                        batch_state['provider_switches'].append({
                                            'from': batch_state.get('last_provider', provider),
                                            'to': provider,
                                            'reason': error,
                                            'at_sample': batch_state['samples_generated']
                                        })
                                        batch_state['last_provider'] = provider

                                        # Get new rate limits for new provider from database
                                        rate_limits = LLMProviderFactory.get_rate_limits(provider, use_db=True)
                                        requests_per_minute = rate_limits['requests_per_minute']
                                        request_delay = 60 / requests_per_minute

                                        # Reset minute tracking
                                        minute_start = time.time()
                                        minute_requests = 0
                                        minute_tokens = 0

                                        # Reset failure counters after successful switch
                                        batch_state['consecutive_failures'] = 0
                                        sample_retries = 0  # Reset retries to try with new provider

                                        print(f"✅ Switched to {provider}/{model} (rate limit: {requests_per_minute} req/min)")

                                        # Break retry loop to use new provider immediately
                                        continue

                            if sample_retries < MAX_SAMPLE_RETRIES:
                                time.sleep(2)

                    iteration += 1
                    batch_state['progress'] = iteration

                    if batch_state['samples_generated'] % 10 == 0:
                        self._save_batch_to_db(batch_state)

                    time.sleep(request_delay)

                # Final save (after loop completes)
                if generated_samples:
                    data_service.add_bulk(generated_samples)

                batch_state['completed_at'] = datetime.now().isoformat()
                batch_state['running'] = False
                batch_state['circuit_breaker_summary'] = circuit_breaker.get_summary()

                self._save_batch_to_db(batch_state)

                # Broadcast final completion update to SSE subscribers
                sse_service = get_sse_service()
                sse_service.broadcast_batch_update(batch_id=batch_id, batch_data=batch_state)

        except Exception as e:
            # Catch and log any unhandled exceptions
            import traceback
            error_msg = f"Batch worker crashed: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"❌ {error_msg}")
            print(error_trace)

            # Save error to batch state (needs app context for DB access)
            with app.app_context():
                with self.batch_lock:
                    if batch_id in self.active_batches:
                        batch_state = self.active_batches[batch_id]
                        batch_state['running'] = False
                        batch_state['completed_at'] = datetime.now().isoformat()
                        batch_state['errors'].append({
                            'error': error_msg,
                            'traceback': error_trace,
                            'timestamp': datetime.now().isoformat()
                        })
                        self._save_batch_to_db(batch_state)

    def get_batch(self, batch_id: str) -> Optional[Dict]:
        """Get specific batch status."""
        with self.batch_lock:
            return self.active_batches.get(batch_id)

    def get_running_batches(self) -> Dict:
        """Get all running batches."""
        with self.batch_lock:
            running = {
                bid: batch
                for bid, batch in self.active_batches.items()
                if batch.get('running', False)
            }
            return running

    def get_all_batches(self) -> Dict:
        """Get all active batches."""
        with self.batch_lock:
            return self.active_batches.copy()

    def stop_all_batches(self) -> Dict:
        """Stop all running batches."""
        stopped_batch_ids = []
        stopped_batch_states = []

        with self.batch_lock:
            running_batch_ids = [
                bid for bid, batch in self.active_batches.items()
                if batch.get('running', False)
            ]

            for bid in running_batch_ids:
                batch_state = self.active_batches[bid]
                batch_state['running'] = False
                batch_state['completed_at'] = datetime.now().isoformat()
                stopped_batch_ids.append(bid)
                stopped_batch_states.append(batch_state)

        # Save all stopped batches to database
        for batch_state in stopped_batch_states:
            try:
                self._save_batch_to_db(batch_state)
            except Exception as e:
                print(f"Warning: Failed to save batch {batch_state.get('batch_id')} to database: {e}")

        if len(stopped_batch_ids) > 0:
            return {
                'success': True,
                'message': f'Stopped {len(stopped_batch_ids)} batch(es)',
                'stopped_batch_ids': stopped_batch_ids
            }

        # Check for stuck batches in database
        from flask import current_app
        with current_app.app_context():
            stuck_batches = BatchHistory.query.filter_by(status='running').all()
            if stuck_batches:
                for batch in stuck_batches:
                    batch.status = 'stopped'
                    batch.completed_at = datetime.now().isoformat()
                db.session.commit()
                return {
                    'success': True,
                    'message': f'Stopped {len(stuck_batches)} stuck batch(es) from database'
                }

        return {
            'success': False,
            'error': 'No batch generation running'
        }

    def get_batch_history(self) -> List[Dict]:
        """Get all batch generation history from database."""
        from flask import current_app

        with current_app.app_context():
            batches = BatchHistory.query.order_by(BatchHistory.started_at.desc()).all()
            batch_list = [batch.to_dict() for batch in batches]

            # Merge live state from active batches
            with self.batch_lock:
                for batch_id, batch_state in self.active_batches.items():
                    if batch_state.get('running'):
                        # Find and update or add
                        found = False
                        for i, batch in enumerate(batch_list):
                            if batch['id'] == batch_id:
                                # Update with live data
                                batch_list[i].update({
                                    'samples_generated': batch_state.get('samples_generated', 0),
                                    'tokens_used': batch_state.get('total_tokens', 0),
                                    'status': 'running',
                                    'errors': batch_state.get('errors', []),
                                    'model_switches': batch_state.get('model_switches', []),
                                    'provider_switches': batch_state.get('provider_switches', []),
                                    'model': batch_state.get('current_model'),
                                    'provider': batch_state.get('current_provider'),
                                    'progress': batch_state.get('progress', 0),
                                    'current_sample': batch_state.get('current_sample')
                                })
                                found = True
                                break

                        if not found:
                            batch_list.insert(0, {
                                'id': batch_id,
                                'started_at': batch_state['started_at'],
                                'completed_at': None,
                                'model': batch_state.get('current_model'),
                                'provider': batch_state.get('current_provider'),
                                'topic_filter': batch_state.get('topic_filter'),
                                'difficulty_filter': batch_state.get('difficulty_filter'),
                                'target': batch_state.get('total', 0),
                                'samples_generated': batch_state.get('samples_generated', 0),
                                'tokens_used': batch_state.get('total_tokens', 0),
                                'status': 'running',
                                'errors': batch_state.get('errors', []),
                                'model_switches': batch_state.get('model_switches', []),
                                'progress': batch_state.get('progress', 0),
                                'current_sample': batch_state.get('current_sample')
                            })

            return batch_list

    def check_stuck_batches(self) -> Dict:
        """Detect stuck batches (disabled zombie detection - only checks truly stuck batches)."""
        from flask import current_app

        stuck_threshold_minutes = 60  # Increased threshold to 1 hour
        now = datetime.now()

        with current_app.app_context():
            running_batches = BatchHistory.query.filter_by(status='running').all()

            stuck_batches = []
            stopped_batches = []

            for batch in running_batches:
                try:
                    # Skip zombie detection - only check batches that are in memory and actively running
                    if batch.batch_id not in self.active_batches:
                        continue  # Skip zombie batches - let them run

                    started_at = datetime.fromisoformat(batch.started_at)
                    time_elapsed = (now - started_at).total_seconds() / 60

                    # Only detect truly stuck batches (running for very long with no progress)
                    is_stuck = (
                        (time_elapsed > stuck_threshold_minutes and batch.samples_generated == 0) or
                        (time_elapsed > 120)  # 2 hours absolute timeout
                    )

                    if is_stuck:
                        stuck_info = {
                            'batch_id': batch.batch_id,
                            'started_at': batch.started_at,
                            'elapsed_minutes': round(time_elapsed, 1),
                            'samples_generated': batch.samples_generated,
                            'target': batch.target_count,
                            'model': batch.model
                        }
                        stuck_batches.append(stuck_info)

                        # Stop the batch
                        with self.batch_lock:
                            if batch.batch_id in self.active_batches:
                                batch_state = self.active_batches[batch.batch_id]
                                batch_state['running'] = False
                                batch_state['completed_at'] = datetime.now().isoformat()
                                batch_state['errors'].append({
                                    'error': f'Automatically stopped: stuck for {round(time_elapsed, 1)} minutes',
                                    'auto_stopped': True
                                })

                        # Update database
                        batch.status = 'stopped'
                        batch.completed_at = datetime.now().isoformat()
                        db.session.commit()

                        stopped_batches.append(stuck_info)
                        print(f"🛑 Auto-stopped stuck batch {batch.batch_id} (running {round(time_elapsed, 1)} min)")

                except Exception as e:
                    print(f"Error checking batch {batch.batch_id}: {str(e)}")
                    continue

            message = f'Automatically stopped {len(stopped_batches)} stuck batch(es)' if stopped_batches else 'No stuck batches found'

            return {
                'success': True,
                'stuck_batches': stuck_batches,
                'stopped_batches': stopped_batches,
                'count': len(stuck_batches),
                'stopped_count': len(stopped_batches),
                'threshold_minutes': stuck_threshold_minutes,
                'message': message
            }

    def _save_batch_to_db(self, batch_state: Dict):
        """Save batch state to database."""
        import json
        from flask import current_app

        try:
            batch_id = batch_state.get('batch_id')
            if not batch_id:
                return

            with current_app.app_context():
                batch = BatchHistory.query.filter_by(batch_id=batch_id).first()

                if batch:
                    # Update existing
                    batch.completed_at = batch_state.get('completed_at')
                    batch.samples_generated = batch_state.get('samples_generated', 0)
                    batch.total_tokens = batch_state.get('total_tokens', 0)
                    batch.status = 'running' if batch_state.get('running') else 'completed'
                    batch.errors = json.dumps(batch_state.get('errors', []))
                    batch.model_switches = json.dumps(batch_state.get('model_switches', []))
                    batch.model = batch_state.get('current_model', batch.model)
                else:
                    # Create new
                    batch = BatchHistory(
                        batch_id=batch_id,
                        started_at=batch_state['started_at'],
                        model=batch_state.get('current_model'),
                        topic_filter=batch_state.get('topic_filter'),
                        difficulty_filter=batch_state.get('difficulty_filter'),
                        reasoning_instruction=batch_state.get('reasoning_instruction'),
                        target_count=batch_state.get('total', 0),
                        samples_generated=batch_state.get('samples_generated', 0),
                        total_tokens=batch_state.get('total_tokens', 0),
                        status='running' if batch_state.get('running') else 'stopped',
                        errors=json.dumps(batch_state.get('errors', [])),
                        model_switches=json.dumps(batch_state.get('model_switches', []))
                    )
                    db.session.add(batch)

                db.session.commit()
        except Exception as e:
            print(f"Error saving batch to database: {str(e)}")
            db.session.rollback()
