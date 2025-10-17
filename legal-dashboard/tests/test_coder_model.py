#!/usr/bin/env python3
"""
Dedicated test for qwen-3-coder-480b to assess its legal reasoning quality.
Testing with new validation rules (no word/citation thresholds).
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.generation_service import GenerationService

def test_coder_model(difficulty="advanced"):
    """Test the 480B coder model with specified difficulty."""
    print(f"\n{'='*80}")
    print(f"Testing: qwen-3-coder-480b (480B parameters - LARGEST MODEL)")
    print(f"Difficulty: {difficulty}")
    print('='*80)

    service = GenerationService()

    try:
        sample, tokens_used, elapsed, error = service.generate_single_sample(
            practice_area="Company Law",
            topic="Directors Duties",
            difficulty=difficulty,
            counter=1,
            provider="cerebras",
            model="qwen-3-coder-480b"
        )

        if error or not sample:
            print(f"\n❌ GENERATION FAILED")
            print(f"Error: {error}")
            return None

        # Extract metrics
        answer = sample.get('answer', '')
        reasoning = sample.get('reasoning', '')
        case_citation = sample.get('case_citation', '')
        question = sample.get('question', '')

        word_count = len(answer.split())

        import re
        citation_count = len(re.findall(r'\[\d{4}\]', case_citation))
        reasoning_steps = len(re.findall(r'Step \d+:', reasoning, re.IGNORECASE))

        has_irac = all(keyword in answer.upper() for keyword in ['ISSUE', 'RULE', 'APPLICATION', 'CONCLUSION'])
        has_thinking = '<thinking>' in answer.lower() or '<thinking>' in reasoning.lower()

        # Print full results
        print(f"\n✅ GENERATION SUCCESSFUL")
        print(f"\n📊 METRICS:")
        print(f"  • Word Count: {word_count}")
        print(f"  • Citations: {citation_count}")
        print(f"  • Reasoning Steps: {reasoning_steps}")
        print(f"  • IRAC Structure: {'✅ YES' if has_irac else '❌ NO'}")
        print(f"  • Thinking Tags: {'❌ YES (BAD)' if has_thinking else '✅ NO (GOOD)'}")
        print(f"  • Tokens Used: {tokens_used}")
        print(f"  • Generation Time: {elapsed:.2f}s")

        print(f"\n❓ QUESTION:")
        print(f"{question}\n")

        print(f"\n📄 FULL ANSWER:")
        print(f"{answer}\n")

        print(f"\n🧠 REASONING:")
        print(f"{reasoning}\n")

        print(f"\n📚 CITATIONS:")
        print(f"{case_citation}\n")

        # Quality assessment
        print(f"\n{'='*80}")
        print("QUALITY ASSESSMENT")
        print('='*80)

        quality_issues = []
        quality_strengths = []

        if word_count < 300:
            quality_issues.append(f"Short answer ({word_count} words - below typical 350+)")
        else:
            quality_strengths.append(f"Good length ({word_count} words)")

        if citation_count < 3:
            quality_issues.append(f"Few citations ({citation_count} - typical is 3-4)")
        else:
            quality_strengths.append(f"Good citations ({citation_count})")

        if reasoning_steps >= 6:
            quality_strengths.append(f"Solid reasoning ({reasoning_steps} steps)")
        else:
            quality_issues.append(f"Weak reasoning ({reasoning_steps} steps - need 6+)")

        if has_irac:
            quality_strengths.append("Proper IRAC structure")
        else:
            quality_issues.append("Missing IRAC structure")

        if not has_thinking:
            quality_strengths.append("Clean output (no thinking tags)")
        else:
            quality_issues.append("Thinking tags present (needs fixing)")

        print("\n✅ STRENGTHS:")
        for strength in quality_strengths:
            print(f"  ✅ {strength}")

        if quality_issues:
            print("\n⚠️  WEAKNESSES:")
            for issue in quality_issues:
                print(f"  ⚠️  {issue}")

        # Overall verdict
        score = len(quality_strengths) * 2 - len(quality_issues)
        max_score = 10

        print(f"\n⭐ QUALITY SCORE: {max(0, score)}/{max_score}")

        if score >= 8:
            print("✅ Verdict: EXCELLENT - Production ready")
        elif score >= 6:
            print("✅ Verdict: GOOD - Suitable for use")
        elif score >= 4:
            print("⚠️  Verdict: FAIR - Use with caution")
        else:
            print("❌ Verdict: POOR - Not recommended")

        # Save for review
        output = {
            'model': 'qwen-3-coder-480b',
            'difficulty': difficulty,
            'metrics': {
                'word_count': word_count,
                'citations': citation_count,
                'reasoning_steps': reasoning_steps,
                'has_irac': has_irac,
                'has_thinking': has_thinking,
                'tokens_used': tokens_used,
                'elapsed_time': elapsed,
                'quality_score': max(0, score)
            },
            'sample': sample
        }

        with open(f'/tmp/coder_model_{difficulty}_test.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n💾 Detailed output saved to: /tmp/coder_model_{difficulty}_test.json")

        return output

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 QWEN-3-CODER-480B QUALITY TEST")
    print("Testing the largest Cerebras model (480B parameters)")
    print("="*80)

    # Test with advanced difficulty
    result_advanced = test_coder_model("advanced")

    if result_advanced:
        # If successful, also test intermediate for comparison
        print("\n\n" + "="*80)
        print("BONUS: Testing with intermediate difficulty")
        print("="*80)
        time.sleep(2)
        result_intermediate = test_coder_model("intermediate")

        # Comparison
        if result_intermediate:
            print("\n\n" + "="*80)
            print("📊 DIFFICULTY COMPARISON")
            print("="*80)
            print(f"\nAdvanced: {result_advanced['metrics']['word_count']} words, "
                  f"{result_advanced['metrics']['citations']} citations, "
                  f"score {result_advanced['metrics']['quality_score']}/10")
            print(f"Intermediate: {result_intermediate['metrics']['word_count']} words, "
                  f"{result_intermediate['metrics']['citations']} citations, "
                  f"score {result_intermediate['metrics']['quality_score']}/10")
