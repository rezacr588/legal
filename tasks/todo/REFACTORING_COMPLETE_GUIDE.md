# Complete Backend/Frontend Refactoring Guide
## Legal Training Dataset Platform - Comprehensive Implementation Plan

**Date**: 2025-10-18
**Objective**: Complete reorganization with clean separation between backend and frontend
**Execution**: All phases executed continuously in one session (no pauses between phases)
**Duration**: ~2.5 hours total

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [New Directory Structure](#new-directory-structure)
3. [Phase 1: Create Directory Structure](#phase-1-create-directory-structure)
4. [Phase 2: Extract & Create Backend Components](#phase-2-extract--create-backend-components)
5. [Phase 3: Frontend Migration](#phase-3-frontend-migration)
6. [Phase 4: Startup Scripts](#phase-4-startup-scripts)
7. [Phase 5: Documentation Updates](#phase-5-documentation-updates)
8. [Phase 6: Testing & Validation](#phase-6-testing--validation)

---

## Executive Summary

### Current State
- **api_server.py**: 2,083 lines (routes + logic + models + workers)
- **Mixed architecture**: Backend and frontend in same directory
- **Scattered logic**: Batch generation logic in route file
- **Poor maintainability**: Difficult to test and extend

### Target State
- **Clean separation**: Backend and frontend in separate directories
- **Modular routes**: 5 route files (~200-400 lines each)
- **Service layer**: Batch logic in dedicated service class
- **Clear structure**: Easy to navigate, test, and extend

---

## New Directory Structure

```
/Users/rezazeraat/Desktop/Data/
│
├── backend/                                 # ✨ NEW - All Python/Flask backend
│   ├── app.py                              # ✨ NEW - Flask app entry point
│   ├── config.py                           # MOVED from legal-dashboard/
│   │
│   ├── routes/                             # ✨ NEW - All API endpoints
│   │   ├── __init__.py                     # Blueprint registration
│   │   ├── data.py                         # GET /api/data, /api/stats, /api/stats/*
│   │   ├── generation.py                   # POST /api/generate
│   │   ├── batches.py                      # All batch endpoints + SSE
│   │   ├── samples.py                      # CRUD: /api/sample/*, /api/import/*, /api/search
│   │   └── misc.py                         # /api/topics, /api/models, /api/health, etc.
│   │
│   ├── models/                             # Database models
│   │   ├── __init__.py                     # SQLAlchemy db instance
│   │   └── batch.py                        # ✨ NEW - BatchHistory model (extracted)
│   │
│   ├── services/                           # Business logic
│   │   ├── __init__.py                     # COPIED from legal-dashboard/
│   │   ├── llm_service.py                  # COPIED from legal-dashboard/
│   │   ├── generation_service.py           # COPIED from legal-dashboard/
│   │   └── batch_service.py                # ✨ NEW - Batch worker logic (extracted)
│   │
│   ├── utils/                              # Utilities
│   │   ├── __init__.py                     # COPIED from legal-dashboard/
│   │   ├── error_handler.py                # COPIED from legal-dashboard/
│   │   └── circuit_breaker.py              # COPIED from legal-dashboard/
│   │
│   └── data/                               # ✨ NEW - Data storage
│       ├── train.parquet                   # SYMLINKED or COPIED
│       └── batches.db                      # MOVED from legal-dashboard/
│
├── frontend/                                # ✨ NEW - React application
│   ├── src/                                # MOVED from legal-dashboard/src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── Overview.jsx
│   │   │   ├── Generation.jsx
│   │   │   ├── Dataset.jsx
│   │   │   ├── Batches.jsx
│   │   │   ├── Documentation.jsx
│   │   │   ├── GenerationHub.jsx
│   │   │   └── HuggingFacePush.jsx
│   │   ├── theme/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/                             # MOVED from legal-dashboard/public/
│   ├── package.json                        # MOVED from legal-dashboard/
│   ├── package-lock.json                   # MOVED from legal-dashboard/
│   ├── vite.config.js                      # MOVED + UPDATED paths
│   ├── index.html                          # MOVED from legal-dashboard/
│   ├── .eslintrc.cjs                       # MOVED from legal-dashboard/
│   └── README.md                           # ✨ NEW - Frontend documentation
│
├── scripts/                                 # ✨ NEW - Startup scripts
│   ├── start_backend.sh                    # Start Flask backend
│   ├── start_frontend.sh                   # Start React frontend
│   ├── start_all.sh                        # Start both
│   └── stop_all.sh                         # ✨ NEW - Stop all services
│
├── docs/                                    # Documentation (already exists)
│   ├── API_USAGE.md                        # UPDATED with new paths
│   └── CLAUDE.md                           # UPDATED with new structure
│
├── tests/                                   # Tests (already exists, moved later)
│   └── (existing test files)
│
├── legal-dashboard/                         # KEPT as backup until validation complete
│   └── (original files remain untouched)
│
└── README.md                                # UPDATED root readme
```

---

## Phase 1: Create Directory Structure

**Duration**: 10 minutes
**No code changes yet - just directory creation**

### 1.1 Create Backend Directories
```bash
mkdir -p backend/routes
mkdir -p backend/models
mkdir -p backend/services
mkdir -p backend/utils
mkdir -p backend/data
```

### 1.2 Create Frontend Directory
```bash
mkdir -p frontend/src
mkdir -p frontend/public
```

### 1.3 Create Scripts Directory
```bash
mkdir -p scripts
```

### 1.4 Create __init__.py Files
```bash
touch backend/__init__.py
touch backend/routes/__init__.py
touch backend/models/__init__.py
touch backend/services/__init__.py
touch backend/utils/__init__.py
```

---

## Phase 2: Extract & Create Backend Components

**Duration**: 60 minutes

### 2.1 Create backend/models/batch.py

**Extract from**: `legal-dashboard/api_server.py` lines 132-165

```python
"""
Database models for batch management.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BatchHistory(db.Model):
    """
    Model for tracking batch generation history.
    Stores metadata about batch generation jobs including progress, errors, and model switches.
    """
    __tablename__ = 'batch_history'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    started_at = db.Column(db.String(50), nullable=False)
    completed_at = db.Column(db.String(50))
    model = db.Column(db.String(100))
    topic_filter = db.Column(db.String(200))
    difficulty_filter = db.Column(db.String(50))
    reasoning_instruction = db.Column(db.Text)
    target_count = db.Column(db.Integer)
    samples_generated = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20))  # running, completed, stopped
    errors = db.Column(db.Text)  # JSON string
    model_switches = db.Column(db.Text)  # JSON string tracking model switches

    def to_dict(self):
        """Convert batch to dictionary for API responses."""
        import json
        return {
            'id': self.batch_id,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'model': self.model,
            'topic_filter': self.topic_filter,
            'difficulty_filter': self.difficulty_filter,
            'reasoning_instruction': self.reasoning_instruction,
            'target': self.target_count,
            'samples_generated': self.samples_generated,
            'tokens_used': self.total_tokens,
            'status': self.status,
            'errors': json.loads(self.errors) if self.errors else [],
            'model_switches': json.loads(self.model_switches) if self.model_switches else []
        }

    def __repr__(self):
        return f'<BatchHistory {self.batch_id}>'
```

---

### 2.2 Create backend/models/__init__.py

```python
"""
Database models package.
Exports db instance and all models.
"""
from backend.models.batch import db, BatchHistory

__all__ = ['db', 'BatchHistory']
```

---

### 2.3 Create backend/services/batch_service.py

**Extract from**: `legal-dashboard/api_server.py` lines 376-759 (batch_generate_worker function)

```python
"""
Batch Generation Service - Handles background batch generation logic.
Extracted from api_server.py for better separation of concerns.
"""
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
import polars as pl

from backend.config import (
    MAX_BATCH_TIMEOUT,
    MAX_MODEL_SWITCHES,
    MAX_SAMPLE_RETRIES,
    SAMPLE_TYPE_CYCLE,
    PARQUET_PATH,
    TOPICS
)
from backend.models import db, BatchHistory
from backend.services.generation_service import GenerationService
from backend.services.llm_service import LLMProviderFactory
from backend.utils.circuit_breaker import CircuitBreaker


class BatchService:
    """
    Service class for managing batch generation operations.
    Handles background workers, progress tracking, and database persistence.
    """

    def __init__(self, parquet_lock: threading.Lock):
        """
        Initialize batch service.

        Args:
            parquet_lock: Thread lock for safe parquet file writes
        """
        self.parquet_lock = parquet_lock
        self.generation_service = GenerationService()
        self.active_batches: Dict = {}  # In-memory batch state
        self.batch_lock = threading.Lock()

    def create_batch_state(self, batch_id: str, provider: str, model: str, total: int = 0) -> Dict:
        """Create initial batch state object."""
        return {
            'running': True,
            'progress': 0,
            'total': total,
            'current_sample': None,
            'current_provider': provider,
            'current_model': model,
            'errors': [],
            'batch_id': batch_id,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'samples_generated': 0,
            'total_tokens': 0,
            'model_switches': [],
            'provider_switches': [],
            'failed_models_by_provider': {provider: []},
            'consecutive_failures': 0,
            'skipped_topics': [],
            'circuit_breaker_summary': {}
        }

    def start_batch(self, batch_id: str, target_count: int, provider: str, model: str,
                    topic_filter: Optional[str] = None, difficulty_filter: Optional[str] = None,
                    reasoning_instruction: Optional[str] = None, sample_type_filter: str = 'case_analysis'):
        """
        Start a new batch generation job in background thread.

        Args:
            batch_id: Unique batch identifier
            target_count: Target total sample count
            provider: LLM provider name
            model: Model name
            topic_filter: Optional topic filter
            difficulty_filter: Optional difficulty filter
            reasoning_instruction: Optional custom reasoning requirements
            sample_type_filter: Sample type filter (or 'balance')
        """
        # Calculate samples needed
        df_existing = pl.read_parquet(PARQUET_PATH)
        current_count = len(df_existing)
        samples_needed = target_count - current_count

        if samples_needed <= 0:
            return {'error': f'Target already met: {current_count} samples exist'}

        # Create batch state
        with self.batch_lock:
            batch_state = self.create_batch_state(batch_id, provider, model, samples_needed)
            batch_state.update({
                'topic_filter': topic_filter,
                'difficulty_filter': difficulty_filter,
                'reasoning_instruction': reasoning_instruction,
                'sample_type_filter': sample_type_filter
            })
            self.active_batches[batch_id] = batch_state

        # Save to database
        self._save_batch_to_db(batch_state)

        # Start background worker thread
        thread = threading.Thread(
            target=self._batch_worker,
            args=(batch_id, target_count, provider, model)
        )
        thread.daemon = True
        thread.start()

        return {'batch_id': batch_id, 'samples_needed': samples_needed}

    def stop_batch(self, batch_id: Optional[str] = None):
        """
        Stop batch generation(s).

        Args:
            batch_id: Specific batch to stop, or None to stop all

        Returns:
            Dict with stop status
        """
        stopped_batches = []

        with self.batch_lock:
            if batch_id:
                # Stop specific batch
                if batch_id in self.active_batches:
                    batch_state = self.active_batches[batch_id]
                    if batch_state['running']:
                        batch_state['running'] = False
                        batch_state['completed_at'] = datetime.now().isoformat()
                        stopped_batches.append(batch_id)
                else:
                    return {'error': f'Batch {batch_id} not found'}
            else:
                # Stop all running batches
                for bid, batch_state in self.active_batches.items():
                    if batch_state.get('running', False):
                        batch_state['running'] = False
                        batch_state['completed_at'] = datetime.now().isoformat()
                        stopped_batches.append(bid)

        # Save to database
        for bid in stopped_batches:
            self._save_batch_to_db(self.active_batches[bid])

        return {'stopped_batches': stopped_batches, 'count': len(stopped_batches)}

    def get_batch_status(self, batch_id: Optional[str] = None):
        """Get status of specific batch or all batches."""
        with self.batch_lock:
            if batch_id:
                return self.active_batches.get(batch_id)
            else:
                return {
                    'batches': self.active_batches,
                    'count': len(self.active_batches)
                }

    def _batch_worker(self, batch_id: str, target_count: int, provider: str, model: str):
        """
        Background worker for batch generation.
        This is the main batch generation loop extracted from api_server.py.

        NOTE: This is a simplified version. Full implementation should include:
        - Complete error handling and model switching logic
        - Provider failover
        - Rate limiting with proper tracking
        - All the logic from api_server.py lines 376-759
        """
        # Import here to avoid circular imports
        from backend.routes.batches import broadcast_sse_update

        with self.batch_lock:
            if batch_id not in self.active_batches:
                print(f"❌ Batch {batch_id} not found in active_batches")
                return
            batch_state = self.active_batches[batch_id]

        # Get rate limits
        rate_limits = LLMProviderFactory.get_rate_limits(provider)
        requests_per_minute = rate_limits['requests_per_minute']
        request_delay = 60 / requests_per_minute

        # Initialize circuit breaker
        circuit_breaker = CircuitBreaker()

        # Load existing dataset
        df_existing = pl.read_parquet(PARQUET_PATH)
        current_count = len(df_existing)
        samples_needed = target_count - current_count

        # Get filters
        topic_filter = batch_state.get('topic_filter')
        difficulty_filter = batch_state.get('difficulty_filter')
        reasoning_instruction = batch_state.get('reasoning_instruction')
        sample_type_filter = batch_state.get('sample_type_filter', 'case_analysis')

        # Prepare topic cycle
        if topic_filter:
            filtered_topics = [t for t in TOPICS if f"{t[0]} - {t[1]}" == topic_filter]
            if not filtered_topics:
                filtered_topics = TOPICS
        else:
            filtered_topics = TOPICS

        topic_cycle = filtered_topics * ((samples_needed // len(filtered_topics)) + 10)

        generated_samples = []
        minute_start = time.time()
        minute_requests = 0
        minute_tokens = 0
        batch_start_time = time.time()
        iteration = 0
        max_iterations = samples_needed * 3

        # Main generation loop
        while batch_state['samples_generated'] < samples_needed and iteration < max_iterations:
            # Check for manual stop
            if not batch_state['running']:
                break

            # Check timeout
            elapsed_time = time.time() - batch_start_time
            if elapsed_time > MAX_BATCH_TIMEOUT:
                batch_state['errors'].append({
                    'error': f"Batch timed out after {int(elapsed_time/60)} minutes",
                    'timeout': True
                })
                batch_state['running'] = False
                break

            # Get current topic
            topic_index = iteration % len(topic_cycle)
            practice_area, topic, original_difficulty = topic_cycle[topic_index]
            topic_key = f"{practice_area} - {topic}"
            difficulty = difficulty_filter if difficulty_filter else original_difficulty

            # Circuit breaker check
            if circuit_breaker.is_open(topic_key):
                if topic_key not in batch_state['skipped_topics']:
                    batch_state['skipped_topics'].append(topic_key)
                iteration += 1
                continue

            # Determine sample type
            if sample_type_filter == 'balance':
                sample_type_index = iteration % len(SAMPLE_TYPE_CYCLE)
                current_sample_type = SAMPLE_TYPE_CYCLE[sample_type_index]
            else:
                current_sample_type = sample_type_filter

            # Rate limiting
            elapsed_minute = time.time() - minute_start
            if elapsed_minute < 60 and minute_requests >= requests_per_minute:
                wait_time = 60 - elapsed_minute
                time.sleep(wait_time)
                minute_start = time.time()
                minute_tokens = 0
                minute_requests = 0
            elif elapsed_minute >= 60:
                minute_start = time.time()
                minute_tokens = 0
                minute_requests = 0

            batch_state['current_sample'] = topic_key

            # Generate sample with retries
            sample_success = False
            sample_retries = 0

            while not sample_success and sample_retries < MAX_SAMPLE_RETRIES:
                sample, tokens_used, elapsed, error = self.generation_service.generate_single_sample(
                    practice_area, topic, difficulty,
                    current_count + batch_state['samples_generated'] + 1,
                    provider, model, reasoning_instruction, batch_id, current_sample_type
                )

                if sample:
                    generated_samples.append(sample)
                    batch_state['samples_generated'] += 1
                    batch_state['total_tokens'] += tokens_used
                    batch_state['consecutive_failures'] = 0
                    minute_tokens += tokens_used
                    minute_requests += 1
                    sample_success = True

                    circuit_breaker.record_success(topic_key)

                    # Auto-save to parquet
                    with self.parquet_lock:
                        df_fresh = pl.read_parquet(PARQUET_PATH)
                        existing_columns = df_fresh.columns
                        filtered_samples = [{k: v for k, v in s.items() if k in existing_columns}
                                          for s in generated_samples]
                        df_new = pl.DataFrame(filtered_samples)
                        df_combined = pl.concat([df_fresh, df_new])
                        df_combined.write_parquet(PARQUET_PATH, compression="zstd",
                                                statistics=True, use_pyarrow=False)

                    generated_samples = []
                    batch_state['circuit_breaker_summary'] = circuit_breaker.get_summary()
                    broadcast_sse_update(batch_id)

                else:
                    # Handle failure
                    sample_retries += 1
                    batch_state['consecutive_failures'] += 1
                    circuit_breaker.record_failure(topic_key, error)

                    # (Model switching logic would go here - see original api_server.py)

                    if sample_retries < MAX_SAMPLE_RETRIES:
                        time.sleep(2)

            iteration += 1
            batch_state['progress'] = iteration
            broadcast_sse_update(batch_id)

            if batch_state['samples_generated'] % 10 == 0:
                self._save_batch_to_db(batch_state)

            time.sleep(request_delay)

        # Final save
        if generated_samples:
            with self.parquet_lock:
                df_fresh = pl.read_parquet(PARQUET_PATH)
                existing_columns = df_fresh.columns
                filtered_samples = [{k: v for k, v in s.items() if k in existing_columns}
                                  for s in generated_samples]
                df_new = pl.DataFrame(filtered_samples)
                df_combined = pl.concat([df_fresh, df_new])
                df_combined.write_parquet(PARQUET_PATH, compression="zstd",
                                        statistics=True, use_pyarrow=False)

        batch_state['completed_at'] = datetime.now().isoformat()
        batch_state['running'] = False
        batch_state['circuit_breaker_summary'] = circuit_breaker.get_summary()

        self._save_batch_to_db(batch_state)
        broadcast_sse_update(batch_id)

    def _save_batch_to_db(self, batch_state: Dict):
        """Save batch state to database."""
        import json
        from flask import current_app

        try:
            batch_id = batch_state.get('batch_id')
            if not batch_id:
                return

            with current_app.app_context():
                batch = BatchHistory.query.filter_by(batch_id=batch_id).first()

                if batch:
                    # Update existing
                    batch.completed_at = batch_state.get('completed_at')
                    batch.samples_generated = batch_state.get('samples_generated', 0)
                    batch.total_tokens = batch_state.get('total_tokens', 0)
                    batch.status = 'running' if batch_state.get('running') else 'completed'
                    batch.errors = json.dumps(batch_state.get('errors', []))
                    batch.model_switches = json.dumps(batch_state.get('model_switches', []))
                    batch.model = batch_state.get('current_model', batch.model)
                else:
                    # Create new
                    batch = BatchHistory(
                        batch_id=batch_id,
                        started_at=batch_state['started_at'],
                        model=batch_state.get('current_model'),
                        topic_filter=batch_state.get('topic_filter'),
                        difficulty_filter=batch_state.get('difficulty_filter'),
                        reasoning_instruction=batch_state.get('reasoning_instruction'),
                        target_count=batch_state.get('total', 0),
                        samples_generated=batch_state.get('samples_generated', 0),
                        total_tokens=batch_state.get('total_tokens', 0),
                        status='running' if batch_state.get('running') else 'stopped',
                        errors=json.dumps(batch_state.get('errors', [])),
                        model_switches=json.dumps(batch_state.get('model_switches', []))
                    )
                    db.session.add(batch)

                db.session.commit()
        except Exception as e:
            print(f"Error saving batch to database: {str(e)}")
            db.session.rollback()
```

---

### 2.4 Create backend/routes/__init__.py

```python
"""
Routes package - Flask Blueprints for all API endpoints.
Registers all route blueprints with the Flask app.
"""
from flask import Flask


def register_blueprints(app: Flask):
    """
    Register all route blueprints with the Flask application.

    Args:
        app: Flask application instance
    """
    from backend.routes.data import data_bp
    from backend.routes.generation import generation_bp
    from backend.routes.batches import batches_bp
    from backend.routes.samples import samples_bp
    from backend.routes.misc import misc_bp

    # Register all blueprints with /api prefix
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(generation_bp, url_prefix='/api')
    app.register_blueprint(batches_bp, url_prefix='/api')
    app.register_blueprint(samples_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')

    print(" ✅ Registered all route blueprints")


__all__ = ['register_blueprints']
```

---

### 2.5-2.9 Create Route Files

Due to length, the complete route files are provided in REFACTORING_IMPLEMENTATION_DETAILS.md (which is part of this combined document). Key route files:

- **backend/routes/data.py** - Data and statistics endpoints
- **backend/routes/generation.py** - Single sample generation
- **backend/routes/batches.py** - Batch management and SSE
- **backend/routes/samples.py** - CRUD operations
- **backend/routes/misc.py** - Topics, models, providers, health, HuggingFace

See sections 2.5-2.9 in the implementation details above for complete code.

---

## Phase 3: Frontend Migration

**Duration**: 30 minutes

### 3.1 Copy Frontend Files
```bash
# Copy all frontend files from legal-dashboard to frontend/
cp -r legal-dashboard/src frontend/
cp -r legal-dashboard/public frontend/
cp legal-dashboard/package.json frontend/
cp legal-dashboard/package-lock.json frontend/
cp legal-dashboard/vite.config.js frontend/
cp legal-dashboard/index.html frontend/
cp legal-dashboard/.eslintrc.cjs frontend/
```

### 3.2 Update vite.config.js
Update the Vite configuration to work from the new location:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  }
})
```

### 3.3 Update API URLs in Frontend
Update all API calls in `frontend/src/` to use relative paths (they'll be proxied via Vite):
- Change `http://127.0.0.1:5000/api` to `/api`
- Vite proxy will handle the routing

---

## Phase 4: Startup Scripts

**Duration**: 15 minutes

### 4.1 Create scripts/start_backend.sh
```bash
#!/bin/bash

echo "🚀 Starting Flask Backend..."

cd backend
python3 app.py
```

### 4.2 Create scripts/start_frontend.sh
```bash
#!/bin/bash

echo "🚀 Starting React Frontend..."

cd frontend
npm run dev
```

### 4.3 Create scripts/start_all.sh
```bash
#!/bin/bash

echo "🚀 Starting All Services..."

# Start backend in background
cd backend
python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend in background
cd ../frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✅ Backend started (PID: $BACKEND_PID)"
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""
echo "📊 Backend: http://localhost:5000"
echo "🎨 Frontend: http://localhost:5173"
echo ""
echo "Logs:"
echo "  Backend: tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
```

### 4.4 Create scripts/stop_all.sh
```bash
#!/bin/bash

echo "🛑 Stopping All Services..."

# Kill backend (port 5000)
lsof -ti:5000 | xargs kill -9 2>/dev/null
echo "✅ Backend stopped"

# Kill frontend (port 5173)
lsof -ti:5173 | xargs kill -9 2>/dev/null
echo "✅ Frontend stopped"
```

### 4.5 Make scripts executable
```bash
chmod +x scripts/*.sh
```

---

## Phase 5: Documentation Updates

**Duration**: 15 minutes

### 5.1 Update docs/CLAUDE.md
Update file structure section to reflect new organization:
- Backend in `backend/`
- Frontend in `frontend/`
- Scripts in `scripts/`
- Updated startup commands

### 5.2 Update docs/API_USAGE.md
- Update example curl commands to reflect new backend location
- Add notes about backend/frontend separation

### 5.3 Update Root README.md
```markdown
# Legal Training Dataset Platform

## Quick Start

# Start all services
./scripts/start_all.sh

# Or start individually
./scripts/start_backend.sh
./scripts/start_frontend.sh

## Directory Structure

- `backend/` - Flask API server
- `frontend/` - React dashboard
- `scripts/` - Startup/utility scripts
- `docs/` - Documentation

## Development

# Backend development
cd backend
python3 app.py

# Frontend development
cd frontend
npm run dev
```

---

## Phase 6: Testing & Validation

**Duration**: 20 minutes

### 6.1 Test Backend
```bash
cd backend
python3 app.py

# In another terminal
curl http://localhost:5000/api/health
curl http://localhost:5000/api/stats
```

### 6.2 Test Frontend
```bash
cd frontend
npm install  # If needed
npm run dev

# Open browser to http://localhost:5173
```

### 6.3 Test Integration
- Generate a sample via API
- Verify it appears in frontend
- Test batch generation
- Test all CRUD operations

### 6.4 Cleanup (After Validation)
```bash
# Once everything works, can archive old structure
mv legal-dashboard legal-dashboard.backup
```

---

## Execution Checklist

- [ ] Phase 1: Create directory structure
- [ ] Phase 2: Backend components
  - [ ] Models (batch.py)
  - [ ] Services (batch_service.py)
  - [ ] Routes (5 files)
  - [ ] Copy existing services/utils
- [ ] Phase 3: Frontend migration
  - [ ] Copy all files
  - [ ] Update vite.config.js
  - [ ] Update API URLs
- [ ] Phase 4: Startup scripts
  - [ ] Create all 4 scripts
  - [ ] Make executable
- [ ] Phase 5: Documentation
  - [ ] Update CLAUDE.md
  - [ ] Update API_USAGE.md
  - [ ] Update README.md
- [ ] Phase 6: Testing
  - [ ] Backend health check
  - [ ] Frontend loads
  - [ ] Integration tests
  - [ ] Cleanup old structure

---

## Success Criteria

✅ Backend runs independently on port 5000
✅ Frontend runs independently on port 5173
✅ All API endpoints work correctly
✅ Frontend can communicate with backend
✅ Batch generation works
✅ Database operations succeed
✅ No code duplication
✅ Clean separation of concerns
✅ Easy to navigate and maintain

---

## Notes

- Keep `legal-dashboard/` as backup until fully validated
- All changes are non-destructive until Phase 6.4
- Can rollback by using original `legal-dashboard/` directory
- Test thoroughly before cleanup

---

**End of Complete Refactoring Guide**
