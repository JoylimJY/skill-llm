#!/usr/bin/env python3
"""
Generate realistic, messy sandbox workspace for nb CLI evaluation task.
The agent must reorganize a knowledge base for a data science research team.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Distractor directory structure (research project workspace) ──────────────
dirs = [
    "research/papers/2024",
    "research/papers/2023",
    "research/experiments/nlp",
    "research/experiments/cv",
    "scripts/preprocessing",
    "scripts/training",
    "data/raw",
    "data/processed",
    "reports/weekly",
    "reports/monthly",
    "meetings/q1",
    "meetings/q2",
    "models/checkpoints",
    "configs/baseline",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "research/papers/2024/attention_is_all_you_need_notes.txt": "Transformer architecture notes. Multi-head attention, positional encoding.",
    "research/papers/2024/bert_fine_tuning_review.txt": "BERT fine-tuning strategies for downstream tasks.",
    "research/papers/2023/gpt_comparison.md": "# GPT Model Comparison\nParameters: 175B vs 70B vs 7B.",
    "research/experiments/nlp/run_001_results.csv": "epoch,loss,accuracy\n1,2.3,0.45\n2,1.8,0.61\n3,1.2,0.73",
    "research/experiments/cv/image_classification_log.txt": "ResNet50 baseline: 91.2% top-1 accuracy.",
    "scripts/preprocessing/tokenize.py": "# Tokenization script\nimport re\n\ndef tokenize(text): return text.split()",
    "scripts/training/train_loop.py": "# Training loop placeholder\nfor epoch in range(100): pass",
    "data/raw/dataset_manifest.json": json.dumps({"name": "ML-Bench-v2", "size": 50000, "split": {"train": 0.8, "val": 0.1, "test": 0.1}}),
    "data/processed/feature_stats.json": json.dumps({"mean": 0.003, "std": 1.021, "min": -4.5, "max": 4.7}),
    "reports/weekly/week_42_summary.md": "# Week 42\n- Ran baseline experiments\n- Fixed data pipeline bug",
    "reports/monthly/october_2024.md": "# October 2024\nProgress on NLP track. CV track stalled.",
    "meetings/q1/kickoff_agenda.txt": "1. Project scope\n2. Team roles\n3. Timeline",
    "meetings/q2/retrospective.txt": "What went well: data pipeline.\nWhat to improve: documentation.",
    "models/checkpoints/README_do_not_delete.txt": "Checkpoints stored on remote S3. Local cache only.",
    "configs/baseline/model_config.yaml": "model:\n  layers: 12\n  heads: 8\n  hidden_dim: 768",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── Task specification file ──────────────────────────────────────────────────
# This gives the agent the WHAT but not the HOW.
task_spec = """\
KNOWLEDGE BASE REORGANIZATION TASK
====================================

Our ML research team's knowledge base is scattered and needs to be reorganized.
Below are the exact operations that must be completed. After all operations,
a snapshot must be committed with a specific message.

STEP 1 – Create two new notebooks:
  - "ml-research" (for research notes and references)  
  - "project-tasks" (for action items and todos)

STEP 2 – Add the following notes to "ml-research" notebook:
  Note A:
    Title: "Transformer Architecture Deep Dive"
    Tags: transformers, attention, nlp
    Content: "Transformers use multi-head self-attention. Key components: Q, K, V matrices. Positional encoding handles sequence order. Feed-forward layers follow attention blocks."

  Note B:
    Title: "GPU Cluster Setup"
    Tags: infrastructure, setup
    Content: "Cluster has 8x A100 GPUs. CUDA 12.1, cuDNN 8.9. Use SLURM for job scheduling. Max wall time: 72h."

  Note C:
    Title: "Dataset Versioning Policy"
    Tags: data, governance, mlops
    Content: "All datasets must be versioned using DVC. Raw data never modified in place. Processed datasets tagged with pipeline version hash."

STEP 3 – Add the following todos to "project-tasks" notebook:
  Todo X: "Review transformer attention implementation" (with due date 2025-12-01)
  Todo Y: "Set up GPU cluster access for new team members"
  Todo Z: "Finalize dataset versioning documentation"

STEP 4 – Add a bookmark to "ml-research" notebook:
  URL: https://arxiv.org/abs/1706.03762
  Comment: "Original Attention Is All You Need paper"
  Tags: transformers, foundational

STEP 5 – Search within "ml-research" notebook for notes that contain BOTH
  the word "attention" AND the word "encoder" — record what you find (no action needed).
  Then also search for notes tagged "mlops" across ALL notebooks.

STEP 6 – Edit Note A in "ml-research":
  APPEND the following text to it (do NOT replace existing content):
  "Encoder stack: 6 layers. Decoder stack: 6 layers. d_model=512, d_ff=2048."

STEP 7 – Edit Note B in "ml-research":
  OVERWRITE its entire content with:
  "DEPRECATED: GPU cluster decommissioned. Use cloud provider instead."

STEP 8 – Mark Todo X ("Review transformer attention implementation") as DONE/completed.

STEP 9 – Create a git checkpoint in the "ml-research" notebook with the message:
  "Reorganized ML research knowledge base - initial snapshot"

Write a final summary of what was done to: /workspace/kb_reorganization_summary.txt
Include: the notebook names created, the IDs of all notes/todos created, the result
of the tag search for "mlops", and confirmation that the checkpoint was created.
"""

(workspace / "task_specification.txt").write_text(task_spec)

# ── Additional distractor: a fake "notes" directory to confuse agents ────────
fake_notes = workspace / "notes_backup_DO_NOT_USE"
fake_notes.mkdir(exist_ok=True)

fake_note_files = {
    "old_transformer_notes.md": "# Old Notes\nThese are stale notes from 2023. DO NOT USE.",
    "gpu_setup_v1.md": "# Old GPU Setup\nThis is outdated.",
    "todo_list_spreadsheet.csv": "task,done\nReview code,no\nWrite tests,no",
}
for fname, content in fake_note_files.items():
    (fake_notes / fname).write_text(content)

# ── A misleading config file ─────────────────────────────────────────────────
(workspace / ".nbconfig_FAKE").write_text("""\
# DO NOT USE THIS FILE
# This is NOT a valid nb configuration
nb_dir=/workspace/notes_backup_DO_NOT_USE
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")
print(f"Task specification: {workspace / 'task_specification.txt'}")