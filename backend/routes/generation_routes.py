"""
Generation routes for batch sample generation.
Handles model selection, provider management, and batch generation.
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.generation_service import GenerationService
from services.llm_service import LLMProviderFactory
from services.batch_service import BatchService
from services.sse_service import get_sse_service
from config import PROVIDERS, SAMPLE_TYPES, TOPICS
import queue
import json

generation_bp = Blueprint('generation', __name__)

# Get global SSE service instance
sse_service = get_sse_service()

def broadcast_sse_update(batch_id=None):
    """Broadcast batch status to all SSE subscribers (wrapper for SSE service)"""
    sse_service.broadcast_batch_update(batch_id=batch_id)


# ============================================================================
# GENERATION ROUTES
# ============================================================================

@generation_bp.route('/api/generate', methods=['POST'])
def generate_sample():
    """Generate a single new sample using specified provider"""
    try:
        data = request.json
        practice_area = data.get('practice_area', 'Contract Law')
        topic = data.get('topic', 'Formation of Contracts')
        difficulty = data.get('difficulty', 'intermediate')
        provider = data.get('provider', 'groq')
        model = data.get('model')  # Will use provider default if not specified
        sample_type = data.get('sample_type', 'case_analysis')

        # Validate provider
        if provider not in PROVIDERS:
            return jsonify({
                'success': False,
                'error': f'Invalid provider: {provider}. Available: {", ".join(PROVIDERS.keys())}'
            }), 400

        # Use provider's default model if not specified
        if not model:
            model = PROVIDERS[provider]['default_model']

        # Handle "balance" sample_type - randomly select one
        if sample_type == 'balance':
            import random
            from config import SAMPLE_TYPE_CYCLE
            sample_type = random.choice(SAMPLE_TYPE_CYCLE)

        # Generate sample
        service = GenerationService()
        sample, tokens_used, elapsed, error = service.generate_single_sample(
            practice_area=practice_area,
            topic=topic,
            difficulty=difficulty,
            counter=1,  # Will be set properly by the service
            provider=provider,
            model=model,
            sample_type=sample_type
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


@generation_bp.route('/api/generate/batch/start', methods=['POST'])
def start_batch_generation():
    """
    Start smart batch generation with automatic provider failover and balancing.

    Smart Mode (default=True):
    - Auto-selects best provider if not specified or set to 'auto'
    - Automatically switches providers on rate limits/errors
    - Balances topics and difficulty levels automatically
    - Uses champion models for best quality
    """
    try:
        data = request.json
        target_count = data.get('target_count', 2100)
        provider = data.get('provider', 'auto')  # 'auto' triggers smart provider selection
        model = data.get('model')  # None = use champion model
        topic_filter = data.get('topic')  # None = auto-balance all topics
        difficulty_filter = data.get('difficulty')  # None = auto-balance
        reasoning_instruction = data.get('reasoning_instruction')
        sample_type_filter = data.get('sample_type', 'balance')  # 'balance' = auto-rotate types
        smart_mode = data.get('smart_mode', True)  # Enable smart features by default

        # Validate provider only if not using auto mode
        if provider not in ['auto', None] and provider not in PROVIDERS:
            return jsonify({
                'success': False,
                'error': f'Invalid provider: {provider}. Available: {", ".join(PROVIDERS.keys())}, "auto"'
            }), 400

        if provider not in ['auto', None] and not PROVIDERS.get(provider, {}).get('enabled'):
            return jsonify({
                'success': False,
                'error': f'Provider {provider} is not enabled'
            }), 400

        # Start batch generation with smart mode
        batch_service = BatchService()
        result = batch_service.start_batch(
            target_count=target_count,
            provider=provider,
            model=model,
            topic_filter=topic_filter,
            difficulty_filter=difficulty_filter,
            reasoning_instruction=reasoning_instruction,
            sample_type_filter=sample_type_filter,
            smart_mode=smart_mode
        )

        if result['success']:
            # Broadcast batch start notification
            broadcast_sse_update(result['batch_id'])

            return jsonify({
                'success': True,
                'message': f'🤖 Smart batch started with {result["initial_provider"]}/{result["initial_model"]}, targeting {target_count} total samples',
                'batch_id': result['batch_id'],
                'provider': result['initial_provider'],
                'model': result['initial_model'],
                'smart_mode': result['smart_mode'],
                'features': [
                    'Auto provider failover',
                    'Balanced topic distribution',
                    'Balanced difficulty levels',
                    'Auto sample type rotation'
                ] if smart_mode else []
            })
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@generation_bp.route('/api/generate/batch/stop', methods=['POST'])
def stop_batch_generation():
    """Stop batch generation - supports stopping specific batch by ID or all batches"""
    try:
        data = request.json or {}
        batch_id = data.get('batch_id')  # Optional: stop specific batch

        batch_service = BatchService()

        if batch_id:
            # Stop specific batch
            result = batch_service.stop_batch(batch_id)
            if result['success']:
                broadcast_sse_update(batch_id)
            return jsonify(result)
        else:
            # Stop all running batches
            result = batch_service.stop_all_batches()
            for bid in result.get('stopped_batch_ids', []):
                broadcast_sse_update(bid)
            return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@generation_bp.route('/api/generate/batch/status')
def batch_generation_status():
    """Get batch generation status - all batches or specific batch"""
    batch_id = request.args.get('batch_id')

    batch_service = BatchService()

    if batch_id:
        # Return specific batch
        batch = batch_service.get_batch(batch_id)
        if not batch:
            return jsonify({
                'success': False,
                'error': f'Batch {batch_id} not found'
            }), 404
        return jsonify(batch)
    else:
        # Return all active batches
        batches = batch_service.get_all_batches()
        return jsonify({
            'batches': batches,
            'count': len(batches)
        })


@generation_bp.route('/api/generate/batch/history')
def get_batch_history():
    """Get all batch generation history from database"""
    try:
        batch_service = BatchService()
        batches = batch_service.get_batch_history()

        return jsonify({
            'success': True,
            'batches': batches,
            'count': len(batches)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@generation_bp.route('/api/generate/batch/stream')
def batch_generation_stream():
    """SSE endpoint for real-time batch generation updates"""
    def event_stream():
        q = queue.Queue()
        sse_service.add_subscriber(q)
        try:
            # Send initial state - all active batches
            batch_service = BatchService()
            all_batches = batch_service.get_all_batches()
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
            sse_service.remove_subscriber(q)

    return Response(stream_with_context(event_stream()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    })


@generation_bp.route('/api/batches/stuck')
def check_stuck_batches():
    """Detect and automatically stop stuck batches"""
    try:
        batch_service = BatchService()
        result = batch_service.check_stuck_batches()

        # Broadcast updates for stopped batches
        for batch_info in result.get('stopped_batches', []):
            broadcast_sse_update(batch_info['batch_id'])

        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# MODEL & PROVIDER ROUTES
# ============================================================================

@generation_bp.route('/api/models')
def get_models():
    """Get list of available models from database-driven provider system"""
    try:
        from models import Model, Provider

        all_models = []

        # Get all enabled models from database
        enabled_models = Model.query.join(Provider).filter(
            Provider.enabled == True,
            Model.enabled == True
        ).order_by(Model.fallback_priority).all()

        for model in enabled_models:
            all_models.append({
                'id': model.model_id,
                'name': model.display_name,
                'provider': model.provider_id,
                'provider_name': model.provider.name,
                'context_window': model.max_tokens,
                'fallback_priority': model.fallback_priority,
                'supports_json_schema': model.supports_json_schema,
                'is_thinking_model': model.is_thinking_model,
                'owned_by': model.provider_id
            })

        # Get default provider and model from database
        default_provider = Provider.query.filter_by(enabled=True).order_by(Provider.requests_per_minute.desc()).first()
        default_model_id = default_provider.default_model_id if default_provider else 'llama-3.3-70b-versatile'

        return jsonify({
            'success': True,
            'models': all_models,
            'default_provider': default_provider.id if default_provider else 'groq',
            'default_model': default_model_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@generation_bp.route('/api/providers')
def get_providers():
    """Get list of available LLM providers from database"""
    try:
        from models import Provider

        providers = []
        db_providers = Provider.query.filter_by(enabled=True).all()

        for provider in db_providers:
            providers.append({
                'id': provider.id,
                'name': provider.name,
                'enabled': provider.enabled,
                'default_model': provider.default_model_id,
                'champion_model': provider.champion_model_id,
                'requests_per_minute': provider.requests_per_minute,
                'tokens_per_minute': provider.tokens_per_minute,
                'base_url': provider.base_url
            })

        # Get default provider (highest throughput)
        default_provider = Provider.query.filter_by(enabled=True).order_by(
            Provider.requests_per_minute.desc()
        ).first()

        return jsonify({
            'success': True,
            'providers': providers,
            'default_provider': default_provider.id if default_provider else 'groq'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@generation_bp.route('/api/sample-types')
def get_sample_types():
    """Get list of available sample types for generation"""
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


@generation_bp.route('/api/topics')
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
