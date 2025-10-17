# UK Legal Dataset API Usage Guide

## Quick Start

Start the unified backend:
```bash
./start_apps.sh
```

This starts:
- Flask API at http://localhost:5000
- React UI at http://localhost:5173

## API Endpoints

### 1. Get All Samples
```bash
curl http://localhost:5000/api/data
```

### 2. Get Statistics
```bash
curl http://localhost:5000/api/stats
```

Response includes:
- Total samples
- Difficulty distribution
- Top 10 topics
- File size

### 3. Generate Single Sample
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area": "Contract Law",
    "topic": "Formation of Contracts",
    "difficulty": "intermediate"
  }'
```

### 4. Start Batch Generation
```bash
curl -X POST http://localhost:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{"target_count": 2100}'
```

This runs in the background and auto-saves every 10 samples.

### 5. Check Batch Generation Status
```bash
curl http://localhost:5000/api/generate/batch/status
```

Response includes:
```json
{
  "running": true,
  "progress": 15,
  "total": 52,
  "current_sample": "Tort Law - Professional Negligence",
  "samples_generated": 15,
  "total_tokens": 45231,
  "started_at": "2025-10-09T21:30:00",
  "errors": []
}
```

### 6. Stop Batch Generation
```bash
curl -X POST http://localhost:5000/api/generate/batch/stop
```

### 7. Add Sample Manually
```bash
curl -X POST http://localhost:5000/api/add \
  -H "Content-Type: application/json" \
  -d '{
    "id": "custom_001",
    "question": "What is the test for duty of care?",
    "answer": "The test was established in Caparo v Dickman...",
    "topic": "Tort Law - Negligence",
    "difficulty": "intermediate",
    "case_citation": "Caparo Industries plc v Dickman [1990] 2 AC 605",
    "reasoning": "Step 1: Apply foreseeability test..."
  }'
```

### 8. Get Available Topics
```bash
curl http://localhost:5000/api/topics
```

Returns 42 UK legal topics across 11 practice areas.

### 9. Health Check
```bash
curl http://localhost:5000/api/health
```

Response:
```json
{
  "status": "healthy",
  "dataset_exists": true,
  "groq_configured": true,
  "batch_generation_running": false
}
```

## Batch Generation Workflow

1. **Start batch generation:**
   ```bash
   curl -X POST http://localhost:5000/api/generate/batch/start \
     -H "Content-Type: application/json" \
     -d '{"target_count": 2100}'
   ```

2. **Poll status every 5-10 seconds:**
   ```bash
   while true; do
     curl -s http://localhost:5000/api/generate/batch/status | jq
     sleep 5
   done
   ```

3. **Stop if needed:**
   ```bash
   curl -X POST http://localhost:5000/api/generate/batch/stop
   ```

## Rate Limiting

The backend respects Groq free tier limits:
- **25 requests per minute**
- **5,500 tokens per minute**
- Auto-waits when limits are hit
- Progress saved every 10 samples

## Features

### Auto-Save
- Batch generation saves progress every 10 samples
- Survives crashes/interruptions
- Can resume by restarting

### Error Tracking
- All errors logged in batch status
- Continues generation on errors
- View errors via `/api/generate/batch/status`

### Real-Time Progress
- Poll status endpoint for live updates
- Track current sample being generated
- Monitor token usage
- View completion percentage

## Integration Examples

### Python
```python
import requests
import time

# Start batch generation
response = requests.post('http://localhost:5000/api/generate/batch/start',
                        json={'target_count': 2100})
print(response.json())

# Poll status
while True:
    status = requests.get('http://localhost:5000/api/generate/batch/status').json()
    if not status['running']:
        break
    print(f"Progress: {status['progress']}/{status['total']} - {status['current_sample']}")
    time.sleep(5)

print("Generation complete!")
```

### JavaScript (React)
```javascript
// Start batch generation
const startGeneration = async () => {
  const response = await fetch('http://localhost:5000/api/generate/batch/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_count: 2100 })
  });
  return response.json();
};

// Poll status
const pollStatus = async () => {
  const response = await fetch('http://localhost:5000/api/generate/batch/status');
  return response.json();
};

// Use in component
useEffect(() => {
  const interval = setInterval(async () => {
    const status = await pollStatus();
    setProgress(status);
    if (!status.running) clearInterval(interval);
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

## Architecture Benefits

### Unified Backend
- Single Flask server handles all operations
- No need for separate Streamlit or standalone scripts
- Batch generation runs in background thread
- State persists for session lifetime

### Comparison to Old Architecture

**Old (3 processes):**
- Streamlit UI (port 8501)
- Flask API (port 5000)
- React UI (port 5173)
- Separate `generate_groq_samples.py` script

**New (2 processes):**
- Flask API with integrated batch generation (port 5000)
- React UI (port 5173)
- All generation through API endpoints

### Why This Is Better
1. **Simpler deployment** - One backend instead of two
2. **Better monitoring** - Real-time progress via API
3. **More reliable** - Background threads instead of separate processes
4. **Easier integration** - React can trigger generation directly
5. **Single source of truth** - Flask manages all state

## Troubleshooting

### Port already in use
```bash
lsof -ti:5000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### Batch generation stuck
```bash
curl -X POST http://localhost:5000/api/generate/batch/stop
```

### Check server health
```bash
curl http://localhost:5000/api/health
```

### View logs
```bash
tail -f /tmp/flask.log
tail -f /tmp/react.log
```
