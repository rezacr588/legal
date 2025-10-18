# Parquet to PostgreSQL Migration

**Date Created**: 2025-10-18
**Priority**: High
**Status**: Not Started

---

## Objective

Migrate all legal training dataset from Parquet files to PostgreSQL database to eliminate file-based storage and use a single, centralized database for all data.

---

## Requirements

- [ ] Create PostgreSQL table schema for legal samples
- [ ] Create migration script to import parquet data to PostgreSQL
- [ ] Update backend API to read from PostgreSQL instead of Parquet
- [ ] Update data insertion endpoints to write to PostgreSQL
- [ ] Create indexes for optimal query performance
- [ ] Test all API endpoints with PostgreSQL backend
- [ ] Remove parquet file dependencies from codebase

---

## Current State

**Data Storage**:
- Legal samples: `backend/data/train.parquet` (2,054+ samples)
- Batch history: PostgreSQL `batches.db` table (already migrated)

**Schema** (7 required fields):
```python
{
  "id": str,              # Unique identifier
  "question": str,        # Legal question
  "answer": str,          # Comprehensive answer
  "topic": str,           # Practice Area - Subtopic
  "difficulty": str,      # basic|intermediate|advanced|expert
  "case_citation": str,   # Real cases/statutes
  "reasoning": str        # Chain of thought
}
```

**Optional fields**:
```python
{
  "jurisdiction": str,    # uk|us|eu|international
  "batch_id": str,        # Batch tracking
  "sample_type": str      # case_analysis|educational|client_interaction|statutory_interpretation
}
```

---

## Implementation Steps

### 1. Create PostgreSQL Table Schema

Create `backend/models/legal_sample.py`:

```python
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class LegalSample(Base):
    __tablename__ = 'legal_samples'

    # Required fields
    id = Column(String(200), primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    topic = Column(String(200), nullable=False)
    difficulty = Column(String(50), nullable=False)
    case_citation = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)

    # Optional fields
    jurisdiction = Column(String(50), default='uk')
    batch_id = Column(String(100), nullable=True)
    sample_type = Column(String(50), default='case_analysis')

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_topic', 'topic'),
        Index('idx_difficulty', 'difficulty'),
        Index('idx_jurisdiction', 'jurisdiction'),
        Index('idx_sample_type', 'sample_type'),
        Index('idx_batch_id', 'batch_id'),
    )
```

### 2. Create Migration Script

Create `backend/scripts/migrate_parquet_to_postgres.py`:

```python
import polars as pl
from pathlib import Path
from sqlalchemy import create_engine
from backend.models.legal_sample import LegalSample, Base
from backend.config import DATABASE_URI, PARQUET_PATH

def migrate_parquet_to_postgres():
    # Read parquet file
    df = pl.read_parquet(PARQUET_PATH)

    # Create engine and tables
    engine = create_engine(DATABASE_URI)
    Base.metadata.create_all(engine)

    # Convert to records
    records = df.to_dicts()

    # Insert records
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    for record in records:
        sample = LegalSample(**record)
        session.add(sample)

    session.commit()
    print(f"Migrated {len(records)} samples to PostgreSQL")
```

### 3. Update Backend Services

Update `backend/services/data_service.py`:

```python
class DataService:
    @staticmethod
    def get_all_samples():
        session = get_session()
        samples = session.query(LegalSample).all()
        return [sample.to_dict() for sample in samples]

    @staticmethod
    def get_sample_by_id(sample_id):
        session = get_session()
        return session.query(LegalSample).filter_by(id=sample_id).first()

    @staticmethod
    def add_sample(sample_data):
        session = get_session()
        sample = LegalSample(**sample_data)
        session.add(sample)
        session.commit()
        return sample

    @staticmethod
    def get_stats():
        session = get_session()
        total = session.query(LegalSample).count()
        by_difficulty = session.query(
            LegalSample.difficulty,
            func.count(LegalSample.id)
        ).group_by(LegalSample.difficulty).all()
        # ... etc
```

### 4. Update API Routes

Update all API routes in `legal-dashboard/api_server.py` or create new routes in `backend/routes/`:

```python
@app.route('/api/data', methods=['GET'])
def get_data():
    samples = DataService.get_all_samples()
    return jsonify(samples)

@app.route('/api/add', methods=['POST'])
def add_sample():
    data = request.json
    sample = DataService.add_sample(data)
    return jsonify(sample.to_dict())
```

### 5. Create Indexes for Performance

```sql
CREATE INDEX idx_topic ON legal_samples(topic);
CREATE INDEX idx_difficulty ON legal_samples(difficulty);
CREATE INDEX idx_jurisdiction ON legal_samples(jurisdiction);
CREATE INDEX idx_sample_type ON legal_samples(sample_type);
CREATE INDEX idx_batch_id ON legal_samples(batch_id);
CREATE INDEX idx_created_at ON legal_samples(created_at);
```

### 6. Update Configuration

Update `backend/config.py`:

```python
# Remove PARQUET_PATH or mark as deprecated
# PARQUET_PATH = Path(__file__).parent / "data" / "train.parquet"  # DEPRECATED

# Use only DATABASE_URI for all data
DATABASE_URI = os.getenv(
    'DATABASE_URL',
    'postgresql://legal_user:password@postgres:5432/legal_dashboard'
)
```

---

## Acceptance Criteria

- [ ] PostgreSQL table `legal_samples` created with proper schema
- [ ] All 2,054+ samples migrated from parquet to PostgreSQL
- [ ] GET `/api/data` returns samples from PostgreSQL
- [ ] POST `/api/add` writes to PostgreSQL
- [ ] GET `/api/stats` calculates from PostgreSQL
- [ ] All search/filter endpoints use PostgreSQL
- [ ] Batch generation saves directly to PostgreSQL
- [ ] JSONL import writes to PostgreSQL
- [ ] HuggingFace export reads from PostgreSQL
- [ ] Performance tests show acceptable query times (<100ms for most queries)
- [ ] No parquet file references in active code
- [ ] Documentation updated

---

## Benefits

1. **Single Source of Truth**: All data in PostgreSQL (samples + batch history)
2. **Better Performance**: Indexed queries faster than full parquet scans
3. **ACID Compliance**: Transactions prevent data corruption
4. **Concurrent Access**: Multiple processes can safely read/write
5. **Advanced Queries**: Use SQL for complex filtering and aggregation
6. **Relationships**: Can add foreign keys between samples and batches
7. **Backups**: Standard PostgreSQL backup tools
8. **Scalability**: Ready for millions of samples

---

## Risks & Mitigations

**Risk**: Data loss during migration
**Mitigation**: Keep parquet file as backup, test migration on copy first

**Risk**: Performance degradation
**Mitigation**: Create proper indexes, test query performance

**Risk**: API downtime during migration
**Mitigation**: Migrate data offline, switch atomically

---

## Migration Strategy

### Option A: Offline Migration (Recommended)
1. Stop services
2. Run migration script
3. Test PostgreSQL backend
4. Restart services with PostgreSQL
5. Keep parquet as backup for 30 days

### Option B: Dual Read/Write
1. Write to both parquet and PostgreSQL
2. Gradually migrate reads to PostgreSQL
3. Verify data consistency
4. Switch fully to PostgreSQL
5. Remove parquet writes

**Recommendation**: Use Option A (simpler, cleaner cutover)

---

## Testing Plan

1. **Unit Tests**: Test DataService methods
2. **Integration Tests**: Test API endpoints end-to-end
3. **Performance Tests**: Benchmark query times
4. **Load Tests**: Test with 10K+ samples
5. **Data Validation**: Verify all fields migrated correctly

---

## Rollback Plan

If PostgreSQL migration fails:

```bash
# Restore from parquet backup
docker-compose down
git checkout backend/  # Restore old code
docker-compose up -d
```

---

## Estimated Duration

~2-3 hours

**Breakdown**:
- Create table schema: 30 min
- Create migration script: 30 min
- Update backend services: 45 min
- Update API routes: 30 min
- Testing and verification: 45 min

---

## Dependencies

- PostgreSQL service running (completed ✅)
- Backend/PostgreSQL connection working (completed ✅)
- Parquet file accessible (`backend/data/train.parquet`)

---

## Files to Create/Modify

**New Files**:
- `backend/models/legal_sample.py`
- `backend/services/data_service.py`
- `backend/scripts/migrate_parquet_to_postgres.py`
- `backend/routes/data.py` (optional, if breaking out routes)

**Modified Files**:
- `backend/config.py` (deprecate PARQUET_PATH)
- `legal-dashboard/api_server.py` (update all data access)
- `backend/models/__init__.py` (add LegalSample)

---

## Notes

- Keep parquet files for backup until PostgreSQL proven stable
- Consider adding full-text search using PostgreSQL's tsvector
- Could add versioning/history tracking for samples
- Future: Add user accounts and permissions
- Future: Add audit logging for data changes

---

## Success Metrics

- [ ] 100% of parquet samples in PostgreSQL
- [ ] All API endpoints functional
- [ ] Query performance <100ms for common queries
- [ ] Zero data loss or corruption
- [ ] All tests passing
- [ ] Documentation complete

---

## Related Tasks

- Depends on: PostgreSQL Migration (Completed ✅)
- Blocks: None
- Related: Codebase Cleanup (could remove parquet files after migration)
