from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import polars as pl
from groq import Groq
import json
import time
import threading
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import queue
import uuid
import tiktoken

# Import modular services and utilities
from services.generation_service import GenerationService
from services.llm_service import LLMProviderFactory
from utils.error_handler import categorize_error, should_switch_immediately
from utils.circuit_breaker import CircuitBreaker
from config import (
    MAX_BATCH_TIMEOUT,
    MAX_MODEL_SWITCHES,
    PROVIDERS,
    MODEL_FALLBACK_ORDER,
    CEREBRAS_FALLBACK_ORDER,
    MAX_SAMPLE_RETRIES,
    SAMPLE_TYPE_CYCLE
)

app = Flask(__name__)
CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///batches.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuration
PARQUET_PATH = Path("train.parquet")

# Legacy compatibility (for older code that still references these)
API_KEY = PROVIDERS['groq']['api_key']
DEFAULT_MODEL = PROVIDERS['groq']['default_model']
REQUESTS_PER_MINUTE = PROVIDERS['groq']['requests_per_minute']
TOKENS_PER_MINUTE = PROVIDERS['groq']['tokens_per_minute']
REQUEST_DELAY = 60 / REQUESTS_PER_MINUTE if REQUESTS_PER_MINUTE > 0 else 2.4

# Removed duplicate CircuitBreaker class - now imported from utils.circuit_breaker
# Removed duplicate LLMProviderFactory class - now imported from services.llm_service
# Removed duplicate categorize_error function - now imported from utils.error_handler

# UK Legal topics
TOPICS = [
    ("Contract Law", "Formation of Contracts", "intermediate"),
    ("Contract Law", "Breach of Contract", "intermediate"),
    ("Contract Law", "Remedies for Breach", "advanced"),
    ("Contract Law", "Terms and Conditions", "basic"),
    ("Contract Law", "Misrepresentation", "advanced"),
    ("Tort Law", "Professional Negligence", "advanced"),
    ("Tort Law", "Occupiers Liability", "intermediate"),
    ("Tort Law", "Vicarious Liability", "intermediate"),
    ("Tort Law", "Defamation", "advanced"),
    ("Tort Law", "Nuisance", "intermediate"),
    ("Company Law", "Directors Duties", "advanced"),
    ("Company Law", "Shareholder Rights", "intermediate"),
    ("Company Law", "Corporate Governance", "advanced"),
    ("Company Law", "Insolvency", "expert"),
    ("Company Law", "Company Formation", "basic"),
    ("Employment Law", "Discrimination", "intermediate"),
    ("Employment Law", "Wrongful Dismissal", "advanced"),
    ("Employment Law", "Employment Contracts", "basic"),
    ("Employment Law", "TUPE", "advanced"),
    ("Employment Law", "Redundancy", "intermediate"),
    ("Property Law", "Leasehold vs Freehold", "basic"),
    ("Property Law", "Land Registration", "intermediate"),
    ("Property Law", "Easements and Covenants", "advanced"),
    ("Property Law", "Mortgages", "intermediate"),
    ("Criminal Law", "Actus Reus and Mens Rea", "basic"),
    ("Criminal Law", "Murder and Manslaughter", "intermediate"),
    ("Criminal Law", "Criminal Defenses", "advanced"),
    ("Criminal Law", "Fraud", "advanced"),
    ("Trusts Law", "Constructive Trusts", "advanced"),
    ("Trusts Law", "Charitable Trusts", "intermediate"),
    ("Trusts Law", "Breach of Trust", "advanced"),
    ("Family Law", "Divorce Proceedings", "intermediate"),
    ("Family Law", "Child Custody", "intermediate"),
    ("Family Law", "Financial Settlements", "advanced"),
    ("Tax Law", "Capital Gains Tax", "advanced"),
    ("Tax Law", "VAT", "intermediate"),
    ("Tax Law", "Income Tax", "intermediate"),
    ("Administrative Law", "Judicial Review", "advanced"),
    ("Administrative Law", "Public Law Remedies", "expert"),
    ("Legal Ethics", "Conflicts of Interest", "intermediate"),
    ("Legal Ethics", "Client Confidentiality", "basic"),
    ("Legal Ethics", "Money Laundering", "advanced"),
]

# Batch generation state - supports multiple concurrent batches
# Dictionary mapping batch_id -> batch state
active_batches = {}
batch_lock = threading.Lock()
parquet_lock = threading.Lock()  # Thread-safe parquet file writes

def create_batch_state(batch_id, provider, model, total=0):
    """Create a new batch state object"""
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

# Database Model for Batch History
class BatchHistory(db.Model):
    __tablename__ = 'batch_history'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(100), unique=True, nullable=False)
    started_at = db.Column(db.String(50), nullable=False)
    completed_at = db.Column(db.String(50))
    model = db.Column(db.String(100))
    topic_filter = db.Column(db.String(200))
    difficulty_filter = db.Column(db.String(50))
    reasoning_instruction = db.Column(db.Text)
    target_count = db.Column(db.Integer)
    samples_generated = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20))  # running, completed, stopped
    errors = db.Column(db.Text)  # JSON string
    model_switches = db.Column(db.Text)  # JSON string tracking model switches

    def to_dict(self):
        return {
            'id': self.batch_id,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'model': self.model,
            'topic_filter': self.topic_filter,
            'difficulty_filter': self.difficulty_filter,
            'reasoning_instruction': self.reasoning_instruction,
            'target': self.target_count,
            'samples_generated': self.samples_generated,
            'tokens_used': self.total_tokens,
            'status': self.status,
            'errors': json.loads(self.errors) if self.errors else [],
            'model_switches': json.loads(self.model_switches) if self.model_switches else []
        }

# Create database tables
with app.app_context():
    db.create_all()

# SSE subscribers
sse_subscribers = []

def broadcast_sse_update(batch_id=None):
    """Broadcast batch status to all SSE subscribers"""
    global sse_subscribers

    with batch_lock:
        if batch_id and batch_id in active_batches:
            # Broadcast specific batch update
            data = {'type': 'batch_update', 'batch_id': batch_id, 'batch': active_batches[batch_id]}
        else:
            # Broadcast all active batches
            data = {'type': 'all_batches', 'batches': active_batches}

    message = f"data: {json.dumps(data)}\n\n"

    # Remove disconnected subscribers
    active_subscribers = []
    for subscriber in sse_subscribers:
        try:
            subscriber.put_nowait(message)
            active_subscribers.append(subscriber)
        except:
            pass
    sse_subscribers = active_subscribers

def save_batch_to_db(batch_state):
    """Save or update batch in database"""
    try:
        batch_id = batch_state.get('batch_id')
        if not batch_id:
            print("Warning: No batch_id in batch_state, skipping database save")
            return

        batch = BatchHistory.query.filter_by(batch_id=batch_id).first()

        if batch:
            # Update existing batch
            batch.completed_at = batch_state.get('completed_at')
            batch.samples_generated = batch_state.get('samples_generated', 0)
            batch.total_tokens = batch_state.get('total_tokens', 0)
            batch.status = 'running' if batch_state.get('running') else ('completed' if batch_state.get('completed_at') else 'stopped')
            batch.errors = json.dumps(batch_state.get('errors', []))
            batch.model_switches = json.dumps(batch_state.get('model_switches', []))
            batch.model = batch_state.get('current_model', batch.model)  # Update to current model
        else:
            # Create new batch
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

# Initialize Groq client
groq_client = None

def get_groq_client():
    global groq_client
    if groq_client is None:
        groq_client = Groq(api_key=API_KEY)
    return groq_client

# Model fallback helper functions (kept here as they're specific to batch generation logic)
def get_next_model(current_model: str, failed_models: list, provider: str = 'groq') -> Optional[str]:
    """
    Get next available model from fallback list, excluding failed models.

    Args:
        current_model: The model that just failed
        failed_models: List of models that have already failed
        provider: The provider ('groq', 'cerebras', or 'ollama')

    Returns:
        Next model to try, or None if all models exhausted
    """
    # Select appropriate fallback order based on provider
    if provider == 'cerebras':
        fallback_order = CEREBRAS_FALLBACK_ORDER
    elif provider == 'ollama':
        from config import OLLAMA_FALLBACK_ORDER
        fallback_order = OLLAMA_FALLBACK_ORDER
    else:  # groq or default
        fallback_order = MODEL_FALLBACK_ORDER

    try:
        current_index = fallback_order.index(current_model) if current_model in fallback_order else -1
    except ValueError:
        current_index = -1

    # Try models after the current one
    for i in range(current_index + 1, len(fallback_order)):
        model = fallback_order[i]
        if model not in failed_models:
            return model

    # If we've tried all models after current, try from the beginning
    for model in fallback_order:
        if model != current_model and model not in failed_models:
            return model

    return None  # No models left to try for this provider

def get_next_provider_and_model(current_provider: str, current_model: str,
                                failed_models_by_provider: Dict[str, List[str]]) -> tuple:
    """
    Get next provider/model combination, including cross-provider fallback.

    Args:
        current_provider: The provider that just failed
        current_model: The model that just failed
        failed_models_by_provider: Dict mapping provider -> list of failed models

    Returns:
        Tuple of (next_provider, next_model) or (None, None) if all exhausted
    """
    # Try next model in same provider first
    failed_models = failed_models_by_provider.get(current_provider, [])
    next_model = get_next_model(current_model, failed_models, current_provider)

    if next_model:
        return current_provider, next_model

    # All models in current provider failed, try switching provider
    print(f"⚠️  All {current_provider} models exhausted, attempting cross-provider fallback")

    # Define provider fallback order
    provider_order = ['groq', 'cerebras', 'ollama']

    # Try each provider in order, skipping the current one
    for provider in provider_order:
        if provider == current_provider or not PROVIDERS.get(provider, {}).get('enabled'):
            continue

        # Get failed models for this provider
        provider_failed = failed_models_by_provider.get(provider, [])

        # Get fallback order for this provider
        if provider == 'groq':
            fallback_order = MODEL_FALLBACK_ORDER
        elif provider == 'cerebras':
            fallback_order = CEREBRAS_FALLBACK_ORDER
        elif provider == 'ollama':
            from config import OLLAMA_FALLBACK_ORDER
            fallback_order = OLLAMA_FALLBACK_ORDER
        else:
            continue

        # Try to find an unfailed model
        for model in fallback_order:
            if model not in provider_failed:
                print(f"🔄 Switching to {provider} provider with model {model}")
                return provider, model

    # All providers and models exhausted
    return None, None

# Initialize GenerationService instance (module-level for reuse)
_generation_service = None

def get_generation_service():
    """Get or create GenerationService instance."""
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service

def generate_single_sample(practice_area: str, topic: str, difficulty: str, counter: int, provider: str = 'groq', model: str = None, reasoning_instruction: str = None, batch_id: str = None, sample_type: str = 'case_analysis') -> tuple:
    """
    Generate a single legal Q&A sample using enhanced GenerationService.

    This function delegates to GenerationService which uses:
    - Research-based prompts with IRAC framework
    - Few-shot examples for quality consistency
    - Post-generation quality validation
    - Difficulty-specific requirements
    """
    service = get_generation_service()
    return service.generate_single_sample(
        practice_area=practice_area,
        topic=topic,
        difficulty=difficulty,
        counter=counter,
        provider=provider,
        model=model,
        reasoning_instruction=reasoning_instruction,
        batch_id=batch_id,
        sample_type=sample_type
    )

def batch_generate_worker(batch_id: str, target_count: int, provider: str = 'groq', model: str = None):
    """Background worker for batch generation with circuit breaker protection"""
    with app.app_context():
        try:
            # Get batch state from active_batches
            with batch_lock:
                if batch_id not in active_batches:
                    print(f"❌ Batch {batch_id} not found in active_batches")
                    return
                batch_state = active_batches[batch_id]

            # Validate provider
            if provider not in PROVIDERS:
                with batch_lock:
                    batch_state['errors'].append({'error': f'Invalid provider: {provider}'})
                    batch_state['running'] = False
                broadcast_sse_update(batch_id)
                return

            # Get rate limits for the provider
            rate_limits = LLMProviderFactory.get_rate_limits(provider)
            requests_per_minute = rate_limits['requests_per_minute']
            tokens_per_minute = rate_limits['tokens_per_minute']
            request_delay = 60 / requests_per_minute

            if model is None:
                model = PROVIDERS[provider]['default_model']

            # Initialize circuit breaker for this batch
            circuit_breaker = CircuitBreaker()

            # Load existing dataset
            df_existing = pl.read_parquet(PARQUET_PATH)
            current_count = len(df_existing)
            samples_needed = target_count - current_count

            # Check if target is already met
            if samples_needed <= 0:
                with batch_lock:
                    batch_state.update({
                        'running': False,
                        'completed_at': datetime.now().isoformat(),
                        'total': 0,
                        'progress': 0,
                        'samples_generated': 0,
                        'errors': [{'error': f'Target already met: {current_count} samples exist, target is {target_count}'}]
                    })
                save_batch_to_db(batch_state)
                broadcast_sse_update(batch_id)
                return

            with batch_lock:
                batch_state.update({
                    'total': samples_needed,
                'progress': 0,
                'samples_generated': 0,
                'total_tokens': 0,
                'current_provider': provider,  # Track current provider
                'current_model': model,
                'errors': [],
                'model_switches': [],
                'provider_switches': [],
                'failed_models_by_provider': {provider: []},  # Initialize with current provider
                'consecutive_failures': 0,
                'skipped_topics': [],
                'circuit_breaker_summary': {}
            })

            generated_samples = []
            minute_start = time.time()
            minute_requests = 0
            minute_tokens = 0

            # Apply filters if provided
            topic_filter = batch_state.get('topic_filter')
            difficulty_filter = batch_state.get('difficulty_filter')
            reasoning_instruction = batch_state.get('reasoning_instruction')
            sample_type_filter = batch_state.get('sample_type_filter', 'case_analysis')  # Get sample_type

            # Prepare topic cycle based on filters
            if topic_filter:
                # Find matching topic
                filtered_topics = [t for t in TOPICS if f"{t[0]} - {t[1]}" == topic_filter]
                if not filtered_topics:
                    filtered_topics = TOPICS  # Fallback to all topics
            else:
                filtered_topics = TOPICS

            # Create extended topic cycle to ensure we have enough topics even with skips
            topic_cycle = filtered_topics * ((samples_needed // len(filtered_topics)) + 10)

            # Track batch start time for timeout
            batch_start_time = time.time()

            # Loop until we reach the target sample count
            iteration = 0
            max_iterations = samples_needed * 3  # Safety limit: 3x target to prevent infinite loops

            while batch_state['samples_generated'] < samples_needed and iteration < max_iterations:
                # Check for manual stop
                if not batch_state['running']:
                    break

                # Check for timeout (30 minutes)
                elapsed_time = time.time() - batch_start_time
                if elapsed_time > MAX_BATCH_TIMEOUT:
                    timeout_msg = f"Batch timed out after {int(elapsed_time/60)} minutes (limit: {int(MAX_BATCH_TIMEOUT/60)} minutes)"
                    print(f"⏱️  {timeout_msg}")
                    batch_state['errors'].append({
                        'error': timeout_msg,
                        'timeout': True,
                        'elapsed_seconds': int(elapsed_time)
                    })
                    batch_state['running'] = False
                    break

                # Cycle through topics
                topic_index = iteration % len(topic_cycle)
                practice_area, topic, original_difficulty = topic_cycle[topic_index]
                topic_key = f"{practice_area} - {topic}"

                # Apply difficulty filter if provided
                difficulty = difficulty_filter if difficulty_filter else original_difficulty

                # Circuit breaker check - skip if circuit is open
                if circuit_breaker.is_open(topic_key):
                    print(f"⏭️  Skipping '{topic_key}' (circuit breaker OPEN, {batch_state['samples_generated']}/{samples_needed})")
                    if topic_key not in batch_state['skipped_topics']:
                        batch_state['skipped_topics'].append(topic_key)
                    iteration += 1

                    # Check if all circuits are open (safety check)
                    cb_summary = circuit_breaker.get_summary()
                    if len(cb_summary['open_circuits']) >= len(filtered_topics):
                        print(f"⚠️  WARNING: All topics have open circuit breakers!")
                        print(f"   Generated {batch_state['samples_generated']}/{samples_needed} samples")
                        print(f"   Waiting 60 seconds for circuits to transition to HALF-OPEN...")
                        time.sleep(60)  # Wait for some circuits to transition to half-open
                    continue

                # Rate limiting (provider-specific)
                elapsed_minute = time.time() - minute_start
                if elapsed_minute < 60:
                    if minute_requests >= requests_per_minute or minute_tokens >= tokens_per_minute:
                        wait_time = 60 - elapsed_minute
                        print(f"⏸️  Rate limit reached, waiting {wait_time:.1f}s (requests: {minute_requests}/{requests_per_minute}, tokens: {minute_tokens}/{tokens_per_minute})")
                        time.sleep(wait_time)
                        minute_start = time.time()
                        minute_tokens = 0
                        minute_requests = 0
                else:
                    minute_start = time.time()
                    minute_tokens = 0
                    minute_requests = 0

                batch_state['current_sample'] = topic_key

                # Determine sample_type for this iteration
                if sample_type_filter == 'balance':
                    # Cycle through all sample types for variety
                    sample_type_index = iteration % len(SAMPLE_TYPE_CYCLE)
                    current_sample_type = SAMPLE_TYPE_CYCLE[sample_type_index]
                else:
                    # Use the specified sample_type (or default to case_analysis)
                    current_sample_type = sample_type_filter if sample_type_filter else 'case_analysis'

                # Retry logic for each sample
                sample_success = False
                sample_retries = 0

                while not sample_success and sample_retries < MAX_SAMPLE_RETRIES:
                    sample, tokens_used, elapsed, error = generate_single_sample(
                        practice_area, topic, difficulty, current_count + batch_state['samples_generated'] + 1,
                        provider, model, reasoning_instruction, batch_id, current_sample_type
                    )

                    if sample:
                        generated_samples.append(sample)
                        batch_state['samples_generated'] += 1
                        batch_state['total_tokens'] += tokens_used
                        batch_state['consecutive_failures'] = 0  # Reset consecutive failures
                        minute_tokens += tokens_used
                        minute_requests += 1
                        sample_success = True

                        # Record success in circuit breaker
                        circuit_breaker.record_success(topic_key)

                        # Auto-save after EACH sample (to prevent data loss)
                        # Only include fields that exist in the parquet file (to avoid column mismatch)
                        # Thread-safe write with fresh dataset load
                        with parquet_lock:
                            df_fresh = pl.read_parquet(PARQUET_PATH)
                            existing_columns = df_fresh.columns

                            # Filter samples to only include columns that exist in parquet
                            filtered_samples = [{k: v for k, v in sample.items() if k in existing_columns} for sample in generated_samples]
                            df_new = pl.DataFrame(filtered_samples)

                            df_combined = pl.concat([df_fresh, df_new])
                            df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

                        # Clear generated_samples after save to prevent duplicates
                        generated_samples = []

                        # Update circuit breaker summary
                        batch_state['circuit_breaker_summary'] = circuit_breaker.get_summary()
                        broadcast_sse_update(batch_id)
                    else:
                        # Sample generation failed
                        sample_retries += 1
                        batch_state['consecutive_failures'] += 1

                        # Record failure in circuit breaker
                        circuit_opened = circuit_breaker.record_failure(topic_key, error)

                        # Check if we should switch models/providers
                        should_switch = False
                        error_category = categorize_error(error, provider) if error else "general"

                        # Immediate switch for critical errors
                        if error_category in ['model_unavailable', 'rate_limit', 'timeout',
                                             'connection_error', 'server_error']:
                            should_switch = True
                            print(f"⚠️ {error_category.upper()} detected, switching model/provider")

                            # Track failed model for this provider
                            if provider not in batch_state['failed_models_by_provider']:
                                batch_state['failed_models_by_provider'][provider] = []
                            if model not in batch_state['failed_models_by_provider'][provider]:
                                batch_state['failed_models_by_provider'][provider].append(model)

                        # Switch after 3 consecutive failures (reduced from 5)
                        elif batch_state['consecutive_failures'] >= 3:
                            should_switch = True
                            print(f"⚠️ 3 consecutive failures, switching model/provider")

                        if should_switch and len(batch_state['model_switches']) < MAX_MODEL_SWITCHES:
                            # Try to get next provider/model combination
                            next_provider, next_model = get_next_provider_and_model(
                                provider,
                                model,
                                batch_state['failed_models_by_provider']
                            )

                            if next_provider and next_model:
                                # Check if we're switching providers
                                if next_provider != provider:
                                    # Record provider switch
                                    provider_switch_record = {
                                        'from_provider': provider,
                                        'to_provider': next_provider,
                                        'from_model': model,
                                        'to_model': next_model,
                                        'reason': error if error else f'Consecutive failures: {batch_state["consecutive_failures"]}',
                                        'timestamp': datetime.now().isoformat(),
                                        'samples_generated': batch_state['samples_generated']
                                    }
                                    batch_state['provider_switches'].append(provider_switch_record)
                                    print(f"🔄 PROVIDER SWITCH: {provider} → {next_provider}")
                                    print(f"   Model: {model} → {next_model}")
                                    print(f"   Reason: {provider_switch_record['reason'][:100]}")

                                    # Update provider and model
                                    provider = next_provider
                                    model = next_model
                                    batch_state['current_provider'] = next_provider
                                    batch_state['current_model'] = next_model

                                    # Update rate limits for new provider
                                    rate_limits = LLMProviderFactory.get_rate_limits(next_provider)
                                    requests_per_minute = rate_limits['requests_per_minute']
                                    tokens_per_minute = rate_limits['tokens_per_minute']
                                    request_delay = 60 / requests_per_minute

                                else:
                                    # Just switching model within same provider
                                    switch_record = {
                                        'from_model': model,
                                        'to_model': next_model,
                                        'provider': provider,
                                        'reason': error if error else f'Consecutive failures: {batch_state["consecutive_failures"]}',
                                        'timestamp': datetime.now().isoformat(),
                                        'samples_generated': batch_state['samples_generated']
                                    }
                                    batch_state['model_switches'].append(switch_record)
                                    print(f"🔄 Model switch ({provider}): {model} → {next_model}")
                                    print(f"   Reason: {switch_record['reason'][:100]}")

                                    model = next_model
                                    batch_state['current_model'] = next_model

                                # Reset consecutive failures
                                batch_state['consecutive_failures'] = 0

                                # Save switch to database
                                save_batch_to_db(batch_state)
                                broadcast_sse_update(batch_id)
                                break  # Exit retry loop to use new model/provider
                            else:
                                # All providers and models exhausted
                                error_msg = "All providers and models exhausted, cannot continue generation"
                                batch_state['errors'].append({
                                    'topic': f"{practice_area} - {topic}",
                                    'error': error_msg,
                                    'fatal': True
                                })
                                batch_state['running'] = False
                                print(f"❌ {error_msg}")
                                break

                        # If circuit breaker opened, skip remaining retries and move on
                        if circuit_opened:
                            batch_state['errors'].append({
                                'topic': topic_key,
                                'error': error,
                                'model': model,
                                'retries': sample_retries,
                                'circuit_breaker': 'opened'
                            })
                            print(f"⏭️  Moving to next topic (circuit breaker triggered)")
                            break  # Exit retry loop, move to next sample

                        # If not switching models, record the error
                        if sample_retries >= MAX_SAMPLE_RETRIES:
                            batch_state['errors'].append({
                                'topic': topic_key,
                                'error': error,
                                'model': model,
                                'retries': sample_retries
                            })

                        # Wait a bit before retrying
                        if sample_retries < MAX_SAMPLE_RETRIES:
                            time.sleep(2)  # Short delay before retry

                # Increment iteration counter
                iteration += 1

                # Update progress based on iterations
                batch_state['progress'] = iteration
                broadcast_sse_update(batch_id)  # Notify SSE subscribers

                # Save to database every 10 successful samples
                if batch_state['samples_generated'] % 10 == 0 and batch_state['samples_generated'] > 0:
                    save_batch_to_db(batch_state)

                time.sleep(request_delay)

            # Final save (if any remaining samples not yet saved)
            if generated_samples:
                # Only include fields that exist in the parquet file (to avoid column mismatch)
                # Thread-safe write with fresh dataset load
                with parquet_lock:
                    df_fresh = pl.read_parquet(PARQUET_PATH)
                    existing_columns = df_fresh.columns

                    # Filter samples to only include columns that exist in parquet
                    filtered_samples = [{k: v for k, v in sample.items() if k in existing_columns} for sample in generated_samples]
                    df_new = pl.DataFrame(filtered_samples)

                    df_combined = pl.concat([df_fresh, df_new])
                    df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

            # Get final circuit breaker summary
            cb_summary = circuit_breaker.get_summary()
            batch_state['circuit_breaker_summary'] = cb_summary

            # Log circuit breaker status
            if cb_summary['open_circuits']:
                print(f"\n⛔ Circuit Breaker Summary:")
                print(f"   Open circuits: {len(cb_summary['open_circuits'])}")
                for circuit in cb_summary['open_circuits']:
                    print(f"   - {circuit['topic']}: {circuit['failures']} failures, open for {circuit['opened_for_seconds']}s")
            if batch_state['skipped_topics']:
                print(f"   Total topics skipped: {len(batch_state['skipped_topics'])}")

            batch_state['completed_at'] = datetime.now().isoformat()
            batch_state['running'] = False

            # Save final state to database
            save_batch_to_db(batch_state)

            # Final broadcast with circuit breaker stats - include batch completion notification
            broadcast_sse_update(batch_id)

        except Exception as e:
            with batch_lock:
                batch_state['errors'].append({'error': f"Worker error: {str(e)}"})
                batch_state['running'] = False
            save_batch_to_db(batch_state)
            broadcast_sse_update(batch_id)

@app.route('/api/data')
def get_data():
    """Get all samples from the dataset"""
    df = pl.read_parquet(PARQUET_PATH)
    return jsonify(df.to_dicts())

@app.route('/api/stats')
def get_stats():
    """Get dataset statistics"""
    df = pl.read_parquet(PARQUET_PATH)

    # Calculate statistics
    difficulty_counts = df.group_by("difficulty").len().to_dicts()
    topic_counts = df.group_by("topic").len().sort("len", descending=True).limit(10).to_dicts()

    return jsonify({
        'total': len(df),
        'columns': df.columns,
        'difficulty_distribution': difficulty_counts,
        'top_topics': topic_counts,
        'file_size_kb': PARQUET_PATH.stat().st_size / 1024 if PARQUET_PATH.exists() else 0
    })

@app.route('/api/generate', methods=['POST'])
def generate_sample():
    """Generate a single new sample using specified provider"""
    try:
        data = request.json
        practice_area = data.get('practice_area', 'Contract Law')
        topic = data.get('topic', 'Formation of Contracts')
        difficulty = data.get('difficulty', 'intermediate')
        provider = data.get('provider', 'groq')
        model = data.get('model')  # Will use provider default if not specified
        sample_type = data.get('sample_type', 'case_analysis')  # Default to case_analysis

        # Validate provider
        if provider not in PROVIDERS:
            return jsonify({
                'success': False,
                'error': f'Invalid provider: {provider}. Available: {", ".join(PROVIDERS.keys())}'
            }), 400

        # Use provider's default model if not specified
        if not model:
            model = PROVIDERS[provider]['default_model']

        # Handle "balance" sample_type - randomly select one of the 4 types for single sample
        if sample_type == 'balance':
            import random
            sample_type = random.choice(SAMPLE_TYPE_CYCLE)

        # Get current count for ID generation
        df = pl.read_parquet(PARQUET_PATH)
        counter = len(df) + 1

        sample, tokens_used, elapsed, error = generate_single_sample(
            practice_area, topic, difficulty, counter, provider, model, None, None, sample_type
        )

        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400

        return jsonify({
            'success': True,
            'sample': sample,
            'tokens_used': tokens_used,
            'elapsed': elapsed
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/batch/start', methods=['POST'])
def start_batch_generation():
    """Start batch generation in background - supports multiple concurrent batches"""
    try:
        data = request.json
        target_count = data.get('target_count', 2100)
        provider = data.get('provider', 'groq')
        model = data.get('model')
        topic_filter = data.get('topic')
        difficulty_filter = data.get('difficulty')
        reasoning_instruction = data.get('reasoning_instruction')
        sample_type_filter = data.get('sample_type', 'case_analysis')  # Extract sample_type

        # Validate provider
        if provider not in PROVIDERS:
            return jsonify({
                'success': False,
                'error': f'Invalid provider: {provider}. Available: {", ".join(PROVIDERS.keys())}'
            }), 400

        if not PROVIDERS[provider]['enabled']:
            return jsonify({
                'success': False,
                'error': f'Provider {provider} is not enabled'
            }), 400

        # Use provider's default model if not specified
        if not model:
            model = PROVIDERS[provider]['default_model']

        # Validate target count against current dataset
        df = pl.read_parquet(PARQUET_PATH)
        current_count = len(df)

        if target_count <= current_count:
            return jsonify({
                'success': False,
                'error': f'Target count ({target_count}) must be greater than current samples ({current_count}). Please increase the target count.'
            }), 400

        # Generate unique batch ID
        batch_id = f"batch_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        # Create new batch state in active_batches
        with batch_lock:
            batch_state = create_batch_state(batch_id, provider, model, target_count - current_count)
            batch_state.update({
                'topic_filter': topic_filter,
                'difficulty_filter': difficulty_filter,
                'reasoning_instruction': reasoning_instruction,
                'sample_type_filter': sample_type_filter  # Store sample_type
            })
            active_batches[batch_id] = batch_state

        # Save initial batch to database
        save_batch_to_db(batch_state)

        # Broadcast batch start notification
        broadcast_sse_update(batch_id)

        # Start background thread with batch_id
        thread = threading.Thread(target=batch_generate_worker, args=(batch_id, target_count, provider, model))
        thread.daemon = True
        thread.start()

        print(f"🚀 Started batch {batch_id} with {provider}/{model}, targeting {target_count} total samples")

        return jsonify({
            'success': True,
            'message': f'Batch generation started with {provider}/{model}, targeting {target_count} total samples',
            'batch_id': batch_id,
            'provider': provider,
            'model': model
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/batch/stop', methods=['POST'])
def stop_batch_generation():
    """Stop batch generation - supports stopping specific batch by ID or all batches"""
    try:
        data = request.json or {}
        batch_id = data.get('batch_id')  # Optional: stop specific batch

        stopped_count = 0

        # If batch_id provided, stop specific batch
        if batch_id:
            with batch_lock:
                if batch_id in active_batches:
                    batch_state = active_batches[batch_id]
                    if batch_state['running']:
                        batch_state['running'] = False
                        batch_state['completed_at'] = datetime.now().isoformat()
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Batch {batch_id} is not running'
                        }), 400
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Batch {batch_id} not found'
                    }), 404

            # Save to database immediately (outside lock to avoid deadlock)
            try:
                save_batch_to_db(batch_state)
            except Exception as e:
                print(f"Warning: Failed to save batch {batch_id} to database: {e}")

            # Broadcast SSE update outside lock to notify frontend immediately
            broadcast_sse_update(batch_id)
            return jsonify({
                'success': True,
                'message': f'Batch {batch_id} stopped',
                'batch_id': batch_id
            })

        # If no batch_id provided, stop all running batches
        stopped_batch_ids = []
        stopped_batch_states = []
        with batch_lock:
            running_batch_ids = [
                bid for bid, batch in active_batches.items()
                if batch.get('running', False)
            ]

            for bid in running_batch_ids:
                batch_state = active_batches[bid]
                batch_state['running'] = False
                batch_state['completed_at'] = datetime.now().isoformat()
                stopped_batch_ids.append(bid)
                stopped_batch_states.append(batch_state)
                stopped_count += 1

        # Save all stopped batches to database (outside lock to avoid deadlock)
        for batch_state in stopped_batch_states:
            try:
                save_batch_to_db(batch_state)
            except Exception as e:
                print(f"Warning: Failed to save batch {batch_state.get('batch_id')} to database: {e}")

        # Broadcast SSE updates outside lock
        for bid in stopped_batch_ids:
            broadcast_sse_update(bid)

        if stopped_count > 0:
            return jsonify({
                'success': True,
                'message': f'Stopped {stopped_count} batch(es)',
                'stopped_batch_ids': stopped_batch_ids
            })

        # If no running batches in memory, check for stuck batches in database
        with app.app_context():
            stuck_batches = BatchHistory.query.filter_by(status='running').all()
            if stuck_batches:
                # Mark all stuck batches as stopped
                for batch in stuck_batches:
                    batch.status = 'stopped'
                    batch.completed_at = datetime.now().isoformat()
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Stopped {len(stuck_batches)} stuck batch(es) from database'
                })

        return jsonify({
            'success': False,
            'error': 'No batch generation running'
        }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/batch/status')
def batch_generation_status():
    """Get batch generation status - all batches or specific batch"""
    batch_id = request.args.get('batch_id')

    with batch_lock:
        if batch_id:
            # Return specific batch
            batch = active_batches.get(batch_id)
            if not batch:
                return jsonify({
                    'success': False,
                    'error': f'Batch {batch_id} not found'
                }), 404
            return jsonify(batch)
        else:
            # Return all active batches
            return jsonify({
                'batches': active_batches,
                'count': len(active_batches)
            })

@app.route('/api/generate/batch/history')
def get_batch_history():
    """Get all batch generation history from database, including currently running batches"""
    try:
        batches = BatchHistory.query.order_by(BatchHistory.started_at.desc()).all()
        batch_list = [batch.to_dict() for batch in batches]

        # Merge live state from all active batches
        with batch_lock:
            for batch_id, batch_state in active_batches.items():
                if batch_state.get('running'):
                    # Find the batch in the list or add it
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

                    # If not found in database yet, add it from in-memory state
                    if not found:
                        batch_list.insert(0, {
                            'id': batch_id,
                            'started_at': batch_state['started_at'],
                            'completed_at': None,
                            'model': batch_state.get('current_model'),
                            'provider': batch_state.get('current_provider'),
                            'topic_filter': batch_state.get('topic_filter'),
                            'difficulty_filter': batch_state.get('difficulty_filter'),
                            'reasoning_instruction': batch_state.get('reasoning_instruction'),
                            'target': batch_state.get('total', 0),
                            'samples_generated': batch_state.get('samples_generated', 0),
                            'tokens_used': batch_state.get('total_tokens', 0),
                            'status': 'running',
                            'errors': batch_state.get('errors', []),
                            'model_switches': batch_state.get('model_switches', []),
                            'provider_switches': batch_state.get('provider_switches', []),
                            'progress': batch_state.get('progress', 0),
                            'current_sample': batch_state.get('current_sample')
                        })

        return jsonify({
            'success': True,
            'batches': batch_list,
            'count': len(batch_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/batch/stream')
def batch_generation_stream():
    """SSE endpoint for real-time batch generation updates"""
    def event_stream():
        q = queue.Queue()
        sse_subscribers.append(q)
        try:
            # Send initial state - all active batches
            with batch_lock:
                all_batches = active_batches.copy()
            yield f"data: {json.dumps({'type': 'all_batches', 'batches': all_batches})}\n\n"

            # Stream updates
            while True:
                try:
                    message = q.get(timeout=30)  # 30 second timeout
                    yield message
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            sse_subscribers.remove(q)

    return Response(stream_with_context(event_stream()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    })

@app.route('/api/add', methods=['POST'])
def add_sample():
    """Add a sample to the dataset"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # Load existing dataset
        df_existing = pl.read_parquet(PARQUET_PATH)

        # Check for duplicate ID
        if data['id'] in df_existing['id'].to_list():
            return jsonify({
                'success': False,
                'error': f"ID '{data['id']}' already exists"
            }), 400

        # Add new sample
        df_new = pl.DataFrame([data])
        df_combined = pl.concat([df_existing, df_new])

        # Save to parquet
        df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

        return jsonify({
            'success': True,
            'total_samples': len(df_combined)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/topics')
def get_topics():
    """Get list of available topics for generation"""
    return jsonify({
        'topics': [
            {
                'practice_area': area,
                'topic': topic,
                'difficulty': difficulty
            }
            for area, topic, difficulty in TOPICS
        ]
    })

@app.route('/api/sample-types')
def get_sample_types():
    """Get list of available sample types for generation"""
    from config import SAMPLE_TYPES

    return jsonify({
        'success': True,
        'sample_types': [
            {
                'id': sample_id,
                'name': config['name'],
                'description': config['description'],
                'focus': config['focus'],
                'example': config['example']
            }
            for sample_id, config in SAMPLE_TYPES.items()
        ],
        'default': 'case_analysis'
    })

@app.route('/api/providers')
def get_providers():
    """Get list of available LLM providers"""
    try:
        providers = []
        for provider_id, config in PROVIDERS.items():
            if config['enabled']:
                providers.append({
                    'id': provider_id,
                    'name': provider_id.capitalize(),
                    'enabled': True,
                    'default_model': config['default_model'],
                    'requests_per_minute': config.get('requests_per_minute', 25),
                    'tokens_per_minute': config.get('tokens_per_minute', 5500)
                })

        return jsonify({
            'success': True,
            'providers': providers,
            'default_provider': 'groq'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models')
def get_models():
    """Get list of available models from all providers"""
    try:
        all_models = []

        # Groq models
        if PROVIDERS['groq']['enabled']:
            try:
                client = get_groq_client()
                models_response = client.models.list()

                for model in models_response.data:
                    # Filter out non-text models
                    if not any(x in model.id.lower() for x in ['whisper', 'guard', 'vision']):
                        all_models.append({
                            'id': model.id,
                            'name': model.id,
                            'provider': 'groq',
                            'provider_name': 'Groq',
                            'context_window': getattr(model, 'context_window', None),
                            'owned_by': getattr(model, 'owned_by', 'groq')
                        })
            except Exception as e:
                print(f"Error loading Groq models: {e}")

        # Cerebras models
        if PROVIDERS['cerebras']['enabled']:
            try:
                import requests
                response = requests.get(
                    'https://api.cerebras.ai/v1/models',
                    headers={'Authorization': f'Bearer {PROVIDERS["cerebras"]["api_key"]}'},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    for model in data.get('data', []):
                        all_models.append({
                            'id': model['id'],
                            'name': model['id'],
                            'provider': 'cerebras',
                            'provider_name': 'Cerebras',
                            'context_window': 200000 if '235b' in model['id'] else 128000,
                            'owned_by': 'Cerebras'
                        })
            except Exception as e:
                print(f"Error loading Cerebras models: {e}")

        # Ollama Cloud models
        if PROVIDERS.get('ollama', {}).get('enabled'):
            try:
                from config import OLLAMA_ALL_MODELS
                for model_id in OLLAMA_ALL_MODELS:
                    # Extract parameter size from model name for context window estimation
                    if '1t' in model_id:
                        context_window = 200000  # 1T model
                        params = '1T'
                    elif '671b' in model_id:
                        context_window = 128000  # 671B model
                        params = '671B'
                    elif '480b' in model_id:
                        context_window = 128000  # 480B model
                        params = '480B'
                    elif '120b' in model_id:
                        context_window = 128000  # 120B model
                        params = '120B'
                    elif '20b' in model_id:
                        context_window = 32000   # 20B model
                        params = '20B'
                    else:
                        context_window = 32000
                        params = 'Unknown'

                    all_models.append({
                        'id': model_id,
                        'name': f"{model_id} ({params})",
                        'provider': 'ollama',
                        'provider_name': 'Ollama Cloud',
                        'context_window': context_window,
                        'owned_by': 'Ollama'
                    })
            except Exception as e:
                print(f"Error loading Ollama models: {e}")

        return jsonify({
            'success': True,
            'models': all_models,
            'default_provider': 'groq',
            'default_model': DEFAULT_MODEL
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'default_model': DEFAULT_MODEL
        }), 500

@app.route('/api/stats/detailed')
def get_detailed_stats():
    """Get detailed dataset statistics"""
    try:
        df = pl.read_parquet(PARQUET_PATH)

        # Calculate comprehensive statistics
        stats = {
            'total_samples': len(df),
            'difficulty_breakdown': df.group_by("difficulty").agg([
                pl.count().alias("count"),
                pl.col("question").str.len_bytes().mean().alias("avg_question_length"),
                pl.col("answer").str.len_bytes().mean().alias("avg_answer_length")
            ]).to_dicts(),
            'topic_breakdown': df.group_by("topic").len().sort("len", descending=True).to_dicts(),
            'practice_areas': df.select(
                pl.col("topic").str.split(" - ").list.get(0).alias("practice_area")
            ).group_by("practice_area").len().sort("len", descending=True).to_dicts(),
            'avg_lengths': {
                'question': df.select(pl.col("question").str.len_bytes().mean())[0,0],
                'answer': df.select(pl.col("answer").str.len_bytes().mean())[0,0],
                'reasoning': df.select(pl.col("reasoning").str.len_bytes().mean())[0,0],
                'case_citation': df.select(pl.col("case_citation").str.len_bytes().mean())[0,0]
            },
            'unique_topics': df.select("topic").unique().height,
            'unique_practice_areas': df.select(
                pl.col("topic").str.split(" - ").list.get(0)
            ).unique().height
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/tokens')
def get_token_stats():
    """Get comprehensive token statistics for the dataset"""
    try:
        df = pl.read_parquet(PARQUET_PATH)

        # Initialize tiktoken encoder (GPT-4 encoding)
        enc = tiktoken.get_encoding("cl100k_base")

        # Calculate tokens for each field
        def count_tokens(text):
            if not text or not isinstance(text, str):
                return 0
            return len(enc.encode(text))

        # Calculate total tokens and per-field breakdown
        total_tokens = 0
        field_tokens = {
            'question': 0,
            'answer': 0,
            'reasoning': 0,
            'case_citation': 0,
            'topic': 0
        }

        samples = df.to_dicts()
        for sample in samples:
            for field in field_tokens.keys():
                tokens = count_tokens(sample.get(field, ''))
                field_tokens[field] += tokens
                total_tokens += tokens

        # Calculate average tokens per sample
        num_samples = len(df)
        avg_tokens_per_sample = total_tokens / num_samples if num_samples > 0 else 0

        # Calculate tokens by difficulty
        tokens_by_difficulty = {}
        for difficulty in df['difficulty'].unique().to_list():
            difficulty_samples = df.filter(pl.col('difficulty') == difficulty).to_dicts()
            difficulty_tokens = 0
            difficulty_count = len(difficulty_samples)

            for sample in difficulty_samples:
                for field in ['question', 'answer', 'reasoning', 'case_citation', 'topic']:
                    difficulty_tokens += count_tokens(sample.get(field, ''))

            tokens_by_difficulty[difficulty] = {
                'total_tokens': difficulty_tokens,
                'avg_tokens': difficulty_tokens / difficulty_count if difficulty_count > 0 else 0,
                'sample_count': difficulty_count
            }

        # Calculate tokens by practice area (top 10)
        practice_area_tokens = {}
        for sample in samples:
            topic = sample.get('topic', '')
            if ' - ' in topic:
                practice_area = topic.split(' - ')[0]
            else:
                practice_area = topic

            if practice_area not in practice_area_tokens:
                practice_area_tokens[practice_area] = {'tokens': 0, 'count': 0}

            sample_tokens = sum(count_tokens(sample.get(field, '')) for field in ['question', 'answer', 'reasoning', 'case_citation', 'topic'])
            practice_area_tokens[practice_area]['tokens'] += sample_tokens
            practice_area_tokens[practice_area]['count'] += 1

        # Sort and limit to top 10 practice areas
        sorted_practice_areas = sorted(
            [{'practice_area': k, 'total_tokens': v['tokens'], 'avg_tokens': v['tokens'] / v['count'], 'count': v['count']}
             for k, v in practice_area_tokens.items()],
            key=lambda x: x['total_tokens'],
            reverse=True
        )[:10]

        # Estimated costs for Groq API models
        # Prices per 1M tokens (averaged input + output for training estimates)
        # Note: Groq offers competitive pricing - actual costs vary by input/output ratio
        model_pricing = {
            'llama-3.3-70b': {'price_per_1m': 0.69, 'name': 'Llama 3.3 70B (Groq)'},
            'llama-3.1-70b': {'price_per_1m': 0.69, 'name': 'Llama 3.1 70B (Groq)'},
            'llama-3.1-8b': {'price_per_1m': 0.065, 'name': 'Llama 3.1 8B (Groq)'},
            'mixtral-8x7b': {'price_per_1m': 0.24, 'name': 'Mixtral 8x7B (Groq)'},
            'gemma-7b': {'price_per_1m': 0.07, 'name': 'Gemma 7B (Groq)'}
        }

        estimated_costs = {}
        for model_id, pricing in model_pricing.items():
            cost = (total_tokens / 1_000_000) * pricing['price_per_1m']
            estimated_costs[model_id] = {
                'name': pricing['name'],
                'cost_usd': round(cost, 4),
                'price_per_1m': pricing['price_per_1m']
            }

        return jsonify({
            'success': True,
            'stats': {
                'total_tokens': total_tokens,
                'total_samples': num_samples,
                'avg_tokens_per_sample': round(avg_tokens_per_sample, 2),
                'tokens_by_field': {
                    field: {
                        'total': tokens,
                        'avg_per_sample': round(tokens / num_samples, 2) if num_samples > 0 else 0,
                        'percentage': round((tokens / total_tokens * 100), 2) if total_tokens > 0 else 0
                    }
                    for field, tokens in field_tokens.items()
                },
                'tokens_by_difficulty': tokens_by_difficulty,
                'tokens_by_practice_area': sorted_practice_areas,
                'estimated_costs': estimated_costs,
                'encoding': 'cl100k_base (GPT-4 tokenizer)'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/samples/random')
def get_random_samples():
    """Get random samples from dataset"""
    try:
        count = request.args.get('count', default=5, type=int)
        difficulty = request.args.get('difficulty', default=None, type=str)

        df = pl.read_parquet(PARQUET_PATH)

        if difficulty:
            df = df.filter(pl.col("difficulty") == difficulty)

        # Sample randomly
        sampled = df.sample(min(count, len(df)))

        return jsonify({
            'success': True,
            'samples': sampled.to_dicts(),
            'count': len(sampled)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search')
def search_samples():
    """Search samples by query"""
    try:
        query = request.args.get('q', default='', type=str)
        field = request.args.get('field', default='all', type=str)
        limit = request.args.get('limit', default=100, type=int)

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required'
            }), 400

        df = pl.read_parquet(PARQUET_PATH)

        # Search in specified field or all fields
        if field == 'all':
            mask = (
                df['question'].str.contains(f'(?i){query}') |
                df['answer'].str.contains(f'(?i){query}') |
                df['topic'].str.contains(f'(?i){query}') |
                df['case_citation'].str.contains(f'(?i){query}')
            )
        else:
            if field not in df.columns:
                return jsonify({
                    'success': False,
                    'error': f'Invalid field: {field}'
                }), 400
            mask = df[field].str.contains(f'(?i){query}')

        results = df.filter(mask).head(limit)

        return jsonify({
            'success': True,
            'results': results.to_dicts(),
            'count': len(results),
            'query': query,
            'field': field
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/import/jsonl', methods=['POST'])
def import_jsonl():
    """Import samples from JSONL content"""
    try:
        data = request.json
        jsonl_content = data.get('content', '')

        if not jsonl_content:
            return jsonify({'success': False, 'error': 'No JSONL content provided'}), 400

        # Parse JSONL
        import json
        samples = []
        lines = jsonl_content.strip().split('\n')

        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                sample = json.loads(line)

                # Validate required fields
                required_fields = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']
                missing_fields = [f for f in required_fields if f not in sample]

                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': f'Line {idx}: Missing required fields: {", ".join(missing_fields)}'
                    }), 400

                samples.append(sample)
            except json.JSONDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': f'Line {idx}: Invalid JSON - {str(e)}'
                }), 400

        if not samples:
            return jsonify({'success': False, 'error': 'No valid samples found'}), 400

        # Load existing dataset
        df_existing = pl.read_parquet(PARQUET_PATH)

        # Create new dataframe from samples
        df_new = pl.DataFrame(samples)

        # Check for duplicate IDs
        existing_ids = set(df_existing['id'].to_list())
        new_ids = set(df_new['id'].to_list())
        duplicates = existing_ids.intersection(new_ids)

        if duplicates:
            return jsonify({
                'success': False,
                'error': f'Duplicate IDs found: {", ".join(list(duplicates)[:5])}...'
            }), 400

        # Append to existing dataset
        df_combined = pl.concat([df_existing, df_new])

        # Save to parquet
        df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

        return jsonify({
            'success': True,
            'message': f'Successfully imported {len(samples)} samples',
            'total_samples': len(df_combined)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    with batch_lock:
        running_batches = sum(1 for batch in active_batches.values() if batch.get('running', False))

    return jsonify({
        'status': 'healthy',
        'dataset_exists': PARQUET_PATH.exists(),
        'groq_configured': bool(API_KEY),
        'active_batches': len(active_batches),
        'running_batches': running_batches
    })

@app.route('/api/batches/stuck')
def check_stuck_batches():
    """Detect and automatically stop stuck batches (zombie batches and long-running batches)"""
    try:
        from datetime import datetime, timedelta

        # Define stuck threshold (10 minutes)
        stuck_threshold_minutes = 10
        now = datetime.now()

        # Get all running batches from database
        running_batches = BatchHistory.query.filter_by(status='running').all()

        stuck_batches = []
        stopped_batches = []

        for batch in running_batches:
            try:
                # Parse start time
                started_at = datetime.fromisoformat(batch.started_at)
                time_elapsed = (now - started_at).total_seconds() / 60  # minutes

                # Check if this is a zombie batch (in database but not in memory)
                # This happens when Flask restarts and worker threads are killed
                is_zombie = batch.batch_id not in active_batches

                # Check if batch has been running too long with no progress
                # A stuck batch is one that's been running > threshold with 0 samples generated
                # OR running > 30 minutes with no completion
                # OR is a zombie batch (in DB but not in memory)
                is_stuck = (
                    is_zombie or  # Zombie batches are immediately stuck
                    (time_elapsed > stuck_threshold_minutes and batch.samples_generated == 0) or
                    (time_elapsed > 30)  # Any batch running > 30 min is suspicious
                )

                if is_stuck:
                    stuck_info = {
                        'batch_id': batch.batch_id,
                        'started_at': batch.started_at,
                        'elapsed_minutes': round(time_elapsed, 1),
                        'samples_generated': batch.samples_generated,
                        'target': batch.target_count,
                        'model': batch.model,
                        'is_zombie': is_zombie
                    }
                    stuck_batches.append(stuck_info)

                    # Automatically stop the stuck batch
                    with batch_lock:
                        # Check if batch is in active_batches and mark as stopped
                        if batch.batch_id in active_batches:
                            batch_state = active_batches[batch.batch_id]
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
                    reason = "zombie (Flask restarted)" if is_zombie else f"stuck for {round(time_elapsed, 1)} min"
                    print(f"🛑 Auto-stopped {reason} batch {batch.batch_id}")

                    # Broadcast SSE update
                    broadcast_sse_update(batch.batch_id)

            except Exception as e:
                print(f"Error checking batch {batch.batch_id}: {str(e)}")
                continue

        # Count zombie vs time-based stopped batches
        zombie_count = sum(1 for b in stopped_batches if b.get('is_zombie'))
        time_stuck_count = len(stopped_batches) - zombie_count

        message_parts = []
        if zombie_count > 0:
            message_parts.append(f'{zombie_count} zombie batch(es)')
        if time_stuck_count > 0:
            message_parts.append(f'{time_stuck_count} time-stuck batch(es)')

        message = f'Automatically stopped {", ".join(message_parts)}' if stopped_batches else 'No stuck batches found'

        return jsonify({
            'success': True,
            'stuck_batches': stuck_batches,
            'stopped_batches': stopped_batches,
            'count': len(stuck_batches),
            'stopped_count': len(stopped_batches),
            'zombie_count': zombie_count,
            'time_stuck_count': time_stuck_count,
            'threshold_minutes': stuck_threshold_minutes,
            'message': message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sample/<sample_id>', methods=['PUT'])
def update_sample(sample_id):
    """Update an existing sample in the dataset"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # Load existing dataset
        df = pl.read_parquet(PARQUET_PATH)

        # Find sample by ID
        if sample_id not in df['id'].to_list():
            return jsonify({
                'success': False,
                'error': f"Sample with ID '{sample_id}' not found"
            }), 404

        # If ID is being changed, check for duplicates
        if data['id'] != sample_id and data['id'] in df['id'].to_list():
            return jsonify({
                'success': False,
                'error': f"ID '{data['id']}' already exists"
            }), 400

        # Update the sample
        df_dict = df.to_dicts()
        for i, row in enumerate(df_dict):
            if row['id'] == sample_id:
                df_dict[i] = data
                break

        # Create new dataframe and save
        df_updated = pl.DataFrame(df_dict)
        df_updated.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

        return jsonify({
            'success': True,
            'message': f'Sample {sample_id} updated successfully',
            'total_samples': len(df_updated)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sample/<sample_id>', methods=['DELETE'])
def delete_sample(sample_id):
    """Delete a sample from the dataset"""
    try:
        # Load existing dataset
        df = pl.read_parquet(PARQUET_PATH)

        # Check if sample exists
        if sample_id not in df['id'].to_list():
            return jsonify({
                'success': False,
                'error': f"Sample with ID '{sample_id}' not found"
            }), 404

        # Remove the sample
        df_filtered = df.filter(pl.col('id') != sample_id)

        # Save updated dataset
        df_filtered.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

        return jsonify({
            'success': True,
            'message': f'Sample {sample_id} deleted successfully',
            'total_samples': len(df_filtered)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch/<batch_id>/samples')
def get_batch_samples(batch_id):
    """Get all samples generated in a specific batch"""
    try:
        # Load existing dataset
        df = pl.read_parquet(PARQUET_PATH)

        # Check if batch_id column exists
        if 'batch_id' not in df.columns:
            return jsonify({
                'success': False,
                'error': 'Dataset does not have batch_id tracking (older version)'
            }), 400

        # Filter samples by batch_id
        batch_samples = df.filter(pl.col('batch_id') == batch_id)

        if len(batch_samples) == 0:
            return jsonify({
                'success': False,
                'error': f"No samples found for batch ID '{batch_id}'"
            }), 404

        # Get batch info from database
        batch_info = BatchHistory.query.filter_by(batch_id=batch_id).first()

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'samples': batch_samples.to_dicts(),
            'count': len(batch_samples),
            'batch_info': batch_info.to_dict() if batch_info else None
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sample/<sample_id>/download', methods=['GET'])
def download_sample(sample_id):
    """Download a single sample as a JSON file"""
    try:
        # Load existing dataset
        df = pl.read_parquet(PARQUET_PATH)

        # Find sample by ID
        sample_df = df.filter(pl.col('id') == sample_id)

        if len(sample_df) == 0:
            return jsonify({
                'success': False,
                'error': f"Sample with ID '{sample_id}' not found"
            }), 404

        # Get the sample as a dictionary
        sample = sample_df.to_dicts()[0]

        # Create JSON string with proper formatting
        json_str = json.dumps(sample, indent=2, ensure_ascii=False)

        # Create response with download headers
        response = make_response(json_str)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename="{sample_id}.json"'

        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/samples/download', methods=['POST'])
def download_samples():
    """Download multiple samples as a JSONL file"""
    try:
        data = request.json
        sample_ids = data.get('sample_ids', [])

        if not sample_ids:
            return jsonify({
                'success': False,
                'error': 'No sample IDs provided'
            }), 400

        # Load existing dataset
        df = pl.read_parquet(PARQUET_PATH)

        # Filter samples by IDs
        samples_df = df.filter(pl.col('id').is_in(sample_ids))

        if len(samples_df) == 0:
            return jsonify({
                'success': False,
                'error': 'No samples found with provided IDs'
            }), 404

        # Convert to list of dictionaries
        samples = samples_df.to_dicts()

        # Create JSONL string (one JSON object per line)
        jsonl_lines = [json.dumps(sample, ensure_ascii=False) for sample in samples]
        jsonl_str = '\n'.join(jsonl_lines)

        # Create response with download headers
        response = make_response(jsonl_str)
        response.headers['Content-Type'] = 'application/x-ndjson'
        response.headers['Content-Disposition'] = f'attachment; filename="samples_{len(samples)}.jsonl"'

        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/huggingface/push', methods=['POST', 'OPTIONS'])
def push_to_huggingface():
    """Push dataset to Hugging Face Hub"""
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        return '', 200

    try:
        import os
        from huggingface_hub import HfApi, create_repo

        data = request.json
        token = data.get('token') or os.getenv('HUGGINGFACE_TOKEN')
        repo_name = data.get('repo_name', 'legal-training-dataset')
        format_type = data.get('format', 'parquet')
        is_private = data.get('private', False)
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Hugging Face token is required'
            }), 400
            
        # Initialize Hugging Face API
        api = HfApi()
        
        # Get username
        user_info = api.whoami(token=token)
        username = user_info['name']
        repo_id = f"{username}/{repo_name}"
        
        # Create repository if it doesn't exist
        try:
            create_repo(
                repo_id=repo_id,
                token=token,
                repo_type="dataset",
                private=is_private,
                exist_ok=True
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to create repository: {str(e)}'
            }), 400
        
        # Prepare file for upload
        file_path = PARQUET_PATH
        
        if format_type == 'json':
            # Convert to JSON
            df = pl.read_parquet(PARQUET_PATH)
            json_path = Path("train.json")
            with open(json_path, 'w') as f:
                json.dump(df.to_dicts(), f, indent=2)
            file_path = json_path
        elif format_type == 'csv':
            # Convert to CSV
            df = pl.read_parquet(PARQUET_PATH)
            csv_path = Path("train.csv")
            df.write_csv(csv_path)
            file_path = csv_path
        
        # Upload file
        api.upload_file(
            path_or_fileobj=str(file_path),
            path_in_repo=f"train.{format_type}",
            repo_id=repo_id,
            repo_type="dataset",
            token=token
        )
        
        # Clean up temp files
        if format_type != 'parquet':
            file_path.unlink()
        
        return jsonify({
            'success': True,
            'message': f'Successfully pushed to Hugging Face',
            'repo_url': f'https://huggingface.co/datasets/{repo_id}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 UK Legal Dataset API Server")
    print(f"📊 Dataset: {PARQUET_PATH}")
    print(f"🤖 Groq API: {'Configured' if API_KEY else 'Not configured'}")
    print(f"🌐 Starting server on http://localhost:5001")
    app.run(port=5001, debug=True, threaded=True)
