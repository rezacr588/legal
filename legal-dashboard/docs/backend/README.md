# Legal Training Platform - Backend Documentation

**Version**: 2.0 (October 2025)
**Technology Stack**: Flask 3.0, Python 3.9+, SQLAlchemy, Polars
**Multi-Provider Support**: Groq (19 models), Cerebras (9 models), Ollama (5 models)

---

## 📚 Table of Contents

### Part I: System Overview
1. **Architecture** - System design, modular structure, data flow (see "Architecture at a Glance" below)
2. **Configuration** - Environment setup, API keys, settings (see "Configuration Preview" below)

### Part II: Core Systems
3. **Features & Systems** - Deep dive into all backend features (see "System Highlights" below)
   - Multi-Provider LLM System
   - Generation Service Architecture
   - Sample Types System
   - Circuit Breaker Pattern
   - Error Handling & Failover
   - Quality Validation Pipeline
   - Batch Management & Persistence
   - Real-time Progress Tracking (SSE)

### Part III: API Reference
4. **API Endpoints** - Complete REST API documentation (see "Use Cases" below)
   - Generation Endpoints
   - Configuration Endpoints
   - Data Management (CRUD)
   - Batch Operations
   - Statistics & Analytics
   - HuggingFace Integration
   - Health & Monitoring

### Part IV: Development
5. **Development Guide** - Development workflows, testing, patterns (see "Development Workflow" below)
6. **Troubleshooting** - Common issues and solutions (see "Common Issues" below)

**Note**: This README consolidates all backend documentation into a single comprehensive guide.

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.9+ required
python3 --version

# Install dependencies
cd legal-dashboard
pip3 install -r requirements.txt
```

### Environment Setup
```bash
# Set API keys (choose providers)
export GROQ_API_KEY="your_groq_key"
export CEREBRAS_API_KEY="your_cerebras_key"
export OLLAMA_API_KEY="your_ollama_key"  # Optional
export HUGGINGFACE_TOKEN="your_hf_token"  # For dataset publishing
```

### Start Server
```bash
# IMPORTANT: Must run from legal-dashboard/ directory
cd legal-dashboard
python3 api_server.py

# Server starts on http://localhost:5001
# API available at http://localhost:5001/api/*
```

### Health Check
```bash
curl http://localhost:5001/api/health
```

---

## 📊 System Highlights

### Multi-Provider Architecture
- **3 Providers**: Groq, Cerebras, Ollama Cloud
- **28+ Models**: Automatic fallback across providers
- **Intelligent Switching**: Cross-provider failover on errors
- **Rate Limit Management**: Provider-specific throttling

### Generation Capabilities
- **4 Sample Types**: Case Analysis, Educational, Client Interaction, Statutory Interpretation
- **4 Difficulty Levels**: Basic, Intermediate, Advanced, Expert
- **75+ Legal Topics**: UK, US, EU, International jurisdictions
- **Quality Validation**: Post-generation checks with difficulty-specific requirements

### Batch Processing
- **Concurrent Batches**: Multiple batch generations simultaneously
- **Auto-Save**: Every 10 samples to prevent data loss
- **Real-time Updates**: SSE streaming for live progress
- **Persistence**: SQLite database for batch history

### Data Management
- **Apache Parquet**: ZSTD compression, Polars processing
- **2000+ Samples**: Legal Q&A dataset with full metadata
- **CRUD Operations**: Add, update, delete, import/export
- **HuggingFace Push**: One-click dataset publishing

---

## 🏗️ Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flask API Server                          │
│                     (api_server.py - Port 5001)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Services   │    │    Models    │    │   Utilities  │
│              │    │              │    │              │
│ • generation │    │ • database   │    │ • error_     │
│   _service   │    │   (SQLAlch-  │    │   handler    │
│ • llm_       │    │    emy)      │    │ • circuit_   │
│   service    │    │              │    │   breaker    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Provider Abstraction │
                │  (Factory Pattern)    │
                └───────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ GroqProvider │    │ Cerebras     │    │ Ollama       │
│              │    │ Provider     │    │ Provider     │
│ 19 models    │    │ 9 models     │    │ 5 models     │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 📁 Project Structure

```
legal-dashboard/
├── api_server.py           # Main Flask application (2067 lines)
├── config.py               # Centralized configuration (359 lines)
│
├── services/               # Business logic layer
│   ├── generation_service.py   # Sample generation orchestration
│   └── llm_service.py          # Provider abstraction (Factory pattern)
│
├── models/                 # Data models
│   └── database.py             # SQLAlchemy models (BatchHistory)
│
├── utils/                  # Utility functions
│   ├── error_handler.py        # Error categorization
│   └── circuit_breaker.py      # Circuit breaker pattern
│
├── train.parquet           # Main dataset (SNAPPY compression)
├── batches.db              # SQLite batch history
│
└── docs/                   # Documentation
    └── backend/            # This documentation
```

---

## 🔑 Key Concepts

### 1. Provider Abstraction
All LLM providers implement `BaseLLMProvider` interface, enabling seamless switching:
```python
provider = LLMProviderFactory.get_provider('cerebras')
result = provider.generate(model='gpt-oss-120b', prompt='...')
```

### 2. Generation Service
Orchestrates sample generation with:
- Type-specific prompts (IRAC, Educational, Client, Statutory)
- Quality validation (reasoning steps, structure, content)
- Error handling with intelligent failover
- JSON extraction for thinking models

### 3. Circuit Breaker
Prevents wasting tokens on consistently failing topics:
- **CLOSED**: Normal operation
- **OPEN**: Skip topic for 5 minutes after 3 failures
- **HALF-OPEN**: Test recovery after timeout

### 4. Batch State Management
Concurrent batch support via:
```python
active_batches = {
    'batch_123': {
        'running': True,
        'progress': 50,
        'samples_generated': 25,
        'current_model': 'gpt-oss-120b',
        'circuit_breaker_summary': {...}
    }
}
```

---

## 📈 Performance Characteristics

### Provider Comparison
| Provider  | Requests/Min | Tokens/Min | Models | Champion Model         |
|-----------|--------------|------------|--------|------------------------|
| Groq      | 25           | 5,500      | 19     | llama-3.3-70b-versatile|
| Cerebras  | 600          | 48,000     | 9      | gpt-oss-120b (10/10)   |
| Ollama    | 60           | 10,000     | 5      | kimi-k2:1t-cloud       |

### Generation Speed
- **Single Sample**: 2-4 seconds (varies by model/provider)
- **Batch (100 samples)**: ~8-15 minutes (with rate limiting)
- **Auto-save**: Every 10 samples (prevents data loss)

### Data Storage
- **Parquet Compression**: ZSTD (30-40% smaller than SNAPPY)
- **Polars Processing**: 10x faster than Pandas for large datasets
- **Thread-safe Writes**: Mutex lock prevents concurrent write conflicts

---

## 🎯 Use Cases

### 1. High-Volume Generation
```bash
curl -X POST http://localhost:5001/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{"target_count": 3000, "provider": "cerebras"}'
```

### 2. Filtered Generation
```bash
curl -X POST http://localhost:5001/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_count": 2200,
    "topic": "Company Law - Directors Duties",
    "difficulty": "advanced",
    "sample_type": "case_analysis"
  }'
```

### 3. Real-time Monitoring
```javascript
const eventSource = new EventSource('http://localhost:5001/api/generate/batch/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.samples_generated}/${data.total}`);
};
```

### 4. Dataset Publishing
```bash
curl -X POST http://localhost:5001/api/huggingface/push \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "uk-legal-dataset", "format": "parquet", "private": false}'
```

---

## 📝 Sample Data Schema

Every sample has exactly **7 required fields** + optional metadata:

```json
{
  "id": "cerebras_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "question": "Legal question text",
  "answer": "Comprehensive answer (follows sample_type structure)",
  "topic": "Practice Area - Subtopic",
  "difficulty": "basic|intermediate|advanced|expert",
  "case_citation": "Real UK cases and statutes",
  "reasoning": "Step 1: ... Step 2: ... (chain of thought)",
  "sample_type": "case_analysis|educational|client_interaction|statutory_interpretation",

  // Metadata (auto-generated)
  "created_at": "2025-10-17T12:34:56.789",
  "updated_at": "2025-10-17T12:34:56.789",
  "provider": "cerebras",
  "model": "gpt-oss-120b",
  "batch_id": "batch_1729168496_a1b2c3d4"
}
```

---

## 🔧 Configuration Preview

See Configuration section above for full details.

**Key Settings** (`config.py`):
- `PROVIDERS`: API keys, rate limits, default models
- `DIFFICULTY_SPECS`: Quality thresholds per difficulty level
- `SAMPLE_TYPES`: 4 distinct sample type definitions
- `TOPICS`: 75+ legal topics across jurisdictions
- `CIRCUIT_BREAKER_*`: Failure handling configuration

---

## 🛠️ Development Workflow

1. **Setup**: Install dependencies, set environment variables
2. **Start Server**: `python3 api_server.py` (from legal-dashboard/)
3. **Test Generation**: Use `/api/generate` for single samples
4. **Start Batch**: Use `/api/generate/batch/start` for bulk
5. **Monitor**: Poll `/api/generate/batch/status` or use SSE stream
6. **Export**: Push to HuggingFace via `/api/huggingface/push`

See sections above for detailed workflows and guidance.

---

## 🚨 Common Issues

### Port Already in Use
```bash
lsof -ti:5001 | xargs kill -9
```

### Flask Can't Find Dataset
```bash
# Ensure you're in legal-dashboard/ directory
cd legal-dashboard
python3 api_server.py
```

### API Key Not Found
```bash
# Check environment variables
env | grep -E "(GROQ|CEREBRAS|OLLAMA)_API_KEY"
```

For additional issues, see CLAUDE.md in the project root.

---

## 📞 Support & Resources

- **GitHub Issues**: [Report bugs/request features]
- **API Documentation**: See Use Cases section above
- **Architecture Details**: See Architecture section above
- **Feature Deep Dives**: See System Highlights section above

---

## 📄 License

This project is part of the Global Legal AI Training Platform.

---

## 🎓 Next Steps

1. Read **Architecture at a Glance** section to understand system design
2. Review **Configuration Preview** and **Environment Setup** to set up your environment
3. Explore **Use Cases** section for API endpoint examples
4. Study **System Highlights** for deep dives into capabilities
5. Check **Development Workflow** section for development patterns
6. Keep **Common Issues** section handy for troubleshooting

**Additional Resources**:
- See `/Users/rezazeraat/Desktop/Data/CLAUDE.md` for comprehensive project documentation
- See `/Users/rezazeraat/Desktop/Data/API_USAGE.md` for complete API reference

**Happy Building! 🚀**
