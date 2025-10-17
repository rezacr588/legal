#!/usr/bin/env python3
"""
Remove extra columns from train.parquet, keeping only essential columns.
"""
import polars as pl
from pathlib import Path

PARQUET_PATH = Path("train.parquet")
KEEP_COLUMNS = ["id", "question", "answer", "topic", "difficulty", "case_citation", "reasoning"]

def main():
    print(f"Reading {PARQUET_PATH}...")
    df = pl.read_parquet(PARQUET_PATH)

    print(f"Original columns: {df.columns}")
    print(f"Original shape: {df.shape}")

    # Keep only essential columns
    df_clean = df.select(KEEP_COLUMNS)

    print(f"\nNew columns: {df_clean.columns}")
    print(f"New shape: {df_clean.shape}")

    # Save back to same file
    df_clean.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

    print(f"\n✅ Saved cleaned parquet to {PARQUET_PATH}")
    print(f"Removed {len(df.columns) - len(KEEP_COLUMNS)} columns")

if __name__ == "__main__":
    main()
