#!/usr/bin/env python3
"""
Upload UK Legal Training Dataset to HuggingFace Hub

This script uploads the train.parquet dataset to HuggingFace Hub as a public dataset.
Requires huggingface_hub library and authentication.

Installation:
    pip install huggingface_hub

Usage:
    python upload_to_huggingface.py --repo-id "your-username/uk-legal-dataset" --token "your_hf_token"

    Or use environment variable:
    export HF_TOKEN="your_hf_token"
    python upload_to_huggingface.py --repo-id "your-username/uk-legal-dataset"
"""

import argparse
import os
import sys
from pathlib import Path
import polars as pl

try:
    from huggingface_hub import HfApi, create_repo, upload_file
except ImportError:
    print("Error: huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)


def validate_dataset(parquet_path):
    """Validate the dataset has required fields and format"""
    print("📊 Validating dataset...")

    if not Path(parquet_path).exists():
        print(f"❌ Dataset not found at {parquet_path}")
        return False

    try:
        df = pl.read_parquet(parquet_path)

        # Check required columns
        required_cols = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return False

        print(f"✅ Dataset valid: {len(df):,} samples, 7 columns")

        # Print summary statistics
        print(f"\n📈 Dataset Summary:")
        print(f"   Total Samples: {len(df):,}")
        print(f"   Unique Topics: {df['topic'].n_unique()}")
        print(f"   Difficulty Distribution:")
        for diff in ['basic', 'intermediate', 'advanced', 'expert']:
            count = df.filter(pl.col('difficulty') == diff).height
            pct = (count / len(df) * 100)
            print(f"      {diff.capitalize()}: {count:,} ({pct:.1f}%)")

        return True
    except Exception as e:
        print(f"❌ Error validating dataset: {e}")
        return False


def create_dataset_card(repo_id, total_samples, difficulty_dist):
    """Create a comprehensive README.md for the HuggingFace dataset"""

    username = repo_id.split('/')[0] if '/' in repo_id else 'unknown'
    dataset_name = repo_id.split('/')[-1]

    return f"""---
language:
- en
license: apache-2.0
size_categories:
- 1K<n<10K
task_categories:
- question-answering
- text-generation
pretty_name: UK Legal Training Dataset
tags:
- legal
- uk-law
- legal-qa
- training-data
- legal-reasoning
- case-law
---

# UK Legal Training Dataset

A comprehensive dataset of {total_samples:,} legal question-answer pairs covering UK law, designed for training and fine-tuning large language models for legal applications.

## Dataset Overview

This dataset contains high-quality legal Q&A samples spanning 42+ topics in UK law, including Contract Law, Tort Law, Company Law, Employment Law, Immigration Law, and more. Each sample includes:

- **Question**: Realistic legal scenarios requiring analysis
- **Answer**: Comprehensive responses with legal reasoning
- **Topic**: Practice area and subtopic classification
- **Difficulty**: Skill level (basic, intermediate, advanced, expert)
- **Case Citation**: References to real UK cases and statutes
- **Reasoning**: Step-by-step legal analysis (chain of thought)

### Key Features

- ✅ **{total_samples:,} curated samples** across 42+ UK legal topics
- ✅ **Multiple difficulty levels** for progressive learning
- ✅ **Real case citations** from UK jurisprudence
- ✅ **Structured reasoning** with step-by-step analysis
- ✅ **Authentic scenarios** reflecting real legal practice
- ✅ **Quality validated** samples with comprehensive answers

## Dataset Structure

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for each sample |
| `question` | string | Legal question or scenario |
| `answer` | string | Comprehensive answer with legal analysis |
| `topic` | string | Practice area and subtopic (e.g., "Contract Law - Formation") |
| `difficulty` | string | Complexity level: basic, intermediate, advanced, or expert |
| `case_citation` | string | References to relevant UK cases, statutes, or regulations |
| `reasoning` | string | Step-by-step breakdown of legal reasoning (chain of thought) |

### Data Splits

| Split | Samples |
|-------|---------|
| train | {total_samples:,} |

## Difficulty Distribution

{difficulty_dist}

## Topics Covered

### Core Practice Areas
- **Contract Law**: Formation, terms, breach, remedies, frustration
- **Tort Law**: Negligence, nuisance, defamation, occupiers' liability
- **Company Law**: Directors' duties, corporate governance, shareholder rights
- **Employment Law**: Contracts, discrimination, unfair dismissal, redundancy
- **Property Law**: Land law, leases, mortgages, easements
- **Criminal Law**: Offenses, defenses, sentencing, evidence
- **EU/Constitutional Law**: Human rights, judicial review, constitutional principles

### Specialized Areas
- Immigration Law, Family Law, Intellectual Property, Tax Law, Trusts & Estates
- Data Protection, Competition Law, Insolvency, Civil Procedure
- Legal Skills & Professional Ethics

## Sample Types

The dataset includes four distinct answer structures:

1. **Case Analysis** (IRAC): Issue, Rule, Application, Conclusion
2. **Educational**: Definition, legal basis, key elements, examples
3. **Client Interaction**: Practical advice with options and recommendations
4. **Statutory Interpretation**: Detailed analysis of legislation

## Usage Examples

### Load with Hugging Face Datasets

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("{repo_id}")

# Access samples
sample = dataset['train'][0]
print(sample['question'])
print(sample['answer'])
```

### Load with Polars (recommended for speed)

```python
import polars as pl

df = pl.read_parquet("hf://datasets/{repo_id}/train.parquet")
print(df.head())
```

### Load with Pandas

```python
import pandas as pd

df = pd.read_parquet("hf://datasets/{repo_id}/train.parquet")
print(df.head())
```

### Filter by Difficulty

```python
from datasets import load_dataset

dataset = load_dataset("{repo_id}")

# Get only advanced-level questions
advanced = dataset['train'].filter(lambda x: x['difficulty'] == 'advanced')
```

### Filter by Topic

```python
# Get only Contract Law samples
contract_law = dataset['train'].filter(lambda x: 'Contract Law' in x['topic'])
```

## Use Cases

### Fine-Tuning LLMs
Train models to:
- Answer UK legal questions accurately
- Apply IRAC methodology to legal problems
- Reference appropriate case law and statutes
- Provide step-by-step legal reasoning

### Legal AI Applications
- Legal research assistants
- Client Q&A chatbots for law firms
- Legal education platforms
- Automated legal document analysis
- Legal reasoning evaluation benchmarks

### Research
- Study legal reasoning patterns
- Evaluate LLM performance on legal tasks
- Compare model outputs against expert analysis
- Benchmark legal AI systems

## Generation Process

Samples were generated using:
- **AI Providers**: Groq (Llama 3.3 70B, Llama 3.1 8B) and Cerebras (GPT-OSS-120B, Qwen 3)
- **Validation**: Multi-stage quality checks for reasoning depth, legal accuracy, and citation authenticity
- **Expert Review**: Samples follow UK legal standards and real case law
- **Diversity**: Balanced across difficulty levels and practice areas

## Data Quality Standards

Each sample meets these criteria:
- ✅ Realistic legal scenario or question
- ✅ Comprehensive answer (250-500+ words depending on difficulty)
- ✅ Valid UK case citations and statutory references
- ✅ Structured reasoning with 4-8 steps (difficulty-dependent)
- ✅ Legally accurate for UK jurisdiction
- ✅ Unique identifier with no duplicates

## Limitations

⚠️ **Important Disclaimers:**
- This dataset is for training and research purposes only
- Not a substitute for professional legal advice
- UK-specific content may not apply to other jurisdictions
- Generated content should be verified by qualified legal professionals
- Some complex legal nuances may be simplified
- Law changes over time - verify current legislation

## Citation

If you use this dataset in your research or applications, please cite:

```bibtex
@dataset{{uk_legal_dataset_2025,
  title={{UK Legal Training Dataset}},
  author={{{username}}},
  year={{2025}},
  publisher={{Hugging Face}},
  url={{https://huggingface.co/datasets/{repo_id}}}
}}
```

## License

Apache 2.0

This dataset is released under the Apache 2.0 license, allowing commercial and research use with attribution.

## Dataset Card Authors

- {username}

## Dataset Card Contact

For questions, issues, or contributions, please open an issue on the [dataset repository](https://huggingface.co/datasets/{repo_id}/discussions).

---

**Disclaimer**: This dataset contains AI-generated legal content for training purposes. It should not be used as a substitute for professional legal advice. Always consult qualified legal professionals for actual legal matters.
"""


def upload_to_huggingface(parquet_path, repo_id, token=None, private=False):
    """Upload the dataset to HuggingFace Hub"""

    # Validate dataset first
    if not validate_dataset(parquet_path):
        return False

    # Get token from environment if not provided
    if token is None:
        token = os.environ.get('HF_TOKEN')
        if token is None:
            print("❌ No HuggingFace token provided. Set HF_TOKEN environment variable or use --token")
            return False

    try:
        api = HfApi()

        # Get dataset stats for README
        df = pl.read_parquet(parquet_path)
        total_samples = len(df)

        # Calculate difficulty distribution
        diff_dist = []
        for diff in ['basic', 'intermediate', 'advanced', 'expert']:
            count = df.filter(pl.col('difficulty') == diff).height
            pct = (count / total_samples * 100)
            diff_dist.append(f"- **{diff.capitalize()}**: {count:,} samples ({pct:.1f}%)")
        difficulty_dist = '\n'.join(diff_dist)

        # Create repository
        print(f"\n📦 Creating repository: {repo_id}")
        try:
            create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                token=token,
                private=private,
                exist_ok=True
            )
            print(f"✅ Repository created/exists: https://huggingface.co/datasets/{repo_id}")
        except Exception as e:
            print(f"⚠️  Repository may already exist: {e}")

        # Upload parquet file
        print(f"\n⬆️  Uploading train.parquet...")
        upload_file(
            path_or_fileobj=parquet_path,
            path_in_repo="train.parquet",
            repo_id=repo_id,
            repo_type="dataset",
            token=token
        )
        print(f"✅ Parquet file uploaded")

        # Create and upload README
        print(f"\n📝 Creating dataset card (README.md)...")
        readme_content = create_dataset_card(repo_id, total_samples, difficulty_dist)
        readme_path = Path("README_temp.md")
        readme_path.write_text(readme_content)

        upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            token=token
        )
        readme_path.unlink()  # Clean up temp file
        print(f"✅ Dataset card uploaded")

        print(f"\n🎉 Success! Dataset published at:")
        print(f"   https://huggingface.co/datasets/{repo_id}")
        print(f"\n💡 Usage:")
        print(f"   from datasets import load_dataset")
        print(f"   dataset = load_dataset('{repo_id}')")

        return True

    except Exception as e:
        print(f"❌ Error uploading to HuggingFace: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Upload UK Legal Training Dataset to HuggingFace Hub',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload with token from environment variable (HF_TOKEN)
  python upload_to_huggingface.py --repo-id "username/uk-legal-dataset"

  # Upload with explicit token
  python upload_to_huggingface.py --repo-id "username/uk-legal-dataset" --token "hf_xxxxx"

  # Upload as private dataset
  python upload_to_huggingface.py --repo-id "username/uk-legal-dataset" --private

  # Specify custom parquet file location
  python upload_to_huggingface.py --repo-id "username/uk-legal-dataset" --file "legal-dashboard/train.parquet"
        """
    )

    parser.add_argument(
        '--repo-id',
        type=str,
        required=True,
        help='HuggingFace repository ID (format: username/dataset-name)'
    )

    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='HuggingFace API token (or set HF_TOKEN env var)'
    )

    parser.add_argument(
        '--file',
        type=str,
        default='train.parquet',
        help='Path to parquet file (default: train.parquet)'
    )

    parser.add_argument(
        '--private',
        action='store_true',
        help='Create private dataset (default: public)'
    )

    args = parser.parse_args()

    print("🚀 UK Legal Dataset → HuggingFace Hub")
    print("=" * 50)

    success = upload_to_huggingface(
        parquet_path=args.file,
        repo_id=args.repo_id,
        token=args.token,
        private=args.private
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
