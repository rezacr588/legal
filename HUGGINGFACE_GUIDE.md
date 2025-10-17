# HuggingFace Dataset Upload Guide

This guide explains how to upload the UK Legal Training Dataset to HuggingFace Hub.

## Quick Start

### 1. Install Dependencies

```bash
pip install huggingface_hub
```

### 2. Get Your HuggingFace Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "uk-legal-dataset")
4. Select "Write" permission
5. Copy the token (starts with `hf_...`)

### 3. Upload the Dataset

```bash
# Set your token
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxx"

# Upload to HuggingFace (change username to yours!)
python3 upload_to_huggingface.py --repo-id "your-username/uk-legal-dataset"
```

## Dataset Information

**Current Dataset Stats:**
- **5,140 samples** (as of 2025-10-11)
- **7 fields**: id, question, answer, topic, difficulty, case_citation, reasoning
- **42+ UK legal topics** across practice areas
- **4 difficulty levels**: basic, intermediate, advanced, expert
- **Real case citations** from UK jurisprudence

## Upload Script Usage

### Basic Upload (Public Dataset)

```bash
# Public dataset (recommended)
python3 upload_to_huggingface.py --repo-id "username/uk-legal-dataset"
```

### Private Dataset

```bash
# Private dataset (only you can see it)
python3 upload_to_huggingface.py --repo-id "username/uk-legal-dataset" --private
```

### Custom File Location

```bash
# If train.parquet is in a different location
python3 upload_to_huggingface.py \
  --repo-id "username/uk-legal-dataset" \
  --file "legal-dashboard/train.parquet"
```

### With Inline Token (Not Recommended)

```bash
# Not recommended - token visible in command history
python3 upload_to_huggingface.py \
  --repo-id "username/uk-legal-dataset" \
  --token "hf_xxxxx"
```

## What Gets Uploaded

The script uploads:

1. **train.parquet** - The full dataset in Apache Parquet format
2. **README.md** - Comprehensive dataset card with:
   - Dataset overview and statistics
   - Field descriptions
   - Usage examples (Python, Pandas, Polars)
   - Difficulty distribution
   - Topic coverage
   - Use cases
   - Limitations and disclaimers
   - Citation information

## After Upload

Once uploaded, your dataset will be available at:
```
https://huggingface.co/datasets/your-username/uk-legal-dataset
```

### Using the Dataset

Anyone can load your public dataset:

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("your-username/uk-legal-dataset")

# Access samples
sample = dataset['train'][0]
print(sample['question'])
print(sample['answer'])
```

Or with Polars (faster):

```python
import polars as pl

df = pl.read_parquet("hf://datasets/your-username/uk-legal-dataset/train.parquet")
print(df.head())
```

## UI Button

The dashboard includes a **🤗 HuggingFace** button in the Dataset tab that links directly to:
```
https://huggingface.co/datasets/rezazerait/uk-legal-training-data
```

**To update the URL:**
1. Edit `src/components/Dataset.jsx`
2. Find line ~497: `window.open('https://huggingface.co/datasets/...')`
3. Replace with your HuggingFace dataset URL
4. Changes appear instantly with hot-reload

## Updating the Dataset

To update an existing dataset:

1. Make changes to your local `train.parquet`
2. Run the upload script again:
   ```bash
   python3 upload_to_huggingface.py --repo-id "your-username/uk-legal-dataset"
   ```
3. The script will overwrite the old files with new ones

## Dataset Card (README.md)

The auto-generated dataset card includes:

- **Statistics**: Total samples, difficulty distribution, topic coverage
- **Schema**: Detailed field descriptions with examples
- **Usage Examples**: Code snippets for loading the dataset
- **Use Cases**: Fine-tuning LLMs, legal AI applications, research
- **Quality Standards**: What makes a valid sample
- **Limitations**: Important disclaimers about AI-generated content
- **Citation**: BibTeX format for academic papers
- **License**: Apache 2.0

## Troubleshooting

### Error: "huggingface_hub not installed"

```bash
pip install huggingface_hub
```

### Error: "No HuggingFace token provided"

Set your token:
```bash
export HF_TOKEN="hf_xxxxx"
```

Or pass it inline:
```bash
python3 upload_to_huggingface.py --repo-id "username/dataset" --token "hf_xxxxx"
```

### Error: "Dataset not found at train.parquet"

Specify the correct path:
```bash
python3 upload_to_huggingface.py \
  --repo-id "username/dataset" \
  --file "legal-dashboard/train.parquet"
```

### Error: "Repository already exists"

This is normal! The script will:
- Use the existing repository
- Overwrite old files with new ones
- Update the dataset card

### Error: "Missing required columns"

Make sure your parquet file has all 7 required fields:
- id
- question
- answer
- topic
- difficulty
- case_citation
- reasoning

## Best Practices

### 1. Dataset Naming

Good names:
- `uk-legal-training-data`
- `uk-law-qa-dataset`
- `legal-reasoning-uk`

Avoid:
- Generic names like `dataset` or `data`
- Names with special characters or spaces
- Extremely long names

### 2. Repository Description

When creating the repository, add a clear description:
```
UK Legal Training Dataset - 5,000+ Q&A pairs for training legal AI models on UK law with case citations and reasoning
```

### 3. Public vs Private

**Public** (recommended):
- ✅ Anyone can use your dataset
- ✅ Gets indexed by search engines
- ✅ Can be cited in papers
- ✅ Contributes to the community

**Private**:
- ✅ Only you can see it
- ❌ Others can't use it
- ❌ Can't be cited easily
- Use for: work-in-progress, proprietary data

### 4. Updating the Dataset

Update whenever you:
- Add significant new samples (100+ samples)
- Fix quality issues (citations, reasoning)
- Change the schema or structure
- Reach major milestones (5,000, 10,000 samples)

### 5. Version Control

HuggingFace automatically tracks versions, but you should:
- Keep local backups of `train.parquet`
- Document major changes in commit messages
- Tag important versions (v1.0, v2.0, etc.)

## Example Session

Here's a complete example of uploading your dataset:

```bash
# 1. Install dependencies
pip install huggingface_hub

# 2. Set your token
export HF_TOKEN="hf_abcdefghijklmnopqrstuvwxyz123456"

# 3. Validate the dataset first
python3 -c "import polars as pl; df = pl.read_parquet('train.parquet'); print(f'{len(df)} samples, {len(df.columns)} columns')"

# Output: 5140 samples, 7 columns

# 4. Upload to HuggingFace
python3 upload_to_huggingface.py --repo-id "johndoe/uk-legal-dataset"

# Output:
# 📊 Validating dataset...
# ✅ Dataset valid: 5,140 samples, 7 columns
#
# 📈 Dataset Summary:
#    Total Samples: 5,140
#    Unique Topics: 87
#    Difficulty Distribution:
#       Basic: 1,234 (24.0%)
#       Intermediate: 1,567 (30.5%)
#       Advanced: 1,789 (34.8%)
#       Expert: 550 (10.7%)
#
# 📦 Creating repository: johndoe/uk-legal-dataset
# ✅ Repository created/exists: https://huggingface.co/datasets/johndoe/uk-legal-dataset
#
# ⬆️  Uploading train.parquet...
# ✅ Parquet file uploaded
#
# 📝 Creating dataset card (README.md)...
# ✅ Dataset card uploaded
#
# 🎉 Success! Dataset published at:
#    https://huggingface.co/datasets/johndoe/uk-legal-dataset
#
# 💡 Usage:
#    from datasets import load_dataset
#    dataset = load_dataset('johndoe/uk-legal-dataset')
```

## Additional Resources

- **HuggingFace Docs**: https://huggingface.co/docs/datasets
- **Creating Datasets**: https://huggingface.co/docs/datasets/create_dataset
- **Dataset Cards**: https://huggingface.co/docs/hub/datasets-cards
- **Access Tokens**: https://huggingface.co/settings/tokens

## Support

For issues with:
- **Upload script**: Check this guide or edit `upload_to_huggingface.py`
- **HuggingFace platform**: Visit https://huggingface.co/docs
- **Dataset quality**: Use the dashboard to review and edit samples

## License

The upload script and documentation are part of the UK Legal Training Dataset project, released under Apache 2.0 license.
