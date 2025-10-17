#!/usr/bin/env python3
"""
End-to-End Tests for AI Legal Sample Generation

Tests multi-provider generation, batch processing, and data integrity.
"""

import pytest
import requests
import time
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_TIMEOUT = 120  # 2 minutes for generation tests


class TestProviderEndpoints:
    """Test provider and model listing endpoints"""

    def test_get_providers(self):
        """Test /api/providers endpoint returns valid providers"""
        response = requests.get(f"{BASE_URL}/api/providers")
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert 'providers' in data
        assert len(data['providers']) >= 2  # At least Groq and Cerebras

        # Verify each provider has required fields
        for provider in data['providers']:
            assert 'id' in provider
            assert 'name' in provider
            assert 'enabled' in provider
            assert 'default_model' in provider
            assert 'requests_per_minute' in provider
            assert 'tokens_per_minute' in provider

    def test_get_models(self):
        """Test /api/models endpoint returns models from all providers"""
        response = requests.get(f"{BASE_URL}/api/models")
        assert response.status_code == 200

        data = response.json()
        assert data['success'] is True
        assert 'models' in data

        # Group models by provider
        models_by_provider = {}
        for model in data['models']:
            provider = model['provider']
            if provider not in models_by_provider:
                models_by_provider[provider] = []
            models_by_provider[provider].append(model)

        # Should have models from both providers
        assert 'groq' in models_by_provider
        assert 'cerebras' in models_by_provider

        # Verify model structure
        for model in data['models']:
            assert 'id' in model
            assert 'name' in model
            assert 'provider' in model
            assert 'provider_name' in model
            assert 'context_window' in model


class TestSingleGeneration:
    """Test single sample generation with different providers"""

    def test_groq_single_generation(self):
        """Test generating a single sample with Groq"""
        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation of Contracts",
            "difficulty": "intermediate",
            "provider": "groq",
            "model": "llama-3.3-70b-versatile"
        }

        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert 'sample' in data
        assert 'tokens_used' in data
        assert 'elapsed' in data

        # Validate sample structure
        sample = data['sample']
        required_fields = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']
        for field in required_fields:
            assert field in sample, f"Missing field: {field}"

        # Validate metadata
        assert 'created_at' in sample
        assert 'updated_at' in sample
        assert 'provider' in sample
        assert sample['provider'] == 'groq'
        assert 'model' in sample

        # Validate ID format
        assert sample['id'].startswith('groq_')

    def test_cerebras_single_generation(self):
        """Test generating a single sample with Cerebras"""
        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation of Contracts",
            "difficulty": "intermediate",
            "provider": "cerebras",
            "model": "qwen-3-235b-a22b-thinking-2507"
        }

        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert 'sample' in data

        sample = data['sample']
        # Validate provider-specific metadata
        assert sample['provider'] == 'cerebras'
        assert sample['id'].startswith('cerebras_')

        # Cerebras thinking model should generate reasoning
        assert len(sample['reasoning']) > 0

    def test_invalid_provider(self):
        """Test error handling for invalid provider"""
        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation",
            "difficulty": "basic",
            "provider": "invalid_provider"
        }

        response = requests.post(f"{BASE_URL}/api/generate", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        assert 'invalid_provider' in data['error'].lower()


class TestBatchGeneration:
    """Test batch generation with multiple providers"""

    def test_start_batch_groq(self):
        """Test starting a batch with Groq"""
        # Get current count
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        payload = {
            "target_count": current_count + 5,  # Generate 5 samples
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "difficulty": "intermediate"
        }

        response = requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert 'message' in data
        assert data['provider'] == 'groq'
        assert data['model'] == 'llama-3.3-70b-versatile'

    def test_start_batch_cerebras(self):
        """Test starting a batch with Cerebras"""
        # First stop any running batch
        requests.post(f"{BASE_URL}/api/generate/batch/stop")
        time.sleep(2)

        # Get current count
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        payload = {
            "target_count": current_count + 3,  # Generate 3 samples
            "provider": "cerebras",
            "model": "qwen-3-235b-a22b-thinking-2507"
        }

        response = requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert data['provider'] == 'cerebras'

    def test_batch_status_tracking(self):
        """Test batch status polling during generation"""
        # Stop any running batch first
        requests.post(f"{BASE_URL}/api/generate/batch/stop")
        time.sleep(2)

        # Start a small batch
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        start_response = requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json={
                "target_count": current_count + 2,
                "provider": "groq"
            }
        )

        assert start_response.status_code == 200

        # Poll status
        max_polls = 60  # 60 * 5 = 5 minutes max
        poll_count = 0
        batch_completed = False

        while poll_count < max_polls:
            status_response = requests.get(f"{BASE_URL}/api/generate/batch/status")
            status = status_response.json()

            # Validate status structure
            assert 'running' in status
            assert 'progress' in status
            assert 'total' in status
            assert 'samples_generated' in status
            assert 'current_provider' in status

            # Check if completed
            if not status['running'] and status['samples_generated'] > 0:
                batch_completed = True
                assert status['completed_at'] is not None
                break

            time.sleep(5)
            poll_count += 1

        assert batch_completed, "Batch did not complete within timeout"

    def test_batch_stop(self):
        """Test stopping a running batch"""
        # Start a large batch
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json={
                "target_count": current_count + 100,  # Large batch
                "provider": "groq"
            }
        )

        time.sleep(3)  # Let it start

        # Stop it
        stop_response = requests.post(f"{BASE_URL}/api/generate/batch/stop")
        assert stop_response.status_code == 200

        data = stop_response.json()
        assert data['success'] is True

        # Verify it stopped
        time.sleep(2)
        status_response = requests.get(f"{BASE_URL}/api/generate/batch/status")
        status = status_response.json()
        assert status['running'] is False

    def test_batch_history(self):
        """Test batch history tracking"""
        response = requests.get(f"{BASE_URL}/api/generate/batch/history")

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert 'batches' in data
        assert 'count' in data

        # Verify batch structure
        if len(data['batches']) > 0:
            batch = data['batches'][0]
            assert 'id' in batch
            assert 'started_at' in batch
            assert 'status' in batch
            assert batch['status'] in ['running', 'completed', 'stopped']
            assert 'samples_generated' in batch
            assert 'model' in batch


class TestDataIntegrity:
    """Test data integrity and validation"""

    def test_unique_ids_per_provider(self):
        """Test that generated IDs are unique per provider"""
        response = requests.get(f"{BASE_URL}/api/data")
        samples = response.json()

        # Group by provider
        ids_by_provider = {'groq': set(), 'cerebras': set()}

        for sample in samples:
            if 'provider' in sample:
                provider = sample['provider']
                sample_id = sample['id']

                # Check ID prefix matches provider
                if provider in ids_by_provider:
                    assert sample_id.startswith(f"{provider}_"), \
                        f"ID {sample_id} doesn't match provider {provider}"

                    # Check uniqueness
                    assert sample_id not in ids_by_provider[provider], \
                        f"Duplicate ID found: {sample_id}"

                    ids_by_provider[provider].add(sample_id)

    def test_required_fields_present(self):
        """Test that all samples have required fields"""
        response = requests.get(f"{BASE_URL}/api/data")
        samples = response.json()

        required_fields = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']

        for sample in samples:
            for field in required_fields:
                assert field in sample, f"Sample {sample.get('id', 'unknown')} missing field: {field}"
                assert sample[field], f"Sample {sample.get('id', 'unknown')} has empty {field}"

    def test_metadata_tracking(self):
        """Test that metadata fields are properly tracked"""
        # Generate one sample to ensure we have fresh metadata
        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation",
            "difficulty": "basic",
            "provider": "groq"
        }

        gen_response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        assert gen_response.status_code == 200
        sample = gen_response.json()['sample']

        # Verify metadata
        assert 'created_at' in sample
        assert 'updated_at' in sample
        assert 'provider' in sample
        assert 'model' in sample

        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(sample['created_at'])
        datetime.fromisoformat(sample['updated_at'])

    def test_batch_id_tracking(self):
        """Test that batch_id is tracked in samples"""
        # Stop any running batch
        requests.post(f"{BASE_URL}/api/generate/batch/stop")
        time.sleep(2)

        # Start a small batch
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        start_response = requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json={
                "target_count": current_count + 1,
                "provider": "groq"
            }
        )

        batch_id = None

        # Wait for batch to complete and get batch_id
        for _ in range(60):
            status = requests.get(f"{BASE_URL}/api/generate/batch/status").json()
            if status.get('batch_id'):
                batch_id = status['batch_id']
            if not status['running']:
                break
            time.sleep(5)

        assert batch_id is not None, "No batch_id found"

        # Check if samples have the batch_id
        samples_response = requests.get(f"{BASE_URL}/api/batch/{batch_id}/samples")

        if samples_response.status_code == 200:
            data = samples_response.json()
            assert data['success'] is True
            assert data['batch_id'] == batch_id
            assert len(data['samples']) > 0


class TestProviderComparison:
    """Compare output quality between providers"""

    def test_cerebras_thinking_quality(self):
        """Test that Cerebras thinking model produces detailed reasoning"""
        payload = {
            "practice_area": "Contract Law",
            "topic": "Misrepresentation",
            "difficulty": "advanced",
            "provider": "cerebras",
            "model": "qwen-3-235b-a22b-thinking-2507"
        }

        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        sample = response.json()['sample']

        # Thinking model should produce longer, more detailed reasoning
        assert len(sample['reasoning']) > 100, "Reasoning too short for thinking model"

        # Should have multiple reasoning steps
        assert 'Step' in sample['reasoning'] or 'step' in sample['reasoning'].lower()

    def test_groq_response_time(self):
        """Test that Groq responds within reasonable time"""
        start_time = time.time()

        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation",
            "difficulty": "basic",
            "provider": "groq"
        }

        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 30, f"Groq generation took too long: {elapsed}s"

    def test_cerebras_response_time(self):
        """Test that Cerebras responds within reasonable time"""
        start_time = time.time()

        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation",
            "difficulty": "basic",
            "provider": "cerebras",
            "model": "llama-3.3-70b"  # Use faster model
        }

        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        elapsed = time.time() - start_time

        assert response.status_code == 200
        # Cerebras should be fast
        assert elapsed < 20, f"Cerebras generation took too long: {elapsed}s"


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_difficulty(self):
        """Test handling of invalid difficulty level"""
        payload = {
            "practice_area": "Contract Law",
            "topic": "Formation",
            "difficulty": "invalid_difficulty",
            "provider": "groq"
        }

        # Should still work but use the invalid difficulty in the prompt
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=TEST_TIMEOUT
        )

        # API should handle gracefully
        assert response.status_code in [200, 400]

    def test_batch_already_running(self):
        """Test starting a batch when one is already running"""
        # Stop any running batch first
        requests.post(f"{BASE_URL}/api/generate/batch/stop")
        time.sleep(2)

        # Start first batch
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json={"target_count": current_count + 10, "provider": "groq"}
        )

        time.sleep(2)

        # Try to start another
        response = requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json={"target_count": current_count + 20, "provider": "cerebras"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'already running' in data['error'].lower()

        # Clean up
        requests.post(f"{BASE_URL}/api/generate/batch/stop")

    def test_target_count_validation(self):
        """Test validation of target count"""
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        current_count = stats_response.json()['total']

        # Try to set target lower than current count
        response = requests.post(
            f"{BASE_URL}/api/generate/batch/start",
            json={
                "target_count": current_count - 10,
                "provider": "groq"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'greater than current' in data['error'].lower()


# Test fixtures
@pytest.fixture(scope="module", autouse=True)
def check_server_running():
    """Ensure the server is running before tests"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            pytest.fail("API server is not healthy")
    except requests.exceptions.RequestException:
        pytest.fail("API server is not running. Please start it with: cd legal-dashboard && python3 api_server.py")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
