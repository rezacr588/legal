#!/usr/bin/env python3
"""
Test script for new sample type functionality.
Tests educational, client_interaction, and statutory_interpretation types.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.generation_service import GenerationService
from config import SAMPLE_TYPES

def test_sample_type(sample_type: str, difficulty: str = "intermediate"):
    """Test a specific sample type"""
    print(f"\n{'='*80}")
    print(f"Testing Sample Type: {sample_type.upper()}")
    print(f"Difficulty: {difficulty}")
    print('='*80)

    # Get sample type config
    config = SAMPLE_TYPES.get(sample_type, SAMPLE_TYPES['case_analysis'])
    print(f"\nSample Type Name: {config['name']}")
    print(f"Description: {config['description']}")
    print(f"Focus: {config['focus']}")
    print(f"Example: {config['example']}")

    service = GenerationService()

    try:
        sample, tokens_used, elapsed, error = service.generate_single_sample(
            practice_area="Contract Law",
            topic="Formation of Contracts",
            difficulty=difficulty,
            counter=1,
            provider="cerebras",
            model="gpt-oss-120b",  # Use the champion model
            sample_type=sample_type  # NEW PARAMETER
        )

        if error or not sample:
            print(f"\n❌ GENERATION FAILED")
            print(f"Error: {error}")
            return None

        # Print results
        print(f"\n✅ GENERATION SUCCESSFUL")
        print(f"\n📊 METRICS:")
        print(f"  • Tokens Used: {tokens_used}")
        print(f"  • Generation Time: {elapsed:.2f}s")
        print(f"  • Word Count: {len(sample.get('answer', '').split())}")

        print(f"\n❓ QUESTION:")
        print(f"{sample.get('question', 'N/A')}")

        print(f"\n📄 ANSWER (first 500 chars):")
        answer = sample.get('answer', 'N/A')
        print(f"{answer[:500]}...")

        print(f"\n🧠 REASONING (first 300 chars):")
        reasoning = sample.get('reasoning', 'N/A')
        print(f"{reasoning[:300]}...")

        print(f"\n📚 CITATIONS:")
        print(f"{sample.get('case_citation', 'N/A')}")

        return sample

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 SAMPLE TYPES TESTING")
    print("Testing new sample type functionality")
    print("="*80)

    # Test all sample types
    sample_types = [
        'case_analysis',
        'educational',
        'client_interaction',
        'statutory_interpretation'
    ]

    results = {}

    for sample_type in sample_types:
        result = test_sample_type(sample_type, difficulty="intermediate")
        results[sample_type] = result is not None

        if len(sample_types) > 1:
            import time
            print("\n\nWaiting 3 seconds before next test...")
            time.sleep(3)

    # Summary
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    for sample_type, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{sample_type}: {status}")

    total = len(results)
    passed = sum(1 for success in results.values() if success)
    print(f"\nTotal: {passed}/{total} tests passed")
