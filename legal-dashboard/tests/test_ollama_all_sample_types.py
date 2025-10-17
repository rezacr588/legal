#!/usr/bin/env python3
"""
Test Ollama Cloud with ALL 4 sample types to verify validation alignment
"""

import os
from services.generation_service import GenerationService

# Check API key
api_key = os.getenv('OLLAMA_API_KEY')
if not api_key:
    print("❌ OLLAMA_API_KEY not set")
    exit(1)

service = GenerationService()

# Define test cases for all 4 sample types
test_cases = [
    {
        'name': 'case_analysis',
        'keywords': ['ISSUE', 'RULE', 'APPLICATION', 'CONCLUSION'],
        'topic': 'Breach of Contract'
    },
    {
        'name': 'educational',
        'keywords': ['DEFINITION', 'LEGAL BASIS', 'KEY ELEMENTS', 'EXAMPLES'],
        'topic': 'Consideration'
    },
    {
        'name': 'client_interaction',
        'keywords': ['UNDERSTANDING', 'LEGAL POSITION', 'OPTIONS', 'RECOMMENDATION'],
        'topic': 'Employment Contracts'
    },
    {
        'name': 'statutory_interpretation',
        'keywords': ['STATUTORY TEXT', 'PURPOSE', 'INTERPRETATION', 'APPLICATION'],
        'topic': 'Directors Duties'
    }
]

results = []

for idx, test_case in enumerate(test_cases, 1):
    sample_type = test_case['name']
    expected_keywords = test_case['keywords']

    print(f"\n{'='*70}")
    print(f"TEST {idx}/4: {sample_type}")
    print(f"Topic: {test_case['topic']}")
    print(f"Expected keywords: {', '.join(expected_keywords)}")
    print('='*70)

    # Generate sample
    sample, tokens, elapsed, error = service.generate_single_sample(
        practice_area="Contract Law" if sample_type != 'statutory_interpretation' else "Company Law",
        topic=test_case['topic'],
        difficulty="basic",
        counter=idx,
        provider="ollama",
        model="gpt-oss:120b-cloud",
        sample_type=sample_type
    )

    if error:
        print(f"❌ FAILED: {error}")
        results.append({'type': sample_type, 'status': 'FAIL', 'error': error})
        continue

    print(f"✅ Generated in {elapsed:.2f}s ({tokens} tokens)")

    # Verify sample_type field
    if sample['sample_type'] != sample_type:
        print(f"❌ Wrong sample_type: got '{sample['sample_type']}', expected '{sample_type}'")
        results.append({'type': sample_type, 'status': 'FAIL', 'error': 'Wrong sample_type'})
        continue

    print(f"✅ Correct sample_type: '{sample_type}'")

    # Check structure
    answer_upper = sample['answer'].upper()
    found_keywords = [kw for kw in expected_keywords if kw in answer_upper]

    print(f"\nStructure validation:")
    for kw in expected_keywords:
        status = "✅" if kw in answer_upper else "❌"
        print(f"  {status} {kw}")

    # Validation requires 3/4 keywords
    if len(found_keywords) >= 3:
        print(f"\n✅ PASS: {len(found_keywords)}/4 keywords found (need 3/4)")
        results.append({'type': sample_type, 'status': 'PASS', 'found': len(found_keywords)})
    else:
        print(f"\n❌ FAIL: Only {len(found_keywords)}/4 keywords (need 3/4)")
        results.append({'type': sample_type, 'status': 'FAIL', 'error': 'Insufficient keywords'})

    print(f"\nQuestion: {sample['question'][:100]}...")
    print(f"Answer preview: {sample['answer'][:150]}...")

# Final summary
print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)

passed = sum(1 for r in results if r['status'] == 'PASS')
total = len(results)

for result in results:
    status_icon = "✅" if result['status'] == 'PASS' else "❌"
    print(f"{status_icon} {result['type']:30} {result['status']}")

print(f"\nScore: {passed}/{total} sample types validated correctly")

if passed == total:
    print("\n🎉 ALL TESTS PASSED - Ollama Cloud validation fully aligned with sample types!")
else:
    print(f"\n⚠️  {total - passed} test(s) failed")
