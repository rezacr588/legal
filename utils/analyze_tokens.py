#!/usr/bin/env python3
"""
Analyze token counts in the dataset and identify long samples.
"""
import polars as pl
from pathlib import Path
import tiktoken

PARQUET_PATH = Path("train.parquet")
MAX_TOKENS = 4000

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens using OpenAI's tiktoken."""
    if not text:
        return 0
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

def main():
    print(f"Reading {PARQUET_PATH}...")
    df = pl.read_parquet(PARQUET_PATH)

    print(f"Total samples: {len(df)}\n")

    # Analyze each row
    long_samples = []

    for idx, row in enumerate(df.iter_rows(named=True)):
        # Combine all text fields
        combined_text = (
            f"Question: {row['question']}\n"
            f"Answer: {row['answer']}\n"
            f"Reasoning: {row['reasoning']}\n"
            f"Topic: {row['topic']}\n"
            f"Case Citation: {row['case_citation']}"
        )

        token_count = count_tokens(combined_text)

        if token_count > MAX_TOKENS:
            long_samples.append({
                'index': idx,
                'id': row['id'],
                'token_count': token_count,
                'question_len': len(row['question'] or ''),
                'answer_len': len(row['answer'] or ''),
                'reasoning_len': len(row['reasoning'] or ''),
                'topic': row['topic'][:50] + '...' if len(row['topic'] or '') > 50 else row['topic']
            })

    print(f"Samples exceeding {MAX_TOKENS} tokens: {len(long_samples)}\n")

    if long_samples:
        print("Long samples details:")
        print("-" * 100)
        for sample in sorted(long_samples, key=lambda x: x['token_count'], reverse=True)[:10]:
            print(f"ID: {sample['id']}")
            print(f"  Tokens: {sample['token_count']} | Q: {sample['question_len']} | A: {sample['answer_len']} | R: {sample['reasoning_len']}")
            print(f"  Topic: {sample['topic']}")
            print()

    # Statistics
    all_tokens = []
    for row in df.iter_rows(named=True):
        combined = f"{row['question']} {row['answer']} {row['reasoning']}"
        all_tokens.append(count_tokens(combined))

    print(f"\nToken Statistics:")
    print(f"  Max tokens: {max(all_tokens)}")
    print(f"  Min tokens: {min(all_tokens)}")
    print(f"  Average tokens: {sum(all_tokens) / len(all_tokens):.2f}")
    print(f"  Samples > 4000 tokens: {len(long_samples)}")
    print(f"  Samples > 3000 tokens: {sum(1 for t in all_tokens if t > 3000)}")
    print(f"  Samples > 2000 tokens: {sum(1 for t in all_tokens if t > 2000)}")

if __name__ == "__main__":
    main()
