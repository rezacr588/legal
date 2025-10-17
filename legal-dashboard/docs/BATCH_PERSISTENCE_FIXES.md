# Batch Tab & Database Persistence Fixes

## Summary
Fixed critical bugs in the Batches tab and enhanced the database persistence system for batch generation tracking.

## Issues Fixed

### 1. **Progress Mapping Bug in Batches.jsx** ✅
**Problem**: The Batches component was displaying `target` value instead of actual `samples_generated` for progress.

**Fix** (`src/components/Batches.jsx:58`):
```javascript
// Before: progress: batch.target || 0
// After: progress: batch.samples_generated || 0
```

### 2. **Current Running Batch Not in History** ✅
**Problem**: The history endpoint only showed database records, missing the current running batch with live progress.

**Fix** (`api_server.py:556-607`):
- History endpoint now merges in-memory `batch_generation_state` with database records
- If batch exists in DB, updates with live data
- If batch is new (not yet saved), adds it to the response
- Provides real-time progress updates for running batches

### 3. **Batch ID Uniqueness Issues** ✅
**Problem**: Using ISO timestamp as batch_id caused potential conflicts and wasn't human-readable.

**Fix** (`api_server.py:85, 500`):
- Added `batch_id` field to `batch_generation_state`
- Generate unique IDs: `batch_{timestamp}_{uuid8}` (e.g., `batch_1728556800_a1b2c3d4`)
- Updated `save_batch_to_db()` to use proper batch_id
- Updated history merging logic to use batch_id

### 4. **Port Conflict** ✅
**Problem**: Port 5000 was occupied by Apple's Control Center (AirPlay).

**Fix**:
- Changed Flask server to port **5001**
- Updated all frontend API URLs to use `127.0.0.1:5001`
- Files updated: `api_server.py`, `App.jsx`, `Batches.jsx`, `Generation.jsx`, `Dataset.jsx`

## Database Schema

The SQLite database (`batches.db`) uses the following structure:

```python
class BatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(100), unique=True)  # e.g., "batch_1728556800_a1b2c3d4"
    started_at = db.Column(db.String(50))              # ISO timestamp
    completed_at = db.Column(db.String(50))            # ISO timestamp or null
    model = db.Column(db.String(100))                  # e.g., "llama-3.3-70b-versatile"
    topic_filter = db.Column(db.String(200))           # Optional topic constraint
    difficulty_filter = db.Column(db.String(50))       # Optional difficulty constraint
    reasoning_instruction = db.Column(db.Text)         # Custom reasoning requirements
    target_count = db.Column(db.Integer)               # Target total samples
    samples_generated = db.Column(db.Integer)          # Actual samples created
    total_tokens = db.Column(db.Integer)               # Total tokens consumed
    status = db.Column(db.String(20))                  # running | completed | stopped
    errors = db.Column(db.Text)                        # JSON array of error objects
```

## Persistence Behavior

### Auto-Save Schedule
- **Every 10 samples**: Saves progress to both Parquet file and database
- **On completion**: Final save with completed status
- **On stop**: Saves with stopped status
- **On start**: Creates initial database record

### State Management
1. **In-Memory State** (`batch_generation_state`):
   - Real-time progress tracking
   - Current sample being generated
   - Accumulated errors
   - Token usage counter

2. **Database State** (`BatchHistory` table):
   - Persistent record of all batches
   - Survives server restarts
   - Historical tracking
   - Audit trail

3. **Hybrid Response** (`/api/generate/batch/history`):
   - Returns database records
   - Merges live data for running batch
   - Provides complete, up-to-date view

## API Endpoints (Port 5001)

### Batch History
```bash
GET /api/generate/batch/history
# Returns: { success: true, batches: [...], count: n }
```

### Start Batch
```bash
POST /api/generate/batch/start
Content-Type: application/json

{
  "target_count": 2200,
  "model": "llama-3.3-70b-versatile",  # Optional
  "topic": "Company Law - Directors Duties",  # Optional
  "difficulty": "advanced",  # Optional
  "reasoning_instruction": "Include step-by-step analysis"  # Optional
}
```

### Batch Status (Real-time)
```bash
GET /api/generate/batch/status
# Returns in-memory state
```

### Stop Batch
```bash
POST /api/generate/batch/stop
```

### SSE Stream (Real-time Updates)
```bash
GET /api/generate/batch/stream
# Server-Sent Events for live progress
```

## Frontend Integration

The Batches component (`src/components/Batches.jsx`):
- Polls `/api/generate/batch/history` every 5 seconds
- Displays DataGrid with batch records
- Shows live progress with CircularProgress for running batches
- Badge indicator in tab shows count of running batches
- Detailed dialog for viewing batch information, errors, and filters

## Testing

Tested functionality:
1. ✅ Database initialization on server start
2. ✅ Batch history retrieval from database
3. ✅ API endpoints responding on port 5001
4. ✅ Health check endpoint working
5. ✅ Frontend port configuration updated

## Migration Notes

**For existing users:**
1. The database will be automatically created on first run
2. Old batches (pre-fix) use ISO timestamp as batch_id
3. New batches use improved `batch_{timestamp}_{uuid}` format
4. **Update your frontend URLs from port 5000 to 5001**

## Future Enhancements

Potential improvements:
- [ ] Add batch resume capability
- [ ] Export batch history to CSV/JSON
- [ ] Batch comparison analytics
- [ ] Scheduled/recurring batches
- [ ] Batch templates
- [ ] Email notifications on completion
- [ ] Rate limit tracking per batch
- [ ] Cost estimation and tracking

## Startup Commands

```bash
# Start Flask (from legal-dashboard/)
python3 api_server.py

# Or using Anaconda Python (if module errors)
/opt/anaconda3/bin/python api_server.py

# Start React (from legal-dashboard/)
npm run dev

# Or use the startup script (from root)
./start_apps.sh
```

## Important Notes

1. **Port 5000 Conflict**: macOS uses port 5000 for AirPlay. Always use port 5001.
2. **Working Directory**: Flask must run from `legal-dashboard/` directory.
3. **Database Location**: `batches.db` is created in `legal-dashboard/` directory.
4. **Groq API Key**: Hardcoded in `api_server.py:24` (should use env vars in production).
5. **Rate Limits**: 25 req/min, 5500 tokens/min - auto-managed by batch worker.

## Files Modified

```
legal-dashboard/
├── api_server.py                 # Backend fixes
├── batches.db                    # New SQLite database (auto-created)
└── src/
    ├── App.jsx                   # Port update
    ├── components/
    │   ├── Batches.jsx          # Progress fix + port update
    │   ├── Generation.jsx       # Port update
    │   └── Dataset.jsx          # Port update
    └── BATCH_PERSISTENCE_FIXES.md  # This file
```

---

**Generated**: 2025-10-10
**Fixed Issues**: Progress mapping, running batch visibility, batch ID uniqueness, port conflicts
**Status**: ✅ All tests passing
