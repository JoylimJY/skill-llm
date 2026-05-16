#!/usr/bin/env python3
"""
Generate sandbox workspace for the LanceDB memory management task.
"""
import os
import json
import csv
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Create deep directory structure with distractor files ──────────────────────

dirs = [
    "lab/experiments/q1_2024",
    "lab/experiments/q2_2024",
    "lab/meetings/weekly",
    "lab/meetings/reviews",
    "lab/publications/drafts",
    "lab/publications/submitted",
    "lab/personnel",
    "lab/resources/datasets",
    "lab/resources/code_snippets",
    "archive/2023",
    "archive/2022",
    "tools/scripts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files that look relevant but must NOT be processed
distractors = {
    "lab/experiments/q1_2024/raw_readings.csv": (
        "timestamp,sensor,value\n"
        "2024-01-15,temp,22.3\n"
        "2024-01-16,temp,22.8\n"
        "2024-01-17,pressure,1013.2\n"
    ),
    "lab/experiments/q2_2024/failed_runs.txt": (
        "Run 42: segfault at epoch 3\n"
        "Run 43: OOM error\n"
        "Run 44: converged but accuracy 0.12\n"
    ),
    "lab/meetings/weekly/template.docx.txt": (
        "MEETING TEMPLATE - DO NOT USE AS DATA SOURCE\n"
        "Agenda: ...\nNotes: ...\nAction items: ...\n"
    ),
    "lab/publications/drafts/outline.md": (
        "# Draft Outline\n## Introduction\n## Related Work\n## Methodology\n"
    ),
    "lab/publications/submitted/submission_log.csv": (
        "paper_id,journal,date_submitted,status\n"
        "P001,NeurIPS,2024-05-01,under_review\n"
        "P002,ICML,2024-03-15,rejected\n"
    ),
    "lab/personnel/team_roster.json": json.dumps({
        "pi": "Dr. Evelyn Marsh",
        "postdocs": ["Dr. Amir Saleh", "Dr. Priya Nair"],
        "phd_students": ["Wei Zhang", "Fatima Al-Rashid", "Tom Eriksson"],
    }, indent=2),
    "lab/resources/datasets/index.txt": (
        "CIFAR-10: /mnt/nas/datasets/cifar10\n"
        "ImageNet: /mnt/nas/datasets/imagenet\n"
        "custom_bench: /mnt/nas/datasets/bench_v2\n"
    ),
    "lab/resources/code_snippets/utils.py": (
        "def moving_average(data, window=5):\n"
        "    return [sum(data[i:i+window])/window for i in range(len(data)-window+1)]\n"
    ),
    "archive/2023/experiment_log.txt": (
        "2023-11-01: Baseline established, acc=0.783\n"
        "2023-11-15: Augmentation added, acc=0.801\n"
        "2023-12-01: Final model frozen\n"
    ),
    "archive/2022/budget_notes.txt": (
        "GPU cluster: $12,400\nCloud compute: $3,200\nConferences: $8,100\n"
    ),
    "tools/scripts/cleanup.sh": (
        "#!/bin/bash\n# Remove temp files\nfind /tmp -name '*.tmp' -delete\n"
    ),
    "tools/scripts/sync_nas.py": (
        "# Sync local results to NAS\nimport shutil\n# TODO: implement\n"
    ),
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── PRIMARY INPUT 1: research_notes.json ──────────────────────────────────────
# Messy array of research notes to be ingested as memories.
# Fields are inconsistent: some have extra keys, some are missing optional fields,
# importance values vary, category names need normalization.

research_notes = [
    {
        "note_id": "N001",
        "text": "Transformer attention mechanism shows quadratic memory scaling; consider sparse attention for sequences longer than 4096 tokens.",
        "topic": "architecture",
        "labels": ["transformers", "attention", "scalability"],
        "priority": 9,
        "extra_field": "irrelevant data here",
        "source": "weekly_review_2024_03_11",
    },
    {
        "note_id": "N002",
        "text": "Dropout rate of 0.3 consistently outperforms 0.5 on our benchmark for the regularization ablation study.",
        "topic": "training",
        "labels": ["dropout", "regularization", "ablation"],
        "priority": 7,
        "source": "experiment_q1_2024",
    },
    {
        "note_id": "N003",
        "text": "Dr. Marsh suggested exploring curriculum learning for the low-resource NLP task; follow up at next group meeting.",
        "topic": "research_direction",
        "labels": ["curriculum_learning", "NLP", "low_resource"],
        "priority": 6,
        "source": "meeting_2024_03_18",
    },
    {
        "note_id": "N004",
        "text": "NAS allocation request for Q2 approved: 40TB reserved on nas03.",
        "topic": "infrastructure",
        "labels": ["NAS", "storage", "Q2"],
        "priority": 3,
        "source": "admin_email",
    },
    {
        "note_id": "N005",
        "text": "Gradient clipping at max_norm=1.0 prevents loss spikes; mandatory for all future RNN experiments.",
        "topic": "training",
        "labels": ["gradient_clipping", "RNN", "training_stability"],
        "priority": 8,
        "source": "experiment_notes_2024_02",
    },
    {
        "note_id": "N006",
        "text": "Paper submission deadline for NeurIPS 2024: May 22. Abstract registration by May 15.",
        "topic": "publication",
        "labels": ["NeurIPS", "deadline", "2024"],
        "priority": 10,
        "source": "conference_calendar",
    },
    {
        "note_id": "N007",
        "text": "Wei Zhang's GPU allocation increased from 2 to 4 A100s following project approval.",
        "topic": "infrastructure",
        "labels": ["GPU", "allocation", "personnel"],
        "priority": 2,
        "source": "admin_log",
    },
    {
        "note_id": "N008",
        "text": "Mixed precision training (FP16) reduces VRAM usage by ~40% with negligible accuracy loss on our vision tasks.",
        "topic": "training",
        "labels": ["mixed_precision", "FP16", "VRAM", "efficiency"],
        "priority": 8,
        "source": "experiment_q1_2024",
    },
    {
        "note_id": "N009",
        "text": "Literature review: contrastive learning approaches (SimCLR, MoCo, BYOL) all require large batch sizes (>2048) to be effective.",
        "topic": "literature",
        "labels": ["contrastive_learning", "SimCLR", "MoCo", "BYOL"],
        "priority": 5,
        "source": "literature_review_march",
    },
    {
        "note_id": "N010",
        "text": "Office hours for external collaborators scheduled every Thursday 14:00-15:00 in room B204.",
        "topic": "admin",
        "labels": ["schedule", "collaborators", "office_hours"],
        "priority": 1,
        "source": "admin_notice",
    },
    {
        "note_id": "N011",
        "text": "Benchmark dataset v2 released: includes 15K additional labeled samples for the rare-event class.",
        "topic": "research_direction",
        "labels": ["dataset", "benchmark", "rare_event"],
        "priority": 7,
        "source": "data_team_announcement",
    },
    {
        "note_id": "N012",
        "text": "Learning rate warmup for 500 steps improves convergence on all transformer-based models tested so far.",
        "topic": "training",
        "labels": ["learning_rate", "warmup", "transformers"],
        "priority": 7,
        "source": "experiment_notes_2024_02",
    },
    {
        "note_id": "N013",
        "text": "Printer on 3rd floor requires toner replacement; IT ticket #4821 filed.",
        "topic": "admin",
        "labels": ["admin", "printer", "IT"],
        "priority": 1,
        "extra_field": "low priority noise",
        "source": "admin_log",
    },
    {
        "note_id": "N014",
        "text": "Fatima's submission to EMNLP 2024 accepted with minor revisions; camera-ready due July 10.",
        "topic": "publication",
        "labels": ["EMNLP", "acceptance", "camera_ready"],
        "priority": 9,
        "source": "email_notification",
    },
    {
        "note_id": "N015",
        "text": "Knowledge distillation from GPT-4 teacher achieves 94% of full model performance at 10% parameter count.",
        "topic": "architecture",
        "labels": ["knowledge_distillation", "GPT-4", "efficiency"],
        "priority": 9,
        "source": "experiment_q2_2024",
    },
]

(workspace / "research_notes.json").write_text(json.dumps(research_notes, indent=2))

# ── PRIMARY INPUT 2: corrections_manifest.csv ─────────────────────────────────
# A CSV file specifying post-ingestion corrections to apply.
# The agent must apply these AFTER ingestion using update_memory().
# References notes by note_id — agent must track the mapping note_id -> DB id.

corrections_rows = [
    # note_id, field_to_update, new_value
    # N006: NeurIPS deadline priority should be bumped to max
    ["N006", "importance", "10"],
    # N009: category should be corrected to 'literature_review'
    ["N009", "category", "literature_review"],
    # N011: add metadata with verified=true
    ["N011", "metadata", '{"verified": true, "data_team_contact": "priya.nair@lab.org"}'],
    # N015: tags need extending — but update replaces, so new full list
    ["N015", "tags", '["knowledge_distillation", "GPT-4", "efficiency", "distillation_benchmark"]'],
    # N002: importance correction downward
    ["N002", "importance", "6"],
]

with open(workspace / "corrections_manifest.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["note_id", "field", "new_value"])
    writer.writerows(corrections_rows)

# ── PRIMARY INPUT 3: pruning_policy.json ─────────────────────────────────────
# Specifies which memories to delete after corrections.
# Delete all memories whose FINAL importance is strictly less than this threshold.
pruning_policy = {
    "delete_if_importance_below": 4,
    "description": "Remove low-signal memories to keep the store focused on high-value research insights."
}
(workspace / "pruning_policy.json").write_text(json.dumps(pruning_policy, indent=2))

# ── PRIMARY INPUT 4: db_config.json ──────────────────────────────────────────
# Specifies where the LanceDB instance should be created.
db_config = {
    "db_path": "/workspace/lab_memory/lancedb",
    "report_output": "memory_report.json"
}
(workspace / "db_config.json").write_text(json.dumps(db_config, indent=2))

print("Workspace generated successfully.")
print(f"Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")