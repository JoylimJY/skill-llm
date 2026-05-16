import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic distractor directory structure ---
dirs = [
    workspace / "agent_configs" / "scheduler",
    workspace / "agent_configs" / "vision_bot",
    workspace / "agent_configs" / "data_pipeline",
    workspace / "logs" / "2024-01" / "errors",
    workspace / "logs" / "2024-01" / "audit",
    workspace / "tools" / "launchers" / "deprecated",
    workspace / "tools" / "launchers" / "active",
    workspace / "policies" / "v1",
    workspace / "policies" / "v2" / "drafts",
    workspace / "shared" / "references",
    workspace / "shared" / "temp",
    workspace / "backups" / "registry_snapshots",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- Distractor files (realistic but irrelevant) ---
distractor_files = {
    workspace / "agent_configs" / "scheduler" / "scheduler_config.yaml": """\
agent_id: scheduler_bot
max_tasks: 10
poll_interval_sec: 30
log_level: INFO
""",
    workspace / "agent_configs" / "vision_bot" / "vision_config.json": json.dumps({
        "agent_id": "vision_bot",
        "resolution": "1080p",
        "frame_rate": 30,
        "enabled": True
    }, indent=2),
    workspace / "agent_configs" / "data_pipeline" / "pipeline.toml": """\
[pipeline]
name = "etl_pipeline"
version = "2.1"
enabled = true

[pipeline.source]
type = "postgres"
host = "localhost"
""",
    workspace / "logs" / "2024-01" / "errors" / "error_log.txt": """\
2024-01-15 08:23:11 ERROR scheduler_bot: Task timeout on job #44
2024-01-15 09:00:02 ERROR vision_bot: Frame drop detected, skipping frame 301
2024-01-17 14:55:09 ERROR data_pipeline: Connection refused to postgres:5432
""",
    workspace / "logs" / "2024-01" / "audit" / "audit_trail.csv": """\
timestamp,agent_id,action,resource
2024-01-15 08:00:00,scheduler_bot,launch,TaskRunner.exe
2024-01-15 08:01:00,system_engineer,login,workstation-01
2024-01-16 10:30:00,vision_bot,capture,camera_feed_01
""",
    workspace / "tools" / "launchers" / "deprecated" / "old_launcher.bat": """\
@echo off
REM Deprecated launcher - do not use
start "" "C:\\OldApps\\LegacyTool\\legacy.exe"
""",
    workspace / "tools" / "launchers" / "active" / "README_IGNORE.txt": """\
This folder contains active launcher scripts managed by ops.
Do not modify manually.
""",
    workspace / "policies" / "v1" / "access_policy_v1.json": json.dumps({
        "version": 1,
        "default_mode": "allowlist",
        "global_admins": ["system_engineer"]
    }, indent=2),
    workspace / "policies" / "v2" / "drafts" / "proposed_policy_v2.md": """\
# Proposed Policy v2 (DRAFT)

## Access Control Changes
- Move RobotArm Controller to full access for all agents
- Restrict DataVault to allowlist: system_engineer only
- Deprecate LegacyTool entry
""",
    workspace / "shared" / "references" / "agent_ids.txt": """\
Known agent IDs (as of 2024-01-20):
- system_engineer
- vision_bot
- scheduler_bot
- data_pipeline_agent
- ops_monitor
""",
    workspace / "shared" / "temp" / ".gitkeep": "",
    workspace / "backups" / "registry_snapshots" / "snapshot_2024-01-10.json": json.dumps({
        "RobotArm Controller": {
            "launch_path": "C:\\Apps\\RobotArm\\RobotArm.lnk",
            "runtime_exe": "C:\\Apps\\RobotArm\\arm_control.exe",
            "process_name": "arm_control.exe",
            "mode": "allowlist",
            "allowed_agents": ["system_engineer", "ops_monitor"]
        }
    }, indent=2),
}

for path, content in distractor_files.items():
    path.write_text(content, encoding="utf-8")

# --- PROBLEM: Create a BROKEN pre-existing registry with bad entries ---
# This simulates a partially-migrated, messy registry that the agent must work with
registry_dir = Path.home() / ".openclaw" / "registries"
registry_dir.mkdir(parents=True, exist_ok=True)

# The registry already exists but has problems:
# 1. "DataVault" has mode=allowlist but allowed_agents is empty -> policy mismatch
# 2. "LegacyTool" is missing launch_path -> incomplete
# 3. "RobotArm Controller" is valid and correct
broken_registry = {
    "RobotArm Controller": {
        "launch_path": "C:\\Apps\\RobotArm\\RobotArm.lnk",
        "runtime_exe": "C:\\Apps\\RobotArm\\arm_control.exe",
        "process_name": "arm_control.exe",
        "mode": "allowlist",
        "allowed_agents": [
            "system_engineer",
            "ops_monitor"
        ]
    },
    "DataVault": {
        "launch_path": "C:\\Apps\\DataVault\\DataVault.exe",
        "runtime_exe": "C:\\Apps\\DataVault\\DataVault.exe",
        "process_name": "DataVault.exe",
        "mode": "allowlist",
        "allowed_agents": []
    },
    "LegacyTool": {
        "launch_path": "",
        "runtime_exe": "C:\\OldApps\\LegacyTool\\legacy.exe",
        "process_name": "legacy.exe",
        "mode": "full",
        "allowed_agents": []
    }
}

registry_path = registry_dir / "application_registry.json"
registry_path.write_text(json.dumps(broken_registry, indent=2), encoding="utf-8")

print("Workspace and broken registry created successfully.")
print(f"Registry written to: {registry_path}")