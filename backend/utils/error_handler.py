"""
Error handling utilities for LLM API calls.
Provides comprehensive error categorization for both Groq and Cerebras providers.
"""

from typing import Literal

ErrorCategory = Literal[
    "authentication",
    "model_unavailable",
    "rate_limit",
    "timeout",
    "connection_error",
    "server_error",
    "bad_request",
    "general"
]


def categorize_error(error_str: str, provider: str = 'groq') -> ErrorCategory:
    """
    Categorize error with comprehensive pattern matching for both Groq and Cerebras.

    Args:
        error_str: The error message string
        provider: The provider that generated the error

    Returns:
        Error category string for determining retry/fallback strategy
    """
    error_lower = error_str.lower()

    # Authentication errors (both providers)
    if any(keyword in error_lower for keyword in [
        'authentication', 'unauthorized', '401', 'invalid api key', 'api key'
    ]):
        return "authentication"

    # Model unavailability (broad patterns for both providers)
    if any(keyword in error_lower for keyword in [
        'model', 'unavailable', 'not found', 'does not exist', '404',
        'busy', 'overloaded', 'capacity', 'service unavailable', '503',
        'flex tier', '498'  # Groq-specific
    ]):
        return "model_unavailable"

    # Rate limiting (broad patterns for both providers)
    if any(keyword in error_lower for keyword in [
        'rate limit', 'quota', 'too many requests', '429',
        'resource exhausted', 'throttled', 'limited',
        'rpm', 'tpm'  # Requests/Tokens per minute
    ]):
        return "rate_limit"

    # Timeout (should trigger immediate switch)
    if any(keyword in error_lower for keyword in [
        'timeout', 'timed out', 'deadline exceeded', 'took too long', '408'
    ]):
        return "timeout"

    # Connection errors (should trigger switch)
    if any(keyword in error_lower for keyword in [
        'connection', 'network', 'refused', 'unreachable',
        'bad gateway', '502', 'gateway', 'dns'
    ]):
        return "connection_error"

    # Server errors (5xx)
    if any(keyword in error_lower for keyword in [
        '500', '502', '503', '504', 'internal server', 'server error'
    ]):
        return "server_error"

    # Bad request (usually non-retryable)
    if any(keyword in error_lower for keyword in [
        '400', 'bad request', 'invalid request', 'unprocessable', '422'
    ]):
        return "bad_request"

    return "general"


def should_switch_immediately(error_category: ErrorCategory) -> bool:
    """
    Determine if an error should trigger immediate model/provider switch.

    Args:
        error_category: The categorized error type

    Returns:
        True if should switch immediately, False otherwise
    """
    immediate_switch_categories = {
        'model_unavailable',
        'rate_limit',
        'timeout',
        'connection_error',
        'server_error'
    }
    return error_category in immediate_switch_categories
