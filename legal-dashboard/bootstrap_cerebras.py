#!/usr/bin/env python3
"""
Bootstrap with Cerebras - Generate seed samples using Cerebras provider.
Uses the champion model (gpt-oss-120b) for high quality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.generation_service import GenerationService
import polars as pl
import json

def generate_sample(service, sample_type, topic_info, difficulty, counter):
    """Generate a single sample with Cerebras"""
    practice_area, topic = topic_info

    print(f"  [{counter}] {practice_area} - {topic} ({difficulty}, {sample_type})...", end=" ", flush=True)

    sample, tokens, elapsed, error = service.generate_single_sample(
        practice_area=practice_area,
        topic=topic,
        difficulty=difficulty,
        counter=counter,
        provider="cerebras",  # Use Cerebras instead of Groq
        model="gpt-oss-120b",  # Champion model
        sample_type=sample_type
    )

    if error:
        print(f"❌ {error[:80]}")
        return None

    print(f"✅ ({tokens} tokens, {elapsed:.1f}s)")
    return sample

def main():
    print("="*80)
    print("  BOOTSTRAP WITH CEREBRAS")
    print("="*80)
    print("\nUsing Cerebras gpt-oss-120b (champion model) for high-quality samples")
    print("Target: 2-3 samples per type to test the system\n")

    parquet_path = "train.parquet"

    # Load existing dataset
    df_existing = pl.read_parquet(parquet_path)
    print(f"📂 Loaded dataset: {len(df_existing)} samples")

    # Check sample_type distribution
    if 'sample_type' in df_existing.columns:
        type_counts = df_existing.group_by('sample_type').len().to_dicts()
        print("\n📊 Current distribution:")
        for tc in sorted(type_counts, key=lambda x: x['sample_type']):
            print(f"   - {tc['sample_type']}: {tc['len']} samples")
    else:
        print("\n⚠️  No sample_type column found! Run migrate_add_sample_type.py first")
        sys.exit(1)

    service = GenerationService()

    # Define topics for diversity
    topics = [
        ("Contract Law", "Formation of Contracts"),
        ("Company Law", "Directors Duties"),
        ("Employment Law", "Discrimination"),
    ]

    difficulties = ["intermediate", "advanced", "basic"]

    # Generate samples for each type
    all_samples = []
    sample_types_to_generate = [
        "case_analysis",
        "educational",
        "client_interaction",
        "statutory_interpretation"
    ]

    for sample_type in sample_types_to_generate:
        print(f"\n{'='*80}")
        print(f"  Generating {sample_type} samples")
        print('='*80)

        # Generate 2-3 samples per type
        for i in range(min(3, len(topics))):
            sample = generate_sample(
                service=service,
                sample_type=sample_type,
                topic_info=topics[i],
                difficulty=difficulties[i % len(difficulties)],
                counter=len(all_samples) + 1
            )

            if sample:
                all_samples.append(sample)

    # Summary
    print(f"\n{'='*80}")
    print("  GENERATION SUMMARY")
    print('='*80)

    print(f"\n✅ Successfully generated: {len(all_samples)} samples")

    # Show distribution
    type_dist = {}
    for sample in all_samples:
        stype = sample.get('sample_type', 'unknown')
        type_dist[stype] = type_dist.get(stype, 0) + 1

    print("\n📊 Generated distribution:")
    for stype in sorted(type_dist.keys()):
        print(f"   - {stype}: {type_dist[stype]} samples")

    if not all_samples:
        print("\n❌ No samples generated! Check errors above")
        sys.exit(1)

    # Save to parquet
    print(f"\n💾 Saving {len(all_samples)} new samples...")

    # Keep only the 8 fields (7 required + sample_type)
    required_fields = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning", "sample_type"]
    filtered_samples = []

    for sample in all_samples:
        filtered_sample = {k: v for k, v in sample.items() if k in required_fields}
        # Ensure sample_type exists
        if 'sample_type' not in filtered_sample:
            filtered_sample['sample_type'] = 'case_analysis'  # fallback
        filtered_samples.append(filtered_sample)

    df_new = pl.DataFrame(filtered_samples)
    df_combined = pl.concat([df_existing, df_new])
    df_combined.write_parquet(parquet_path, compression="zstd", statistics=True, use_pyarrow=False)

    print(f"✅ Saved to {parquet_path}")
    print(f"📊 Total dataset: {len(df_combined)} samples")

    # Show final distribution
    final_type_counts = df_combined.group_by('sample_type').len().to_dicts()
    print("\n📊 Final distribution:")
    for tc in sorted(final_type_counts, key=lambda x: x['sample_type']):
        print(f"   - {tc['sample_type']}: {tc['len']} samples")

    print("\n🎉 Bootstrap complete!")
    print("   Next step: Review samples and push to HuggingFace")

if __name__ == "__main__":
    main()
