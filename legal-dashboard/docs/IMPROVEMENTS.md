# Backend Improvements & Fixes

## Executive Summary

This document outlines critical issues found in the AI generation system and proposed solutions, including:
1. **Model Switching Bug** - Why Groq API gets stuck and doesn't relocate to another model
2. **E2E Test Suite** - Comprehensive tests for multi-provider generation
3. **Backend Code Refactoring** - High-quality code improvements

---

## 1. MODEL SWITCHING BUG ANALYSIS

### Problem

The Groq API sometimes gets stuck and doesn't switch to another model even when alternatives are available.

### Root Causes

#### Issue 1: **Narrow Error Detection**
**Location**: `api_server.py` lines 608-620

```python
except Exception as e:
    error_str = str(e).lower()
    # Categorize errors to determine if model switch is needed
    error_type = "general"
    if any(keyword in error_str for keyword in ['model', 'unavailable', 'not found', 'does not exist']):
        error_type = "model_unavailable"
    elif any(keyword in error_str for keyword in ['rate limit', 'quota', 'too many requests']):
        error_type = "rate_limit"
    elif any(keyword in error_str for keyword in ['timeout', 'timed out']):
        error_type = "timeout"
```

**Problem**: The error detection is too specific. Groq API errors might use different wording like:
- "Resource exhausted" instead of "rate limit"
- "Service temporarily unavailable" instead of "unavailable"
- "Model busy" instead of "model unavailable"

#### Issue 2: **Limited Model Switching Triggers**
**Location**: `api_server.py` lines 214-231

```python
# Check if we should switch models
should_switch_model = False

# Check error type for model unavailability
if error and '[model_unavailable]' in error:
    should_switch_model = True

# Switch model on rate limit errors (key requirement!)
if error and '[rate_limit]' in error:
    should_switch_model = True

# Switch model if too many consecutive failures (5+)
if batch_generation_state['consecutive_failures'] >= 5:
    should_switch_model = True
```

**Problem**: Only 3 specific conditions trigger model switching:
1. `[model_unavailable]` in error → but generic errors won't match
2. `[rate_limit]` in error → but "resource exhausted" won't match
3. 5+ consecutive failures → requires 5 failures before trying another model (wasteful)

#### Issue 3: **Timeout Errors Not Handled**
**Problem**: Timeout errors are detected but don't trigger model switching. A slow/overloaded model should trigger failover immediately.

#### Issue 4: **No Cross-Provider Fallback**
**Problem**: The fallback logic only works within Groq models. If Groq is down entirely, it never tries Cerebras as a backup.

### Solution

#### Fix 1: Broaden Error Detection
```python
def categorize_error(error_str: str) -> str:
    """Categorize error with broader pattern matching"""
    error_lower = error_str.lower()

    # Model unavailability (broad patterns)
    if any(keyword in error_lower for keyword in [
        'model', 'unavailable', 'not found', 'does not exist',
        'busy', 'overloaded', 'capacity', 'service unavailable'
    ]):
        return "model_unavailable"

    # Rate limiting (broad patterns)
    elif any(keyword in error_lower for keyword in [
        'rate limit', 'quota', 'too many requests',
        'resource exhausted', 'throttled', 'limited'
    ]):
        return "rate_limit"

    # Timeout (should trigger immediate switch)
    elif any(keyword in error_lower for keyword in [
        'timeout', 'timed out', 'deadline exceeded', 'took too long'
    ]):
        return "timeout"

    # Connection errors (should trigger switch)
    elif any(keyword in error_lower for keyword in [
        'connection', 'network', 'refused', 'unreachable'
    ]):
        return "connection_error"

    return "general"
```

#### Fix 2: More Aggressive Switching
```python
# Switch model on ANY critical error, not just specific ones
should_switch_model = False

if error:
    error_category = categorize_error(error)

    # Immediate switch for these errors
    if error_category in ['model_unavailable', 'rate_limit', 'timeout', 'connection_error']:
        should_switch_model = True
        print(f"⚠️ {error_category.upper()} detected, switching model")

    # Switch after 3 failures (not 5)
    elif batch_generation_state['consecutive_failures'] >= 3:
        should_switch_model = True
        print(f"⚠️ 3 consecutive failures, switching model")
```

#### Fix 3: Cross-Provider Fallback
```python
def get_next_provider_and_model(current_provider: str, current_model: str,
                                failed_providers: dict) -> tuple:
    """Get next provider/model combo, including cross-provider fallback"""

    # Try next model in same provider first
    if current_provider == 'groq':
        next_model = get_next_model(current_model, failed_providers.get('groq', []))
        if next_model:
            return 'groq', next_model

        # If all Groq models failed, try Cerebras
        if 'cerebras' not in failed_providers or not failed_providers['cerebras']:
            return 'cerebras', PROVIDERS['cerebras']['default_model']

    elif current_provider == 'cerebras':
        # Try Groq if Cerebras fails
        if 'groq' not in failed_providers or not failed_providers['groq']:
            return 'groq', PROVIDERS['groq']['default_model']

    return None, None  # All providers exhausted
```

#### Fix 4: Early Detection & Logging
```python
# Add detailed logging for debugging
def log_error_detail(error: str, provider: str, model: str):
    """Log error details for debugging model switching"""
    error_category = categorize_error(error)
    print(f"❌ Generation Error:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   Category: {error_category}")
    print(f"   Message: {error[:200]}")  # First 200 chars
    return error_category
```

---

## 2. E2E TEST SUITE

### Overview

Comprehensive End-to-End tests created in `tests/test_e2e_generation.py`:

### Test Coverage

1. **TestProviderEndpoints** - Test provider/model listing
   - `test_get_providers()` - Verify providers API
   - `test_get_models()` - Verify models from all providers

2. **TestSingleGeneration** - Single sample generation
   - `test_groq_single_generation()` - Generate with Groq
   - `test_cerebras_single_generation()` - Generate with Cerebras
   - `test_invalid_provider()` - Error handling

3. **TestBatchGeneration** - Batch processing
   - `test_start_batch_groq()` - Start batch with Groq
   - `test_start_batch_cerebras()` - Start batch with Cerebras
   - `test_batch_status_tracking()` - Monitor progress
   - `test_batch_stop()` - Stop running batch
   - `test_batch_history()` - Check batch history

4. **TestDataIntegrity** - Data validation
   - `test_unique_ids_per_provider()` - ID uniqueness
   - `test_required_fields_present()` - Field validation
   - `test_metadata_tracking()` - Timestamp tracking
   - `test_batch_id_tracking()` - Batch association

5. **TestProviderComparison** - Quality comparison
   - `test_cerebras_thinking_quality()` - Reasoning depth
   - `test_groq_response_time()` - Latency testing
   - `test_cerebras_response_time()` - Speed comparison

6. **TestErrorHandling** - Edge cases
   - `test_invalid_difficulty()` - Invalid inputs
   - `test_batch_already_running()` - Concurrent batches
   - `test_target_count_validation()` - Validation logic

### Running Tests

```bash
# Install dependencies
cd legal-dashboard/tests
pip install -r requirements.txt

# Run all tests
pytest test_e2e_generation.py -v

# Run specific test class
pytest test_e2e_generation.py::TestSingleGeneration -v

# Run with coverage
pytest test_e2e_generation.py --cov=api_server --cov-report=html
```

---

## 3. BACKEND CODE REFACTORING

### Current Issues

1. **Monolithic `api_server.py`** - 1367 lines, hard to maintain
2. **Hardcoded API Keys** - Security risk
3. **No Type Hints** - Harder to debug
4. **Mixed Concerns** - Business logic + HTTP routing in same file
5. **Limited Error Handling** - Generic exception catching
6. **No Logging** - Print statements instead of proper logging

### Proposed Structure

```
legal-dashboard/
├── api_server.py           # Main Flask app (routes only)
├── config.py               # Configuration & environment variables
├── models/
│   ├── __init__.py
│   ├── database.py         # SQLAlchemy models
│   └── schemas.py          # Pydantic schemas for validation
├── services/
│   ├── __init__.py
│   ├── llm_providers.py    # LLMProviderFactory (refactored)
│   ├── generation.py       # Sample generation logic
│   └── batch_worker.py     # Batch generation worker
├── utils/
│   ├── __init__.py
│   ├── circuit_breaker.py  # Circuit breaker class
│   ├── error_handler.py    # Centralized error handling
│   └── validators.py       # Input validation
└── tests/
    ├── __init__.py
    ├── test_e2e_generation.py
    ├── test_providers.py
    └── test_validators.py
```

### Key Refactorings

#### 1. Externalize Configuration

**Create `config.py`:**
```python
import os
from dataclasses import dataclass
from typing import Dict

@dataclass
class ProviderConfig:
    api_key: str
    enabled: bool
    default_model: str
    requests_per_minute: int
    tokens_per_minute: int

class Config:
    # Load from environment variables
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'gsk_...')
    CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY', 'csk_...')

    PROVIDERS: Dict[str, ProviderConfig] = {
        'groq': ProviderConfig(
            api_key=GROQ_API_KEY,
            enabled=True,
            default_model='llama-3.3-70b-versatile',
            requests_per_minute=25,
            tokens_per_minute=5500
        ),
        'cerebras': ProviderConfig(
            api_key=CEREBRAS_API_KEY,
            enabled=True,
            default_model='qwen-3-235b-a22b-thinking-2507',
            requests_per_minute=600,
            tokens_per_minute=48000
        )
    }

    # Database
    DATABASE_URI = 'sqlite:///batches.db'

    # Paths
    PARQUET_PATH = Path("train.parquet")
```

#### 2. Extract Provider Logic

**Create `services/llm_providers.py`:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from groq import Groq
from cerebras.cloud.sdk import Cerebras

class BaseLLMProvider(ABC):
    """Abstract base for LLM providers"""

    @abstractmethod
    def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict:
        pass

    @abstractmethod
    def get_rate_limits(self) -> Dict:
        pass

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict:
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return {
            'text': response.choices[0].message.content.strip(),
            'tokens_used': response.usage.total_tokens,
            'finish_reason': response.choices[0].finish_reason
        }

    def get_rate_limits(self) -> Dict:
        return {'requests_per_minute': 25, 'tokens_per_minute': 5500}

class CerebrasProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = Cerebras(api_key=api_key)

    def generate_completion(self, model: str, prompt: str, **kwargs) -> Dict:
        # ... implementation ...
        pass
```

#### 3. Add Proper Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler('api_server.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use throughout code
logger.info(f"Starting batch generation with {provider}/{model}")
logger.error(f"Generation failed: {error}", exc_info=True)
logger.warning(f"Rate limit reached, waiting {wait_time}s")
```

#### 4. Add Type Hints

```python
from typing import Optional, Dict, List, Tuple

def generate_single_sample(
    practice_area: str,
    topic: str,
    difficulty: str,
    counter: int,
    provider: str = 'groq',
    model: Optional[str] = None,
    reasoning_instruction: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Tuple[Optional[Dict], int, float, Optional[str]]:
    """
    Generate a single legal Q&A sample.

    Returns:
        Tuple of (sample_dict, tokens_used, elapsed_time, error_message)
    """
    pass
```

#### 5. Centralized Error Handling

**Create `utils/error_handler.py`:**
```python
class GenerationError(Exception):
    """Base exception for generation errors"""
    pass

class ModelUnavailableError(GenerationError):
    """Model is unavailable or overloaded"""
    pass

class RateLimitError(GenerationError):
    """Rate limit exceeded"""
    pass

class TimeoutError(GenerationError):
    """Request timed out"""
    pass

def parse_error(exception: Exception) -> GenerationError:
    """Convert generic exceptions to specific error types"""
    error_str = str(exception).lower()

    if any(k in error_str for k in ['rate limit', 'quota', 'throttled']):
        return RateLimitError(str(exception))
    elif any(k in error_str for k in ['unavailable', 'overloaded', 'busy']):
        return ModelUnavailableError(str(exception))
    elif any(k in error_str for k in ['timeout', 'deadline']):
        return TimeoutError(str(exception))
    else:
        return GenerationError(str(exception))
```

---

## 4. IMPLEMENTATION PRIORITY

### Phase 1: Critical Fixes (Immediate)
1. ✅ Fix model switching logic (broaden error detection)
2. ✅ Reduce failure threshold from 5 to 3
3. ✅ Add timeout error handling

### Phase 2: Testing & Validation (Week 1)
4. ✅ E2E test suite complete
5. Run tests to validate multi-provider functionality
6. Document test results

### Phase 3: Code Quality (Week 2)
7. Extract configuration to `config.py`
8. Add type hints throughout codebase
9. Implement proper logging

### Phase 4: Architecture (Week 3)
10. Refactor providers into separate classes
11. Extract business logic from routes
12. Add comprehensive error handling

---

## 5. TESTING CHECKLIST

Before deploying fixes:

- [ ] Run E2E test suite
- [ ] Test Groq model switching with simulated failures
- [ ] Test Cerebras failover when Groq is unavailable
- [ ] Verify batch generation completes with mixed providers
- [ ] Check rate limiting works correctly per provider
- [ ] Validate metadata tracking (timestamps, provider, model, batch_id)
- [ ] Test concurrent batch prevention
- [ ] Verify circuit breaker functionality

---

## 6. MONITORING & ALERTS

Recommended monitoring after deployment:

```python
# Add metrics tracking
class MetricsTracker:
    def __init__(self):
        self.model_switches = 0
        self.provider_switches = 0
        self.rate_limit_hits = 0
        self.timeout_errors = 0

    def log_model_switch(self, from_model, to_model, reason):
        self.model_switches += 1
        logger.warning(f"Model switch #{self.model_switches}: {from_model} → {to_model} ({reason})")

    def should_alert(self) -> bool:
        # Alert if too many switches (indicates systemic issue)
        return self.model_switches > 10 or self.timeout_errors > 20
```

---

## CONCLUSION

The model switching bug is due to:
1. ❌ Too narrow error pattern matching
2. ❌ Only 3 specific conditions trigger switching
3. ❌ Requires 5 failures before switch (wasteful)
4. ❌ No cross-provider fallback

Fixes include:
1. ✅ Broader error categorization
2. ✅ Switch on ANY critical error
3. ✅ Reduce threshold to 3 failures
4. ✅ Add cross-provider fallback
5. ✅ Comprehensive E2E tests
6. ✅ Code quality improvements

All solutions are documented and ready for implementation.
