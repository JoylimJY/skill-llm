import os
import random
import shutil
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── 1. Simulate a realistic AI workspace with deeply nested files ──────────────
dirs = [
    "ai_workspace/models/llama3",
    "ai_workspace/models/mistral",
    "ai_workspace/prompts/system",
    "ai_workspace/prompts/user",
    "ai_workspace/conversations/2024-01",
    "ai_workspace/conversations/2024-02",
    "ai_workspace/config",
    "ai_workspace/scripts/utils",
    "ai_workspace/logs",
    "ai_workspace/embeddings/vectors",
    "ai_workspace/finetune/datasets",
    "ai_workspace/finetune/checkpoints",
    "backups_dir",   # target backup directory (initially empty — agent must configure script to use it)
    "mirror_drive",  # simulates a secondary drive
    "task_setup",    # where setup metadata lives
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files — realistic AI workspace content
files = {
    "ai_workspace/models/llama3/config.json": '{"model":"llama3","layers":32,"heads":32}',
    "ai_workspace/models/llama3/tokenizer.json": '{"vocab_size":32000}',
    "ai_workspace/models/mistral/config.json": '{"model":"mistral-7b","layers":32}',
    "ai_workspace/prompts/system/assistant.txt": "You are a helpful assistant specialized in code review.",
    "ai_workspace/prompts/system/analyst.txt": "You are a data analyst. Respond with structured JSON.",
    "ai_workspace/prompts/user/daily_standup.txt": "Summarize the work done today in bullet points.",
    "ai_workspace/conversations/2024-01/session_001.json": '{"messages":[{"role":"user","content":"Hello"}]}',
    "ai_workspace/conversations/2024-01/session_002.json": '{"messages":[{"role":"user","content":"Explain RLHF"}]}',
    "ai_workspace/conversations/2024-02/session_010.json": '{"messages":[{"role":"user","content":"Debug this code"}]}',
    "ai_workspace/config/ollama.yaml": "host: localhost\nport: 11434\nmodel: llama3",
    "ai_workspace/config/settings.json": '{"theme":"dark","retention":30,"auto_save":true}',
    "ai_workspace/scripts/utils/cleanup.py": "import os\n# placeholder cleanup utility",
    "ai_workspace/scripts/utils/export.py": "import json\n# placeholder export utility",
    "ai_workspace/logs/ollama_2024-02-10.log": "[INFO] Model loaded successfully\n[INFO] Serving on port 11434",
    "ai_workspace/logs/ollama_2024-02-11.log": "[WARN] High memory usage detected",
    "ai_workspace/embeddings/vectors/index.bin": "BINARY_PLACEHOLDER_DATA_" * 10,
    "ai_workspace/finetune/datasets/train.jsonl": '{"text":"sample training data"}\n{"text":"more data"}',
    "ai_workspace/finetune/checkpoints/step_1000.pt": "CHECKPOINT_PLACEHOLDER_" * 5,
}

for path, content in files.items():
    (workspace / path).write_text(content)

# ── 2. CREATE THE PROBLEM: a partially broken/incomplete backup config ─────────
# An old, broken backup attempt — agent must NOT reuse this, must create proper scripts
broken_backup = workspace / "ai_workspace/scripts/old_backup_attempt.sh"
broken_backup.write_text("""#!/bin/bash
# OLD ATTEMPT - BROKEN, DO NOT USE
# This script was abandoned because it doesn't handle retention or mirroring
cp -r /workspace/ai_workspace /tmp/backup_$(date +%Y%m%d)
""")

# A stale task registration attempt with wrong parameters
stale_task = workspace / "ai_workspace/scripts/old_register_task.ps1"
stale_task.write_text("""# STALE - wrong task name and trigger
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2AM
Register-ScheduledTask -TaskName "BackupJob" -Action $action -Trigger $trigger
""")

# ── 3. Write task specification to a neutral config file ─────────────────────
# This tells the agent what paths to configure (business context only)
task_spec = workspace / "task_setup/environment.conf"
task_spec.write_text("""# Environment Configuration for Workspace Protection System
# ---------------------------------------------------------
# Workspace to protect:
WORKSPACE_PATH=/workspace/ai_workspace

# Primary backup destination:
BACKUP_DIR=/workspace/backups_dir

# Secondary drive / mirror destination:
MIRROR_PATH=/workspace/mirror_drive

# Note: This file contains the infrastructure paths.
# The backup and registration scripts must be created from scratch.
""")

print("Workspace initialized successfully.")
print("Structure:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")