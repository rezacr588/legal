#!/usr/bin/env python3
"""
Test suite for sample_type structure validation.
Verifies that _validate_answer_structure() correctly enforces type-specific structures.
"""

import sys
sys.path.insert(0, '/Users/rezazeraat/Desktop/Data/legal-dashboard')

from services.generation_service import GenerationService

def test_structure_validation():
    """Test all sample types with correct and incorrect structures."""
    gs = GenerationService()

    # Padding to meet 100-word minimum
    padding = " " + " ".join([f"word{i}" for i in range(100)])

    test_cases = [
        # (description, sample_dict, should_pass)
        (
            "Educational with IRAC (wrong)",
            {
                'answer': f'ISSUE: Issue text. RULE: Rule text. APPLICATION: Application text. CONCLUSION: Conclusion text.{padding}',
                'reasoning': 'Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...',
                'sample_type': 'educational'
            },
            False
        ),
        (
            "Educational with educational structure (correct)",
            {
                'answer': f'DEFINITION: Definition text. LEGAL BASIS: Legal basis text. KEY ELEMENTS: Key elements text. EXAMPLES: Example text.{padding}',
                'reasoning': 'Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...',
                'sample_type': 'educational'
            },
            True
        ),
        (
            "Case analysis with IRAC (correct)",
            {
                'answer': f'ISSUE: Issue text. RULE: Rule text. APPLICATION: Application text. CONCLUSION: Conclusion text.{padding}',
                'reasoning': 'Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...',
                'sample_type': 'case_analysis'
            },
            True
        ),
        (
            "Client with educational structure (wrong)",
            {
                'answer': f'DEFINITION: Definition text. LEGAL BASIS: Legal basis. KEY ELEMENTS: Elements. EXAMPLES: Examples.{padding}',
                'reasoning': 'Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...',
                'sample_type': 'client_interaction'
            },
            False
        ),
        (
            "Client with client structure (correct)",
            {
                'answer': f'UNDERSTANDING: I understand. LEGAL POSITION: The law states. OPTIONS: You have options. RECOMMENDATION: I recommend.{padding}',
                'reasoning': 'Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...',
                'sample_type': 'client_interaction'
            },
            True
        ),
        (
            "Statutory with statutory structure (correct)",
            {
                'answer': f'STATUTORY TEXT: Text here. PURPOSE: Legislative intent. INTERPRETATION: Meaning. APPLICATION: How it applies.{padding}',
                'reasoning': 'Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...',
                'sample_type': 'statutory_interpretation'
            },
            True
        )
    ]

    print("=" * 80)
    print("STRUCTURE VALIDATION TEST SUITE")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for description, sample, should_pass in test_cases:
        # Add required fields
        sample.update({
            'case_citation': 'Test Case [2020] UKHL 1',
            'question': 'Test question',
            'topic': 'Test Topic',
            'difficulty': 'intermediate'
        })

        result = gs._validate_sample_quality(sample, 'intermediate')
        did_pass = result is None

        test_passed = (did_pass == should_pass)

        status = "✅ PASS" if test_passed else "❌ FAIL"
        expectation = "should pass" if should_pass else "should fail"
        actual = "passed" if did_pass else f"failed: {result}"

        print(f"{status} {description}")
        print(f"     Expected: {expectation}, Actual: {actual}")
        print()

        if test_passed:
            passed += 1
        else:
            failed += 1

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return failed == 0

if __name__ == '__main__':
    success = test_structure_validation()
    exit(0 if success else 1)
