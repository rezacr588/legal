"""
Provider and Model Management Routes
Provides CRUD operations for dynamic provider/model configuration.
"""

from flask import Blueprint, jsonify, request
from models import db, Provider, Model, ProviderConfig
from sqlalchemy.exc import IntegrityError

provider_bp = Blueprint('provider', __name__, url_prefix='/api')


# ============================================================================
# PROVIDER ENDPOINTS
# ============================================================================

@provider_bp.route('/providers/all', methods=['GET'])
def get_all_providers():
    """Get all providers with their models."""
    try:
        include_models = request.args.get('include_models', 'true').lower() == 'true'
        include_config = request.args.get('include_config', 'false').lower() == 'true'

        providers = Provider.query.all()
        return jsonify({
            'success': True,
            'providers': [p.to_dict(include_models=include_models, include_config=include_config)
                         for p in providers]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/providers/<provider_id>', methods=['GET'])
def get_provider(provider_id):
    """Get single provider by ID."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        include_models = request.args.get('include_models', 'true').lower() == 'true'
        include_config = request.args.get('include_config', 'true').lower() == 'true'

        return jsonify({
            'success': True,
            'provider': provider.to_dict(include_models=include_models, include_config=include_config)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@provider_bp.route('/providers/<provider_id>', methods=['PUT'])
def update_provider(provider_id):
    """Update provider configuration."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        data = request.get_json()

        # Update allowed fields
        if 'name' in data:
            provider.name = data['name']
        if 'base_url' in data:
            provider.base_url = data['base_url']
        if 'enabled' in data:
            provider.enabled = data['enabled']
        if 'requests_per_minute' in data:
            provider.requests_per_minute = data['requests_per_minute']
        if 'tokens_per_minute' in data:
            provider.tokens_per_minute = data['tokens_per_minute']
        if 'default_model_id' in data:
            provider.default_model_id = data['default_model_id']
        if 'champion_model_id' in data:
            provider.champion_model_id = data['champion_model_id']
        if 'extra_config' in data:
            import json
            provider.extra_config = json.dumps(data['extra_config'])

        db.session.commit()

        return jsonify({
            'success': True,
            'provider': provider.to_dict(include_models=True)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/providers/<provider_id>/toggle', methods=['POST'])
def toggle_provider(provider_id):
    """Enable or disable a provider."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        provider.enabled = not provider.enabled
        db.session.commit()

        return jsonify({
            'success': True,
            'provider': provider.to_dict(),
            'message': f'Provider {provider_id} {"enabled" if provider.enabled else "disabled"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/providers/<provider_id>/config', methods=['PUT'])
def update_provider_config(provider_id):
    """Update provider API key and sensitive configuration."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        data = request.get_json()

        # Get or create ProviderConfig
        config = ProviderConfig.query.filter_by(provider_id=provider_id).first()
        if not config:
            config = ProviderConfig(provider_id=provider_id)
            db.session.add(config)

        # Update API key if provided
        if 'api_key' in data and data['api_key']:
            config.set_api_key(data['api_key'])

        # Update extra config if provided
        if 'config' in data and data['config']:
            config.set_config(data['config'])

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Configuration updated for provider {provider_id}',
            'config': config.to_dict(include_secrets=False)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/providers/<provider_id>/config', methods=['GET'])
def get_provider_config(provider_id):
    """Get provider configuration (without secrets by default)."""
    try:
        config = ProviderConfig.query.filter_by(provider_id=provider_id).first_or_404()
        include_secrets = request.args.get('include_secrets', 'false').lower() == 'true'

        return jsonify({
            'success': True,
            'config': config.to_dict(include_secrets=include_secrets)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


# ============================================================================
# MODEL ENDPOINTS
# ============================================================================

@provider_bp.route('/models/all', methods=['GET'])
def get_all_models():
    """Get all models, optionally filtered by provider."""
    try:
        provider_id = request.args.get('provider')
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'

        query = Model.query

        if provider_id:
            query = query.filter_by(provider_id=provider_id)

        if enabled_only:
            query = query.filter_by(enabled=True)

        # Order by provider and fallback priority
        models = query.order_by(Model.provider_id, Model.fallback_priority).all()

        return jsonify({
            'success': True,
            'models': [m.to_dict() for m in models],
            'count': len(models)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/models/<int:model_db_id>', methods=['GET'])
def get_model(model_db_id):
    """Get single model by database ID."""
    try:
        model = Model.query.get_or_404(model_db_id)
        return jsonify({
            'success': True,
            'model': model.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@provider_bp.route('/models/<int:model_db_id>', methods=['PUT'])
def update_model(model_db_id):
    """Update model configuration."""
    try:
        model = Model.query.get_or_404(model_db_id)
        data = request.get_json()

        # Update allowed fields
        if 'display_name' in data:
            model.display_name = data['display_name']
        if 'enabled' in data:
            model.enabled = data['enabled']
        if 'max_tokens' in data:
            model.max_tokens = data['max_tokens']
        if 'supports_json_schema' in data:
            model.supports_json_schema = data['supports_json_schema']
        if 'is_thinking_model' in data:
            model.is_thinking_model = data['is_thinking_model']
        if 'extra_config' in data:
            import json
            model.extra_config = json.dumps(data['extra_config'])

        db.session.commit()

        return jsonify({
            'success': True,
            'model': model.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/models/<int:model_db_id>/toggle', methods=['POST'])
def toggle_model(model_db_id):
    """Enable or disable a model."""
    try:
        model = Model.query.get_or_404(model_db_id)
        model.enabled = not model.enabled
        db.session.commit()

        return jsonify({
            'success': True,
            'model': model.to_dict(),
            'message': f'Model {model.model_id} {"enabled" if model.enabled else "disabled"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@provider_bp.route('/models/<int:model_db_id>/priority', methods=['PUT'])
def update_model_priority(model_db_id):
    """Update model fallback priority."""
    try:
        model = Model.query.get_or_404(model_db_id)
        data = request.get_json()

        if 'fallback_priority' not in data:
            return jsonify({
                'success': False,
                'error': 'fallback_priority is required'
            }), 400

        new_priority = data['fallback_priority']
        old_priority = model.fallback_priority

        # Update priorities to avoid conflicts
        # If moving up (lower number), shift others down
        # If moving down (higher number), shift others up
        if new_priority < old_priority:
            # Moving up - shift affected models down
            Model.query.filter(
                Model.provider_id == model.provider_id,
                Model.fallback_priority >= new_priority,
                Model.fallback_priority < old_priority,
                Model.id != model.id
            ).update({Model.fallback_priority: Model.fallback_priority + 1})
        elif new_priority > old_priority:
            # Moving down - shift affected models up
            Model.query.filter(
                Model.provider_id == model.provider_id,
                Model.fallback_priority > old_priority,
                Model.fallback_priority <= new_priority,
                Model.id != model.id
            ).update({Model.fallback_priority: Model.fallback_priority - 1})

        # Update the model's priority
        model.fallback_priority = new_priority

        db.session.commit()

        # Get updated model list for provider
        updated_models = Model.query.filter_by(provider_id=model.provider_id)\
                                     .order_by(Model.fallback_priority).all()

        return jsonify({
            'success': True,
            'model': model.to_dict(),
            'provider_models': [m.to_dict() for m in updated_models],
            'message': f'Priority updated from {old_priority} to {new_priority}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@provider_bp.route('/models/reorder', methods=['POST'])
def reorder_models():
    """Reorder models for a provider (bulk priority update)."""
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        model_order = data.get('model_order')  # List of model_ids in desired order

        if not provider_id or not model_order:
            return jsonify({
                'success': False,
                'error': 'provider_id and model_order are required'
            }), 400

        # Update priorities based on order
        for priority, model_id in enumerate(model_order):
            model = Model.query.filter_by(model_id=model_id, provider_id=provider_id).first()
            if model:
                model.fallback_priority = priority

        db.session.commit()

        # Get updated models
        updated_models = Model.query.filter_by(provider_id=provider_id)\
                                     .order_by(Model.fallback_priority).all()

        return jsonify({
            'success': True,
            'models': [m.to_dict() for m in updated_models],
            'message': f'Reordered {len(model_order)} models for provider {provider_id}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# STATISTICS
# ============================================================================

@provider_bp.route('/providers/stats', methods=['GET'])
def get_provider_stats():
    """Get statistics about providers and models."""
    try:
        total_providers = Provider.query.count()
        enabled_providers = Provider.query.filter_by(enabled=True).count()
        total_models = Model.query.count()
        enabled_models = Model.query.filter_by(enabled=True).count()

        # Models per provider
        provider_stats = []
        for provider in Provider.query.all():
            total = Model.query.filter_by(provider_id=provider.id).count()
            enabled = Model.query.filter_by(provider_id=provider.id, enabled=True).count()
            provider_stats.append({
                'provider_id': provider.id,
                'provider_name': provider.name,
                'enabled': provider.enabled,
                'total_models': total,
                'enabled_models': enabled
            })

        return jsonify({
            'success': True,
            'stats': {
                'total_providers': total_providers,
                'enabled_providers': enabled_providers,
                'total_models': total_models,
                'enabled_models': enabled_models,
                'providers': provider_stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
