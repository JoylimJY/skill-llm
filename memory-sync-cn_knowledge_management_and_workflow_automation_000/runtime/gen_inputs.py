#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# Create directory structure
dirs = [
    "research/neuroscience/papers",
    "research/neuroscience/notes",
    "research/ml/experiments",
    "research/ml/results",
    "memory/2026-01-15",
    "memory/2026-02-01",
    "memory/2026-02-18",
    "scripts",
    "config",
    "reports",
    "data/raw",
    "data/processed",
    "archive/2025",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "research/neuroscience/papers/hippocampus_study.txt": "Study on hippocampus memory consolidation. N=120, p<0.05.",
    "research/neuroscience/papers/ltm_review.txt": "Long-term memory review. Various encoding mechanisms discussed.",
    "research/neuroscience/notes/experiment_notes.txt": "Day 12: Subjects showed improved recall after sleep consolidation.",
    "research/ml/experiments/run_001.json": json.dumps({"experiment": "baseline", "accuracy": 0.87, "loss": 0.34}),
    "research/ml/experiments/run_002.json": json.dumps({"experiment": "with_forgetting", "accuracy": 0.91, "loss": 0.28}),
    "research/ml/results/summary.csv": "experiment,accuracy\nbaseline,0.87\nwith_forgetting,0.91",
    "memory/2026-01-15/notes.md": "# Jan 15\n- Reviewed Ebbinghaus forgetting curve paper\n- Key finding: spaced repetition improves recall by 40%",
    "memory/2026-02-01/notes.md": "# Feb 01\n- Team meeting: decided to use CortexGraph for knowledge management\n- Action items: configure storage, test API",
    "memory/2026-02-18/notes.md": "# Feb 18\n- Paper accepted at NeurIPS\n- New dataset available: 50k samples",
    "data/raw/survey_responses.txt": "Q1: Memory systems are important\nQ2: Automation would save 3 hours/week",
    "data/processed/cleaned_responses.json": json.dumps({"total": 45, "positive": 38, "negative": 7}),
    "archive/2025/old_notes.txt": "2025 archive - not relevant to current project",
    "config/README_placeholder.txt": "Config directory - do not delete",
}

for path, content in distractor_files.items():
    filepath = workspace / path
    filepath.write_text(content)

# The actual task input: a list of research findings to be ingested into the memory system
# These are provided as a structured JSON file the agent must read and process
research_findings = [
    {
        "id": "finding_001",
        "content": "CRITICAL: Our novel attention mechanism reduces transformer inference latency by 47% on standard NLP benchmarks. Patent filing in progress.",
        "tags": ["attention", "transformer", "performance", "patent"],
        "entities": ["AttentionMechanism", "TransformerModel"],
        "importance": "critical"  # agent must map this to strength=2.0
    },
    {
        "id": "finding_002",
        "content": "Team prefers async standups over synchronous meetings. Productivity increased 23% after switching. This is a permanent team policy.",
        "tags": ["team", "policy", "productivity"],
        "entities": ["TeamPolicy", "AsyncCommunication"],
        "importance": "high"  # agent must map this to strength=1.5
    },
    {
        "id": "finding_003",
        "content": "Today's lunch discussion: someone mentioned trying a new Python profiling tool called py-spy.",
        "tags": ["casual", "tools"],
        "entities": ["py-spy"],
        "importance": "temporary"  # agent must map this to strength=0.5
    },
    {
        "id": "finding_004",
        "content": "Dataset preprocessing pipeline uses median imputation for missing values in sensor readings.",
        "tags": ["data", "preprocessing", "pipeline"],
        "entities": ["PreprocessingPipeline", "SensorData"],
        "importance": "normal"  # agent must map this to strength=1.0
    },
    {
        "id": "finding_005",
        "content": "Key architectural decision: microservices over monolith for the inference server. Documented in ADR-007.",
        "tags": ["architecture", "decision", "microservices", "ADR"],
        "entities": ["InferenceServer", "ADR007", "Microservices"],
        "importance": "critical"  # agent must map this to strength=2.0
    },
]

findings_path = workspace / "data" / "research_findings.json"
findings_path.write_text(json.dumps(research_findings, indent=2))

# A partially filled maintenance log to give context
maintenance_log = """# Knowledge Base Maintenance Log

## Previous Runs
- 2026-01-10: Initial setup, 12 memories imported
- 2026-01-17: GC run, 3 memories pruned
- 2026-02-01: 8 new memories added

## Pending Tasks
- Import new research findings from data/research_findings.json
- Run full maintenance cycle (GC, consolidate, promote)
- Save maintenance report to reports/maintenance_report.json
"""
(workspace / "config" / "maintenance_log.md").write_text(maintenance_log)

# Scripts directory - sync scripts exist as per SKILL.md
(workspace / "scripts" / "sync-memory.sh").write_text("#!/bin/bash\necho 'sync-memory placeholder'\n")
(workspace / "scripts" / "sync-daily.sh").write_text("#!/bin/bash\necho 'sync-daily placeholder'\n")
os.chmod(workspace / "scripts" / "sync-memory.sh", 0o755)
os.chmod(workspace / "scripts" / "sync-daily.sh", 0o755)

# mcporter config directory (required by the skill)
mcporter_config_dir = Path.home() / ".openclaw" / "workspace" / "config"
mcporter_config_dir.mkdir(parents=True, exist_ok=True)

print("Workspace generated successfully.")
print(f"Research findings: {findings_path}")