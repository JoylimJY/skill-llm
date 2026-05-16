#!/usr/bin/env python3
"""
Generate the sandbox workspace for the beads task.
Creates a realistic ML pipeline project directory with distractor files,
but NO beads tracker initialized yet (agent must do that).
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── 1. Create a realistic ML project directory structure ────────────────────
dirs = [
    "src/pipeline",
    "src/models",
    "src/preprocessing",
    "src/evaluation",
    "src/utils",
    "config/envs",
    "config/schemas",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "notebooks",
    "scripts/deploy",
    "scripts/monitoring",
    "docs/architecture",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor source files ───────────────────────────────────────────────
files = {
    "src/pipeline/ingest.py": '''\
"""Data ingestion module."""
import pathlib

def load_raw(path: str):
    return pathlib.Path(path).read_bytes()
''',
    "src/pipeline/transform.py": '''\
"""Feature transformation."""

def normalize(x):
    return (x - x.mean()) / x.std()
''',
    "src/models/trainer.py": '''\
"""Model training stub."""

class Trainer:
    def __init__(self, config):
        self.config = config

    def fit(self, X, y):
        raise NotImplementedError
''',
    "src/models/evaluator.py": '''\
"""Evaluation metrics."""

def accuracy(preds, labels):
    return sum(p == l for p, l in zip(preds, labels)) / len(labels)
''',
    "src/preprocessing/cleaner.py": '''\
"""Data cleaning utilities."""

def drop_nulls(df):
    return df.dropna()
''',
    "src/evaluation/report.py": '''\
"""Report generation."""

def generate_report(metrics: dict) -> str:
    return "\\n".join(f"{k}: {v}" for k, v in metrics.items())
''',
    "src/utils/logger.py": '''\
"""Logging setup."""
import logging

def get_logger(name):
    return logging.getLogger(name)
''',
    "src/utils/config_loader.py": '''\
"""Config loader."""
import json

def load(path):
    with open(path) as f:
        return json.load(f)
''',
    "config/envs/staging.yaml": '''\
environment: staging
model_version: "1.0.0"
batch_size: 128
learning_rate: 0.001
''',
    "config/envs/production.yaml": '''\
environment: production
model_version: "1.0.0"
batch_size: 256
learning_rate: 0.0005
''',
    "config/schemas/input_schema.json": json.dumps({
        "type": "object",
        "properties": {
            "features": {"type": "array", "items": {"type": "number"}},
            "label": {"type": "integer"}
        },
        "required": ["features", "label"]
    }, indent=2),
    "tests/unit/test_cleaner.py": '''\
from src.preprocessing.cleaner import drop_nulls

def test_drop_nulls():
    pass  # TODO
''',
    "tests/integration/test_pipeline.py": '''\
def test_end_to_end():
    pass  # TODO
''',
    "notebooks/exploration.ipynb": json.dumps({
        "nbformat": 4,
        "cells": [
            {"cell_type": "markdown", "source": ["# Exploration"], "metadata": {}}
        ],
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat_minor": 4
    }, indent=2),
    "scripts/deploy/deploy.sh": '''\
#!/bin/bash
echo "Deploying model..."
''',
    "scripts/monitoring/alert.py": '''\
"""Alert on drift."""

def check_drift(baseline, current, threshold=0.05):
    return abs(current - baseline) > threshold
''',
    "docs/architecture/overview.md": '''\
# ML Pipeline Architecture

## Components
- Ingest → Transform → Train → Evaluate → Deploy

## Dependencies
- Data storage: S3-compatible
- Compute: On-premise GPU cluster
''',
    "data/raw/.gitkeep": "",
    "data/processed/.gitkeep": "",
    "scripts/deploy/rollback.sh": '''\
#!/bin/bash
echo "Rolling back..."
''',
}

for rel_path, content in files.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── 3. A project brief (the business task description for the agent) ─────────
brief = """\
ML PIPELINE ROLLOUT — PROJECT BRIEF
====================================

Project: Falcon — GPU-accelerated training pipeline v2

Planned work items (to be tracked):

EPIC: "Falcon Pipeline Rollout" [CRITICAL priority]

  Phase 1 tasks (subtasks of the epic, in order):
    1. "Implement data ingestion module"       [P1, must be done before transform]
    2. "Implement feature transformation"      [P1, blocked by ingestion]
    3. "Train baseline model"                  [P1, blocked by transformation]

  Phase 2 tasks (subtasks of the epic):
    4. "Run evaluation suite"                  [P2, blocked by baseline model]
    5. "Write deployment runbook"              [P2, no blockers]

AGENT INSTRUCTIONS:
- Set up the issue tracker in this directory.
- Create the epic and all 5 subtasks with the correct priorities and blocking dependencies.
- Claim the first available (unblocked) task by assigning it to "agent-falcon" and marking it in_progress.
- Log a newly discovered bug: "Data loader crashes on empty CSV" [P0], discovered while working on the ingestion task.
- Close the ingestion task as complete (reason: "Implementation done").
- After closing ingestion, the transformation task should become unblocked.
- Export the final list of all issues to: task_snapshot.json
"""
(WORKSPACE / "PROJECT_BRIEF.txt").write_text(brief)

print(f"Workspace prepared at: {WORKSPACE}")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")