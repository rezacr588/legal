#!/usr/bin/env python3
"""
Migration script to add sample_type column to existing dataset.
All existing samples default to 'case_analysis'.
"""

import polars as pl

def main():
    print("="*80)
    print("  DATASET MIGRATION: Add sample_type Column")
    print("="*80)

    parquet_path = "train.parquet"

    # Load existing dataset
    df = pl.read_parquet(parquet_path)
    print(f"\n📂 Loaded dataset: {len(df)} samples")
    print(f"   Columns: {df.columns}")

    # Check if sample_type already exists
    if 'sample_type' in df.columns:
        print("\n✅ sample_type column already exists!")

        # Show distribution
        type_counts = df.group_by('sample_type').len().to_dicts()
        print("\n📊 Current distribution:")
        for tc in type_counts:
            print(f"   - {tc['sample_type']}: {tc['len']} samples")
        return

    # Add sample_type column (default to 'case_analysis' for all existing samples)
    print("\n🔄 Adding sample_type column...")
    df = df.with_columns([
        pl.lit("case_analysis").alias("sample_type")
    ])

    print(f"   New columns: {df.columns}")

    # Save back to parquet
    print(f"\n💾 Saving updated dataset...")
    df.write_parquet(parquet_path, compression="zstd", statistics=True, use_pyarrow=False)

    print(f"✅ Migration complete!")
    print(f"   All {len(df)} existing samples now have sample_type='case_analysis'")
    print(f"   Ready to add samples with other sample types")

if __name__ == "__main__":
    main()
