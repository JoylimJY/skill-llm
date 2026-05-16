import os
import random
import json

random.seed(42)

workspace = "/workspace"

# Create a deeply nested, messy directory structure simulating an existing broken AI assistant platform
dirs = [
    "ai-assistant/services/sync-service",
    "ai-assistant/services/backup-service",
    "ai-assistant/services/monitor-service",
    "ai-assistant/scripts/old",
    "ai-assistant/scripts/legacy",
    "ai-assistant/logs/sync",
    "ai-assistant/logs/backup",
    "ai-assistant/logs/monitor",
    "ai-assistant/config",
    "ai-assistant/docs/old",
    "platform/cron-configs",
    "platform/systemd-units",
    "platform/reports",
    "maintenance/weekly",
    "maintenance/monthly",
    "archive/2024",
    "archive/2023",
    "tmp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - messy existing crontab configs (WRONG schedules, conflicting)
with open(os.path.join(workspace, "platform/cron-configs/backup.cron"), "w") as f:
    f.write("# Backup cron job\n")
    f.write("0 2 * * * /ai-assistant/scripts/backup.sh\n")
    f.write("0 2 * * 0 /ai-assistant/scripts/backup-weekly.sh\n")  # Sunday conflict

with open(os.path.join(workspace, "platform/cron-configs/monitor.cron"), "w") as f:
    f.write("# Monitoring\n")
    f.write("*/5 * * * * /ai-assistant/scripts/monitor.sh\n")
    f.write("*/5 * * * * /ai-assistant/scripts/health-check.sh\n")  # duplicate timing

with open(os.path.join(workspace, "platform/cron-configs/sync.cron"), "w") as f:
    f.write("# Sync job - CONFLICTING with systemd\n")
    f.write("@hourly /ai-assistant/scripts/sync.sh\n")
    f.write("@hourly /ai-assistant/scripts/data-sync.sh\n")  # functional overlap

# Distractor: wrong/legacy conflict detection attempt (wrong schedule)
with open(os.path.join(workspace, "platform/cron-configs/conflict-check.cron"), "w") as f:
    f.write("# Old attempt at conflict detection - WRONG schedule\n")
    f.write("0 22 * * 0 /platform/scripts/old-detect.sh\n")  # Sunday, wrong!
    f.write("# TODO: fix this\n")

# Distractor: broken systemd units with overlapping functions
with open(os.path.join(workspace, "platform/systemd-units/sync.service"), "w") as f:
    f.write("[Unit]\nDescription=Data Sync Service\n\n")
    f.write("[Service]\nExecStart=/ai-assistant/scripts/sync.sh\nRestart=always\n\n")
    f.write("[Install]\nWantedBy=multi-user.target\n")

with open(os.path.join(workspace, "platform/systemd-units/data-sync.service"), "w") as f:
    f.write("[Unit]\nDescription=Data Sync Service v2 (DUPLICATE)\n\n")
    f.write("[Service]\nExecStart=/ai-assistant/scripts/data-sync.sh\nRestart=always\n\n")
    f.write("[Install]\nWantedBy=multi-user.target\n")

with open(os.path.join(workspace, "platform/systemd-units/nohup-wrapper.service"), "w") as f:
    f.write("[Unit]\nDescription=Legacy nohup wrapper - should be replaced\n\n")
    f.write("[Service]\nExecStart=nohup /ai-assistant/scripts/legacy-monitor.sh &\n\n")
    f.write("[Install]\nWantedBy=multi-user.target\n")

# Messy scripts with functional overlap
with open(os.path.join(workspace, "ai-assistant/scripts/old/sync-v1.sh"), "w") as f:
    f.write("#!/bin/bash\n# OLD: sync files using rsync\nrsync -av /data/ /backup/\n")

with open(os.path.join(workspace, "ai-assistant/scripts/legacy/sync-v2.sh"), "w") as f:
    f.write("#!/bin/bash\n# LEGACY: also syncs files\nrsync -av /data/ /backup/\necho 'done' >> /var/log/sync.log\n")

with open(os.path.join(workspace, "ai-assistant/scripts/old/cleanup.sh"), "w") as f:
    f.write("#!/bin/bash\n# Uses rm directly - dangerous!\nrm -rf /tmp/cache/*\n")

with open(os.path.join(workspace, "ai-assistant/scripts/legacy/cleanup-v2.sh"), "w") as f:
    f.write("#!/bin/bash\n# Also cleanup but uses trash-put\ntrash-put /tmp/cache/*\n")

# Scattered log paths (inconsistency)
with open(os.path.join(workspace, "ai-assistant/logs/sync/sync.log"), "w") as f:
    f.write("[2025-01-01] sync started\n[2025-01-01] sync complete\n")

with open(os.path.join(workspace, "ai-assistant/logs/backup/backup.log"), "w") as f:
    f.write("[2025-01-01] backup started\n")

with open(os.path.join(workspace, "ai-assistant/logs/monitor/monitor.log"), "w") as f:
    f.write("[2025-01-01] health OK\n")

# Distractor: incomplete/stub docs
with open(os.path.join(workspace, "ai-assistant/docs/old/conflicts.md"), "w") as f:
    f.write("# Conflicts\nTODO: document conflicts\n")

with open(os.path.join(workspace, "archive/2024/old-conflict-report.txt"), "w") as f:
    f.write("Date: 2024-01-15\nFound 3 conflicts in crontab. Action: NONE\n")

with open(os.path.join(workspace, "archive/2023/conflict-notes.txt"), "w") as f:
    f.write("Someone noticed cron and systemd both running sync. No fix applied.\n")

# Partially filled config that agent must NOT reuse as-is
with open(os.path.join(workspace, "ai-assistant/config/platform.json"), "w") as f:
    json.dump({
        "platform": "ai-assistant",
        "version": "2.1.0",
        "services": ["sync", "backup", "monitor"],
        "conflict_detection": {
            "enabled": False,
            "schedule": "UNCONFIGURED",
            "script": "UNCONFIGURED"
        }
    }, f, indent=2)

# Messy maintenance scripts
with open(os.path.join(workspace, "maintenance/weekly/check.sh"), "w") as f:
    f.write("#!/bin/bash\n# Placeholder weekly check - does nothing useful\necho 'week check'\n")

with open(os.path.join(workspace, "maintenance/monthly/report.sh"), "w") as f:
    f.write("#!/bin/bash\n# Monthly report generator\necho 'monthly'\n")

with open(os.path.join(workspace, "tmp/scratch/notes.txt"), "w") as f:
    f.write("Need to fix the conflict detection issue. Ask DevOps.\nWrong cron schedule was set last time - it ran on Sundays.\n")

# Write the task brief that triggers everything
with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write("""INTERNAL DEVOPS TICKET #4471
Team: AI Platform SRE

PROBLEM:
Our AI assistant platform is a mess. We have:
- Multiple cron jobs with conflicting schedules
- Systemd services duplicating each other  
- Scripts that do the same thing scattered everywhere
- Log files in different directories
- No proper conflict detection mechanism in place

ACTION REQUIRED:
Set up the official conflict coordination mechanism for this platform.

The mechanism should be deployed under: /workspace/conflict-coordination/
It must follow the team's official conflict-coordination skill specification (see SKILL.md).

Deliverables:
1. The proper directory structure for the conflict-coordination module
2. A working crontab entry file named 'conflict-detection.cron' containing the
   correct automated schedule for running conflict detection
3. A coordination report file named 'coordination-report.md' documenting all
   conflicts found in the platform and the prescribed resolution strategy for each,
   following the team's official coordination principles

NOTES:
- Previous attempts used wrong schedules (see archive/)
- The platform.json has conflict_detection as disabled/unconfigured - this needs addressing
- Make sure the coordination principles and priority rules are correct per spec
""")

print("Workspace generated successfully.")
print("Key files created:")
for root, dirs_list, files in os.walk(workspace):
    for f in files:
        print(f"  {os.path.join(root, f)}")