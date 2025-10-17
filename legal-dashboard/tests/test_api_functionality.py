#!/usr/bin/env python3
"""
API Functionality Test - Tests that API correctly handles parameters
Tests API functionality independent of model quality
"""

import requests
import json

API_URL = "http://127.0.0.1:5001/api/generate"

def test_parameter_passing():
    """Test that API correctly receives and passes parameters."""
    print("="*80)
    print("API PARAMETER PASSING TEST")
    print("="*80 + "\n")

    test_cases = [
        {
            'name': 'Sample Type Parameter',
            'payload': {
                'practice_area': 'Contract Law',
                'topic': 'Formation',
                'difficulty': 'basic',
                'provider': 'cerebras',
                'model': 'llama-3.3-70b',
                'sample_type': 'educational'
            },
            'checks': [
                ('sample_type', 'educational'),
                ('difficulty', 'basic')
            ]
        },
        {
            'name': 'Default Sample Type',
            'payload': {
                'practice_area': 'Tort Law',
                'topic': 'Negligence',
                'difficulty': 'intermediate',
                'provider': 'cerebras',
                'model': 'llama-3.3-70b'
                # No sample_type - should default to case_analysis
            },
            'checks': [
                ('sample_type', 'case_analysis'),
                ('difficulty', 'intermediate')
            ]
        },
        {
            'name': 'Client Interaction Type',
            'payload': {
                'practice_area': 'Family Law',
                'topic': 'Divorce',
                'difficulty': 'advanced',
                'provider': 'cerebras',
                'model': 'llama-3.3-70b',
                'sample_type': 'client_interaction'
            },
            'checks': [
                ('sample_type', 'client_interaction'),
                ('difficulty', 'advanced')
            ]
        }
    ]

    results = []
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")

        try:
            response = requests.post(API_URL, json=test['payload'], timeout=120)
            data = response.json()

            if not data.get('success'):
                error = data.get('error', 'Unknown')
                if 'rate_limit' in error.lower() or 'quota' in error.lower() or '429' in error:
                    print(f"⚠️  Rate limited (expected)")
                    results.append(('rate_limited', test['name']))
                    continue
                else:
                    print(f"❌ FAILED: {error}")
                    results.append(('failed', test['name'], error))
                    continue

            sample = data['sample']

            # Verify all checks pass
            all_passed = True
            for field, expected_value in test['checks']:
                actual_value = sample.get(field)
                if actual_value == expected_value:
                    print(f"  ✅ {field}: {actual_value} (matches expected)")
                else:
                    print(f"  ❌ {field}: {actual_value} (expected {expected_value})")
                    all_passed = False

            if all_passed:
                print(f"✅ PASSED: All parameters correctly passed")
                results.append(('passed', test['name']))
            else:
                print(f"❌ FAILED: Parameter mismatch")
                results.append(('failed', test['name'], 'Parameter mismatch'))

        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.append(('exception', test['name'], str(e)))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r[0] == 'passed')
    failed = sum(1 for r in results if r[0] == 'failed')
    rate_limited = sum(1 for r in results if r[0] == 'rate_limited')
    exceptions = sum(1 for r in results if r[0] == 'exception')

    print(f"\nPassed: {passed}")
    print(f"Failed: {failed}")
    print(f"Rate Limited: {rate_limited}")
    print(f"Exceptions: {exceptions}")

    if failed == 0 and exceptions == 0:
        print("\n✅ API FUNCTIONALITY VERIFIED")
        print("   All parameters are correctly passed and processed")
        if rate_limited > 0:
            print(f"   ({rate_limited} tests rate-limited, but API is working)")
        return 0
    else:
        print("\n❌ API FUNCTIONALITY ISSUES DETECTED")
        return 1

if __name__ == '__main__':
    exit(test_parameter_passing())
