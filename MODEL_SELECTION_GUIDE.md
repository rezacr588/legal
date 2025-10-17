# Model Selection & Multi-Model Generation Guide

## Overview

The UK Legal Dataset API now supports **dynamic model selection** from all available Groq models. You can switch between models on-the-fly for both single and batch generation.

## Available Models

The system automatically fetches available models from Groq. As of the latest check:

### Text Generation Models (19 total)
- `llama-3.3-70b-versatile` (Default) - Best overall performance
- `meta-llama/llama-4-maverick-17b-128e-instruct` - Latest Llama 4
- `openai/gpt-oss-120b` - Large compound model
- `groq/compound-mini` - Faster, smaller model
- `moonshotai/kimi-k2-instruct-0905` - Kimi model
- `llama-3.1-8b-instant` - Fast, lightweight
- `allam-2-7b` - Multilingual model
- And 12 more...

## Fetch Available Models

```bash
# Get all models
curl http://127.0.0.1:5000/api/models | jq

# Response
{
  "success": true,
  "models": [
    {
      "id": "llama-3.3-70b-versatile",
      "name": "llama-3.3-70b-versatile",
      "context_window": 131072,
      "owned_by": "groq"
    },
    ...
  ],
  "default_model": "llama-3.3-70b-versatile"
}
```

## Usage

### Single Sample Generation with Model Selection

```bash
# Generate with default model
curl -X POST http://127.0.0.1:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "Contract Law",
    "topic": "Consideration",
    "difficulty": "intermediate"
  }'

# Generate with specific model
curl -X POST http://127.0.0.1:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "Contract Law",
    "topic": "Consideration",
    "difficulty": "intermediate",
    "model": "llama-3.1-8b-instant"
  }'
```

### Batch Generation with Model Selection

```bash
# Start batch with default model
curl -X POST http://127.0.0.1:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{"target_count": 2100}'

# Start batch with specific model
curl -X POST http://127.0.0.1:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_count": 2100,
    "model": "groq/compound-mini"
  }'

# Monitor progress (shows current model)
curl http://127.0.0.1:5000/api/generate/batch/status
```

### Python Example

```python
import requests

# Get available models
models_resp = requests.get('http://127.0.0.1:5000/api/models').json()

if models_resp['success']:
    # Filter for text models
    text_models = [m for m in models_resp['models']
                   if 'whisper' not in m['id'].lower()]

    # Try each model
    for model in text_models[:3]:
        print(f"Testing {model['id']}...")

        response = requests.post(
            'http://127.0.0.1:5000/api/generate',
            json={
                'practice_area': 'Contract Law',
                'topic': 'Formation',
                'difficulty': 'basic',
                'model': model['id']
            },
            timeout=30
        )

        if response.json().get('success'):
            print(f"  ✓ Success: {response.json()['tokens_used']} tokens")
        else:
            print(f"  ✗ Failed: {response.json().get('error')}")
```

## Model Recommendations

### For Speed
- `llama-3.1-8b-instant` - Fastest, lowest token usage
- `groq/compound-mini` - Good balance

### For Quality
- `llama-3.3-70b-versatile` (Default) - Best legal accuracy
- `meta-llama/llama-4-maverick-17b-128e-instruct` - Latest Llama 4
- `openai/gpt-oss-120b` - Most capable

### For Cost Efficiency
- `llama-3.1-8b-instant` - 50-70% fewer tokens than 70B models
- `allam-2-7b` - Small, efficient

## React UI Integration

The React frontend now includes a model selector:

1. **Model Dropdown** - Select from all available text models
2. **Context Window Display** - Shows each model's context limit
3. **Real-Time Status** - Displays current model during batch generation
4. **Auto-Refresh** - Models list refreshes on load

### Using the UI

1. Open http://localhost:5173
2. Navigate to "🤖 LLM Generation" section
3. Select model from dropdown
4. Set target count
5. Click "▶️ Start Batch"
6. Monitor progress in real-time

## Advanced Usage

### Multi-Model Dataset

Generate samples using different models for diversity:

```python
models = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'groq/compound-mini']

for i, model in enumerate(models):
    print(f"Batch {i+1} with {model}")

    requests.post('http://127.0.0.1:5000/api/generate/batch/start', json={
        'target_count': 2100 + (i * 50),
        'model': model
    })

    # Wait for completion
    while True:
        status = requests.get('http://127.0.0.1:5000/api/generate/batch/status').json()
        if not status['running']:
            break
        time.sleep(5)

    print(f"  Generated {status['samples_generated']} samples")
```

### Rate Limit Handling

Different models may have different rate limits. The system automatically handles:
- 25 requests/minute limit
- 5,500 tokens/minute limit
- Waits when limits are hit
- Auto-saves every 10 samples

## Testing Models

Run the test script to verify all endpoints work with model selection:

```bash
python3 test_api.py
```

Expected output:
```
============================================================
UK Legal Dataset API Test Suite
============================================================

Testing: Health Check
  GET http://127.0.0.1:5000/api/health
  ✓ PASSED (Status: 200)

Testing: Get Available Models
  GET http://127.0.0.1:5000/api/models
  ✓ PASSED (Status: 200)

...

Total Tests: 11
Passed: 11
Failed: 0
Success Rate: 100.0%
```

## Troubleshooting

### Rate Limit Errors
```json
{
  "error": "Error code: 429 - Rate limit reached..."
}
```
**Solution**: Wait 24 hours or use a lighter model like `llama-3.1-8b-instant`

### Model Not Found
```json
{
  "error": "Model not found: invalid-model"
}
```
**Solution**: Check available models with `/api/models` endpoint

### Timeout Issues
- **Large models (70B+)**: May take 2-5 seconds per sample
- **Small models (7-8B)**: Usually 1-2 seconds per sample
- Adjust timeout in requests accordingly

## New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | GET | Get all available Groq models |
| `/api/stats/detailed` | GET | Detailed statistics with breakdowns |
| `/api/samples/random` | GET | Get random samples (with filters) |
| `/api/search` | GET | Search samples by query |

See [API_USAGE.md](API_USAGE.md) for complete documentation.

## Performance Comparison

Based on testing (approximate):

| Model | Tokens/Sample | Speed | Quality |
|-------|---------------|-------|---------|
| llama-3.3-70b-versatile | 800-1200 | Medium | Excellent |
| llama-3.1-8b-instant | 600-800 | Fast | Good |
| groq/compound-mini | 700-900 | Fast | Very Good |
| openai/gpt-oss-120b | 1000-1500 | Slow | Excellent |

## Future Enhancements

- [ ] Model performance analytics
- [ ] Automatic model selection based on difficulty
- [ ] Cost tracking per model
- [ ] Quality comparison across models
- [ ] Ensemble generation (multiple models per sample)

---

**Last Updated**: October 2025
**Version**: 2.1 (Model Selection Feature)
