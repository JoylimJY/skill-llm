import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ---- Distractor files: simulate a messy inherited project ----
distractor_dirs = [
    "src/pipeline",
    "src/preprocessing",
    "src/models",
    "tests/unit",
    "tests/integration",
    "configs",
    "data/raw",
    "data/processed",
    "notebooks",
    "docs",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/pipeline/train.py": "# Training script placeholder\nimport torch\n\ndef train(): pass\n",
    "src/pipeline/evaluate.py": "# Evaluation script\ndef evaluate(model, data): return 0.95\n",
    "src/preprocessing/normalize.py": "# Normalization\ndef normalize(x): return x / x.max()\n",
    "src/models/resnet_variant.py": "# Custom ResNet\nclass ResNetVariant: pass\n",
    "tests/unit/test_normalize.py": "def test_normalize(): assert True\n",
    "tests/integration/test_pipeline.py": "def test_pipeline(): pass\n",
    "configs/base_config.yaml": "learning_rate: 0.001\nbatch_size: 32\nepochs: 50\n",
    "configs/experiment_v2.yaml": "learning_rate: 0.0005\nbatch_size: 64\nepochs: 100\n",
    "data/raw/samples.csv": "id,label\n1,positive\n2,negative\n3,positive\n",
    "data/processed/features.npy": "",  # empty binary placeholder
    "notebooks/eda.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
    "docs/architecture.md": "# Architecture\nSee slides for overview.\n",
}
for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content)

# ---- The messy handover notes ---- (the "raw input" the agent must process)
# This file is intentionally unstructured and contains mixed information
handover_notes = """\
PROJECT HANDOVER NOTES - BioML Pipeline Transfer
=================================================
From: Dr. Priya Nair (leaving 2024-11-15)
To: New engineer

RANDOM STUFF FROM MY HEAD:

** Things we decided **
- Switched from Adam to AdamW optimizer after noticing loss instability on epoch 30+. Validation loss dropped 12% after switch.
- Standardized all input tensors to float32 before feeding into model. Fixes NaN issues we kept hitting.
- Chose batch size 64 over 128 because GPU OOM errors on the v100 cluster.
- The base model is ResNet-50 pretrained on ImageNet. Do NOT use ResNet-101, too slow for our inference SLA.

** Stuff you still need to do **
- Migrate the data pipeline to use the new S3 bucket (bucket name: bioml-data-prod-2024)
- Write unit tests for the preprocessing normalize() function edge cases (zero arrays)
- Update experiment_v2.yaml with final hyperparameters from last week's run
- Investigate the memory leak in the DataLoader — it grows ~200MB/hour during long training runs
- Deploy model checkpoint v3.2.1 to the staging inference endpoint

** How things work around here (procedures) **
- To start a training run: first activate conda env `bioml`, then run `python src/pipeline/train.py --config configs/experiment_v2.yaml --seed 42`
- To evaluate a checkpoint: use `python src/pipeline/evaluate.py --checkpoint <path> --data data/processed/`
- DataLoader caching: set env var BIOML_CACHE_DIR=/scratch/cache before any training job to avoid /tmp filling up
- For cluster jobs: submit via `sbatch jobs/train_job.slurm`, NOT directly. Direct runs get killed by resource manager after 2h.

** Random observations **
- The normalize() function breaks on all-zero arrays (divide by zero). Priya forgot to fix this.
- Experiment v1 was a dead end, don't waste time on it.
- The staging endpoint URL changed last week: now https://staging-api.bioml-internal.net/v2/predict

TASKS THAT ARE ACTIVELY BEING WORKED ON RIGHT NOW:
- Priya is mid-way through writing the integration test for the full pipeline end-to-end

TASKS THAT ARE BLOCKED:
- Cannot upgrade PyTorch to 2.1 until cluster sysadmin (Jake) updates CUDA drivers. Waiting on Jake.

ALREADY FINISHED:
- ResNet-50 pretrained weights downloaded and verified (SHA256 matches)
- Base config YAML finalized and committed to git

That's mostly it. Good luck!
"""

(workspace / "HANDOVER_NOTES.txt").write_text(handover_notes)

# ---- A broken/partial QUEUE.md already exists (messy state) ----
broken_queue = """\
# Task Queue - BioML Project

## done
- download pretrained weights

## ready
- migrate data pipeline to new S3 bucket
- write unit tests for normalize() edge cases  
- update experiment_v2.yaml with final hyperparameters
- investigate DataLoader memory leak
- deploy model checkpoint v3.2.1 to staging

## currently working
- integration test for full pipeline (Priya)

## waiting
- upgrade PyTorch to 2.1 (blocked by Jake / CUDA drivers)
"""
# Note: state labels are WRONG (lowercase, non-standard) — agent must fix them

(workspace / "QUEUE.md").write_text(broken_queue)

# ---- SESSION-STATE.md does NOT exist (agent must create it via WAL before acting) ----
# ---- MEMORY.md does NOT exist ----
# ---- memory/ directory does NOT exist ----
# ---- skills/ directory does NOT exist ----

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")