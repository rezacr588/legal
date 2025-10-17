# Backend Refactoring - Modular Architecture Plan

**Status**: 🚧 IN PROGRESS
**Date**: October 11, 2025

---

## 📊 Current Status

✅ **Completed**:
- Directory structure created (`models/`, `services/`, `utils/`)
- `config.py` - All configuration and constants
- `utils/error_handler.py` - Error categorization module

⏳ **In Progress**:
- Remaining modules (circuit breaker, services, models)
- API server refactoring

---

## 🏗️ Target Architecture

```
legal-dashboard/
├── config.py                    # ✅ Configuration & constants
├── models/
│   ├── __init__.py             # ✅ Created
│   └── database.py             # Database models (SQLAlchemy)
├── services/
│   ├── __init__.py             # ✅ Created
│   ├── llm_service.py          # LLM provider classes (OOP)
│   ├── generation_service.py  # Generation logic
│   └── batch_service.py        # Batch management
├── utils/
│   ├── __init__.py             # ✅ Created
│   ├── error_handler.py        # ✅ Error categorization
│   └── circuit_breaker.py      # Circuit breaker class
└── api_server.py               # Flask routes only (refactored)
```

---

## 📦 Module Responsibilities

### `config.py` ✅
**Purpose**: Centralized configuration
**Contains**:
- Provider settings (API keys, rate limits)
- Model fallback orders
- Circuit breaker settings
- Legal topics
- Database URI

**Example**:
```python
from config import PROVIDERS, MODEL_FALLBACK_ORDER, CEREBRAS_FALLBACK_ORDER
```

### `utils/error_handler.py` ✅
**Purpose**: Error categorization logic
**Contains**:
- `categorize_error(error_str, provider)` - Returns error category
- `should_switch_immediately(error_category)` - Decision logic

**Example**:
```python
from utils.error_handler import categorize_error

error_cat = categorize_error(str(e), 'groq')
if error_cat == 'rate_limit':
    # Switch model
```

### `utils/circuit_breaker.py`
**Purpose**: Circuit breaker pattern implementation
**Contains**:
- `CircuitBreaker` class
- Methods: `is_open()`, `record_success()`, `record_failure()`, `get_summary()`

**Example**:
```python
from utils.circuit_breaker import CircuitBreaker

cb = CircuitBreaker()
if not cb.is_open('Contract Law - Formation'):
    # Generate sample
```

### `models/database.py`
**Purpose**: Database models and schemas
**Contains**:
- `BatchHistory` SQLAlchemy model
- Database initialization

**Example**:
```python
from models.database import BatchHistory, init_db

init_db(app)
batch = BatchHistory(batch_id=batch_id, ...)
```

### `services/llm_service.py`
**Purpose**: LLM provider abstraction (OOP)
**Contains**:
- `BaseLLMProvider` abstract class
- `GroqProvider` class
- `CerebrasProvider` class
- `LLMProviderFactory` class

**Example**:
```python
from services.llm_service import LLMProviderFactory

provider = LLMProviderFactory.get_provider('groq')
result = provider.generate(model='llama-3.3-70b-versatile', prompt=prompt)
```

**Class Structure**:
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, model: str, prompt: str, **kwargs) -> dict:
        pass

    @abstractmethod
    def get_rate_limits(self) -> dict:
        pass

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def generate(self, model, prompt, **kwargs):
        # Implementation

    def get_rate_limits(self):
        return {'requests_per_minute': 25, 'tokens_per_minute': 5500}

class CerebrasProvider(BaseLLMProvider):
    # Similar structure

class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_name: str) -> BaseLLMProvider:
        # Factory method
```

### `services/generation_service.py`
**Purpose**: Sample generation logic
**Contains**:
- `GenerationService` class
- `generate_single_sample()` method
- `get_next_model()` method
- `get_next_provider_and_model()` method

**Example**:
```python
from services.generation_service import GenerationService

service = GenerationService()
sample, tokens, elapsed, error = service.generate_single_sample(
    practice_area='Contract Law',
    topic='Formation',
    difficulty='basic',
    provider='groq'
)
```

**Class Structure**:
```python
class GenerationService:
    def __init__(self):
        self.provider_factory = LLMProviderFactory()

    def generate_single_sample(
        self,
        practice_area: str,
        topic: str,
        difficulty: str,
        counter: int,
        provider: str = 'groq',
        model: str = None,
        **kwargs
    ) -> tuple:
        # Generate single sample with error handling

    def get_next_model(
        self,
        current_model: str,
        failed_models: list,
        provider: str
    ) -> Optional[str]:
        # Get next model in fallback order

    def get_next_provider_and_model(
        self,
        current_provider: str,
        current_model: str,
        failed_models_by_provider: dict
    ) -> tuple:
        # Cross-provider fallback logic
```

### `services/batch_service.py`
**Purpose**: Batch generation orchestration
**Contains**:
- `BatchService` class
- `start_batch()` method
- `stop_batch()` method
- `get_status()` method
- Background worker logic

**Example**:
```python
from services.batch_service import BatchService

batch_service = BatchService()
batch_service.start_batch(target_count=2200, provider='groq')
status = batch_service.get_status()
```

**Class Structure**:
```python
class BatchService:
    def __init__(self):
        self.generation_service = GenerationService()
        self.circuit_breaker = CircuitBreaker()
        self.state = {
            'running': False,
            'current_provider': None,
            # ... other state fields
        }

    def start_batch(self, target_count: int, provider: str = 'groq', **kwargs):
        # Start background batch generation

    def stop_batch(self):
        # Stop running batch

    def get_status(self) -> dict:
        # Return current batch status

    def _worker(self, target_count: int, provider: str, model: str):
        # Background worker method
```

### `api_server.py` (Refactored)
**Purpose**: Flask routes only (thin layer)
**Contains**:
- Route definitions
- Request/response handling
- Dependency injection

**Example Structure**:
```python
from flask import Flask, jsonify, request
from services.generation_service import GenerationService
from services.batch_service import BatchService
from models.database import init_db

app = Flask(__name__)
init_db(app)

# Initialize services
generation_service = GenerationService()
batch_service = BatchService()

@app.route('/api/generate', methods=['POST'])
def generate_sample():
    data = request.json
    sample, tokens, elapsed, error = generation_service.generate_single_sample(
        practice_area=data.get('practice_area'),
        topic=data.get('topic'),
        difficulty=data.get('difficulty'),
        provider=data.get('provider', 'groq')
    )

    if error:
        return jsonify({'success': False, 'error': error}), 400

    return jsonify({'success': True, 'sample': sample, 'tokens_used': tokens})

@app.route('/api/generate/batch/start', methods=['POST'])
def start_batch():
    data = request.json
    batch_service.start_batch(
        target_count=data.get('target_count'),
        provider=data.get('provider', 'groq')
    )
    return jsonify({'success': True})

# ... other routes
```

---

## 🎯 Benefits of This Architecture

### 1. **Separation of Concerns**
- Configuration separate from logic
- Business logic separate from API routes
- Each module has a single responsibility

### 2. **Testability**
- Each service can be unit tested independently
- Mock dependencies easily
- Test business logic without Flask

### 3. **Maintainability**
- Easy to locate code (know which file to edit)
- Changes in one module don't affect others
- Clear dependencies

### 4. **Scalability**
- Easy to add new providers (just extend `BaseLLMProvider`)
- Easy to add new services
- Configuration centralized

### 5. **Readability**
- Smaller, focused files (vs 2000-line monolith)
- Clear class hierarchies
- Type hints throughout

---

## 🔄 Migration Path

### Step 1: Extract to Modules ✅
- Create directory structure ✅
- Create `config.py` ✅
- Create `utils/error_handler.py` ✅

### Step 2: Create Remaining Modules
- Create `utils/circuit_breaker.py`
- Create `models/database.py`
- Create `services/llm_service.py`
- Create `services/generation_service.py`
- Create `services/batch_service.py`

### Step 3: Refactor API Server
- Update imports
- Replace inline code with service calls
- Remove extracted code
- Test each endpoint

### Step 4: Testing
- Test all endpoints
- Verify batch generation works
- Check provider switching
- Validate error handling

---

## 📋 Next Steps

To complete this refactoring, I need to:

1. ⏳ Create `utils/circuit_breaker.py`
2. ⏳ Create `models/database.py`
3. ⏳ Create `services/llm_service.py` (most important - provider abstraction)
4. ⏳ Create `services/generation_service.py`
5. ⏳ Create `services/batch_service.py`
6. ⏳ Refactor `api_server.py` to use all modules
7. ⏳ Test the refactored system
8. ⏳ Update documentation

**Estimated Effort**: This is a significant refactoring (~4-6 hours of careful work)

**Risk**: Need to ensure no breaking changes to existing API

---

## ⚠️ Important Notes

### Compatibility
- All existing API endpoints remain unchanged
- Request/response formats stay the same
- Database schema unchanged
- Frontend requires no changes

### Testing Strategy
- Test each module independently
- Integration test after full refactoring
- Verify both Groq and Cerebras work
- Check batch generation
- Validate error handling and fallbacks

### Rollback Plan
- Keep backup of original `api_server.py`
- Can revert if issues found
- Gradual migration possible (hybrid approach)

---

## 💡 Design Principles

1. **SOLID Principles**:
   - Single Responsibility (each class has one job)
   - Open/Closed (easy to extend, hard to break)
   - Liskov Substitution (providers interchangeable)
   - Interface Segregation (small, focused interfaces)
   - Dependency Inversion (depend on abstractions)

2. **DRY (Don't Repeat Yourself)**:
   - Shared logic in base classes
   - Configuration centralized
   - Error handling reusable

3. **KISS (Keep It Simple)**:
   - Not over-engineered
   - Clear class hierarchies
   - Straightforward dependencies

4. **Separation of Concerns**:
   - Config ≠ Logic ≠ Routes
   - Each module independent
   - Clear boundaries

---

**Status**: Refactoring in progress. Modules being created systematically.
**Goal**: Clean, maintainable, OOP-based architecture without over-complication.
