import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor structure ---
dirs = [
    "config/environments/production",
    "config/environments/staging",
    "config/environments/development",
    "logs/cron",
    "logs/updates",
    "skills/installed/prd",
    "skills/installed/browser",
    "skills/installed/nano-banana-pro",
    "skills/installed/gemini",
    "skills/installed/sag",
    "skills/cache",
    "scripts/maintenance",
    "scripts/backup",
    ".clawdbot/state",
    ".clawdbot/sessions",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "config/environments/production/app.conf").write_text(
    "[server]\nhost=prod.example.com\nport=443\ntimeout=30\n"
)
(workspace / "config/environments/staging/app.conf").write_text(
    "[server]\nhost=staging.example.com\nport=8443\ntimeout=60\n"
)
(workspace / "config/environments/development/app.conf").write_text(
    "[server]\nhost=localhost\nport=8080\ntimeout=120\n"
)
(workspace / "logs/cron/cron.log").write_text(
    "2024-01-15 03:58:01 cron started\n2024-01-15 04:00:01 no jobs scheduled\n"
)
(workspace / "logs/updates/update.log").write_text(
    "2024-01-14 04:00:03 update check started\n2024-01-14 04:00:45 completed\n"
)

# Skill manifests (distractors - show installed state but NOT hints for commands)
skills_data = {
    "prd":             {"version": "2.0.3", "registry_version": "2.0.4"},
    "browser":         {"version": "1.2.0", "registry_version": "1.2.1"},
    "nano-banana-pro": {"version": "3.1.0", "registry_version": "3.1.2"},
    "gemini":          {"version": "1.5.2", "registry_version": "1.5.2"},
    "sag":             {"version": "0.9.1", "registry_version": "0.9.1"},
}

for skill_name, data in skills_data.items():
    manifest = {
        "name": skill_name,
        "installed_version": data["version"],
        "registry_version": data["registry_version"],
        "install_path": f"/workspace/skills/installed/{skill_name}",
        "enabled": True,
    }
    (workspace / f"skills/installed/{skill_name}/manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )

(workspace / "skills/cache/registry_snapshot.json").write_text(
    json.dumps({"last_checked": "2024-01-15T02:00:00Z", "skills_count": 47}, indent=2)
)

# .clawdbot state files (distractors)
(workspace / ".clawdbot/state/version.json").write_text(
    json.dumps({"current": "2026.1.9", "channel": "stable"}, indent=2)
)
(workspace / ".clawdbot/sessions/main.json").write_text(
    json.dumps({"session_id": "main", "created": "2024-01-01T00:00:00Z"}, indent=2)
)

# Scripts directory with unrelated scripts
(workspace / "scripts/maintenance/cleanup.sh").write_text(
    "#!/bin/bash\nfind /tmp -mtime +7 -delete\necho 'Cleanup done'\n"
)
(workspace / "scripts/maintenance/health_check.sh").write_text(
    "#!/bin/bash\ncurl -sf http://localhost:8080/health || exit 1\necho 'Healthy'\n"
)
(workspace / "scripts/backup/daily_backup.sh").write_text(
    "#!/bin/bash\ntar -czf /backup/$(date +%Y%m%d).tar.gz /workspace/data\n"
)

# A deliberately misleading cron-related file with WRONG values
(workspace / "config/environments/production/cron_template.txt").write_text(
    "# Old cron template - DO NOT USE\n# cron schedule: 0 2 * * * (runs at 2am - outdated)\n# This template is deprecated\n"
)

# A partial, incorrect command attempt that should NOT be used
(workspace / "scripts/maintenance/old_update_attempt.sh").write_text(
    "#!/bin/bash\n# ABANDONED ATTEMPT - had wrong flags\n# clawdbot cron add --name 'autoupdate' --cron '0 2 * * *'\n# exit 0\n"
)

# The task brief - tells WHAT is needed, not HOW
task_brief = """# Platform Maintenance Automation Task

## Context
Our team runs Clawdbot as our internal AI assistant platform.
We need to automate daily maintenance to keep it and all its skills current.

## What We Need

1. Set up the daily automated maintenance schedule (the "standard daily auto-update" 
   configuration as documented) so it runs without any manual intervention.
   The job must run at the standard recommended time and use the recommended session 
   and delivery settings.

2. After setting up the schedule, produce a file called `update_summary.txt` 
   in /workspace showing what a completed update run would look like, given 
   that the system was just updated from the state described in the skill manifests 
   under /workspace/skills/installed/. 
   Use the version data from those manifests (installed vs registry versions) 
   and assume Clawdbot itself updated from v2026.1.9 to v2026.1.10.
   The summary must follow the standard format used by this automation tool.

## Notes
- The exact format of the summary matters.
- The scheduling command must use the correct flags and values as specified 
  in the official documentation for this tool.
"""

(workspace / "TASK.md").write_text(task_brief)

# Create the invocation log directory for mock binaries
(workspace / "mock_bin").mkdir(exist_ok=True)
(workspace / "mock_bin/invocations.log").write_text("")  # empty, will be populated

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")