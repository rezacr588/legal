# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**Global Legal AI Training Platform** - Multi-jurisdiction LLM training dataset with 2,054+ legal Q&A samples in Apache Parquet format. Covers UK, US, EU, and International law topics with authentic case citations and step-by-step reasoning. Features a modern React dashboard with real-time generation monitoring, multi-jurisdiction support, HuggingFace integration, and flexible filtering capabilities.

## Architecture

### Application Stack
```
┌─────────────────┐         ┌──────────────────────────┐         ┌────────────────┐
│  React Frontend │ ◄─────► │  Flask Backend (Modular) │ ◄─────► │  HuggingFace   │
│  (Port 5173)    │  HTTP   │  (Port 5000/5001)        │  API    │  Hub           │
│  Vite 4.5.0     │         │  + Multi-Provider AI     │         │  (rzeraat)     │
└─────────────────┘         └────────┬─────────────────┘         └────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  train.parquet  │
                            │  (ZSTD)         │
                            │  Multi-jurisdiction
                            └─────────────────┘
```

**Flask Backend** - **MODULAR ARCHITECTURE** (October 2025):
- **Multi-provider support**: Groq (19 models) + Cerebras (9 models) + Ollama (optional) = 28+ total
- **Modular structure**: config, models, services, utils
- **OOP design**: Provider abstraction with factory pattern
- **UUID-based IDs**: Cryptographically unique sample identifiers
- **Cross-provider failover**: Automatic provider switching
- **Comprehensive error handling**: 7 error categories with intelligent recovery
- **Sample Types System**: 9 distinct sample types including core legal types (case_analysis, educational, client_interaction, statutory_interpretation) and advanced reasoning types (legal_dialogue, pure_conceptual, comparative_analysis, ethical_reasoning, procedural_guide)
- Port 5000 or 5001 - MUST run from `legal-dashboard/` directory
- Dependencies: `flask`, `flask-cors`, `flask-sqlalchemy`, `polars`, `groq`, `cerebras_cloud_sdk`, `tiktoken`, `huggingface_hub`

**Backend Modules**:
```
legal-dashboard/
├── api_server.py           # Flask routes (thin layer)
├── config.py               # Configuration & constants
├── models/
│   └── database.py        # SQLAlchemy models
├── services/
│   ├── llm_service.py     # Provider abstraction (OOP)
│   └── generation_service.py  # Generation logic
└── utils/
    ├── error_handler.py   # Error categorization
    └── circuit_breaker.py # Circuit breaker pattern
```

**React Frontend** (`legal-dashboard/src/`):
- React + Vite 4.5.0 (port 5173) + Recharts for visualization
- **Critical**: Vite 4.5.0 required for Node 18 compatibility (not Vite 5+)
- Glassmorphism dark theme with responsive design
- Three-tab interface: Overview, Generation, Dataset
- Real-time stats sidebar with generation progress indicator
- Interactive charts (PieChart, BarChart for difficulty/topic distributions)
- Dataset explorer with search and JSONL import
- HuggingFace push modal for dataset publishing (supports parquet/json/csv formats)

### Data Schema

7 required fields per sample (all must be present for validation):
```python
{
  "id": str,              # Unique (e.g., "contract_law_formation_001" or UUID)
  "question": str,        # Legal question (multi-jurisdiction)
  "answer": str,          # Comprehensive answer (structure varies by sample_type)
  "topic": str,           # "Practice Area - Subtopic"
  "difficulty": str,      # basic|intermediate|advanced|expert
  "case_citation": str,   # Real cases/statutes (jurisdiction-specific)
  "reasoning": str        # "Step 1: ... Step 2: ..." (chain of thought)
}
```

Optional fields for enhanced tracking:
```python
{
  "jurisdiction": str,    # uk|us|eu|international (defaults to 'uk' if not specified)
  "batch_id": str,        # Tracks which batch generated this sample (auto-added)
  "sample_type": str      # case_analysis|educational|client_interaction|statutory_interpretation
}
```

**Sample Types** (4 distinct answer structures):
1. **case_analysis** (default): IRAC methodology - Issue, Rule, Application, Conclusion
2. **educational**: Structured teaching - Definition, Legal Basis, Key Elements, Examples, Distinctions
3. **client_interaction**: Practical advice - Understanding, Legal Position, Options, Recommendation, Next Steps
4. **statutory_interpretation**: Legislative analysis - Statutory Text, Purpose, Interpretation, Case Law, Application

### Jurisdiction Support

The platform now supports multiple legal jurisdictions:
- **UK** (United Kingdom) - Common Law, 42+ topics
- **US** (United States) - Federal & State law, 15+ topics
- **EU** (European Union) - EU regulations and directives, 10+ topics
- **International** - Treaties, conventions, international courts, 8+ topics

**Configuration**: See `config.py` → `JURISDICTIONS` and `JURISDICTION_TOPICS`
**Default**: UK jurisdiction maintained for backward compatibility

## Essential Commands

### Start/Stop Applications

```bash
# Start everything (recommended)
./start_apps.sh

# Kill stuck processes
lsof -ti:5000 | xargs kill -9  # Flask backend
lsof -ti:5173 | xargs kill -9  # React frontend

# Manual startup (if needed)
cd legal-dashboard
python3 api_server.py &
npm run dev

# View logs
tail -f /tmp/flask.log
tail -f /tmp/react.log
```

### View Dataset

```bash
# Install parquet-tools (if needed)
pip install parquet-tools

# View samples from root directory
parquet-tools show train.parquet --head 10
parquet-tools inspect train.parquet

# Python
python3 -c "import polars as pl; print(pl.read_parquet('train.parquet').head())"
```

### Generate New Samples

```bash
# Start batch generation with all defaults (runs in background)
curl -X POST http://localhost:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{"target_count": 2100}'

# Start batch with filters (specific topic, difficulty, and sample type)
curl -X POST http://localhost:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_count": 2200,
    "provider": "cerebras",
    "model": "gpt-oss-120b",
    "topic": "Company Law - Directors Duties",
    "difficulty": "advanced",
    "sample_type": "case_analysis"
  }'

# Generate with Cerebras provider (higher quality)
curl -X POST http://localhost:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_count": 2150,
    "provider": "cerebras",
    "model": "gpt-oss-120b"
  }'

# Monitor progress (poll every 5 seconds)
watch -n 5 "curl -s http://localhost:5000/api/generate/batch/status | jq"

# View batch history
curl http://localhost:5000/api/generate/batch/history | jq

# Stop generation (all batches)
curl -X POST http://localhost:5000/api/generate/batch/stop

# Stop specific batch
curl -X POST http://localhost:5000/api/generate/batch/stop \
  -H "Content-Type: application/json" \
  -d '{"batch_id": "batch_1234567890_abcd1234"}'

# Get available models (28+ total)
curl http://localhost:5000/api/models | jq '.models[].id'

# Get available providers
curl http://localhost:5000/api/providers | jq

# Get sample types
curl http://localhost:5000/api/sample-types | jq

# Get available topics
curl http://localhost:5000/api/topics | jq '.topics[]'

# Single sample with sample type
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "practice_area":"Contract Law",
    "topic":"Formation",
    "difficulty":"intermediate",
    "provider":"cerebras",
    "model":"gpt-oss-120b",
    "sample_type":"educational"
  }'

# Check health
curl http://localhost:5000/api/health

# Check for stuck batches
curl http://localhost:5000/api/batches/stuck
```

### Import Samples from JSONL

```bash
# Import samples (validates fields and checks for duplicates)
curl -X POST http://localhost:5000/api/import/jsonl \
  -H "Content-Type: application/json" \
  -d '{
    "content": "{\"id\":\"test_001\",\"question\":\"What is...\",\"answer\":\"...\",\"topic\":\"Contract Law\",\"difficulty\":\"basic\",\"case_citation\":\"...\",\"reasoning\":\"Step 1:...\"}\n{\"id\":\"test_002\",\"question\":\"...\",\"answer\":\"...\",\"topic\":\"Tort Law\",\"difficulty\":\"intermediate\",\"case_citation\":\"...\",\"reasoning\":\"Step 1:...\"}"
  }'

# Or use the React UI Dataset tab for easier multi-line pasting
```

### Utility Scripts

Located in `utils/` - run from root directory:
```bash
python3 utils/add_samples.py      # Add samples manually
python3 utils/analyze_tokens.py   # Token count analysis
python3 utils/clean_parquet.py    # Column management
```

## Critical Implementation Details

### Modular Backend Architecture

**Key Design Principle**: Separation of concerns via OOP and service layer pattern

**Service Layer** (`services/`):
- `generation_service.py`: Core generation logic with prompt engineering and quality validation
- `llm_service.py`: Provider abstraction via factory pattern (`LLMProviderFactory`)
  - Supports Groq, Cerebras, and Ollama providers
  - Unified interface for different API clients
  - Provider-specific rate limit configurations

**Utilities** (`utils/`):
- `error_handler.py`: Error categorization (7 categories) with intelligent switching logic
- `circuit_breaker.py`: Prevents repeated failures on problematic topics

**Configuration** (`config.py`):
- Centralized provider settings (API keys, rate limits, model lists)
- Difficulty specifications for validation
- Jurisdiction topics and sample type definitions
- Fallback orders for automatic model switching

**Benefits**:
- Easy to add new providers (implement provider interface in `llm_service.py`)
- Testable components (services can be unit tested independently)
- Maintainable codebase (each module has single responsibility)
- Reusable logic (e.g., `GenerationService` used in both API and test scripts)

### Flask API Requirements
- **MUST** run from `legal-dashboard/` directory
- Expects `train.parquet` in `legal-dashboard/` directory
- API keys configured in `config.py` (Groq, Cerebras, Ollama, HuggingFace)
- Background batch generation state persists to SQLite database
- Auto-saves every 10 samples during batch generation
- Thread-safe parquet writes via `parquet_lock`

### Parquet Compression
- **Both `train.parquet` files**: ZSTD compression (verified Oct 2025)
- Root file and dashboard file are synchronized with identical compression
- Hyparquet (React library) only reads metadata, not row data → Flask API required for data access
- Note: Previous documentation stated dashboard used SNAPPY, but actual implementation uses ZSTD throughout
- Convert if needed: `df.write_parquet("output.parquet", compression="zstd")`

### Data Validation
All operations must validate 7 required fields:
```python
REQUIRED_FIELDS = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']

# Check before adding
if not all(field in sample for field in REQUIRED_FIELDS):
    raise ValueError("Missing required fields")
```

### Rate Limiting
Provider-specific constraints handled automatically:

**Groq**:
- 25 requests/minute
- 5,500 tokens/minute
- Generator auto-waits when hitting limits

**Cerebras**:
- 600 requests/minute
- 48,000 tokens/minute
- Significantly higher throughput

**Generation Params**:
- Max 4000 tokens/sample
- Temperature: 0.9 for variety
- Automatic rate limit tracking per provider

### Data Loading Patterns
```python
# Polars (preferred - fastest)
import polars as pl
df = pl.read_parquet("train.parquet")

# Add samples
new_df = pl.concat([df, pl.DataFrame([new_sample])])
new_df.write_parquet("train.parquet", compression="zstd")
```

## Important Constraints

1. **Vite Version**: MUST use Vite 4.5.0 (not 5+) for Node 18 compatibility
2. **Working Directory**: Flask API MUST run from `legal-dashboard/` directory
3. **Port Conflicts**: Kill with `lsof -ti:PORT | xargs kill -9`
4. **API Key**: Hardcoded in `api_server.py` line 17
5. **Dataset Synchronization**: Root and dashboard files kept in sync with ZSTD compression
6. **Browser Limitation**: Hyparquet can't read row data → use Flask API

## API Endpoints

See [API_USAGE.md](API_USAGE.md) for complete documentation.

**Key endpoints:**
- `GET /api/data` - All samples (2,054+ total)
- `GET /api/stats` - Statistics with difficulty/topic distributions
- `GET /api/stats/detailed` - Comprehensive statistics with practice area breakdown
- `GET /api/stats/tokens` - Token statistics with cost estimates
- `GET /api/topics` - 75+ legal topics across UK, US, EU, and International jurisdictions
- `GET /api/jurisdictions` - Available jurisdictions (UK, US, EU, International)
- `GET /api/models` - 28+ models from Groq and Cerebras
- `GET /api/providers` - Provider configurations and rate limits
- `GET /api/sample-types` - 4 sample types with descriptions
- `POST /api/huggingface/push` - Push dataset to HuggingFace Hub (rzeraat, supports parquet/json/csv)
- `POST /api/generate` - Generate single sample (accepts sample_type parameter)
- `POST /api/generate/batch/start` - Start batch (background, accepts model/topic/difficulty/sample_type filters)
- `GET /api/generate/batch/status` - Poll progress (5s intervals)
- `GET /api/generate/batch/history` - View all batch history from database
- `GET /api/generate/batch/stream` - SSE endpoint for real-time updates
- `POST /api/generate/batch/stop` - Stop batch (optionally by batch_id)
- `POST /api/add` - Add sample manually
- `POST /api/import/jsonl` - Import multiple samples from JSONL (validates & deduplicates)
- `PUT /api/sample/<id>` - Update existing sample
- `DELETE /api/sample/<id>` - Delete sample
- `GET /api/samples/random` - Get random samples with optional filters
- `GET /api/search` - Full-text search across samples
- `GET /api/health` - Health check
- `GET /api/batches/stuck` - Detect stuck batches

## Data Quality Standards

- Real UK case citations only (no fabricated cases)
- Reasoning format: "Step 1: ... Step 2: ..."
- Realistic questions (lawyer/client scenarios)
- Legally accurate for UK jurisdiction
- Unique IDs, no missing fields
- Current quality issues (as of analysis):
  - 576 samples missing citations (need fixing)
  - 54 samples with short answers (<100 chars)
  - 370 samples with short reasoning (<50 chars)
  - Advanced difficulty dominates at 42.7% (878 samples)
  - Expert level underrepresented at 4.9% (101 samples)

## Dataset Insights (from latest analysis)

**Coverage by Practice Area (Top 10):**
- Company Law: 353 samples
- Immigration Law: 204 samples
- Legal Skills: 116 samples
- Contract Law: 94 samples
- Employment Law: 65 samples
- Tort Law: 61 samples
- Property Law: 38 samples
- Data Protection: 38 samples

**Underrepresented Topics (< 30 samples each):**
- Criminal Law, Intellectual Property, Tax Law, Civil Procedure
- 100+ niche topics with < 5 samples each

**Generation Recommendations:**
- Add expert-level samples for Immigration Law, Assistant Experience
- Generate basic-level samples for underrepresented areas
- Fix 576 samples with missing citations
- Balance difficulty distribution (reduce advanced, increase expert/basic)

## File Structure

```
Data/
├── train.parquet              # Main dataset (ZSTD compression)
├── start_apps.sh              # Launch script
├── legal-dashboard/
│   ├── api_server.py         # Flask backend (run from here!)
│   ├── train.parquet         # Synchronized copy (ZSTD)
│   ├── package.json          # Vite 4.5.0
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx           # Main React component
│       └── App.css           # GitHub dark theme
├── utils/                     # Utility scripts
│   ├── add_samples.py        # Manual sample addition
│   ├── analyze_tokens.py     # Token analysis
│   └── clean_parquet.py      # Column management
├── docs/                      # Reference materials
├── README.md
├── CLAUDE.md                  # This file
└── API_USAGE.md               # API reference
```

## Common Issues & Solutions

**Port already in use:**
```bash
lsof -ti:5000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**Flask can't find train.parquet:**
- Ensure you're running from `legal-dashboard/` directory
- Copy root parquet: `cp train.parquet legal-dashboard/`

**Batch generation stuck:**
```bash
curl -X POST http://localhost:5000/api/generate/batch/stop
```

**React can't read parquet directly:**
- Hyparquet limitation - use Flask API instead
- All data access must go through `/api/data` endpoint

**Parquet compression:**
```python
# Both files use ZSTD compression (verified Oct 2025)
df.write_parquet("train.parquet", compression="zstd")

# Note: Previously documented as root=ZSTD, dashboard=SNAPPY
# Actual implementation uses ZSTD for both files
```

## Development Workflow

**Typical session:**
1. Start apps: `./start_apps.sh`
2. Open browser: http://localhost:5173
3. Use the React UI:
   - **Overview Tab**: View stats, charts, quick metrics in sidebar
   - **Generation Tab**: Select model, topic, difficulty, start batch generation
   - **Dataset Tab**: Import JSONL, search samples, view data table
4. Monitor generation progress in sidebar or via API
5. Check logs if issues: `tail -f /tmp/flask.log`

**UI Features:**
- **Sidebar**: Sticky quick stats, real-time generation progress with pulsing indicator
- **Model Selection**: Choose from 19 Groq models (llama-3.3-70b-versatile default)
- **Topic Filtering**: Select specific practice area/topic or use balanced mix
- **Difficulty Filtering**: Generate only specific difficulty level or balanced
- **JSONL Import**: Paste multi-line JSONL in Dataset tab, validates & deduplicates
- **Search**: Full-text search across all fields in dataset explorer
- **Responsive**: Sidebar becomes horizontal on tablets, table scrolls on mobile

**Adding samples programmatically:**
```python
import polars as pl
import requests

# Via API (recommended)
response = requests.post('http://localhost:5000/api/add', json={
    "id": "custom_001",
    "question": "What is...",
    "answer": "Under UK law...",
    "topic": "Contract Law - Formation",
    "difficulty": "intermediate",
    "case_citation": "Carlill v Carbolic Smoke Ball [1893] 1 QB 256",
    "reasoning": "Step 1: ..."
})

# Bulk import via JSONL
jsonl_content = """
{"id":"bulk_001","question":"...","answer":"...","topic":"...","difficulty":"...","case_citation":"...","reasoning":"..."}
{"id":"bulk_002","question":"...","answer":"...","topic":"...","difficulty":"...","case_citation":"...","reasoning":"..."}
"""
response = requests.post('http://localhost:5000/api/import/jsonl',
    json={'content': jsonl_content})

# Or direct file manipulation
df = pl.read_parquet("train.parquet")
new_df = pl.concat([df, pl.DataFrame([sample])])
new_df.write_parquet("train.parquet", compression="zstd")
```

## Key Implementation Notes

**Batch Generation Filters:**
- When `topic` filter is provided, only generates samples for that specific topic
- When `difficulty` filter is provided, overrides default balanced mix
- Filters stored in `batch_generation_state` and applied during generation loop
- State resets on server restart (in-memory only)

**React Component Structure:**
- Single-page app with tab navigation (overview/generation/data)
- Sidebar uses sticky positioning (desktop) or horizontal scroll (mobile)
- Generation status polls every 5 seconds via `/api/generate/batch/status`
- Charts use Recharts library (PieChart for difficulties, potential for more)
- Glassmorphism design with backdrop-filter blur effects

**Critical URL Pattern:**
- React MUST fetch from `http://127.0.0.1:5000` (NOT `localhost:5000`)
- Reason: Flask CORS configuration or local DNS resolution issue
- All API URLs in App.jsx use 127.0.0.1 explicitly

## Recent Enhancements (October 2025)

**1. Multi-Provider System:**
- Added Cerebras provider alongside Groq (28+ total models)
- Intelligent cross-provider failover with error categorization
- Provider-specific rate limit handling (Cerebras: 600 req/min vs Groq: 25 req/min)
- Champion model identified: Cerebras `gpt-oss-120b` (10/10 quality score in empirical testing)
- Automatic provider switching when all models in current provider exhausted

**2. Sample Types System:**
- 9 distinct sample types with unique answer structures for comprehensive training
- Type-specific prompts and validation logic in `GenerationService`
- **Core Legal Types**:
  - `case_analysis` (IRAC methodology)
  - `educational` (structured teaching)
  - `client_interaction` (practical advice)
  - `statutory_interpretation` (legislative analysis)
- **Advanced Reasoning Types**:
  - `legal_dialogue` (multi-turn conversations for dialectical reasoning)
  - `pure_conceptual` (encyclopedic knowledge without reasoning - textbook style)
  - `comparative_analysis` (cross-jurisdiction/doctrine comparisons)
  - `ethical_reasoning` (professional conduct and moral dilemmas)
  - `procedural_guide` (step-by-step procedural instructions)
- Configurable per-sample or per-batch via API parameters
- Special handling: `pure_conceptual` type doesn't require reasoning steps

**3. Enhanced Generation Architecture:**
- Circuit breaker pattern prevents repeated failures (3 failures → 5-minute pause per topic)
- 7-category error classification system for intelligent failover
- Quality validation with difficulty-specific reasoning step requirements
- JSON extraction pipeline handles thinking model outputs (removes `<thinking>` tags)
- Model switch tracking and analytics in batch history

**4. Batch Management & Persistence:**
- SQLite database (`batches.db`) for batch history persistence
- Multiple concurrent batches supported via unique batch IDs
- Real-time SSE streaming endpoint for live progress updates
- Comprehensive batch history API with model switch tracking
- Stuck batch detection endpoint for monitoring long-running jobs

**5. HuggingFace Integration:**
- One-click push to HuggingFace Hub via `/api/huggingface/push`
- Support for parquet, json, and csv export formats
- Public/private repository options
- Token management across multiple environment locations (bashrc, zshrc, LaunchAgents)
- Optional frontend token field (uses environment variable by default)

**6. Frontend Modernization:**
- Upgraded to React 19 with Material UI v7
- Glassmorphism dark theme with frosted glass effects
- Five-tab interface: Overview, Generation, Dataset, Batches, Documentation
- Real-time statistics with auto-refresh every 10 seconds
- DataGrid with CRUD operations (add, edit, delete samples)
- Batch history viewer with filtering and model switch analytics

**7. Token Analytics & Cost Estimation:**
- Comprehensive token counting via tiktoken (GPT-4 encoding)
- `/api/stats/tokens` endpoint with detailed breakdowns
- Token statistics by field, difficulty, and practice area
- Cost estimates for multiple Groq model tiers
- Average tokens per sample tracking across dataset
