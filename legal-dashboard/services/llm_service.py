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

from config import PROVIDERS, MODEL_FALLBACK_ORDER, CEREBRAS_FALLBACK_ORDER, OLLAMA_FALLBACK_ORDER, THINKING_MODELS


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


class LLMProviderFactory:
    """
    Factory class for creating LLM provider instances.
    Handles provider selection and instantiation.
    """

    @staticmethod
    def get_provider(provider_name: str) -> BaseLLMProvider:
        """
        Get provider instance by name.

        Args:
            provider_name: Name of the provider ('groq', 'cerebras', or 'ollama')

        Returns:
            Provider instance

        Raises:
            ValueError: If provider name is unknown or not enabled
        """
        if provider_name not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")

        config = PROVIDERS[provider_name]

        if not config['enabled']:
            raise ValueError(f"Provider {provider_name} is not enabled")

        if provider_name == 'groq':
            return GroqProvider(config['api_key'])
        elif provider_name == 'cerebras':
            return CerebrasProvider(config['api_key'])
        elif provider_name == 'ollama':
            return OllamaProvider(config['api_key'], config.get('base_url', 'https://ollama.com/api'))
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    @staticmethod
    def get_all_providers() -> Dict[str, BaseLLMProvider]:
        """
        Get all enabled providers.

        Returns:
            Dictionary mapping provider names to provider instances
        """
        providers = {}
        for name, config in PROVIDERS.items():
            if config['enabled']:
                try:
                    providers[name] = LLMProviderFactory.get_provider(name)
                except Exception as e:
                    print(f"Warning: Could not initialize provider {name}: {e}")
        return providers

    @staticmethod
    def get_rate_limits(provider_name: str) -> Dict[str, int]:
        """
        Get rate limits for a specific provider.

        Args:
            provider_name: Name of the provider ('groq', 'cerebras', or 'ollama')

        Returns:
            Dictionary with 'requests_per_minute' and 'tokens_per_minute'

        Raises:
            ValueError: If provider name is unknown
        """
        if provider_name not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")

        config = PROVIDERS[provider_name]
        return {
            'requests_per_minute': config.get('requests_per_minute', 25),
            'tokens_per_minute': config.get('tokens_per_minute', 5500)
        }

    @staticmethod
    def get_next_model(
        current_model: str,
        failed_models: list,
        provider: BaseLLMProvider
    ) -> Optional[str]:
        """
        Get next model in fallback order for a provider.

        Args:
            current_model: Model that just failed
            failed_models: List of models that have failed
            provider: Provider instance

        Returns:
            Next model to try, or None if all exhausted
        """
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
