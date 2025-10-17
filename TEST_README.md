# API Test Suite

Comprehensive test suite for the UK Legal Dataset API Server.

## Overview

The test suite (`test_api.py`) validates all API endpoints with various scenarios including:
- Normal operations
- Edge cases
- Error handling
- Performance metrics
- Data validation

## Prerequisites

```bash
# Install required packages
pip install requests

# Ensure the API server is running
cd legal-dashboard
python3 api_server.py
```

## Running Tests

### Full Test Suite

```bash
# From the root directory
python3 test_api.py
```

### Expected Output

The test suite runs **40+ tests** across 13 categories:

1. **Health Check Tests** - Verify API is operational
2. **Data Retrieval Tests** - Test data fetching and structure validation
3. **Statistics Tests** - Basic and detailed statistics endpoints
4. **Topics Tests** - Available legal topics for generation
5. **Models Tests** - Groq model availability and configuration
6. **Search Tests** - Full-text search across all fields
7. **Random Samples Tests** - Random sample retrieval with filters
8. **Batch Generation Tests** - Batch generation status and control
9. **Add Sample Tests** - Manual sample addition with validation
10. **Generate Sample Tests** - Single sample generation (skipped by default)
11. **Import JSONL Tests** - Bulk import from JSONL format
12. **Edge Cases & Error Handling** - Invalid inputs and boundary conditions
13. **Performance Tests** - Response time benchmarks

## Test Results

Each test shows:
- ✓ **PASSED** - Test successful (green)
- ✗ **FAILED** - Test failed (red)
- Status code and response time
- Detailed error messages for failures

Example output:
```
======================================================================
1. Health Check Tests
======================================================================

Testing: Health Check
  GET http://127.0.0.1:5000/api/health
  ✓ PASSED (Status: 200, Time: 0.02s)

======================================================================
Test Summary
======================================================================

Total Tests: 42
✓ Passed: 40
✗ Failed: 2
Success Rate: 95.2%
```

## Test Categories Detail

### 1. Health Check
- Validates API is running
- Checks dataset exists
- Verifies Groq API configured
- Shows batch generation status

### 2. Data Retrieval
- Fetches all samples
- Validates required fields: `id`, `question`, `answer`, `topic`, `difficulty`, `case_citation`, `reasoning`
- Checks data structure integrity

### 3. Statistics
- **Basic Stats**: Total samples, columns, difficulty distribution, top topics
- **Detailed Stats**: Unique topics, practice areas, average field lengths

### 4. Search
- Search across all fields
- Field-specific search (question, answer, topic, case_citation)
- Invalid field handling
- Missing query parameter validation

### 5. Random Samples
- Default count (5 samples)
- Custom counts
- Filter by difficulty (basic, intermediate, advanced, expert)
- Edge cases (zero, negative counts)

### 6. Batch Generation
- Status checking
- Stop command (may fail if not running)
- Progress tracking

### 7. Add Sample
- Valid sample addition with unique ID
- Missing fields validation
- Duplicate ID detection
- All required fields enforcement

### 8. Import JSONL
- Bulk import from JSONL format
- Empty content validation
- Invalid JSON detection
- Missing fields validation
- Duplicate ID prevention
- Empty line handling

### 9. Edge Cases
- Non-existent endpoints (404 errors)
- Invalid JSON payloads
- Large limits in queries
- Zero/negative counts
- Malformed requests

### 10. Performance
- Health check response time
- Stats endpoint performance
- Random samples latency
- Performance benchmarks:
  - **Excellent**: < 100ms
  - **Good**: 100-500ms
  - **Slow**: > 500ms

## API Endpoints Tested

| Endpoint | Method | Purpose | Tests |
|----------|--------|---------|-------|
| `/api/health` | GET | Health check | 1 |
| `/api/data` | GET | Get all samples | 1 |
| `/api/stats` | GET | Basic statistics | 1 |
| `/api/stats/detailed` | GET | Detailed statistics | 1 |
| `/api/topics` | GET | Available topics | 1 |
| `/api/models` | GET | Available Groq models | 1 |
| `/api/search` | GET | Search samples | 6 |
| `/api/samples/random` | GET | Random samples | 7 |
| `/api/generate/batch/status` | GET | Batch status | 1 |
| `/api/generate/batch/stop` | POST | Stop batch | 1 |
| `/api/add` | POST | Add single sample | 3 |
| `/api/import/jsonl` | POST | Import JSONL | 6 |
| **Non-existent** | GET | 404 handling | 1 |

**Total: 31+ individual endpoint tests**

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed
- `130` - Tests interrupted by user (Ctrl+C)

## Customization

### Change Base URL

Edit the `BASE_URL` constant in `test_api.py`:
```python
BASE_URL = "http://localhost:5000"  # Default
# BASE_URL = "http://your-server:8080"  # Custom
```

### Skip Specific Tests

Comment out test functions in the `main()` function:
```python
# run_performance_tests()  # Skip performance tests
```

### Add Custom Tests

Add new test functions following the pattern:
```python
def run_my_custom_tests():
    """Test custom functionality"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}14. My Custom Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    test_endpoint(
        "My Custom Test",
        "GET",
        f"{BASE_URL}/api/my-endpoint",
        expected_fields=['field1', 'field2']
    )
```

Then add to `main()`:
```python
run_my_custom_tests()
```

## Troubleshooting

### Connection Error
```
✗ CONNECTION ERROR
Error: Connection error - is server running?
```

**Solution**: Start the API server first:
```bash
cd legal-dashboard
python3 api_server.py
```

### Port Already in Use
If server won't start:
```bash
lsof -ti:5000 | xargs kill -9
```

### Test Failures

Common causes:
1. **Empty dataset** - Add samples first
2. **Missing required fields** - Check data structure
3. **Duplicate IDs** - Tests may fail if previous test samples exist
4. **API rate limits** - Generation tests skipped to avoid quota

### Timeout Errors

Increase timeout in test function:
```python
test_endpoint(
    "My Test",
    "GET",
    url,
    timeout=30  # Increase from default 10s
)
```

## Test Data Cleanup

Some tests add samples to the dataset. To remove test samples:

```python
import polars as pl

# Load dataset
df = pl.read_parquet("train.parquet")

# Remove test samples
df_cleaned = df.filter(~pl.col("id").str.starts_with("test_"))

# Save
df_cleaned.write_parquet("train.parquet", compression="zstd")
```

## Continuous Integration

To integrate with CI/CD:

```yaml
# .github/workflows/test.yml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start API server
        run: cd legal-dashboard && python3 api_server.py &
      - name: Wait for API
        run: sleep 5
      - name: Run tests
        run: python3 test_api.py
```

## Performance Benchmarks

Expected performance on modern hardware:

| Endpoint | Expected Time |
|----------|--------------|
| Health Check | < 50ms |
| Basic Stats | < 100ms |
| Detailed Stats | < 200ms |
| Random Samples (5) | < 150ms |
| Search (small dataset) | < 100ms |
| Add Sample | < 200ms |
| Import JSONL (10 samples) | < 300ms |

## Coverage

The test suite covers:
- ✅ All GET endpoints
- ✅ All POST endpoints
- ✅ Required field validation
- ✅ Duplicate detection
- ✅ Error responses (400, 404, 500)
- ✅ Success responses (200)
- ✅ JSON structure validation
- ✅ Edge cases and boundary conditions
- ✅ Performance characteristics
- ⚠️ Batch generation (status only, no actual generation to save quota)

## Future Enhancements

Potential additions:
- [ ] Load testing with concurrent requests
- [ ] Integration tests with sample generation
- [ ] Database consistency checks
- [ ] Memory usage profiling
- [ ] Mock Groq API for generation tests
- [ ] Automated regression testing
- [ ] Test data fixtures
- [ ] Coverage reporting

## Support

For issues or questions:
1. Check server logs: `tail -f /tmp/flask.log`
2. Verify dataset exists: `ls -lh train.parquet`
3. Test API manually: `curl http://localhost:5000/api/health`
4. Review [API_USAGE.md](API_USAGE.md) for endpoint documentation

## License

Part of the UK Legal Training Dataset project.
