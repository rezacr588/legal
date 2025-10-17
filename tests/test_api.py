#!/usr/bin/env python3
"""
Comprehensive API Test Suite for UK Legal Dataset API
Tests all endpoints with various scenarios, edge cases, and error handling
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional

BASE_URL = "http://127.0.0.1:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

class TestStats:
    """Track test statistics"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0
        self.results: List[Dict] = []

    def add_result(self, name: str, success: bool, details: Optional[Dict] = None):
        self.total += 1
        if success:
            self.passed += 1
        else:
            self.failed += 1

        self.results.append({
            'name': name,
            'success': success,
            'details': details or {}
        })

    def print_summary(self):
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}Test Summary{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"\nTotal Tests: {self.total}")
        print(f"{Colors.GREEN}✓ Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}✗ Failed: {self.failed}{Colors.END}")
        print(f"Success Rate: {(self.passed/self.total)*100:.1f}%\n")

        if self.failed > 0:
            print(f"{Colors.RED}Failed Tests:{Colors.END}")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['name']}")
                    if result['details'].get('error'):
                        print(f"    Error: {result['details']['error']}")

stats = TestStats()

def test_endpoint(
    name: str,
    method: str,
    url: str,
    expected_status: int = 200,
    expected_fields: Optional[List[str]] = None,
    timeout: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Test a single API endpoint with comprehensive validation

    Args:
        name: Test name
        method: HTTP method (GET/POST)
        url: Full endpoint URL
        expected_status: Expected HTTP status code
        expected_fields: List of fields expected in JSON response
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for requests
    """
    try:
        print(f"\n{Colors.CYAN}Testing:{Colors.END} {name}")
        print(f"  {method} {url}")

        start_time = time.time()

        if method == 'GET':
            response = requests.get(url, timeout=timeout, **kwargs)
        elif method == 'POST':
            response = requests.post(url, timeout=timeout, **kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        elapsed = time.time() - start_time

        result = {
            'status_code': response.status_code,
            'success': response.status_code == expected_status,
            'elapsed': elapsed,
            'data': None,
            'error': None
        }

        # Parse JSON response
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                result['data'] = response.json()
            except json.JSONDecodeError:
                result['success'] = False
                result['error'] = 'Invalid JSON response'

        # Validate expected fields
        if result['success'] and expected_fields and result['data']:
            if isinstance(result['data'], dict):
                missing_fields = [f for f in expected_fields if f not in result['data']]
                if missing_fields:
                    result['success'] = False
                    result['error'] = f"Missing fields: {missing_fields}"

        # Print result
        if result['success']:
            print(f"  {Colors.GREEN}✓ PASSED{Colors.END} (Status: {response.status_code}, Time: {elapsed:.2f}s)")
        else:
            print(f"  {Colors.RED}✗ FAILED{Colors.END} (Status: {response.status_code})")
            if result['error']:
                print(f"    Error: {result['error']}")
            elif result['data']:
                print(f"    Response: {result['data']}")

        stats.add_result(name, result['success'], result)
        return result

    except requests.exceptions.Timeout:
        print(f"  {Colors.RED}✗ TIMEOUT{Colors.END}")
        stats.add_result(name, False, {'error': 'Timeout'})
        return {'success': False, 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        print(f"  {Colors.RED}✗ CONNECTION ERROR{Colors.END}")
        stats.add_result(name, False, {'error': 'Connection error - is server running?'})
        return {'success': False, 'error': 'Connection error'}
    except Exception as e:
        print(f"  {Colors.RED}✗ ERROR{Colors.END}: {str(e)}")
        stats.add_result(name, False, {'error': str(e)})
        return {'success': False, 'error': str(e)}


def run_health_tests():
    """Test health check endpoint"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}1. Health Check Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    test_endpoint(
        "Health Check",
        "GET",
        f"{BASE_URL}/api/health",
        expected_fields=['status', 'dataset_exists', 'groq_configured', 'batch_generation_running']
    )


def run_data_tests():
    """Test data retrieval endpoints"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}2. Data Retrieval Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Get all data
    result = test_endpoint(
        "Get All Data",
        "GET",
        f"{BASE_URL}/api/data"
    )

    # Validate data structure
    if result.get('success') and result.get('data'):
        data = result['data']
        if isinstance(data, list) and len(data) > 0:
            sample = data[0]
            required_fields = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']
            missing = [f for f in required_fields if f not in sample]
            if missing:
                print(f"  {Colors.YELLOW}⚠ Warning: Sample missing fields: {missing}{Colors.END}")
            else:
                print(f"  {Colors.GREEN}✓ Data structure valid{Colors.END}")


def run_stats_tests():
    """Test statistics endpoints"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}3. Statistics Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Basic stats
    result = test_endpoint(
        "Get Basic Stats",
        "GET",
        f"{BASE_URL}/api/stats",
        expected_fields=['total', 'columns', 'difficulty_distribution', 'top_topics', 'file_size_kb']
    )

    # Display stats
    if result.get('success') and result.get('data'):
        data = result['data']
        print(f"  {Colors.YELLOW}→ Total Samples: {data.get('total', 'N/A')}{Colors.END}")
        print(f"  {Colors.YELLOW}→ File Size: {data.get('file_size_kb', 0):.2f} KB{Colors.END}")

    # Detailed stats
    result = test_endpoint(
        "Get Detailed Stats",
        "GET",
        f"{BASE_URL}/api/stats/detailed",
        expected_fields=['success', 'stats']
    )

    # Display detailed stats
    if result.get('success') and result.get('data') and result['data'].get('success'):
        stats_data = result['data']['stats']
        print(f"  {Colors.YELLOW}→ Unique Topics: {stats_data.get('unique_topics', 'N/A')}{Colors.END}")
        print(f"  {Colors.YELLOW}→ Unique Practice Areas: {stats_data.get('unique_practice_areas', 'N/A')}{Colors.END}")
        if 'avg_lengths' in stats_data:
            avg = stats_data['avg_lengths']
            print(f"  {Colors.YELLOW}→ Avg Question: {avg.get('question', 0):.0f} bytes{Colors.END}")
            print(f"  {Colors.YELLOW}→ Avg Answer: {avg.get('answer', 0):.0f} bytes{Colors.END}")


def run_topics_tests():
    """Test topics endpoint"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}4. Topics Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    result = test_endpoint(
        "Get Available Topics",
        "GET",
        f"{BASE_URL}/api/topics",
        expected_fields=['topics']
    )

    if result.get('success') and result.get('data'):
        topics = result['data'].get('topics', [])
        print(f"  {Colors.YELLOW}→ Total Topics: {len(topics)}{Colors.END}")
        if topics and len(topics) > 0:
            print(f"  {Colors.GREEN}✓ Topics structure valid{Colors.END}")


def run_models_tests():
    """Test models endpoint"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}5. Models Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    result = test_endpoint(
        "Get Available Models",
        "GET",
        f"{BASE_URL}/api/models",
        expected_fields=['success', 'default_model']
    )

    if result.get('success') and result.get('data'):
        data = result['data']
        if data.get('success'):
            models = data.get('models', [])
            print(f"  {Colors.YELLOW}→ Available Models: {len(models)}{Colors.END}")
            print(f"  {Colors.YELLOW}→ Default Model: {data.get('default_model', 'N/A')}{Colors.END}")


def run_search_tests():
    """Test search endpoints"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}6. Search Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Basic search
    result = test_endpoint(
        "Search - Basic Query",
        "GET",
        f"{BASE_URL}/api/search?q=contract&limit=5",
        expected_fields=['success', 'results', 'count', 'query', 'field']
    )

    if result.get('success') and result.get('data'):
        count = result['data'].get('count', 0)
        print(f"  {Colors.YELLOW}→ Results Found: {count}{Colors.END}")

    # Search by field
    test_endpoint(
        "Search - By Topic Field",
        "GET",
        f"{BASE_URL}/api/search?q=Contract&field=topic&limit=3",
        expected_fields=['success', 'results', 'count']
    )

    # Search by question field
    test_endpoint(
        "Search - By Question Field",
        "GET",
        f"{BASE_URL}/api/search?q=law&field=question&limit=5",
        expected_fields=['success', 'results', 'count']
    )

    # Search by answer field
    test_endpoint(
        "Search - By Answer Field",
        "GET",
        f"{BASE_URL}/api/search?q=breach&field=answer&limit=5",
        expected_fields=['success', 'results', 'count']
    )

    # Search with invalid field (should fail)
    test_endpoint(
        "Search - Invalid Field (Expected Failure)",
        "GET",
        f"{BASE_URL}/api/search?q=test&field=invalid_field",
        expected_status=400,
        expected_fields=['success', 'error']
    )

    # Search without query (should fail)
    test_endpoint(
        "Search - Missing Query (Expected Failure)",
        "GET",
        f"{BASE_URL}/api/search",
        expected_status=400,
        expected_fields=['success', 'error']
    )


def run_random_samples_tests():
    """Test random samples endpoint"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}7. Random Samples Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Get random samples (default)
    test_endpoint(
        "Random Samples - Default Count",
        "GET",
        f"{BASE_URL}/api/samples/random",
        expected_fields=['success', 'samples', 'count']
    )

    # Get specific count
    test_endpoint(
        "Random Samples - Count 3",
        "GET",
        f"{BASE_URL}/api/samples/random?count=3",
        expected_fields=['success', 'samples', 'count']
    )

    # Get by difficulty
    for difficulty in ['basic', 'intermediate', 'advanced', 'expert']:
        test_endpoint(
            f"Random Samples - {difficulty.capitalize()}",
            "GET",
            f"{BASE_URL}/api/samples/random?count=2&difficulty={difficulty}",
            expected_fields=['success', 'samples', 'count']
        )


def run_batch_generation_tests():
    """Test batch generation endpoints"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}8. Batch Generation Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Check status
    test_endpoint(
        "Batch Generation - Check Status",
        "GET",
        f"{BASE_URL}/api/generate/batch/status",
        expected_fields=['running', 'progress', 'total']
    )

    # Try to stop when not running (should return error)
    result = test_endpoint(
        "Batch Generation - Stop When Not Running",
        "POST",
        f"{BASE_URL}/api/generate/batch/stop",
        expected_status=400,
        expected_fields=['success', 'error']
    )


def run_add_sample_tests():
    """Test add sample endpoint"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}9. Add Sample Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Test with missing fields (should fail)
    test_endpoint(
        "Add Sample - Missing Fields (Expected Failure)",
        "POST",
        f"{BASE_URL}/api/add",
        expected_status=400,
        expected_fields=['success', 'error'],
        json={
            "id": "test_incomplete",
            "question": "Test question?"
        }
    )

    # Test with valid sample (may fail if ID exists)
    unique_id = f"test_api_{int(time.time())}"
    result = test_endpoint(
        "Add Sample - Valid Sample",
        "POST",
        f"{BASE_URL}/api/add",
        json={
            "id": unique_id,
            "question": "What is the test case for API validation?",
            "answer": "This is a test answer for API validation purposes.",
            "topic": "Test - API Validation",
            "difficulty": "basic",
            "case_citation": "Test v API [2025] TEST 001",
            "reasoning": "Step 1: This is a test. Step 2: Validate the API."
        }
    )

    if result.get('success'):
        print(f"  {Colors.GREEN}✓ Sample added successfully{Colors.END}")

    # Test duplicate ID (should fail)
    test_endpoint(
        "Add Sample - Duplicate ID (Expected Failure)",
        "POST",
        f"{BASE_URL}/api/add",
        expected_status=400,
        expected_fields=['success', 'error'],
        json={
            "id": unique_id,  # Same ID as above
            "question": "Duplicate test?",
            "answer": "This should fail.",
            "topic": "Test - Duplicate",
            "difficulty": "basic",
            "case_citation": "Test [2025]",
            "reasoning": "Step 1: Duplicate test."
        }
    )


def run_generate_sample_tests():
    """Test single sample generation endpoint (read-only test)"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}10. Generate Sample Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    print(f"\n{Colors.YELLOW}Note: Skipping actual generation tests to avoid API rate limits.{Colors.END}")
    print(f"{Colors.YELLOW}These tests would generate real samples and consume API quota.{Colors.END}")

    # We could add these if needed:
    # test_endpoint(
    #     "Generate Single Sample",
    #     "POST",
    #     f"{BASE_URL}/api/generate",
    #     timeout=30,
    #     json={
    #         "practice_area": "Contract Law",
    #         "topic": "Formation of Contracts",
    #         "difficulty": "basic"
    #     }
    # )


def run_import_jsonl_tests():
    """Test JSONL import endpoint"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}11. Import JSONL Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Test with empty content (should fail)
    test_endpoint(
        "Import JSONL - Empty Content (Expected Failure)",
        "POST",
        f"{BASE_URL}/api/import/jsonl",
        expected_status=400,
        expected_fields=['success', 'error'],
        json={"content": ""}
    )

    # Test with invalid JSON line (should fail)
    test_endpoint(
        "Import JSONL - Invalid JSON (Expected Failure)",
        "POST",
        f"{BASE_URL}/api/import/jsonl",
        expected_status=400,
        expected_fields=['success', 'error'],
        json={"content": "not valid json\n{incomplete"}
    )

    # Test with missing required fields (should fail)
    incomplete_jsonl = json.dumps({
        "id": "test_incomplete_import",
        "question": "Test question?"
    })
    test_endpoint(
        "Import JSONL - Missing Fields (Expected Failure)",
        "POST",
        f"{BASE_URL}/api/import/jsonl",
        expected_status=400,
        expected_fields=['success', 'error'],
        json={"content": incomplete_jsonl}
    )

    # Test with valid samples
    unique_id1 = f"test_import_1_{int(time.time())}"
    unique_id2 = f"test_import_2_{int(time.time())}"

    sample1 = {
        "id": unique_id1,
        "question": "What is the first test case for JSONL import?",
        "answer": "This is the first test answer for JSONL import validation.",
        "topic": "Test - JSONL Import",
        "difficulty": "basic",
        "case_citation": "Import v Test [2025] JSONL 001",
        "reasoning": "Step 1: Test JSONL import. Step 2: Validate multiple samples."
    }

    sample2 = {
        "id": unique_id2,
        "question": "What is the second test case for JSONL import?",
        "answer": "This is the second test answer for JSONL import validation.",
        "topic": "Test - JSONL Import",
        "difficulty": "intermediate",
        "case_citation": "Import v Test [2025] JSONL 002",
        "reasoning": "Step 1: Test batch import. Step 2: Ensure data integrity."
    }

    valid_jsonl = "\n".join([json.dumps(sample1), json.dumps(sample2)])

    result = test_endpoint(
        "Import JSONL - Valid Samples",
        "POST",
        f"{BASE_URL}/api/import/jsonl",
        expected_fields=['success', 'message', 'total_samples'],
        json={"content": valid_jsonl}
    )

    if result.get('success') and result.get('data'):
        data = result['data']
        if data.get('success'):
            print(f"  {Colors.GREEN}✓ Imported successfully{Colors.END}")
            print(f"  {Colors.YELLOW}→ Total samples in dataset: {data.get('total_samples', 'N/A')}{Colors.END}")

    # Test duplicate IDs (should fail)
    duplicate_jsonl = json.dumps(sample1)  # Reuse same sample
    test_endpoint(
        "Import JSONL - Duplicate IDs (Expected Failure)",
        "POST",
        f"{BASE_URL}/api/import/jsonl",
        expected_status=400,
        expected_fields=['success', 'error'],
        json={"content": duplicate_jsonl}
    )

    # Test with empty lines (should handle gracefully)
    jsonl_with_empty_lines = f"\n{json.dumps(sample1)}\n\n\n"
    test_endpoint(
        "Import JSONL - With Empty Lines (Expected Failure - duplicate)",
        "POST",
        f"{BASE_URL}/api/import/jsonl",
        expected_status=400,
        json={"content": jsonl_with_empty_lines}
    )


def run_edge_case_tests():
    """Test edge cases and error handling"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}12. Edge Cases & Error Handling{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    # Non-existent endpoint
    test_endpoint(
        "Non-existent Endpoint (Expected 404)",
        "GET",
        f"{BASE_URL}/api/nonexistent",
        expected_status=404
    )

    # Invalid JSON in POST
    try:
        response = requests.post(
            f"{BASE_URL}/api/add",
            data="invalid json",
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        success = response.status_code in [400, 500]
        print(f"\n{Colors.CYAN}Testing:{Colors.END} Invalid JSON POST")
        if success:
            print(f"  {Colors.GREEN}✓ PASSED{Colors.END} - Properly rejected invalid JSON")
        else:
            print(f"  {Colors.RED}✗ FAILED{Colors.END} - Did not reject invalid JSON")
        stats.add_result("Invalid JSON POST", success)
    except Exception as e:
        print(f"  {Colors.RED}✗ ERROR{Colors.END}: {str(e)}")
        stats.add_result("Invalid JSON POST", False)

    # Large limit in search
    test_endpoint(
        "Search - Large Limit",
        "GET",
        f"{BASE_URL}/api/search?q=law&limit=10000",
        expected_fields=['success', 'results']
    )

    # Zero count in random samples
    test_endpoint(
        "Random Samples - Zero Count",
        "GET",
        f"{BASE_URL}/api/samples/random?count=0",
        expected_fields=['success', 'samples']
    )

    # Negative count
    test_endpoint(
        "Random Samples - Negative Count",
        "GET",
        f"{BASE_URL}/api/samples/random?count=-5",
        expected_fields=['success', 'samples']
    )


def run_performance_tests():
    """Test API performance"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}13. Performance Tests{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

    endpoints = [
        ("Health Check", "GET", f"{BASE_URL}/api/health"),
        ("Stats", "GET", f"{BASE_URL}/api/stats"),
        ("Random Samples", "GET", f"{BASE_URL}/api/samples/random?count=1"),
    ]

    for name, method, url in endpoints:
        times = []
        for i in range(3):
            start = time.time()
            try:
                requests.get(url, timeout=5) if method == "GET" else requests.post(url, timeout=5)
                times.append(time.time() - start)
            except:
                times.append(None)

        valid_times = [t for t in times if t is not None]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            print(f"\n{Colors.CYAN}{name}:{Colors.END}")
            print(f"  Average Response Time: {avg_time*1000:.2f}ms")
            if avg_time < 0.1:
                print(f"  {Colors.GREEN}✓ Excellent performance{Colors.END}")
            elif avg_time < 0.5:
                print(f"  {Colors.YELLOW}⚠ Good performance{Colors.END}")
            else:
                print(f"  {Colors.RED}⚠ Slow performance{Colors.END}")


def print_dataset_summary(base_url: str):
    """Print a summary of the dataset"""
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\n{Colors.YELLOW}{Colors.BOLD}Dataset Summary:{Colors.END}")
            print(f"  Total Samples: {data.get('total', 'N/A')}")
            print(f"  File Size: {data.get('file_size_kb', 0):.2f} KB")

            # Difficulty distribution
            diff_dist = data.get('difficulty_distribution', [])
            if diff_dist:
                print(f"\n  Difficulty Distribution:")
                for item in sorted(diff_dist, key=lambda x: x.get('count', 0), reverse=True):
                    print(f"    - {item.get('difficulty', 'N/A')}: {item.get('count', 0)}")

            # Top topics
            top_topics = data.get('top_topics', [])
            if top_topics:
                print(f"\n  Top 5 Topics:")
                for item in top_topics[:5]:
                    print(f"    - {item.get('topic', 'N/A')}: {item.get('count', 0)}")
    except:
        pass


def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}UK Legal Dataset API - Comprehensive Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}Base URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.CYAN}Starting tests...{Colors.END}")

    try:
        # Run all test suites
        run_health_tests()
        run_data_tests()
        run_stats_tests()
        run_topics_tests()
        run_models_tests()
        run_search_tests()
        run_random_samples_tests()
        run_batch_generation_tests()
        run_add_sample_tests()
        run_generate_sample_tests()
        run_import_jsonl_tests()
        run_edge_case_tests()
        run_performance_tests()

        # Print dataset summary
        print_dataset_summary(BASE_URL)

        # Print final summary
        stats.print_summary()

        # Exit with appropriate code
        exit(0 if stats.failed == 0 else 1)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.END}\n")
        stats.print_summary()
        exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {e}{Colors.END}\n")
        exit(1)


if __name__ == '__main__':
    main()
