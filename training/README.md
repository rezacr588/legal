# Training Notebooks

This folder contains Jupyter notebooks for training and demonstrating LLMs on the legal dataset.

---

## 📓 Notebooks

### 1. training-cot-sft.ipynb
**Purpose**: Chain-of-Thought Supervised Fine-Tuning

**Description**:
- Fine-tune LLMs on legal Q&A dataset
- Uses chain-of-thought reasoning prompts
- Supports multiple training frameworks
- Includes evaluation metrics

**Requirements**:
```bash
pip install transformers datasets accelerate wandb
```

**Environment Variables**:
```bash
export HUGGINGFACE_TOKEN="your_token_here"
export WANDB_API_KEY="your_wandb_key_here"
```

**Usage**:
```bash
jupyter notebook training-cot-sft.ipynb
# or
jupyter lab training-cot-sft.ipynb
```

---

### 2. legal_assistant_demo.ipynb
**Purpose**: Legal Assistant Demonstration

**Description**:
- Interactive demo of trained legal assistant
- Query the dataset with natural language
- Test model responses
- Visualize results

**Requirements**:
```bash
pip install transformers torch pandas polars
```

**Usage**:
```bash
jupyter notebook legal_assistant_demo.ipynb
```

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install jupyter notebook
pip install transformers datasets accelerate wandb torch
pip install pandas polars matplotlib seaborn
```

### 2. Configure API Keys
```bash
# Add to ~/.zshrc or ~/.bashrc
export HUGGINGFACE_TOKEN="hf_..."
export WANDB_API_KEY="..."
```

### 3. Launch Jupyter
```bash
cd /Users/rezazeraat/Desktop/Data/training
jupyter notebook
```

### 4. Open a Notebook
- Navigate to http://localhost:8888
- Click on a notebook to open
- Run cells sequentially

---

## 📊 Dataset Access

Both notebooks access the legal training dataset:

### PostgreSQL Database (Recommended)
```python
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="legal_dashboard",
    user="legal_user",
    password="legal_pass"
)

df = pd.read_sql("SELECT * FROM samples", conn)
```

### API Access
```python
import requests

response = requests.get('http://localhost:5001/api/data')
samples = response.json()
```

### Direct Parquet (Legacy)
```python
import polars as pl

df = pl.read_parquet('../train.parquet')
```

---

## 🎯 Training Workflow

### 1. Data Preparation
- Load dataset from PostgreSQL or API
- Clean and validate samples
- Split into train/validation/test sets
- Tokenize and format for model

### 2. Model Selection
- Choose base model (e.g., Llama, Mistral, Phi)
- Configure model parameters
- Set training hyperparameters

### 3. Fine-Tuning
- Run training loop with chain-of-thought examples
- Monitor loss and metrics
- Save checkpoints

### 4. Evaluation
- Test on validation set
- Calculate metrics (accuracy, perplexity, etc.)
- Generate sample predictions

### 5. Deployment
- Save fine-tuned model
- Upload to HuggingFace Hub (optional)
- Deploy for inference

---

## 📝 Best Practices

### Training
- **Start small**: Test with 100-500 samples first
- **Monitor closely**: Watch for overfitting
- **Use validation**: Always evaluate on held-out data
- **Save checkpoints**: Don't lose progress
- **Log metrics**: Use W&B or TensorBoard

### Security
- **Never commit API keys**: Use environment variables
- **Use .gitignore**: Add `*.ipynb.bak`, `*-with-keys.ipynb`
- **Clean notebooks**: Remove keys before sharing
- **Use secrets**: Store sensitive data securely

### Performance
- **Use GPU**: Training is much faster with GPU
- **Batch size**: Adjust based on available memory
- **Mixed precision**: Use fp16 for faster training
- **Gradient accumulation**: Train larger batches with limited memory

---

## 🔧 Troubleshooting

### Kernel Crashes
```bash
# Increase Jupyter memory limit
jupyter notebook --NotebookApp.max_buffer_size=10000000000
```

### CUDA Out of Memory
- Reduce batch size
- Use gradient accumulation
- Enable gradient checkpointing
- Use smaller model

### API Connection Issues
```bash
# Check backend is running
curl http://localhost:5001/api/health

# Restart if needed
docker-compose restart backend
```

### Missing Dependencies
```bash
# Install all requirements
pip install -r ../backend/requirements.txt
pip install jupyter notebook ipywidgets
```

---

## 📚 Resources

### Documentation
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [Datasets Library](https://huggingface.co/docs/datasets)
- [W&B Documentation](https://docs.wandb.ai/)
- [PyTorch Documentation](https://pytorch.org/docs/)

### Tutorials
- [Fine-tuning LLMs](https://huggingface.co/docs/transformers/training)
- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)
- [SFT Best Practices](https://huggingface.co/blog/trl-peft)

### Models
- [Llama Models](https://huggingface.co/meta-llama)
- [Mistral Models](https://huggingface.co/mistralai)
- [Legal-specific Models](https://huggingface.co/models?search=legal)

---

## 🎓 Training Tips

### Data Quality
- Ensure all samples have proper reasoning chains
- Verify case citations are accurate
- Check for balanced difficulty distribution
- Remove duplicates

### Hyperparameters
- **Learning rate**: Start with 2e-5 for fine-tuning
- **Epochs**: 3-5 for supervised fine-tuning
- **Batch size**: 4-8 per GPU (adjust based on memory)
- **Max length**: 2048 tokens (adjust based on model)

### Evaluation Metrics
- **Perplexity**: Lower is better
- **Accuracy**: Task-specific metrics
- **Legal reasoning**: Manual review of sample outputs
- **Citation accuracy**: Verify case references

---

## ⚠️ Important Notes

### API Keys
- **NEVER commit notebooks with API keys**
- Use environment variables: `os.getenv('HUGGINGFACE_TOKEN')`
- Add backup files to `.gitignore`

### Dataset
- Use latest version from PostgreSQL (7,540+ samples)
- Check API for real-time data: http://localhost:5001/api/data
- Verify data quality before training

### Compute
- Training requires significant compute resources
- Use Google Colab or cloud GPU for faster training
- Monitor GPU memory usage

---

## 📞 Support

### Issues
- Backend not running: `docker-compose up -d`
- Database connection: Check PostgreSQL container
- API errors: See backend logs with `docker logs data-backend-1`

### Help
- See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for platform overview
- See [API_USAGE.md](../API_USAGE.md) for API reference
- Check [CLAUDE.md](../CLAUDE.md) for development guide

---

**Last Updated**: October 18, 2025
**Notebooks**: 2 (training-cot-sft.ipynb, legal_assistant_demo.ipynb)
**Dataset**: 7,540+ legal training samples
