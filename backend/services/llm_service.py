"""
LLM Provider Service - Abstraction layer for multiple AI providers.
Implements factory pattern and provider-specific logic using OOP.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from groq import Groq
from cerebras.cloud.sdk import Cerebras
import requests
import json

from config import PROVIDERS, MODEL_FALLBACK_ORDER, CEREBRAS_FALLBACK_ORDER, OLLAMA_FALLBACK_ORDER, GOOGLE_FALLBACK_ORDER, MISTRAL_FALLBACK_ORDER, THINKING_MODELS


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All provider implementations must inherit from this class.
    """

    def __init__(self, api_key: str):
        """
        Initialize provider with API key.

        Args:
            api_key: API key for the provider
        """
        self.api_key = api_key

    @abstractmethod
    def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """
        Generate completion using the provider's API.

        Args:
            model: Model identifier
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Dictionary with 'text', 'tokens_used', 'finish_reason'
        """
        pass

    @abstractmethod
    def get_rate_limits(self) -> Dict[str, int]:
        """
        Get rate limits for this provider.

        Returns:
            Dictionary with 'requests_per_minute' and 'tokens_per_minute'
        """
        pass

    @abstractmethod
    def get_fallback_order(self) -> list:
        """
        Get model fallback order for this provider.

        Returns:
            List of model names in fallback priority order
        """
        pass


class GroqProvider(BaseLLMProvider):
    """Groq AI provider implementation."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = Groq(api_key=api_key)

    def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """Generate completion using Groq API."""
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get('temperature', 0.9),
            max_tokens=kwargs.get('max_tokens', 4000),
            top_p=kwargs.get('top_p', 1),
            stream=kwargs.get('stream', False),
            timeout=kwargs.get('timeout', 90)  # 90 second timeout
        )

        return {
            'text': response.choices[0].message.content.strip(),
            'tokens_used': response.usage.total_tokens,
            'finish_reason': response.choices[0].finish_reason
        }

    def get_rate_limits(self) -> Dict[str, int]:
        """Get Groq rate limits."""
        return {
            'requests_per_minute': 25,
            'tokens_per_minute': 5500
        }

    def get_fallback_order(self) -> list:
        """Get Groq model fallback order."""
        return MODEL_FALLBACK_ORDER


class CerebrasProvider(BaseLLMProvider):
    """Cerebras AI provider implementation."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = Cerebras(api_key=api_key)

    def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """
        Generate completion using Cerebras API.

        Thinking models: No JSON schema (outputs thinking tags naturally)
        Instruct models: Use strict JSON schema for structured output
        """
        # Check against THINKING_MODELS constant for robust detection
        is_thinking_model = model in THINKING_MODELS

        # Build request parameters
        request_params = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': kwargs.get('temperature', 0.6),
            'top_p': kwargs.get('top_p', 0.95),
            'max_tokens': kwargs.get('max_tokens', 4000),
            'stream': kwargs.get('stream', False),
            'timeout': kwargs.get('timeout', 90)  # 90 second timeout
        }

        # Only add JSON schema for non-thinking models
        # Thinking models need freedom to output <thinking> tags
        if not is_thinking_model:
            json_schema = {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "topic": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "case_citation": {"type": "string"},
                    "reasoning": {"type": "string"}
                },
                "required": ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"],
                "additionalProperties": False
            }

            request_params['response_format'] = {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'legal_training_sample',
                    'strict': True,
                    'schema': json_schema
                }
            }

        response = self.client.chat.completions.create(**request_params)

        return {
            'text': response.choices[0].message.content.strip(),
            'tokens_used': response.usage.total_tokens,
            'finish_reason': response.choices[0].finish_reason
        }

    def get_rate_limits(self) -> Dict[str, int]:
        """Get Cerebras rate limits."""
        return {
            'requests_per_minute': 600,  # 14400/day conservative
            'tokens_per_minute': 48000  # 60k/min with buffer
        }

    def get_fallback_order(self) -> list:
        """Get Cerebras model fallback order."""
        return CEREBRAS_FALLBACK_ORDER


class OllamaProvider(BaseLLMProvider):
    """Ollama Cloud provider implementation."""

    def __init__(self, api_key: str, base_url: str = 'https://ollama.com/api'):
        super().__init__(api_key)
        self.base_url = base_url

    def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """
        Generate completion using Ollama Cloud API.

        Uses Ollama's native API format (NOT OpenAI-compatible).
        Response structure:
        {
          "message": {"role": "assistant", "content": "..."},
          "done": true,
          "done_reason": "stop",
          "prompt_eval_count": N,
          "eval_count": M
        }
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False
        }

        try:
            response = requests.post(
                f'{self.base_url}/chat',
                headers=headers,
                json=payload,
                timeout=kwargs.get('timeout', 90)
            )
            response.raise_for_status()

            data = response.json()

            # Extract content from Ollama-specific response format
            content = data['message']['content'].strip()

            # Calculate token usage from prompt_eval_count + eval_count
            prompt_tokens = data.get('prompt_eval_count', 0)
            completion_tokens = data.get('eval_count', 0)
            tokens_used = prompt_tokens + completion_tokens

            finish_reason = data.get('done_reason', 'stop')

            return {
                'text': content,
                'tokens_used': tokens_used,
                'finish_reason': finish_reason
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama Cloud API error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Ollama Cloud response format error: missing key {str(e)}")

    def get_rate_limits(self) -> Dict[str, int]:
        """Get Ollama Cloud rate limits."""
        return {
            'requests_per_minute': 60,  # Conservative estimate
            'tokens_per_minute': 10000  # Conservative estimate
        }

    def get_fallback_order(self) -> list:
        """Get Ollama Cloud model fallback order."""
        return OLLAMA_FALLBACK_ORDER


class GoogleProvider(BaseLLMProvider):
    """Google AI Studio (Gemini) provider implementation."""

    def __init__(self, api_key: str, base_url: str = 'https://generativelanguage.googleapis.com/v1beta'):
        super().__init__(api_key)
        self.base_url = base_url

    def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """
        Generate completion using Google Gemini API.

        Uses REST API directly for better control and compatibility.
        Gemini requires BOTH responseMimeType AND responseSchema for structured output.
        """
        headers = {
            'Content-Type': 'application/json'
        }

        # Define JSON schema for legal training samples
        json_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Unique sample identifier"},
                "question": {"type": "string", "description": "Legal question"},
                "answer": {"type": "string", "description": "Comprehensive legal answer"},
                "topic": {"type": "string", "description": "Practice area and subtopic"},
                "difficulty": {"type": "string", "description": "Difficulty level", "enum": ["basic", "intermediate", "advanced", "expert"]},
                "case_citation": {"type": "string", "description": "Relevant case law or statutory references"},
                "reasoning": {"type": "string", "description": "Step-by-step legal reasoning"}
            },
            "required": ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]
        }

        # Gemini API expects content in a specific format
        payload = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }],
            'generationConfig': {
                'temperature': kwargs.get('temperature', 0.9),
                'maxOutputTokens': kwargs.get('max_tokens', 4000),
                'topP': kwargs.get('top_p', 1),
                'responseMimeType': 'application/json',  # Force JSON output
                'responseSchema': json_schema  # Define structure
            }
        }

        try:
            # Gemini API endpoint format: /v1beta/models/{model}:generateContent
            url = f'{self.base_url}/models/{model}:generateContent?key={self.api_key}'

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=kwargs.get('timeout', 90)
            )
            response.raise_for_status()

            data = response.json()

            # Extract content from Gemini response
            if 'candidates' not in data or len(data['candidates']) == 0:
                raise Exception("No response candidates from Gemini API")

            candidate = data['candidates'][0]
            content = candidate['content']['parts'][0]['text'].strip()

            # Get token usage from usageMetadata
            usage = data.get('usageMetadata', {})
            tokens_used = usage.get('totalTokenCount', 0)

            finish_reason = candidate.get('finishReason', 'STOP')

            return {
                'text': content,
                'tokens_used': tokens_used,
                'finish_reason': finish_reason
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Google AI Studio API error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Google AI Studio response format error: {str(e)}")

    def get_rate_limits(self) -> Dict[str, int]:
        """Get Google AI Studio rate limits."""
        return {
            'requests_per_minute': 60,  # Gemini API default (varies by tier)
            'tokens_per_minute': 32000  # Conservative estimate
        }

    def get_fallback_order(self) -> list:
        """Get Google (Gemini) model fallback order."""
        return GOOGLE_FALLBACK_ORDER


class MistralProvider(BaseLLMProvider):
    """Mistral AI provider implementation."""

    def __init__(self, api_key: str, base_url: str = 'https://api.mistral.ai/v1'):
        super().__init__(api_key)
        self.base_url = base_url

    def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """
        Generate completion using Mistral AI API.

        Uses OpenAI-compatible chat completions endpoint.
        Mistral API is compatible with OpenAI's format but uses their own models.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': kwargs.get('temperature', 0.9),
            'max_tokens': kwargs.get('max_tokens', 4000),
            'top_p': kwargs.get('top_p', 1),
            'stream': False,
            'response_format': {'type': 'json_object'}  # Force JSON output
        }

        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=kwargs.get('timeout', 90)
            )
            response.raise_for_status()

            data = response.json()

            # Extract from OpenAI-compatible response
            if 'choices' not in data or len(data['choices']) == 0:
                raise Exception("No response choices from Mistral API")

            choice = data['choices'][0]
            content = choice['message']['content'].strip()

            # Get token usage
            usage = data.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)

            finish_reason = choice.get('finish_reason', 'stop')

            return {
                'text': content,
                'tokens_used': tokens_used,
                'finish_reason': finish_reason
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Mistral AI API error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Mistral AI response format error: {str(e)}")

    def get_rate_limits(self) -> Dict[str, int]:
        """Get Mistral AI rate limits."""
        return {
            'requests_per_minute': 60,  # Conservative estimate for free tier
            'tokens_per_minute': 32000  # Conservative estimate
        }

    def get_fallback_order(self) -> list:
        """Get Mistral model fallback order."""
        return MISTRAL_FALLBACK_ORDER


class LLMProviderFactory:
    """
    Factory class for creating LLM provider instances.
    Handles provider selection and instantiation.
    Supports both database-driven (preferred) and config-based (fallback) modes.
    """

    @staticmethod
    def get_provider_from_db(provider_name: str) -> BaseLLMProvider:
        """
        Get provider instance by name from database (preferred method).

        Args:
            provider_name: Name of the provider ('groq', 'cerebras', 'ollama', 'google', 'mistral')

        Returns:
            Provider instance

        Raises:
            ValueError: If provider name is unknown or not enabled
        """
        from models import Provider, ProviderConfig

        # Query database for provider
        provider = Provider.query.filter_by(id=provider_name).first()
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        if not provider.enabled:
            raise ValueError(f"Provider {provider_name} is not enabled")

        # Get provider config (API key)
        config = ProviderConfig.query.filter_by(provider_id=provider_name).first()
        if not config or not config.has_api_key():
            raise ValueError(f"Provider {provider_name} has no API key configured")

        api_key = config.get_api_key()

        # Create provider instance based on type
        if provider_name == 'groq':
            return GroqProvider(api_key)
        elif provider_name == 'cerebras':
            return CerebrasProvider(api_key)
        elif provider_name == 'ollama':
            return OllamaProvider(api_key, provider.base_url)
        elif provider_name == 'google':
            return GoogleProvider(api_key, provider.base_url)
        elif provider_name == 'mistral':
            return MistralProvider(api_key, provider.base_url)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    @staticmethod
    def get_provider(provider_name: str, use_db: bool = True) -> BaseLLMProvider:
        """
        Get provider instance by name from encrypted database.

        SECURITY: API keys are ONLY loaded from encrypted database storage.
        No fallback to config.py or environment variables.

        Args:
            provider_name: Name of the provider ('groq', 'cerebras', 'ollama', 'google', 'mistral')
            use_db: Must be True (parameter kept for backward compatibility)

        Returns:
            Provider instance

        Raises:
            ValueError: If provider name is unknown, not enabled, or API key not configured
            Exception: If database connection fails
        """
        if not use_db:
            raise ValueError("Database-only mode is enforced. API keys cannot be loaded from config.py")

        # Always use database - no fallback allowed
        return LLMProviderFactory.get_provider_from_db(provider_name)

    @staticmethod
    def get_all_providers(use_db: bool = True) -> Dict[str, BaseLLMProvider]:
        """
        Get all enabled providers from encrypted database.

        SECURITY: API keys are ONLY loaded from encrypted database storage.

        Args:
            use_db: Must be True (parameter kept for backward compatibility)

        Returns:
            Dictionary mapping provider names to provider instances

        Raises:
            ValueError: If use_db is False
        """
        if not use_db:
            raise ValueError("Database-only mode is enforced. API keys cannot be loaded from config.py")

        providers = {}
        from models import Provider

        db_providers = Provider.query.filter_by(enabled=True).all()
        for provider in db_providers:
            try:
                providers[provider.id] = LLMProviderFactory.get_provider_from_db(provider.id)
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize provider {provider.id}: {e}")

        return providers

    @staticmethod
    def get_rate_limits(provider_name: str, use_db: bool = True) -> Dict[str, int]:
        """
        Get rate limits for a specific provider from database.

        Args:
            provider_name: Name of the provider ('groq', 'cerebras', 'ollama', 'google', 'mistral')
            use_db: Must be True (parameter kept for backward compatibility)

        Returns:
            Dictionary with 'requests_per_minute' and 'tokens_per_minute'

        Raises:
            ValueError: If provider name is unknown or use_db is False
        """
        if not use_db:
            raise ValueError("Database-only mode is enforced. Rate limits must be loaded from database")

        from models import Provider

        provider = Provider.query.filter_by(id=provider_name).first()
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")

        return {
            'requests_per_minute': provider.requests_per_minute,
            'tokens_per_minute': provider.tokens_per_minute
        }

    @staticmethod
    def get_next_model_from_db(
        current_model: str,
        failed_models: list,
        provider_id: str
    ) -> Optional[str]:
        """
        Get next model in fallback order for a provider from database.

        Args:
            current_model: Model that just failed
            failed_models: List of models that have failed
            provider_id: Provider ID

        Returns:
            Next model to try, or None if all exhausted
        """
        from models import Model

        # Get all enabled models for this provider, ordered by fallback priority
        models = Model.query.filter_by(provider_id=provider_id, enabled=True)\
                           .order_by(Model.fallback_priority).all()

        fallback_order = [m.model_id for m in models]

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

        return None  # No models left to try

    @staticmethod
    def get_next_model(
        current_model: str,
        failed_models: list,
        provider: BaseLLMProvider,
        provider_id: str = None,
        use_db: bool = True
    ) -> Optional[str]:
        """
        Get next model in fallback order for a provider.

        Args:
            current_model: Model that just failed
            failed_models: List of models that have failed
            provider: Provider instance
            provider_id: Provider ID (required if use_db=True)
            use_db: If True, load from database; if False, use provider's get_fallback_order() (default: True)

        Returns:
            Next model to try, or None if all exhausted
        """
        if use_db and provider_id:
            try:
                return LLMProviderFactory.get_next_model_from_db(current_model, failed_models, provider_id)
            except Exception as e:
                print(f"⚠️  Database model fallback failed, using provider fallback order: {e}")

        # Fallback to provider's get_fallback_order() method
        fallback_order = provider.get_fallback_order()

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

        return None  # No models left to try
