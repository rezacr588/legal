"""
Chat Routes - Interactive testing interface for all providers and models.
Allows real-time conversation with any model from any provider.
"""

from flask import Blueprint, jsonify, request, Response, stream_with_context
from services.llm_service import LLMProviderFactory
from models import Provider, Model
import json
import time

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/completions', methods=['POST'])
def chat_completion():
    """
    Chat completion endpoint supporting all providers and models.

    Request Body:
    {
        "provider": "cerebras",
        "model": "gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are a helpful legal assistant."},
            {"role": "user", "content": "What is contract law?"}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": false
    }

    Returns:
    {
        "success": true,
        "response": "Contract law is...",
        "provider": "cerebras",
        "model": "gpt-oss-120b",
        "tokens_used": 150,
        "finish_reason": "stop",
        "elapsed_time": 1.23
    }
    """
    try:
        data = request.get_json()

        # Extract parameters
        provider_id = data.get('provider', 'cerebras')
        model_id = data.get('model')
        messages = data.get('messages', [])
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)
        stream = data.get('stream', False)

        if not messages:
            return jsonify({
                'success': False,
                'error': 'messages array is required'
            }), 400

        # Auto-select model if not provided
        if not model_id:
            provider = Provider.query.filter_by(id=provider_id).first()
            if provider:
                model_id = provider.champion_model_id
            else:
                return jsonify({
                    'success': False,
                    'error': f'Provider {provider_id} not found'
                }), 404

        # Verify model exists and is enabled
        model = Model.query.filter_by(model_id=model_id, provider_id=provider_id).first()
        if not model:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} not found for provider {provider_id}'
            }), 404

        if not model.enabled:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} is disabled'
            }), 400

        # Get provider instance from database
        try:
            provider_instance = LLMProviderFactory.get_provider(provider_id, use_db=True)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to initialize provider: {str(e)}'
            }), 500

        # Convert messages to prompt (simple concatenation for now)
        # Most providers expect the last user message as the prompt
        prompt = ""
        system_message = None

        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            elif msg['role'] == 'user':
                prompt = msg['content']
            elif msg['role'] == 'assistant':
                # For conversation history, we might need to adjust this
                pass

        # Prepend system message if exists
        if system_message:
            prompt = f"{system_message}\n\nUser: {prompt}\n\nAssistant:"

        # Generate completion
        start_time = time.time()

        result = provider_instance.generate(
            model=model_id,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        elapsed_time = time.time() - start_time

        return jsonify({
            'success': True,
            'response': result['text'],
            'provider': provider_id,
            'model': model_id,
            'tokens_used': result.get('tokens_used', 0),
            'finish_reason': result.get('finish_reason', 'stop'),
            'elapsed_time': round(elapsed_time, 2)
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Chat completion error: {error_trace}")

        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }), 500


@chat_bp.route('/providers', methods=['GET'])
def get_available_providers():
    """
    Get all available providers with their models for chat.

    Returns:
    {
        "success": true,
        "providers": [
            {
                "id": "cerebras",
                "name": "Cerebras",
                "enabled": true,
                "champion_model": "gpt-oss-120b",
                "models": [
                    {"id": "gpt-oss-120b", "name": "GPT-OSS 120B", "enabled": true},
                    ...
                ]
            }
        ]
    }
    """
    try:
        providers = Provider.query.filter_by(enabled=True).all()

        result = []
        for provider in providers:
            models = Model.query.filter_by(provider_id=provider.id, enabled=True)\
                                .order_by(Model.fallback_priority).all()

            result.append({
                'id': provider.id,
                'name': provider.name,
                'enabled': provider.enabled,
                'champion_model': provider.champion_model_id,
                'requests_per_minute': provider.requests_per_minute,
                'models': [
                    {
                        'id': model.model_id,
                        'name': model.display_name,
                        'enabled': model.enabled,
                        'max_tokens': model.max_tokens,
                        'is_thinking': model.is_thinking_model
                    }
                    for model in models
                ]
            })

        return jsonify({
            'success': True,
            'providers': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chat_bp.route('/test', methods=['POST'])
def quick_test():
    """
    Quick test endpoint for single prompt testing.

    Request Body:
    {
        "provider": "cerebras",
        "model": "gpt-oss-120b",
        "prompt": "What is contract law?",
        "system_instruction": "You are a legal expert."
    }
    """
    try:
        data = request.get_json()

        provider_id = data.get('provider', 'cerebras')
        model_id = data.get('model')
        prompt = data.get('prompt', '')
        system_instruction = data.get('system_instruction', 'You are a helpful assistant.')

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'prompt is required'
            }), 400

        # Build messages
        messages = [
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': prompt}
        ]

        # Use the main completion endpoint
        request.json = {
            'provider': provider_id,
            'model': model_id,
            'messages': messages,
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000)
        }

        return chat_completion()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chat_bp.route('/system-prompts', methods=['GET'])
def get_system_prompts():
    """
    Get predefined system prompts for different use cases.
    """
    prompts = {
        'legal_assistant': {
            'name': 'Legal Assistant',
            'prompt': 'You are an expert UK legal assistant. Provide accurate, well-reasoned legal analysis with proper case citations. Always explain legal concepts clearly and cite relevant statutes or case law.'
        },
        'contract_expert': {
            'name': 'Contract Law Expert',
            'prompt': 'You are a contract law specialist with expertise in UK contract formation, terms, breach, and remedies. Provide detailed analysis with references to relevant case law like Carlill v Carbolic Smoke Ball Co.'
        },
        'tort_expert': {
            'name': 'Tort Law Expert',
            'prompt': 'You are a tort law expert specializing in negligence, nuisance, defamation, and vicarious liability. Analyze cases using established precedents and explain duties of care clearly.'
        },
        'general_assistant': {
            'name': 'General Assistant',
            'prompt': 'You are a helpful, accurate, and concise assistant.'
        },
        'thinking_model': {
            'name': 'Deep Reasoning',
            'prompt': 'You are an expert legal analyst. Think through problems step-by-step, showing your reasoning process. Use chain-of-thought analysis to arrive at well-supported conclusions.'
        },
        'educational': {
            'name': 'Legal Educator',
            'prompt': 'You are a legal educator. Explain legal concepts clearly with examples, break down complex topics into understandable parts, and help students learn effectively.'
        }
    }

    return jsonify({
        'success': True,
        'prompts': prompts
    })
