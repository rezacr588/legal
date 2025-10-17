#!/usr/bin/env python3
"""
Test script to verify sample type alignment between generator and training format.
Tests all 4 sample types to ensure proper formatting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.generation_service import GenerationService
import json

def print_separator(title):
    """Print a visual separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def format_training_sample(sample):
    """
    Replicate the training notebook format_sample function to show how it would look in training.
    """
    sample_type = sample.get('sample_type', 'case_analysis')

    # Build instruction
    instruction = f"""### Instruction:
{sample['question']}

### Response:"""

    # Start response with metadata
    response = f"""
### Sample Type: {sample_type}
### Topic: {sample.get('topic', 'Corporate Law')}
### Difficulty: {sample.get('difficulty', 'intermediate')}
"""

    # Add reasoning
    if 'reasoning' in sample and sample['reasoning']:
        response += f"""
### Reasoning:
{sample['reasoning']}
"""

    # Add answer with type-specific hint
    type_hints = {
        'case_analysis': '(IRAC: Issue → Rule → Application → Conclusion)',
        'educational': '(Teaching: Definition → Legal Basis → Key Elements → Examples)',
        'client_interaction': '(Client Advice: Understanding → Position → Options → Recommendation)',
        'statutory_interpretation': '(Statutory: Text → Purpose → Interpretation → Case Law)'
    }

    hint = type_hints.get(sample_type, '')

    response += f"""
### Answer {hint}:
{sample['answer']}"""

    # Add case citations
    if 'case_citation' in sample and sample['case_citation']:
        response += f"""

### Case Citation:
{sample['case_citation']}"""

    return instruction + response

def test_sample_type(sample_type, description):
    """Test generation for a specific sample type"""
    print_separator(f"Testing: {sample_type.upper()} - {description}")

    service = GenerationService()

    # Generate a sample
    print(f"🔄 Generating {sample_type} sample...")
    sample, tokens, elapsed, error = service.generate_single_sample(
        practice_area="Contract Law",
        topic="Formation of Contracts",
        difficulty="intermediate",
        counter=1,
        provider="groq",
        model="llama-3.3-70b-versatile",
        sample_type=sample_type
    )

    if error:
        print(f"❌ Generation failed: {error}")
        return False

    print(f"✅ Generated successfully ({tokens} tokens, {elapsed:.2f}s)")

    # Show raw sample JSON
    print("\n📋 RAW GENERATED SAMPLE (JSON):")
    print("-" * 80)
    print(json.dumps({
        'id': sample['id'],
        'question': sample['question'][:100] + "...",
        'answer': sample['answer'][:200] + "...",
        'topic': sample['topic'],
        'difficulty': sample['difficulty'],
        'sample_type': sample.get('sample_type', 'NOT SET'),
        'case_citation': sample['case_citation'][:100] + "..." if sample['case_citation'] else "None",
        'reasoning': sample['reasoning'][:150] + "..."
    }, indent=2))

    # Show how it would look in training
    print("\n📚 FORMATTED FOR TRAINING (How the model will see it):")
    print("-" * 80)
    training_format = format_training_sample(sample)
    # Show first 500 chars to keep output manageable
    print(training_format[:800] + "\n... [truncated]")

    # Verify sample_type field exists
    if 'sample_type' not in sample:
        print("\n⚠️  WARNING: sample_type field missing in generated sample!")
        return False

    if sample['sample_type'] != sample_type:
        print(f"\n⚠️  WARNING: sample_type mismatch! Expected: {sample_type}, Got: {sample['sample_type']}")
        return False

    print(f"\n✅ Sample type correctly set: {sample['sample_type']}")
    return True

def main():
    """Run tests for all sample types"""
    print_separator("SAMPLE TYPE ALIGNMENT TEST")
    print("Testing generator output alignment with training notebook format")
    print("This verifies that generated samples will train the model correctly")

    # Test all 4 sample types
    test_cases = [
        ("case_analysis", "IRAC methodology for problem-solving"),
        ("educational", "Structured teaching of legal concepts"),
        ("client_interaction", "Practical client communication"),
        ("statutory_interpretation", "Legislative analysis")
    ]

    results = []
    for sample_type, description in test_cases:
        success = test_sample_type(sample_type, description)
        results.append((sample_type, success))

    # Summary
    print_separator("TEST RESULTS SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for sample_type, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {sample_type}")

    print(f"\n📊 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS! All sample types are properly aligned!")
        print("   - Generator creates samples with correct sample_type field")
        print("   - Training notebook will format them correctly")
        print("   - Model will learn to recognize and use different answer structures")
    else:
        print("\n⚠️  ISSUES DETECTED - Review failed tests above")
        sys.exit(1)

if __name__ == "__main__":
    main()
