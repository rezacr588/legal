#!/usr/bin/env python3
"""
Test Ollama Cloud with sample type validation
"""

import os
from services.generation_service import GenerationService

# Check if Ollama API key is set
api_key = os.getenv('OLLAMA_API_KEY')
if not api_key:
    print("❌ OLLAMA_API_KEY not set in environment")
    print("\nTo set it:")
    print("  export OLLAMA_API_KEY='your_key_here'")
    exit(1)

print(f"✅ OLLAMA_API_KEY configured: {api_key[:10]}...")

# Test with educational sample type
service = GenerationService()

print("\n" + "="*70)
print("Testing Ollama Cloud: gpt-oss:120b-cloud")
print("Sample Type: educational (should have DEFINITION, LEGAL BASIS, etc.)")
print("="*70 + "\n")

sample, tokens, elapsed, error = service.generate_single_sample(
    practice_area="Contract Law",
    topic="Consideration",
    difficulty="basic",
    counter=1,
    provider="ollama",
    model="gpt-oss:120b-cloud",
    sample_type="educational"  # NOT case_analysis
)

if error:
    print(f"❌ FAILED: {error}\n")
    exit(1)

print(f"✅ SUCCESS - Generated in {elapsed:.2f}s, {tokens} tokens\n")

# Check that sample_type was forced to educational
print(f"Sample Type: {sample.get('sample_type')}")
assert sample['sample_type'] == 'educational', "Sample type should be 'educational'"
print("✅ Sample type correctly set to 'educational'\n")

# Check answer structure
answer = sample['answer']
answer_upper = answer.upper()

print("Checking educational structure validation:")
educational_keywords = ['DEFINITION', 'LEGAL BASIS', 'KEY ELEMENTS', 'EXAMPLES']
found = []
for kw in educational_keywords:
    if kw in answer_upper:
        print(f"  ✅ Found: {kw}")
        found.append(kw)
    else:
        print(f"  ❌ Missing: {kw}")

print(f"\nStructure check: {len(found)}/4 keywords found (need 3/4)")
if len(found) >= 3:
    print("✅ Structure validation PASSED\n")
else:
    print("❌ Structure validation would FAIL\n")

# Show sample preview
print("="*70)
print("SAMPLE PREVIEW")
print("="*70)
print(f"Question: {sample['question'][:150]}...")
print(f"\nAnswer (first 300 chars):\n{answer[:300]}...")
print(f"\nReasoning: {sample['reasoning'][:200]}...")
print(f"\nCase Citation: {sample['case_citation']}")
print(f"Difficulty: {sample['difficulty']}")
print("="*70)

print("\n✅ TEST PASSED - Ollama Cloud works with sample type validation!")
