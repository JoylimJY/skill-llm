import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create distractor directory structure (simulating a real project)
dirs_to_create = [
    "workspace/subagents/techbot/logs",
    "workspace/subagents/techbot/cache",
    "workspace/subagents/marketbot/optimizer",
    "workspace/subagents/marketbot/logs",
    "workspace/reports/quarterly",
    "workspace/reports/monthly",
    "workspace/config/global",
    "workspace/scripts/analysis",
    "workspace/data/raw",
    "workspace/data/processed",
    "workspace/skills/agent-optimizer/scripts",
    "workspace/skills/agent-optimizer/docs",
    "workspace/archive/2023",
    "workspace/archive/2024",
]

for d in dirs_to_create:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "workspace/subagents/techbot/logs/run_20240101.log": "INFO: Agent started\nINFO: Processing task\nINFO: Task completed in 2.3s\n",
    "workspace/subagents/techbot/cache/session_abc123.json": json.dumps({"session": "abc123", "ttl": 3600, "data": {}}),
    "workspace/subagents/marketbot/logs/errors.log": "ERROR: timeout on request\nERROR: retry attempt 3\n",
    "workspace/reports/quarterly/q3_2024.json": json.dumps({"quarter": "Q3", "revenue": 125000, "agents_deployed": 3}),
    "workspace/reports/monthly/nov_2024.json": json.dumps({"month": "November", "tasks_processed": 4521}),
    "workspace/config/global/settings.json": json.dumps({"max_agents": 10, "log_level": "INFO", "region": "us-east-1"}),
    "workspace/scripts/analysis/legacy_report.py": "# Legacy reporting script - DO NOT USE\nimport pandas as pd\nprint('deprecated')\n",
    "workspace/data/raw/sample_predictions.csv": "task_id,predicted_roi,actual_roi,confidence\n001,2.1,1.9,0.78\n002,3.5,3.8,0.91\n003,1.2,1.1,0.65\n",
    "workspace/data/processed/cleaned_predictions.json": json.dumps({"records": 3, "mean_error": 0.17, "processed_at": "2024-11-01T10:00:00"}),
    "workspace/skills/agent-optimizer/docs/changelog.md": "## Changelog\n### v6.1\n- Added reward trending\n- Fixed trajectory indexing\n",
    "workspace/archive/2023/old_config.json": json.dumps({"version": "5.0", "deprecated": True}),
    "workspace/archive/2024/backup_trajectories.jsonl": '{"agent_id":"legacy","task":"old_task","reward":0.5}\n',
    "workspace/skills/agent-optimizer/scripts/analyze_trends.py": "#!/usr/bin/env python3\n# analyze_trends.py - placeholder\nprint('Trend analysis not yet implemented')\n",
    "workspace/skills/agent-optimizer/scripts/ab_test.py": "#!/usr/bin/env python3\n# ab_test.py\nprint('A/B test runner')\n",
    "workspace/skills/agent-optimizer/scripts/generate_report.py": "#!/usr/bin/env python3\n# generate_report.py\nprint('Report generator')\n",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# The PROBLEM: a partially-set-up financebot agent directory with messy/incomplete data
# Agent must build the full optimizer infrastructure from scratch for "financebot"
# We provide raw business data that needs to be translated into the proper schema

# Create a raw business brief - not in the correct format
raw_brief = {
    "bot_name": "financebot",
    "purpose": "ROI prediction for investment tasks",
    "tasks_run": [
        {
            "run_id": "run_001",
            "description": "预测任务 ROI",
            "predicted_roi": 2.5,
            "actual_roi": 2.3,
            "confidence_score": 0.85,
            "word_count": 450,
            "run_timestamp": "2024-11-01T09:00:00"
        },
        {
            "run_id": "run_002",
            "description": "预测任务 ROI",
            "predicted_roi": 3.1,
            "actual_roi": 3.8,
            "confidence_score": 0.72,
            "word_count": 380,
            "run_timestamp": "2024-11-01T11:30:00"
        },
        {
            "run_id": "run_003",
            "description": "预测任务 ROI",
            "predicted_roi": 1.8,
            "actual_roi": 1.9,
            "confidence_score": 0.91,
            "word_count": 510,
            "run_timestamp": "2024-11-02T08:15:00"
        },
        {
            "run_id": "run_004",
            "description": "预测任务 ROI",
            "predicted_roi": 4.0,
            "actual_roi": 2.5,
            "confidence_score": 0.60,
            "word_count": 290,
            "run_timestamp": "2024-11-02T14:00:00"
        }
    ],
    "prompt_versions_available": ["v1.0", "v1.1", "v2.0"],
    "active_prompt_version": "v2.0"
}

(workspace / "workspace" / "financebot_business_brief.json").parent.mkdir(parents=True, exist_ok=True)
(workspace / "workspace" / "financebot_business_brief.json").write_text(json.dumps(raw_brief, indent=2, ensure_ascii=False))

# Also create a messy "notes" file that hints at what prompts should contain
notes_content = """FinanceBot Prompt Notes (Internal)
===================================
v1.0 prompt: Basic ROI prediction. Ask model to predict return on investment.
  - Simple format, no confidence scoring
  - Used in Q2 2024

v1.1 prompt: Added confidence scoring requirement.
  - Slightly more structured
  - Used in Q3 2024

v2.0 prompt: Current production prompt. Full structured output with confidence and reasoning.
  - Requires: predicted_roi, confidence, reasoning_steps
  - Deployed October 2024
  - Performance target: confidence_score >= 0.80

Optimization target: prediction_accuracy
Key metrics to track: prediction_accuracy, confidence_score
A/B testing enabled: yes
Optimization interval: 100 runs
"""

(workspace / "workspace" / "financebot_prompt_notes.txt").write_text(notes_content)

print("Sandbox workspace initialized successfully.")
print(f"Distractor files created: {len(distractor_files)}")
print("Raw business data created: financebot_business_brief.json")