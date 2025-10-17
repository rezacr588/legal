#!/usr/bin/env python3
"""
Comprehensive Generator API Test Suite
Tests all functionalities: sample types, providers, difficulties, validation
"""

import sys
import requests
import json
from typing import Dict, List, Tuple

API_URL = "http://127.0.0.1:5001/api/generate"

# Test configuration
TEST_CASES = [
    # (sample_type, practice_area, topic, difficulty, provider, model)
    ('case_analysis', 'Contract Law', 'Consideration', 'basic', 'groq', 'llama-3.3-70b-versatile'),
    ('educational', 'Tort Law', 'Negligence', 'basic', 'groq', 'llama-3.3-70b-versatile'),
    ('client_interaction', 'Family Law', 'Divorce Proceedings', 'intermediate', 'groq', 'llama-3.3-70b-versatile'),
    ('statutory_interpretation', 'Employment Law', 'Employment Contracts', 'intermediate', 'groq', 'llama-3.3-70b-versatile'),
]

STRUCTURE_REQUIREMENTS = {
    'case_analysis': ['ISSUE', 'RULE', 'APPLICATION', 'CONCLUSION'],
    'educational': ['DEFINITION', 'LEGAL BASIS', 'KEY ELEMENTS', 'EXAMPLES'],
    'client_interaction': ['UNDERSTANDING', 'LEGAL POSITION', 'OPTIONS', 'RECOMMENDATION'],
    'statutory_interpretation': ['STATUTORY TEXT', 'PURPOSE', 'INTERPRETATION', 'APPLICATION']
}

REQUIRED_FIELDS = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning', 'sample_type']

def validate_structure(answer: str, sample_type: str) -> Tuple[bool, List[str], List[str]]:
    """Validate answer has required structure for sample type."""
    required = STRUCTURE_REQUIREMENTS[sample_type]
    answer_upper = answer.upper()

    found = [s for s in required if s in answer_upper]
    missing = [s for s in required if s not in answer_upper]

    return len(found) >= 3, found, missing

def validate_sample(sample: Dict, expected_type: str, expected_difficulty: str) -> Tuple[bool, List[str]]:
    """Validate sample has all required fields and correct values."""
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in sample:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Check sample_type matches
    if sample.get('sample_type') != expected_type:
        errors.append(f"Wrong sample_type: expected '{expected_type}', got '{sample.get('sample_type')}'")

    # Check difficulty matches
    if sample.get('difficulty') != expected_difficulty:
        errors.append(f"Wrong difficulty: expected '{expected_difficulty}', got '{sample.get('difficulty')}'")

    # Check structure
    is_valid, found, missing = validate_structure(sample['answer'], expected_type)
    if not is_valid:
        errors.append(f"Invalid structure: found {len(found)}/4 sections, missing: {', '.join(missing[:2])}")

    # Check reasoning steps
    step_count = sample.get('reasoning', '').count('Step ')
    if step_count < 4:
        errors.append(f"Insufficient reasoning steps: {step_count} (need at least 4)")

    # Check answer length
    word_count = len(sample.get('answer', '').split())
    if word_count < 100:
        errors.append(f"Answer too short: {word_count} words (need at least 100)")

    return len(errors) == 0, errors

def test_single_generation(sample_type: str, practice_area: str, topic: str,
                          difficulty: str, provider: str, model: str) -> Dict:
    """Test a single sample generation."""
    print(f"\n{'='*80}")
    print(f"Testing: {sample_type.upper()}")
    print(f"{'='*80}")
    print(f"Practice Area: {practice_area}")
    print(f"Topic: {topic}")
    print(f"Difficulty: {difficulty}")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print()

    payload = {
        "practice_area": practice_area,
        "topic": topic,
        "difficulty": difficulty,
        "provider": provider,
        "model": model,
        "sample_type": sample_type
    }

    result = {
        'test': f"{sample_type}_{difficulty}",
        'passed': False,
        'errors': [],
        'details': {}
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        data = response.json()

        if not data.get('success'):
            error = data.get('error', 'Unknown error')
            print(f"❌ GENERATION FAILED")
            print(f"Error: {error}")
            result['errors'].append(f"API error: {error}")

            # Check if it's a rate limit
            if 'rate_limit' in error.lower() or 'quota' in error.lower():
                result['rate_limited'] = True
                print("⚠️  Rate limit hit")
            return result

        sample = data['sample']
        tokens_used = data.get('tokens_used', 0)
        elapsed = data.get('elapsed', 0)

        print(f"✅ GENERATION SUCCESSFUL")
        print(f"Generated {tokens_used} tokens in {elapsed:.2f}s")
        print()

        # Validate sample
        is_valid, errors = validate_sample(sample, sample_type, difficulty)

        result['details'] = {
            'tokens': tokens_used,
            'elapsed': elapsed,
            'sample_type_field': sample.get('sample_type'),
            'difficulty_field': sample.get('difficulty'),
            'word_count': len(sample.get('answer', '').split()),
            'reasoning_steps': sample.get('reasoning', '').count('Step ')
        }

        # Check structure
        is_struct_valid, found, missing = validate_structure(sample['answer'], sample_type)
        result['details']['structure'] = {
            'found': len(found),
            'required': len(STRUCTURE_REQUIREMENTS[sample_type]),
            'found_sections': found,
            'missing_sections': missing
        }

        print(f"Validation Results:")
        print(f"  Sample Type: {sample.get('sample_type')} {'✅' if sample.get('sample_type') == sample_type else '❌'}")
        print(f"  Difficulty: {sample.get('difficulty')} {'✅' if sample.get('difficulty') == difficulty else '❌'}")
        print(f"  Word Count: {result['details']['word_count']} {'✅' if result['details']['word_count'] >= 100 else '❌'}")
        print(f"  Reasoning Steps: {result['details']['reasoning_steps']} {'✅' if result['details']['reasoning_steps'] >= 4 else '❌'}")
        print(f"  Structure: {len(found)}/{len(STRUCTURE_REQUIREMENTS[sample_type])} sections {'✅' if is_struct_valid else '❌'}")

        for section in STRUCTURE_REQUIREMENTS[sample_type]:
            status = "✅" if section in found else "❌"
            print(f"    {status} {section}")

        if is_valid:
            print()
            print(f"✅ ALL VALIDATIONS PASSED")
            result['passed'] = True
        else:
            print()
            print(f"❌ VALIDATION FAILED")
            for error in errors:
                print(f"  - {error}")
            result['errors'] = errors

        return result

    except requests.exceptions.Timeout:
        print(f"❌ REQUEST TIMEOUT (>120s)")
        result['errors'].append("Request timeout")
        return result
    except json.JSONDecodeError as e:
        print(f"❌ JSON DECODE ERROR: {str(e)}")
        result['errors'].append(f"JSON decode error: {str(e)}")
        return result
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        result['errors'].append(f"Exception: {str(e)}")
        return result

def test_api_endpoints():
    """Test supporting API endpoints."""
    print("\n" + "="*80)
    print("TESTING SUPPORTING API ENDPOINTS")
    print("="*80 + "\n")

    endpoints = [
        ('GET', 'http://127.0.0.1:5001/api/sample-types', 'Sample Types'),
        ('GET', 'http://127.0.0.1:5001/api/providers', 'Providers'),
        ('GET', 'http://127.0.0.1:5001/api/models', 'Models'),
        ('GET', 'http://127.0.0.1:5001/api/topics', 'Topics'),
        ('GET', 'http://127.0.0.1:5001/api/health', 'Health Check'),
    ]

    results = []
    for method, url, name in endpoints:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if response.status_code == 200:
                print(f"✅ {name}: OK")

                # Show key info
                if name == 'Sample Types' and 'sample_types' in data:
                    print(f"   Found {len(data['sample_types'])} sample types")
                elif name == 'Providers' and 'providers' in data:
                    print(f"   Found {len(data['providers'])} providers")
                elif name == 'Models' and 'models' in data:
                    print(f"   Found {len(data['models'])} models")
                elif name == 'Topics' and 'topics' in data:
                    print(f"   Found {len(data['topics'])} topics")

                results.append((name, True, None))
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                results.append((name, False, f"HTTP {response.status_code}"))
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            results.append((name, False, str(e)))

    return results

def main():
    """Run comprehensive API tests."""
    print("="*80)
    print("COMPREHENSIVE GENERATOR API TEST SUITE")
    print("="*80)
    print()
    print("This test suite validates:")
    print("1. All 4 sample types generate successfully")
    print("2. Sample_type field matches request")
    print("3. Answer structure matches sample type requirements")
    print("4. All required fields are present")
    print("5. Quality validation (reasoning steps, word count)")
    print("6. Supporting API endpoints work correctly")
    print()

    # Test supporting endpoints first
    endpoint_results = test_api_endpoints()

    # Test sample generation
    test_results = []
    for sample_type, practice_area, topic, difficulty, provider, model in TEST_CASES:
        result = test_single_generation(sample_type, practice_area, topic, difficulty, provider, model)
        test_results.append(result)

    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")

    print("Supporting API Endpoints:")
    for name, passed, error in endpoint_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status:10} {name}")
        if error:
            print(f"             Error: {error}")

    print("\nSample Generation:")
    passed = sum(1 for r in test_results if r['passed'])
    failed = sum(1 for r in test_results if not r['passed'] and not r.get('rate_limited'))
    rate_limited = sum(1 for r in test_results if r.get('rate_limited'))

    for result in test_results:
        if result['passed']:
            status = "✅ PASS"
            extra = f"({result['details']['tokens']} tokens, {result['details']['elapsed']:.2f}s)"
        elif result.get('rate_limited'):
            status = "⚠️  RATE LIMITED"
            extra = ""
        else:
            status = "❌ FAIL"
            extra = f"({len(result['errors'])} errors)"

        print(f"  {status:18} {result['test']:40} {extra}")

        if result['errors'] and not result.get('rate_limited'):
            for error in result['errors'][:2]:  # Show first 2 errors
                print(f"                     - {error}")

    print()
    print(f"Generation Tests: {passed} passed, {failed} failed, {rate_limited} rate limited")
    print(f"Endpoint Tests: {sum(1 for _, p, _ in endpoint_results if p)}/{len(endpoint_results)} passed")
    print()

    if rate_limited > 0:
        print("ℹ️  Note: Rate limits reset at midnight UTC")
        print("   Rerun tests later to verify rate-limited sample types")

    # Overall pass/fail
    all_endpoints_passed = all(passed for _, passed, _ in endpoint_results)
    all_generation_passed = failed == 0

    if all_endpoints_passed and all_generation_passed:
        print("\n✅ ALL TESTS PASSED (excluding rate limits)")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
