#!/usr/bin/env python3
"""
Bootstrap script to generate initial samples for new sample types.
This creates high-quality seed samples that can be used to train the model.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.generation_service import GenerationService
import polars as pl
import json

def generate_seed_samples_for_type(sample_type, count=20):
    """
    Generate seed samples for a specific sample type.
    Uses case_analysis as a fallback if generation fails.
    """
    print(f"\n🌱 Bootstrapping {count} {sample_type} samples...")

    service = GenerationService()
    successful_samples = []
    failed_count = 0

    topics = [
        ("Contract Law", "Formation of Contracts"),
        ("Contract Law", "Breach of Contract"),
        ("Tort Law", "Professional Negligence"),
        ("Company Law", "Directors Duties"),
        ("Employment Law", "Discrimination"),
        ("Property Law", "Leasehold vs Freehold"),
        ("Criminal Law", "Actus Reus and Mens Rea"),
        ("Family Law", "Divorce Proceedings"),
        ("Tax Law", "Capital Gains Tax"),
        ("Administrative Law", "Judicial Review")
    ]

    difficulties = ["basic", "intermediate", "advanced", "expert"]

    for i in range(count):
        topic_idx = i % len(topics)
        practice_area, topic = topics[topic_idx]
        difficulty = difficulties[i % len(difficulties)]

        print(f"  [{i+1}/{count}] {practice_area} - {topic} ({difficulty})...", end=" ")

        # Try with requested sample_type first
        sample, tokens, elapsed, error = service.generate_single_sample(
            practice_area=practice_area,
            topic=topic,
            difficulty=difficulty,
            counter=i+1,
            provider="groq",
            model="llama-3.3-70b-versatile",
            sample_type=sample_type
        )

        if error:
            print(f"❌ {error[:50]}")
            failed_count += 1
            # Don't fallback - we want clean sample types
            continue

        successful_samples.append(sample)
        print(f"✅ ({tokens} tokens)")

    print(f"\n📊 Results: {len(successful_samples)} successful, {failed_count} failed")
    return successful_samples

def main():
    print("="*80)
    print("  SAMPLE TYPE BOOTSTRAPPING")
    print("="*80)
    print("\nThis script generates seed samples for new sample types.")
    print("Start with case_analysis (which already works) to build a foundation.\n")

    # Load existing dataset
    parquet_path = "train.parquet"
    if not os.path.exists(parquet_path):
        print(f"❌ Error: {parquet_path} not found!")
        print("   Please run this script from the legal-dashboard/ directory")
        sys.exit(1)

    df_existing = pl.read_parquet(parquet_path)
    print(f"📂 Loaded existing dataset: {len(df_existing)} samples")

    # Check for existing sample types
    if 'sample_type' in df_existing.columns:
        type_counts = df_existing.group_by('sample_type').len().to_dicts()
        print("\n📊 Current sample type distribution:")
        for tc in type_counts:
            print(f"   - {tc['sample_type']}: {tc['len']} samples")
    else:
        print("\n⚠️  No sample_type field in existing data (all are case_analysis by default)")

    # Generate samples for each type
    print("\n" + "="*80)
    print("  PHASE 1: Generate case_analysis samples (baseline)")
    print("="*80)

    case_analysis_samples = generate_seed_samples_for_type("case_analysis", count=10)

    print("\n" + "="*80)
    print("  PHASE 2: Generate educational samples")
    print("="*80)

    educational_samples = generate_seed_samples_for_type("educational", count=10)

    print("\n" + "="*80)
    print("  PHASE 3: Generate client_interaction samples")
    print("="*80)

    client_samples = generate_seed_samples_for_type("client_interaction", count=10)

    print("\n" + "="*80)
    print("  PHASE 4: Generate statutory_interpretation samples")
    print("="*80)

    statutory_samples = generate_seed_samples_for_type("statutory_interpretation", count=10)

    # Combine all samples
    all_new_samples = (
        case_analysis_samples +
        educational_samples +
        client_samples +
        statutory_samples
    )

    if not all_new_samples:
        print("\n❌ No samples generated successfully!")
        sys.exit(1)

    print("\n" + "="*80)
    print(f"  SAVING {len(all_new_samples)} NEW SAMPLES")
    print("="*80)

    # Filter to 7 required fields only
    required_fields = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]
    filtered_samples = []

    for sample in all_new_samples:
        # Keep required fields + sample_type
        filtered_sample = {k: v for k, v in sample.items() if k in required_fields}
        if 'sample_type' in sample:
            filtered_sample['sample_type'] = sample['sample_type']
        filtered_samples.append(filtered_sample)

    # Create dataframe and save
    df_new = pl.DataFrame(filtered_samples)
    df_combined = pl.concat([df_existing, df_new])
    df_combined.write_parquet(parquet_path, compression="zstd", statistics=True, use_pyarrow=False)

    print(f"\n✅ Saved {len(all_new_samples)} new samples to {parquet_path}")
    print(f"📊 Total dataset size: {len(df_combined)} samples")

    # Show final distribution
    if 'sample_type' in df_combined.columns:
        type_counts = df_combined.group_by('sample_type').len().to_dicts()
        print("\n📊 Final sample type distribution:")
        for tc in type_counts:
            print(f"   - {tc['sample_type']}: {tc['len']} samples")

    print("\n🎉 Bootstrapping complete!")
    print("   Next step: Push updated dataset to HuggingFace and re-train the model")

if __name__ == "__main__":
    main()
