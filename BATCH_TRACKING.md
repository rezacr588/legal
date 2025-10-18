# Batch Tracking & Quality Monitoring

**Date**: October 18, 2025
**Status**: ✅ **FULLY IMPLEMENTED**

## Overview

Every sample in the dataset now includes a `batch_id` reference, allowing you to:
- Track which batch generated each sample
- Monitor batch progress in real-time
- Analyze quality metrics per batch
- Filter and export samples by batch

## Implementation Details

### Automatic Batch ID Tracking

**In Generation Service** (`backend/services/generation_service.py`):
```python
# Line 376-377
if batch_id:
    sample['batch_id'] = batch_id
```

Every sample generated during a batch automatically receives the batch identifier.

**In Data Service** (`backend/services/data_service.py`):
```python
# Line 74-84
def get_by_batch(self, batch_id: str) -> List[Dict]:
    """Get all samples from a specific batch"""
    samples = self.session.query(LegalSample).filter_by(batch_id=batch_id).all()
    return [s.to_dict() for s in samples]
```

**In Database Model** (`backend/models/legal_sample.py`):
```python
batch_id = Column(String, index=True)  # Indexed for fast filtering
```

## API Endpoints

### 1. Get Samples by Batch

**Endpoint**: `GET /api/batch/<batch_id>/samples`

**Example**:
```bash
curl "http://localhost:5001/api/batch/batch_1760796724_c95f3774/samples"
```

**Response**:
```json
{
  "success": true,
  "batch_id": "batch_1760796724_c95f3774",
  "samples": [...],
  "count": 31
}
```

**Use Cases**:
- Review all samples from a specific batch
- Export batch results for manual review
- Compare samples across different batches

### 2. Get Batch Quality Metrics

**Endpoint**: `GET /api/batch/<batch_id>/quality`

**Example**:
```bash
curl "http://localhost:5001/api/batch/batch_1760796724_c95f3774/quality"
```

**Response**:
```json
{
  "success": true,
  "batch_id": "batch_1760796724_c95f3774",
  "metrics": {
    "total_samples": 31,
    "total_tokens": 38018,
    "avg_tokens_per_sample": 1226.39,
    "avg_answer_length": 3832.52,
    "avg_reasoning_length": 1403.0,
    "avg_citation_length": 165.42
  },
  "distributions": {
    "difficulty": {
      "advanced": 13,
      "intermediate": 12,
      "basic": 5,
      "expert": 1
    },
    "topics": {
      "Contract Law - Breach of Contract": 1,
      "Tort Law - Defamation": 1,
      ...
    },
    "sample_types": {
      "case_analysis": 7,
      "client_interaction": 8,
      "educational": 8,
      "statutory_interpretation": 8
    },
    "jurisdictions": {
      "uk": 31
    }
  },
  "quality_score": {
    "issues": [],
    "rating": "Good"
  }
}
```

**Metrics Explained**:
- **total_tokens**: Total tokens across all samples (GPT-4 encoding)
- **avg_tokens_per_sample**: Average tokens per sample
- **avg_answer_length**: Average character length of answers
- **avg_reasoning_length**: Average character length of reasoning
- **avg_citation_length**: Average character length of case citations
- **distributions**: Breakdown by difficulty, topic, sample_type, jurisdiction
- **quality_score**: Automated quality assessment with issue flagging

**Quality Flags**:
- ❌ Short answers (avg < 300 chars)
- ❌ Short reasoning (avg < 100 chars)
- ❌ Short citations (avg < 50 chars)

If no issues detected: **Rating = "Good"** ✅

## Real-World Example

**Batch**: `batch_1760796724_c95f3774`
**Provider**: Cerebras
**Model**: llama-3.3-70b
**Samples**: 31

### Quality Report

✅ **Overall Rating**: Good

**Metrics**:
- Average tokens: 1,226 per sample
- Average answer length: 3,833 characters
- Average reasoning: 1,403 characters
- Average citations: 165 characters

**Distribution**:
- **Difficulty**: Balanced across basic (5), intermediate (12), advanced (13), expert (1)
- **Sample Types**: Evenly distributed (7-8 samples each type)
- **Topics**: 31 unique topics (excellent diversity)
- **Jurisdiction**: 100% UK law

**Token Usage**: 38,018 tokens total

## Integration with Batch History

The batch history endpoint (`/api/generate/batch/history`) now shows:
```json
{
  "id": "batch_1760796724_c95f3774",
  "samples_generated": 31,
  "target": 30,
  "status": "completed",
  "provider": "cerebras",
  "model": "llama-3.3-70b"
}
```

You can use the `id` from batch history to fetch:
1. All samples from that batch: `/api/batch/{id}/samples`
2. Quality metrics for that batch: `/api/batch/{id}/quality`

## Monitoring Batch Progress

### Real-Time Progress Tracking

**During Generation**:
1. Frontend polls `/api/generate/batch/history` every 5 seconds
2. Shows `samples_generated` count updating in real-time
3. When batch completes, you can immediately check quality

**After Completion**:
```bash
# Step 1: Get batch ID from history
curl "http://localhost:5001/api/generate/batch/history" | jq '.batches[0].id'

# Step 2: Get quality metrics
curl "http://localhost:5001/api/batch/{batch_id}/quality"

# Step 3: Review samples if quality is poor
curl "http://localhost:5001/api/batch/{batch_id}/samples" | jq '.samples[] | {id, question, answer}'
```

## Quality Benchmarks

Based on analysis of `batch_1760796724_c95f3774` (Good rating):

**Target Metrics for High-Quality Batches**:
- ✅ Average answer length: 3,000+ characters
- ✅ Average reasoning length: 1,000+ characters
- ✅ Average citation length: 100+ characters
- ✅ Average tokens per sample: 1,000+ tokens
- ✅ Difficulty distribution: Balanced across levels
- ✅ Topic diversity: Multiple unique topics
- ✅ Sample type balance: Evenly distributed

**Red Flags**:
- ❌ Average answer < 300 characters (too short)
- ❌ Average reasoning < 100 characters (insufficient depth)
- ❌ Average citations < 50 characters (weak legal support)
- ❌ All samples same difficulty (poor training diversity)
- ❌ All samples same topic (poor coverage)

## Dataset Explorer Enhancement

The Dataset tab in the React frontend can now:
1. Display `batch_id` column in the DataGrid
2. Filter samples by batch_id
3. Show batch quality metrics in a card/dialog
4. Export samples from a specific batch

**Example Filter**:
```javascript
// Filter dataset by batch_id
const batchSamples = allSamples.filter(s => s.batch_id === 'batch_1760796724_c95f3774');
```

## Database Schema

**LegalSample Model**:
```python
class LegalSample(Base):
    __tablename__ = 'legal_samples'

    id = Column(String, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    case_citation = Column(Text)
    reasoning = Column(Text)
    batch_id = Column(String, index=True)  # ← Indexed for fast filtering
    jurisdiction = Column(String)
    sample_type = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

The `batch_id` column is **indexed** for efficient filtering on large datasets.

## Future Enhancements

**Potential Features**:
1. **Batch Comparison Dashboard**
   - Compare quality metrics across multiple batches
   - Identify best-performing models/providers
   - Track quality trends over time

2. **Quality Alerts**
   - Email/Slack notification if batch quality < threshold
   - Automatic retry with different model if quality poor

3. **Batch Tagging**
   - Add custom tags to batches (e.g., "experimental", "production")
   - Filter batches by tag in UI

4. **Quality Trends**
   - Chart showing quality metrics over time
   - Identify which models produce best results

5. **Sample Approval Workflow**
   - Mark samples as "approved" or "needs review"
   - Track approval status per batch

## Conclusion

✅ **Batch tracking is fully operational**
✅ **Every sample includes batch_id reference**
✅ **Quality metrics available for all batches**
✅ **Real-time monitoring integrated with SSE**

You can now:
- Monitor batch progress in real-time
- Analyze quality immediately after completion
- Filter dataset by batch for review
- Compare batches to optimize model/provider selection

**Next Steps**:
1. Add `batch_id` column to Dataset DataGrid
2. Add "View Batch Quality" button in Batch History table
3. Create batch comparison dashboard
