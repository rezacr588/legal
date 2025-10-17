#!/usr/bin/env python3
"""
Comprehensive test script for all Cerebras models.
Tests generation quality and verifies no thinking tags in final output.
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.generation_service import GenerationService
from config import CEREBRAS_ALL_MODELS

def count_words(text):
    """Count words in text."""
    return len(text.split())

def count_citations(text):
    """Count case citations in text."""
    # Simple heuristic: count patterns like [YEAR] or v.
    import re
    patterns = [
        r'\[\d{4}\]',  # [2023]
        r'\(\d{4}\)',  # (2023)
        r'\bv\.\s',    # v. (versus)
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text))
    return max(1, count // 2)  # Divide by 2 since citations often have multiple markers

def count_reasoning_steps(text):
    """Count reasoning steps in text."""
    import re
    step_pattern = r'Step \d+:'
    return len(re.findall(step_pattern, text, re.IGNORECASE))

def check_thinking_tags(text):
    """Check if thinking tags are present in text."""
    has_opening = '<thinking>' in text.lower()
    has_closing = '</thinking>' in text.lower()
    return has_opening or has_closing

def test_model(service, model_name):
    """Test a single model and return results."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print('='*80)

    try:
        # Generate sample with intermediate difficulty
        sample, tokens_used, elapsed, error = service.generate_single_sample(
            practice_area="Contract Law",
            topic="Formation of Contracts",
            difficulty="intermediate",
            counter=1,  # Test sample counter
            provider="cerebras",
            model=model_name
        )

        if error or not sample:
            print(f"❌ FAILED: {error or 'Sample generation failed'}")
            return {
                'model': model_name,
                'success': False,
                'error': error or 'Sample generation failed'
            }

        # Check for thinking tags in critical fields
        answer_has_thinking = check_thinking_tags(sample.get('answer', ''))
        reasoning_has_thinking = check_thinking_tags(sample.get('reasoning', ''))

        # Count metrics
        word_count = count_words(sample.get('answer', ''))
        citation_count = count_citations(sample.get('case_citation', ''))
        reasoning_steps = count_reasoning_steps(sample.get('reasoning', ''))

        # Quality check
        passes_validation = word_count >= 350 and citation_count >= 2 and reasoning_steps >= 5

        # Print results
        print(f"\n📊 Metrics:")
        print(f"  - Word Count: {word_count} (min: 350)")
        print(f"  - Citations: {citation_count} (min: 2)")
        print(f"  - Reasoning Steps: {reasoning_steps} (min: 5)")
        print(f"  - Tokens Used: {tokens_used}")

        print(f"\n🔍 Thinking Tag Check:")
        print(f"  - Answer has <thinking> tags: {'❌ YES (BAD!)' if answer_has_thinking else '✅ NO (GOOD)'}")
        print(f"  - Reasoning has <thinking> tags: {'❌ YES (BAD!)' if reasoning_has_thinking else '✅ NO (GOOD)'}")

        print(f"\n✅ Quality Validation: {'✅ PASS' if passes_validation else '❌ FAIL'}")

        if passes_validation and not answer_has_thinking and not reasoning_has_thinking:
            print(f"\n🎉 {model_name}: SUCCESS - All checks passed!")
        else:
            print(f"\n⚠️  {model_name}: ISSUES DETECTED")

        # Show sample preview
        print(f"\n📝 Sample Preview:")
        print(f"  Question: {sample.get('question', '')[:100]}...")
        print(f"  Answer: {sample.get('answer', '')[:200]}...")

        return {
            'model': model_name,
            'success': True,
            'word_count': word_count,
            'citations': citation_count,
            'reasoning_steps': reasoning_steps,
            'tokens_used': tokens_used,
            'answer_has_thinking': answer_has_thinking,
            'reasoning_has_thinking': reasoning_has_thinking,
            'passes_validation': passes_validation,
            'all_checks_passed': passes_validation and not answer_has_thinking and not reasoning_has_thinking
        }

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'model': model_name,
            'success': False,
            'error': str(e)
        }

def main():
    """Test all Cerebras models."""
    print("🚀 Starting Comprehensive Cerebras Model Testing")
    print(f"📋 Testing {len(CEREBRAS_ALL_MODELS)} models\n")

    # Initialize service
    service = GenerationService()

    # Test each model
    results = []
    for model in CEREBRAS_ALL_MODELS:
        result = test_model(service, model)
        results.append(result)
        time.sleep(2)  # Brief pause between tests

    # Summary
    print(f"\n\n{'='*80}")
    print("📊 SUMMARY REPORT")
    print('='*80)

    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    all_checks_passed = [r for r in results if r.get('all_checks_passed', False)]

    print(f"\n✅ Successful Generations: {len(successful)}/{len(results)}")
    print(f"❌ Failed Generations: {len(failed)}/{len(results)}")
    print(f"🎉 Passed All Checks: {len(all_checks_passed)}/{len(results)}")

    if all_checks_passed:
        print("\n🏆 Models Passing All Checks:")
        for r in all_checks_passed:
            print(f"  ✅ {r['model']} - {r['word_count']} words, {r['citations']} citations, {r['reasoning_steps']} steps")

    if failed:
        print("\n❌ Failed Models:")
        for r in failed:
            print(f"  ❌ {r['model']}: {r.get('error', 'Unknown error')}")

    # Check for thinking tag issues
    thinking_issues = [r for r in successful if r.get('answer_has_thinking') or r.get('reasoning_has_thinking')]
    if thinking_issues:
        print("\n⚠️  Models with Thinking Tag Issues:")
        for r in thinking_issues:
            fields = []
            if r.get('answer_has_thinking'):
                fields.append('answer')
            if r.get('reasoning_has_thinking'):
                fields.append('reasoning')
            print(f"  ⚠️  {r['model']}: Thinking tags in {', '.join(fields)}")

    # Save detailed results
    output_file = '/tmp/cerebras_model_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
