#!/usr/bin/env python3
"""
Quick bootstrap - Generate just 2 samples of each type to test alignment.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.generation_service import GenerationService
import polars as pl
import json

def test_generate_sample_type(sample_type):
    """Generate one sample and show its structure"""
    print(f"\n{'='*80}")
    print(f"Testing: {sample_type}")
    print('='*80)

    service = GenerationService()

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
        print(f"❌ Error: {error}")
        return None

    print(f"✅ Generated successfully ({tokens} tokens, {elapsed:.2f}s)")

    # Show the sample structure
    print("\n📋 Sample structure:")
    print(f"  - id: {sample['id']}")
    print(f"  - sample_type: {sample.get('sample_type', 'MISSING')}")
    print(f"  - topic: {sample['topic']}")
    print(f"  - difficulty: {sample['difficulty']}")
    print(f"  - question (first 100 chars): {sample['question'][:100]}...")
    print(f"  - answer (first 200 chars): {sample['answer'][:200]}...")

    return sample

def main():
    print("="*80)
    print("  QUICK BOOTSTRAP TEST")
    print("="*80)
    print("\nTesting one sample of each type to identify issues\n")

    # Test each type
    results = {}
    for sample_type in ["case_analysis", "educational", "client_interaction", "statutory_interpretation"]:
        sample = test_generate_sample_type(sample_type)
        results[sample_type] = sample

    # Summary
    print("\n" + "="*80)
    print("  RESULTS SUMMARY")
    print("="*80)

    success_count = sum(1 for s in results.values() if s is not None)
    print(f"\n✅ Successful: {success_count}/4")

    for sample_type, sample in results.items():
        if sample:
            print(f"  ✅ {sample_type}")
        else:
            print(f"  ❌ {sample_type} - FAILED")

    # Save successful samples
    if success_count > 0:
        print(f"\n💾 Saving {success_count} successful samples...")

        parquet_path = "train.parquet"
        df_existing = pl.read_parquet(parquet_path)

        # Filter to 7 required fields + sample_type
        required_fields = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]
        filtered_samples = []

        for sample in results.values():
            if sample:
                filtered_sample = {k: v for k, v in sample.items() if k in required_fields}
                if 'sample_type' in sample:
                    filtered_sample['sample_type'] = sample['sample_type']
                filtered_samples.append(filtered_sample)

        df_new = pl.DataFrame(filtered_samples)
        df_combined = pl.concat([df_existing, df_new])
        df_combined.write_parquet(parquet_path, compression="zstd", statistics=True, use_pyarrow=False)

        print(f"✅ Saved to {parquet_path}")
        print(f"📊 Total: {len(df_combined)} samples")

if __name__ == "__main__":
    main()
