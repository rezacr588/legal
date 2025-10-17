#!/usr/bin/env python3
"""
Test all 4 sample types with live generation to verify structure validation works.
"""

import sys
import requests
import json

# Test configuration
API_URL = "http://127.0.0.1:5001/api/generate"

# Structure requirements for each type
STRUCTURE_REQUIREMENTS = {
    'case_analysis': ['ISSUE', 'RULE', 'APPLICATION', 'CONCLUSION'],
    'educational': ['DEFINITION', 'LEGAL BASIS', 'KEY ELEMENTS', 'EXAMPLES'],
    'client_interaction': ['UNDERSTANDING', 'LEGAL POSITION', 'OPTIONS', 'RECOMMENDATION'],
    'statutory_interpretation': ['STATUTORY TEXT', 'PURPOSE', 'INTERPRETATION', 'APPLICATION']
}

def test_sample_type(sample_type, practice_area, topic, difficulty="basic"):
    """Test generation of a specific sample type."""

    print(f"\n{'='*80}")
    print(f"Testing: {sample_type.upper()}")
    print(f"{'='*80}")

    payload = {
        "practice_area": practice_area,
        "topic": topic,
        "difficulty": difficulty,
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "sample_type": sample_type
    }

    print(f"Request: {practice_area} - {topic} ({difficulty})")
    print(f"Provider: Groq (llama-3.1-8b-instant)")
    print(f"Sample Type: {sample_type}")
    print()

    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        result = response.json()

        if not result.get('success', False):
            error = result.get('error', 'Unknown error')
            print(f"❌ GENERATION FAILED")
            print(f"Error: {error}")

            # Check if it's a rate limit
            if 'rate_limit' in error.lower() or 'quota' in error.lower() or '429' in error:
                print("⚠️  Rate limit hit - this is expected, not a validation failure")
                return 'rate_limited'
            return False

        sample = result['sample']
        answer = sample.get('answer', '')
        returned_type = sample.get('sample_type', 'MISSING')

        print(f"✅ GENERATION SUCCESSFUL")
        print(f"Generated {result.get('tokens_used', 0)} tokens in {result.get('elapsed', 0):.2f}s")
        print()

        # Verify sample_type field
        print(f"Sample Type Field: {returned_type}")
        if returned_type != sample_type:
            print(f"❌ WRONG TYPE: Expected '{sample_type}', got '{returned_type}'")
            return False
        else:
            print(f"✅ Type field correct")
        print()

        # Check structure
        required_sections = STRUCTURE_REQUIREMENTS[sample_type]
        answer_upper = answer.upper()
        found_sections = [s for s in required_sections if s in answer_upper]
        missing_sections = [s for s in required_sections if s not in answer_upper]

        print(f"Structure Validation:")
        print(f"Required sections: {', '.join(required_sections)}")
        print(f"Found: {len(found_sections)}/{len(required_sections)}")

        for section in required_sections:
            status = "✅" if section in answer_upper else "❌"
            print(f"  {status} {section}")

        if len(found_sections) >= 3:  # Require 3 of 4
            print()
            print(f"✅ STRUCTURE VALIDATION PASSED ({len(found_sections)}/4 sections found)")
            return True
        else:
            print()
            print(f"❌ STRUCTURE VALIDATION FAILED")
            print(f"Missing: {', '.join(missing_sections)}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ REQUEST TIMEOUT (>120s)")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def main():
    """Run tests for all sample types."""

    print("="*80)
    print("COMPREHENSIVE SAMPLE TYPE GENERATION TEST")
    print("="*80)
    print()
    print("This test verifies:")
    print("1. Each sample type generates successfully")
    print("2. The sample_type field is correct")
    print("3. The answer structure matches the required format")
    print()

    # Test cases: (sample_type, practice_area, topic, difficulty)
    test_cases = [
        ('case_analysis', 'Contract Law', 'Consideration', 'basic'),
        ('educational', 'Tort Law', 'Negligence', 'basic'),
        ('client_interaction', 'Family Law', 'Divorce Proceedings', 'intermediate'),
        ('statutory_interpretation', 'Employment Law', 'Employment Contracts', 'intermediate')
    ]

    results = {}

    for sample_type, practice_area, topic, difficulty in test_cases:
        result = test_sample_type(sample_type, practice_area, topic, difficulty)
        results[sample_type] = result

    # Summary
    print()
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print()

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    rate_limited = sum(1 for r in results.values() if r == 'rate_limited')

    for sample_type, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result == 'rate_limited':
            status = "⚠️  RATE LIMITED"
        else:
            status = "❌ FAIL"
        print(f"{status:20} {sample_type}")

    print()
    print(f"Passed: {passed}/4")
    print(f"Failed: {failed}/4")
    print(f"Rate Limited: {rate_limited}/4")
    print()

    if rate_limited > 0:
        print("ℹ️  Note: Rate limit errors are expected - quotas reset at midnight UTC")
        print("   Run this test tomorrow to verify all sample types work correctly")

    if failed == 0:
        print("✅ ALL TESTS PASSED (excluding rate limits)")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
