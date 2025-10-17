#!/usr/bin/env python3
"""
Test a single legal question across ALL Cerebras models.
Compare quality, accuracy, and completeness of answers.
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.generation_service import GenerationService

# All Cerebras models from the quota table
ALL_MODELS = [
    "gpt-oss-120b",
    "llama-3.3-70b",
    "llama-4-maverick-17b-128e-instruct",  # NEW
    "llama-4-scout-17b-16e-instruct",
    "llama3.1-8b",
    "qwen-3-235b-a22b-instruct-2507",
    "qwen-3-235b-a22b-thinking-2507",
    "qwen-3-32b",
    "qwen-3-coder-480b"
]

def count_words(text):
    """Count words in text."""
    return len(text.split())

def count_citations(text):
    """Count case citations (year patterns [YYYY])."""
    import re
    return len(re.findall(r'\[\d{4}\]', text))

def count_reasoning_steps(text):
    """Count reasoning steps."""
    import re
    return len(re.findall(r'Step \d+:', text, re.IGNORECASE))

def has_irac_structure(text):
    """Check if answer contains IRAC structure."""
    text_upper = text.upper()
    return all(keyword in text_upper for keyword in ['ISSUE', 'RULE', 'APPLICATION', 'CONCLUSION'])

def check_thinking_tags(text):
    """Check if thinking tags are present."""
    return '<thinking>' in text.lower() or '</thinking>' in text.lower()

def save_sample(model_name, sample, metrics):
    """Save sample to file for review."""
    output_dir = Path('/tmp/model_comparison')
    output_dir.mkdir(exist_ok=True)

    output = {
        'model': model_name,
        'metrics': metrics,
        'sample': sample
    }

    filename = output_dir / f"{model_name.replace('/', '_')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

def test_model(service, model_name):
    """Test a single model with the standard legal question."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print('='*80)

    try:
        # Use advanced difficulty for better differentiation
        sample, tokens_used, elapsed, error = service.generate_single_sample(
            practice_area="Company Law",
            topic="Directors Duties",
            difficulty="advanced",
            counter=1,
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

        # Metrics
        answer = sample.get('answer', '')
        reasoning = sample.get('reasoning', '')
        case_citation = sample.get('case_citation', '')

        word_count = count_words(answer)
        citation_count = count_citations(case_citation)
        reasoning_steps = count_reasoning_steps(reasoning)
        has_irac = has_irac_structure(answer)
        has_thinking = check_thinking_tags(answer) or check_thinking_tags(reasoning)

        metrics = {
            'word_count': word_count,
            'citation_count': citation_count,
            'reasoning_steps': reasoning_steps,
            'tokens_used': tokens_used,
            'elapsed_time': round(elapsed, 2),
            'has_irac': has_irac,
            'has_thinking_tags': has_thinking,
            'passes_citation': citation_count >= 3,  # Advanced needs 3
            'passes_reasoning': reasoning_steps >= 6  # Advanced needs 6
        }

        # Save for detailed review
        save_sample(model_name, sample, metrics)

        # Print summary
        print(f"\n📊 Metrics:")
        print(f"  - Word Count: {word_count}")
        print(f"  - Citations: {citation_count} {'✅' if citation_count >= 3 else '❌'} (min: 3)")
        print(f"  - Reasoning Steps: {reasoning_steps} {'✅' if reasoning_steps >= 6 else '❌'} (min: 6)")
        print(f"  - IRAC Structure: {'✅ YES' if has_irac else '❌ NO'}")
        print(f"  - Thinking Tags: {'❌ YES (BAD)' if has_thinking else '✅ NO (GOOD)'}")
        print(f"  - Tokens Used: {tokens_used}")
        print(f"  - Time: {elapsed:.2f}s")

        print(f"\n📝 Question:")
        print(f"  {sample.get('question', '')[:150]}...")

        print(f"\n📄 Answer Preview (first 300 chars):")
        print(f"  {answer[:300]}...")

        # Quality assessment
        quality_score = 0
        if citation_count >= 3: quality_score += 3
        if reasoning_steps >= 6: quality_score += 2
        if has_irac: quality_score += 2
        if not has_thinking: quality_score += 1
        if word_count >= 450: quality_score += 2  # Advanced should be comprehensive

        print(f"\n⭐ Quality Score: {quality_score}/10")

        return {
            'model': model_name,
            'success': True,
            'metrics': metrics,
            'quality_score': quality_score,
            'question': sample.get('question', ''),
            'answer_preview': answer[:500]
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
    """Test all models with the same question."""
    print("🚀 Testing Single Legal Question Across ALL Cerebras Models")
    print(f"📋 Testing {len(ALL_MODELS)} models")
    print(f"📚 Topic: Company Law - Directors Duties (Advanced)")
    print(f"🎯 Goal: Compare accuracy and quality of legal analysis\n")

    service = GenerationService()
    results = []

    for model in ALL_MODELS:
        result = test_model(service, model)
        results.append(result)
        time.sleep(3)  # Brief pause between tests to respect rate limits

    # Summary comparison
    print(f"\n\n{'='*80}")
    print("📊 COMPARATIVE ANALYSIS")
    print('='*80)

    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]

    print(f"\n✅ Successful Generations: {len(successful)}/{len(results)}")
    print(f"❌ Failed Generations: {len(failed)}/{len(results)}")

    if successful:
        # Sort by quality score
        successful_sorted = sorted(successful, key=lambda x: x.get('quality_score', 0), reverse=True)

        print("\n🏆 RANKING BY QUALITY SCORE:")
        print(f"{'Rank':<6} {'Model':<40} {'Score':<8} {'Words':<8} {'Citations':<11} {'Steps':<8} {'IRAC':<8}")
        print("-" * 95)

        for i, r in enumerate(successful_sorted, 1):
            m = r['metrics']
            emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{emoji} #{i:<3} {r['model']:<40} {r['quality_score']:<8} "
                  f"{m['word_count']:<8} {m['citation_count']:<11} "
                  f"{m['reasoning_steps']:<8} {'✅' if m['has_irac'] else '❌':<8}")

        # Speed comparison
        print("\n⚡ SPEED COMPARISON (Generation Time):")
        speed_sorted = sorted(successful, key=lambda x: x['metrics']['elapsed_time'])
        for i, r in enumerate(speed_sorted[:5], 1):
            print(f"  {i}. {r['model']:<45} {r['metrics']['elapsed_time']:.2f}s")

        # Token efficiency
        print("\n💰 TOKEN EFFICIENCY (Tokens per Word):")
        efficiency = [(r['model'], r['metrics']['tokens_used'] / r['metrics']['word_count'])
                     for r in successful if r['metrics']['word_count'] > 0]
        efficiency_sorted = sorted(efficiency, key=lambda x: x[1])
        for i, (model, ratio) in enumerate(efficiency_sorted[:5], 1):
            print(f"  {i}. {model:<45} {ratio:.2f} tokens/word")

        # Best for citations
        print("\n📚 BEST FOR CITATIONS:")
        citation_sorted = sorted(successful, key=lambda x: x['metrics']['citation_count'], reverse=True)
        for i, r in enumerate(citation_sorted[:3], 1):
            print(f"  {i}. {r['model']:<45} {r['metrics']['citation_count']} citations")

    if failed:
        print("\n❌ FAILED MODELS:")
        for r in failed:
            print(f"  ❌ {r['model']}: {r.get('error', 'Unknown error')[:80]}")

    # Save comparison
    output_file = '/tmp/model_comparison_summary.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to:")
    print(f"   - Summary: {output_file}")
    print(f"   - Individual samples: /tmp/model_comparison/")
    print(f"\n📖 Review individual answers at: /tmp/model_comparison/*.json")

if __name__ == "__main__":
    main()
