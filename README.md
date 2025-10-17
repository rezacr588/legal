# ⚖️ UK Legal Training Dataset

A comprehensive, LLM-generated dataset of UK legal Q&A samples for training AI legal assistants. This repository contains high-quality training data covering multiple practice areas of UK law.

## 📊 Dataset Overview

- **Format**: Apache Parquet (with JSONL export support)
- **Current Size**: 2,100+ samples (growing)
- **Compression**: ZSTD
- **Storage**: ~650KB compressed

### Practice Areas Covered

- ✅ **Contract Law** - Formation, breach, remedies, misrepresentation
- ✅ **Company Law** - Directors' duties, governance, insolvency, formation
- ✅ **Employment Law** - Discrimination, dismissal, contracts, TUPE, redundancy
- ✅ **Tort Law** - Negligence, defamation, liability, nuisance
- ✅ **Property Law** - Land registration, leasehold/freehold, easements, mortgages
- ✅ **Criminal Law** - Actus reus, mens rea, murder, defenses, fraud
- ✅ **Trusts Law** - Three certainties, constructive trusts, charitable trusts
- ✅ **Tax Law** - Capital gains, VAT, income tax
- ✅ **Family Law** - Divorce, custody, financial settlements
- ✅ **Administrative Law** - Judicial review, public law remedies
- ✅ **Legal Ethics** - Conflicts of interest, confidentiality, money laundering

## 📁 Dataset Structure

Each sample contains 7 fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique identifier (e.g., `contract_law_formation_001`) |
| `question` | String | Realistic UK legal question |
| `answer` | String | Comprehensive, legally accurate answer |
| `topic` | String | Practice area and specific topic |
| `difficulty` | String | `basic`, `intermediate`, `advanced`, or `expert` |
| `case_citation` | String | Relevant UK cases or statutes |
| `reasoning` | String | Step-by-step legal analysis |

### Example Sample

```json
{
  "id": "tort_law_negligence_028",
  "question": "What is the test for establishing a duty of care in negligence?",
  "answer": "The test for duty of care was established in Caparo Industries v Dickman [1990] and requires three elements: 1) Foreseeability - was the damage reasonably foreseeable? 2) Proximity - was there sufficient relationship of proximity between claimant and defendant? 3) Fair, just and reasonable - is it fair, just and reasonable to impose a duty in all the circumstances?",
  "topic": "Tort Law - Negligence - Duty of Care",
  "difficulty": "intermediate",
  "case_citation": "Caparo Industries plc v Dickman [1990] 2 AC 605; Donoghue v Stevenson [1932] AC 562",
  "reasoning": "Step 1: State the three-stage Caparo test. Step 2: Explain each element with examples. Step 3: Distinguish between established duty categories and novel situations. Step 4: Apply the incremental approach for new cases. Step 5: Consider policy factors that may negate a duty."
}
```

## 🚀 Quick Start

### Launch Applications

```bash
# Start Flask API + React UI
./start_apps.sh
```

This starts:
- **React UI**: http://localhost:5173 (main interface)
- **Flask API**: http://localhost:5000 (backend)

### Command-Line Tools

```bash
# Install parquet-tools
pip install parquet-tools

# View samples
parquet-tools show train.parquet --head 10

# Export to CSV
parquet-tools csv train.parquet > output.csv

# Inspect metadata
parquet-tools inspect train.parquet
```

### Load in Python

```python
import polars as pl

# Load dataset
df = pl.read_parquet("train.parquet")

# Basic stats
print(f"Total samples: {len(df)}")
print(f"Columns: {df.columns}")

# Filter by difficulty
advanced_samples = df.filter(pl.col("difficulty") == "advanced")

# Export to JSONL
df.write_ndjson("train.jsonl")
```

## 🤖 Generate New Samples

Generate authentic UK legal samples via the unified Flask API:

```bash
# Start batch generation (runs in background)
curl -X POST http://localhost:5000/api/generate/batch/start \
  -H "Content-Type: application/json" \
  -d '{"target_count": 2100}'

# Monitor progress
curl http://localhost:5000/api/generate/batch/status

# Stop if needed
curl -X POST http://localhost:5000/api/generate/batch/stop
```

**Features:**
- Real LLM generation via Groq API (groq/compound model)
- Background batch generation with threading
- Real-time progress tracking
- Authentic UK case citations
- Step-by-step legal reasoning
- Respects Groq free tier limits (25 req/min)
- Auto-saves progress every 10 samples
- Covers 42 UK legal topics

See [API_USAGE.md](API_USAGE.md) for complete API documentation.

## 📈 React UI Features

The React web interface provides:

### 📊 Analytics Dashboard
- Total samples and dataset statistics
- Difficulty distribution visualization
- Practice area distribution
- Top 10 topics
- Real-time data updates

### 🤖 Generation Controls
- Start/stop batch generation
- Real-time progress tracking
- Monitor current sample being generated
- View token usage
- Error tracking

### 🔍 Search & Filter
- Full-text search across all fields
- Filter by difficulty level
- Filter by practice area
- Real-time result counts

### 📥 Data Operations
- View all samples in table
- Add new samples via API
- Export to various formats
- GitHub-style dark theme UI

## 🛠️ Utility Scripts

Located in `utils/` directory:

### `utils/add_samples.py`
Add custom samples manually to the dataset.

### `utils/analyze_tokens.py`
Analyze token counts using tiktoken (verify samples under 4000 tokens).

### `utils/clean_parquet.py`
Remove or manage Parquet columns.

**Note:** Most operations should now go through the Flask API instead of standalone scripts.

## 📊 Dataset Statistics

Current statistics (as of latest update):

- **Total Samples**: 2,100+
- **Difficulty Breakdown**:
  - Basic: ~20%
  - Intermediate: ~45%
  - Advanced: ~30%
  - Expert: ~5%
- **Average Lengths**:
  - Question: ~150 chars
  - Answer: ~400 chars
  - Reasoning: ~250 chars
- **Citation Coverage**: 100% (all samples include UK legal references)
- **Data Quality**: 0 missing values, all unique IDs

## 🎯 Use Cases

This dataset is ideal for:

- 🤖 **Training AI Legal Assistants** - Fine-tune LLMs on UK law
- 📚 **Legal Education** - Study materials for law students
- 🔍 **Semantic Search** - Build legal knowledge bases
- 💬 **Chatbot Training** - Develop legal Q&A systems
- 📊 **Legal Research** - Analyze UK case law patterns
- ✅ **Validation Sets** - Test legal AI models

## 🔧 Technical Stack

- **Storage**: Apache Parquet with ZSTD compression
- **Processing**: Polars (fast DataFrame library)
- **Backend**: Flask with CORS, background threading
- **Frontend**: React + Vite with GitHub dark theme
- **LLM Generation**: Groq API (groq/compound model)
- **CLI Tools**: parquet-tools, tiktoken

## 📝 Data Generation Methodology

All samples are generated using:

1. **Real LLM**: Groq's llama-3.3-70b-versatile model
2. **Authentic Citations**: Only real UK cases and statutes
3. **Legal Accuracy**: Prompts emphasize UK jurisdiction correctness
4. **Structured Reasoning**: Step-by-step legal analysis
5. **Quality Control**: Validation of required fields and formats

**Not used**:
- ❌ Template-based generation
- ❌ Fake citations
- ❌ Non-UK legal content
- ❌ Copied content from websites

## 🗂️ File Structure

```
Data/
├── train.parquet              # Main dataset (Parquet format)
├── start_apps.sh              # Unified startup script
├── legal-dashboard/           # React + Flask application
│   ├── api_server.py         # Unified Flask backend
│   ├── train.parquet         # Dataset copy (SNAPPY)
│   └── src/                  # React components
├── utils/                     # Utility scripts
│   ├── add_samples.py        # Manually add samples
│   ├── analyze_tokens.py     # Token analysis
│   └── clean_parquet.py      # Column management
├── deprecated/                # Old scripts (superseded by API)
│   ├── generate_groq_samples.py
│   ├── parquet_editor.py
│   └── README.md
├── docs/                      # Reference material
│   └── company-law.txt
├── README.md                  # This file
├── CLAUDE.md                  # Developer guide
└── API_USAGE.md               # API documentation
```

## 📜 License & Usage

This dataset is provided for:
- ✅ Educational purposes
- ✅ Research and development
- ✅ Training AI models
- ✅ Legal technology innovation

**Note**: This is a training dataset. AI-generated responses should not be considered legal advice. Always consult qualified solicitors for actual legal matters.

## 🤝 Contributing

To add samples:

1. **Via API** (recommended): Use Flask API endpoints for generation
2. **Manual**: Use `utils/add_samples.py` or POST to `/api/add`
3. Ensure all required fields are present
4. Include real UK case citations
5. Follow the existing format and quality standards

See [API_USAGE.md](API_USAGE.md) for details.

## 📞 Support

For questions or issues:
- Review the dataset using the React UI at http://localhost:5173
- Check API health at http://localhost:5000/api/health
- See [CLAUDE.md](CLAUDE.md) for developer documentation
- See [API_USAGE.md](API_USAGE.md) for API reference

## 🔄 Updates

Dataset is actively maintained and growing. Use the Flask API `/api/generate/batch/start` endpoint to add more samples.

---

**Built with**: Python 3.12, Polars, Flask, React + Vite, Groq API
**Last Updated**: October 2025
**Version**: 2.0 (Unified Backend)
