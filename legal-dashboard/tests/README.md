# Tests Directory

This directory contains all test scripts for the Legal Training Dataset API.

## Test Categories

### 1. Sample Type Tests
Tests for validating sample type generation and structure:
- **`test_all_sample_types.py`** - Tests all 4 sample types with Groq provider
- **`test_ollama_all_sample_types.py`** - Tests all 4 sample types with Ollama Cloud ⭐
- **`test_ollama_sample_type.py`** - Single sample type test with Ollama
- **`test_sample_types.py`** - Sample type generation tests
- **`test_sample_types_alignment.py`** - Validates alignment between prompts and validation
- **`test_structure_validation.py`** - Structure validation tests

### 2. API Tests
Tests for API endpoints and functionality:
- **`test_api_functionality.py`** - Parameter passing and API chain tests
- **`test_generator_api_comprehensive.py`** - Comprehensive API validation suite ⭐
- **`test_stop_batch.py`** - Batch stop endpoint tests

### 3. Provider Tests
Tests for different LLM providers:
- **`test_all_cerebras_models.py`** - Tests all Cerebras models
- **`test_coder_model.py`** - Tests Cerebras qwen-3-coder-480b model
- **`test_single_question_all_models.py`** - Compares all models with identical question
- **`test_ollama_api.py`** - Ollama Cloud API connectivity test

### 4. End-to-End Tests
- **`test_e2e_generation.py`** - Full end-to-end generation pipeline test

## Running Tests

### Prerequisites
```bash
# Ensure environment variables are set
export GROQ_API_KEY="your_groq_key"
export CEREBRAS_API_KEY="your_cerebras_key"
export OLLAMA_API_KEY="your_ollama_key"
```

### Run Individual Tests
```bash
cd /Users/rezazeraat/Desktop/Data/legal-dashboard

# Test all sample types with Ollama (recommended)
python3 tests/test_ollama_all_sample_types.py

# Comprehensive API validation
python3 tests/test_generator_api_comprehensive.py

# Test specific provider
python3 tests/test_all_cerebras_models.py
```

### Run from Tests Directory
```bash
cd tests
python3 test_ollama_all_sample_types.py
```

## Test Requirements

Some tests have specific dependencies listed in `requirements.txt`.

## Key Test Scripts

### ⭐ Recommended for Validation
1. **`test_ollama_all_sample_types.py`** - Validates all 4 sample types with structure checking
2. **`test_generator_api_comprehensive.py`** - Complete API validation suite

### Development Tests
- **`test_sample_types_alignment.py`** - Ensures prompts match validation logic
- **`test_structure_validation.py`** - Validates IRAC/Educational/Client/Statutory structures

### Provider Comparison
- **`test_single_question_all_models.py`** - Fair comparison with identical input

## Test Results

Test results and validation reports can be found in the `docs/` directory:
- `docs/VALIDATION_ALIGNMENT_VERIFIED.md` - Latest validation results
- `docs/SAMPLE_TYPE_VALIDATION_COMPLETE.md` - Sample type system validation
- `docs/API_VALIDATION_REPORT.md` - API endpoint validation

## Adding New Tests

When adding new tests:
1. Follow naming convention: `test_<feature_name>.py`
2. Include docstring explaining test purpose
3. Add entry to this README
4. Document results in `docs/` if significant

## Notes

- Most tests require the Flask API to be running on port 5001
- Some tests make actual API calls and consume provider tokens
- Rate limits may affect test execution time
- Tests are designed to be idempotent (can run multiple times)
