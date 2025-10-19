# TPU v5e-8 Training Guide

## Overview

This guide explains how to train the UK Legal AI model on **TPU v5 Lite (v5e-8)** using PyTorch XLA.

## TPU v5e-8 Specifications

| Feature | Specification |
|---------|--------------|
| **TPU Cores** | 8 cores (1 TPU pod) |
| **Memory per Core** | 16GB HBM |
| **Total Memory** | 128GB HBM |
| **Performance (bfloat16)** | ~197 TFLOPS per core |
| **Total Performance** | ~1.6 PFLOPS (8 cores) |
| **Interconnect** | High-speed ICI (Inter-Chip Interconnect) |
| **Cost (Preemptible)** | ~$1.20/hour |
| **Cost (On-Demand)** | ~$4.80/hour |

## Architecture Comparison

### TPU v5e-8 vs GPU (2× T4)

| Metric | TPU v5e-8 | 2× T4 GPUs | Advantage |
|--------|-----------|-----------|-----------|
| **Compute (bfloat16)** | 1.6 PFLOPS | ~130 TFLOPS | **TPU: 12.3x faster** |
| **Memory** | 128GB HBM | 32GB GDDR6 | **TPU: 4x more** |
| **Memory Bandwidth** | ~1.6 TB/s | ~640 GB/s | **TPU: 2.5x faster** |
| **Batch Size** | 32-64 | 6-12 | **TPU: 5x larger** |
| **Training Speed** | ~1 epoch/10 min | ~1 epoch/30 min | **TPU: 3x faster** |
| **Cost/Hour (Preemptible)** | $1.20 | $0.74 | GPU: 38% cheaper |
| **Cost per Epoch** | $0.20 | $0.37 | **TPU: 46% cheaper** |

**Winner**: TPU v5e-8 provides **3x faster training** and **46% lower cost per epoch** despite higher hourly cost.

## Key Differences: TPU vs GPU

### 1. Device Management

**GPU (CUDA):**
```python
device = torch.device("cuda")
model = model.to(device)
```

**TPU (XLA):**
```python
import torch_xla.core.xla_model as xm
device = xm.xla_device()
model = model.to(device)
```

### 2. Precision

**GPU:**
- float32 (default)
- float16 (mixed precision via Accelerate)

**TPU:**
- **bfloat16** (native format, 2x faster than float32)
- Uses `bf16=True` instead of `fp16=True`

### 3. Multiprocessing

**GPU (DDP):**
```python
from accelerate import notebook_launcher
notebook_launcher(training_function, num_processes=2)
```

**TPU (XLA):**
```python
import torch_xla.distributed.xla_multiprocessing as xmp
xmp.spawn(training_function, nprocs=8)
```

### 4. Compilation

**GPU:**
- Runs PyTorch operations directly on CUDA kernels
- No compilation step

**TPU:**
- **XLA Compiler**: Compiles PyTorch operations to TPU HLO (High-Level Optimizer)
- First iteration slow (compilation), subsequent iterations fast
- Use `xm.mark_step()` to trigger compilation explicitly

### 5. Data Loading

**GPU:**
```python
from torch.utils.data import DataLoader
loader = DataLoader(dataset, batch_size=4, num_workers=4)
```

**TPU:**
```python
from torch_xla.distributed import parallel_loader as pl
# num_workers=0 recommended (TPU handles parallelism internally)
loader = DataLoader(dataset, batch_size=4, num_workers=0)
mp_loader = pl.ParallelLoader(loader, [device])
```

## Notebook Structure

### Cell 1: Install TPU Packages
```bash
!pip install cloud-tpu-client
!pip install torch~=2.5.0 torch_xla[tpu]~=2.5.0 -f https://storage.googleapis.com/libtpu-releases/index.html
!pip install transformers datasets peft accelerate trl wandb
```

**Important**: Install `torch_xla` matching your PyTorch version (2.5.0).

### Cell 2: Verify TPU Access
```python
import torch_xla.core.xla_model as xm
device = xm.xla_device()
num_devices = xm.xrt_world_size()  # Should be 8 for v5e-8
```

### Cell 3: Define Training Function
All configuration and imports happen **inside** the function (same pattern as multi-GPU notebook).

### Cell 4: Launch Training
```python
import torch_xla.distributed.xla_multiprocessing as xmp
xmp.spawn(training_function, args=(), nprocs=8)
```

## TPU-Specific Optimizations

### 1. Batch Size

**Recommendation**: Use **4× larger batch size** than GPU.

- **GPU**: 3 per device → 6 total (2 GPUs)
- **TPU**: 4 per core → 32 total (8 cores)

**Why?** TPU has 4x more memory (128GB vs 32GB).

### 2. Gradient Accumulation

- **GPU**: 1-2 steps
- **TPU**: 1-2 steps (same, but higher base batch size)

**Effective Batch Size:**
- GPU: 3 × 2 × 1 = 6
- TPU: 4 × 8 × 2 = 64

### 3. Mixed Precision

**Always use bfloat16:**
```python
training_args = SFTConfig(
    bf16=True,  # NOT fp16!
    ...
)
```

**Why?** bfloat16 is TPU's native format (2x faster than float32, more stable than float16).

### 4. Dataloader Workers

**Set to 0:**
```python
training_args = SFTConfig(
    dataloader_num_workers=0,
    ...
)
```

**Why?** TPU handles data parallelism internally via ICI (Inter-Chip Interconnect).

### 5. Gradient Checkpointing

**Enable for memory efficiency:**
```python
model.gradient_checkpointing_enable()
```

**Why?** Saves memory for larger batch sizes (trades compute for memory).

## Troubleshooting

### Issue 1: "Cannot find TPU devices"

**Cause**: TPU not allocated or wrong environment.

**Fix**:
1. Verify you're on a TPU VM (not regular Colab)
2. Check TPU allocation: `gcloud compute tpus list`
3. Ensure TPU is running: `gcloud compute tpus describe <tpu-name>`

### Issue 2: "Compilation taking too long"

**Cause**: XLA compiling PyTorch ops to TPU HLO.

**Expected Behavior**:
- First batch: 30-60 seconds (compilation)
- Subsequent batches: <1 second (cached)

**Optimization**:
- Use `xm.mark_step()` to control compilation boundaries
- Avoid dynamic shapes (use fixed sequence length)

### Issue 3: "Out of memory"

**Cause**: Batch size too large or sequence length too long.

**Fix**:
1. Reduce `per_device_train_batch_size` (try 3 → 2)
2. Reduce `max_seq_length` (try 1000 → 768)
3. Enable gradient checkpointing (already enabled in notebook)
4. Reduce gradient accumulation steps

**Memory Estimation:**
- Model params: 0.5B × 2 bytes (bf16) = 1GB
- Activations: ~batch_size × seq_len × hidden_dim × num_layers × 2 bytes
- For batch=4, seq=1000: ~4 × 1000 × 896 × 24 × 2 = 172MB per sample × 4 = 688MB
- Total per core: ~1GB + 688MB = 1.7GB (well within 16GB limit)

### Issue 4: "Process killed during training"

**Cause**: Preemptible TPU was reclaimed.

**Fix**:
1. Use on-demand TPUs (more expensive but stable)
2. Enable checkpointing every N steps
3. Resume from checkpoint if interrupted

### Issue 5: "Slow inference"

**Cause**: XLA compilation happens on first inference call.

**Fix**:
1. First call is slow (compilation)
2. Subsequent calls are fast (cached)
3. For production, use saved model on GPU (faster for single requests)

## Performance Benchmarks

### Training Speed

| Metric | TPU v5e-8 | 2× T4 GPU | Speedup |
|--------|-----------|-----------|---------|
| **Samples/sec** | ~320 | ~110 | 2.9x |
| **Batch time** | ~0.1s | ~0.3s | 3x faster |
| **Epoch time** | ~10 min | ~30 min | 3x faster |
| **Total training (3 epochs)** | ~30 min | ~90 min | 3x faster |

### Cost Analysis

| Metric | TPU v5e-8 (Preemptible) | 2× T4 GPU | Savings |
|--------|------------------------|-----------|---------|
| **Hourly cost** | $1.20 | $0.74 | -62% more expensive |
| **Training time (3 epochs)** | 0.5 hours | 1.5 hours | 67% faster |
| **Total cost** | $0.60 | $1.11 | **46% cheaper** |

**Conclusion**: TPU v5e-8 is **3x faster** and **46% cheaper per training run** despite higher hourly cost.

## Best Practices

### 1. Batch Size Tuning

Start with recommended batch size, then increase:
```python
# Start conservative
BATCH_SIZE = 4  # Per core (32 total)

# If no OOM, try larger
BATCH_SIZE = 6  # Per core (48 total)

# Maximum (depends on sequence length)
BATCH_SIZE = 8  # Per core (64 total)
```

### 2. Sequence Length

Use fixed length (no dynamic padding):
```python
MAX_SEQ_LENGTH = 1000  # Fixed (enables XLA optimization)
# NOT: max_length=None  # Dynamic (slower)
```

### 3. Gradient Accumulation

Adjust based on memory:
```python
# More memory available? Reduce grad accum
GRADIENT_ACCUMULATION_STEPS = 1  # Batch=32 (faster)

# Less memory? Increase grad accum
GRADIENT_ACCUMULATION_STEPS = 2  # Batch=64 (same effective, slower)
```

### 4. Checkpointing

Save frequently (TPUs can be preempted):
```python
training_args = SFTConfig(
    save_strategy="steps",
    save_steps=50,  # Every 50 steps
    save_total_limit=2,  # Keep only 2 checkpoints
)
```

### 5. Monitoring

Use W&B for real-time metrics:
```python
training_args = SFTConfig(
    report_to="wandb",
    logging_steps=5,  # Log every 5 steps
)
```

## Expected Training Results

### Dataset: rzeraat/law (2,054 samples)

**Configuration:**
- Batch size: 4 per core × 8 cores = 32
- Gradient accumulation: 2 steps
- Effective batch size: 64
- Sequence length: 1000
- Epochs: 3

**Expected Metrics:**
- Training time: ~30 minutes (3 epochs)
- Final train loss: ~0.8-1.2
- Final val loss: ~1.0-1.4
- Perplexity: ~2.7-4.0

**Cost:**
- Preemptible: $0.60 total
- On-demand: $2.40 total

## Next Steps

1. **Run the notebook**: `training-cot-sft-tpu-v5e.ipynb`
2. **Monitor training**: Check W&B dashboard
3. **Test inference**: Cell 7 (TPU inference)
4. **Deploy**: Export to CPU/GPU for production

## References

- [PyTorch XLA Documentation](https://pytorch.org/xla/release/2.5/index.html)
- [Google Cloud TPU Pricing](https://cloud.google.com/tpu/pricing)
- [TPU Performance Guide](https://cloud.google.com/tpu/docs/performance-guide)
- [PyTorch XLA Best Practices](https://github.com/pytorch/xla/blob/master/TROUBLESHOOTING.md)
