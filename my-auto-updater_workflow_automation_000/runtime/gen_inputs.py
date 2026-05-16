import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── deeply nested distractor structure ──────────────────────────────────────
dirs = [
    "infra/terraform/modules/vpc",
    "infra/terraform/modules/ec2",
    "infra/ansible/roles/common/tasks",
    "infra/ansible/roles/webserver/templates",
    "services/api/src/handlers",
    "services/api/src/models",
    "services/worker/config",
    "services/worker/logs",
    "docs/runbooks",
    "docs/architecture",
    "scripts/maintenance",
    "scripts/deploy",
    ".github/workflows",
    "monitoring/dashboards",
    "monitoring/alerts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }\n',
    "infra/terraform/modules/ec2/variables.tf": 'variable "instance_type" { default = "t3.micro" }\n',
    "infra/ansible/roles/common/tasks/main.yml": "- name: Install deps\n  apt:\n    name: curl\n    state: present\n",
    "infra/ansible/roles/webserver/templates/nginx.conf.j2": "server { listen 80; server_name {{ domain }}; }\n",
    "services/api/src/handlers/health.py": "def health_check(req): return {'status': 'ok'}\n",
    "services/api/src/models/user.py": "class User:\n    id: int\n    name: str\n",
    "services/worker/config/queue.json": json.dumps({"queue": "tasks", "concurrency": 4}, indent=2) + "\n",
    "services/worker/logs/worker.log": "[2025-01-10 03:12:44] Worker started\n[2025-01-10 03:13:01] Job processed\n",
    "docs/runbooks/deploy.md": "# Deploy Runbook\n1. Pull latest\n2. Run migrations\n3. Restart services\n",
    "docs/architecture/overview.md": "# System Architecture\nMicroservices with API gateway.\n",
    "scripts/deploy/rollback.sh": "#!/bin/bash\necho 'Rolling back...'\ngit checkout HEAD~1\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    "monitoring/dashboards/latency.json": json.dumps({"title": "API Latency", "panels": []}, indent=2) + "\n",
    "monitoring/alerts/cpu_alert.yaml": "alert: HighCPU\ncondition: cpu > 80\nseverity: warning\n",
}
for path, content in distractor_files.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── THE PROBLEM FILES ────────────────────────────────────────────────────────

# 1. Incomplete/wrong colleague notes about the cron setup
#    - Missing --session, --wake, --deliver flags
#    - Wrong cron time (uses 3 AM instead of 4 AM default)
#    - Timezone left as a placeholder
notes_content = """\
# Auto-Update Cron Setup Notes
# Written by: Jordan (left the team)
# Status: INCOMPLETE - DO NOT USE AS-IS

## Attempted command (did not work, missing flags):
clawdbot cron add \\
  --name "Daily Auto-Update" \\
  --cron "0 3 * * *" \\
  --tz "PLACEHOLDER_TZ" \\
  --message "Run daily auto-updates: check for Clawdbot updates and update all skills. Report what was updated."

## Notes from Jordan:
# - The cron time should be the documented default (check the skill docs)
# - Timezone should be America/Los_Angeles
# - I think there were more flags but I can't remember them
# - Something about "isolated" and "now" and "deliver"???
# - The command above is WRONG and incomplete

## What we need:
# 1. A working cron command saved to scripts/maintenance/setup_autoupdate.sh
# 2. An update summary report based on the mock logs in services/worker/logs/
"""
with open(os.path.join(workspace, "docs/runbooks/autoupdate_notes.md"), "w") as f:
    f.write(notes_content)

# 2. Mock raw update logs (messy, unstructured) that the agent must parse
#    to produce a formatted summary
raw_update_log = """\
=== CLAWDBOT UPDATE LOG 2025-01-10 04:00:01 ===
[INFO] Checking clawdbot version...
[INFO] Current version: v2026.1.9
[INFO] Found update: v2026.1.10
[INFO] Running: npm update -g clawdbot@latest
[INFO] clawdbot updated successfully to v2026.1.10
[INFO] Running: clawdbot doctor
[INFO] Migrations applied: 2
[INFO] Doctor check passed.

=== CLAWDHUB SKILL UPDATE LOG ===
[INFO] Checking skills against registry...
[SKILL] prd: current=2.0.3 available=2.0.4 -> UPDATE
[SKILL] browser: current=1.2.0 available=1.2.1 -> UPDATE
[SKILL] nano-banana-pro: current=3.1.0 available=3.1.2 -> UPDATE
[SKILL] gemini: current=1.0.5 available=1.0.5 -> OK
[SKILL] sag: current=0.9.1 available=0.9.1 -> OK
[SKILL] things-mac: current=2.2.0 available=2.2.0 -> OK
[SKILL] himalaya: current=1.1.3 available=1.1.3 -> OK
[SKILL] peekaboo: current=0.3.7 available=0.3.7 -> OK
[INFO] Updating prd...
[INFO] prd updated to 2.0.4
[INFO] Updating browser...
[INFO] browser updated to 1.2.1
[INFO] Updating nano-banana-pro...
[INFO] nano-banana-pro updated to 3.1.2
[INFO] All skill updates complete.
[INFO] No errors encountered.
"""
with open(os.path.join(workspace, "services/worker/logs/autoupdate_raw.log"), "w") as f:
    f.write(raw_update_log)

# 3. A partial/broken config file to further confuse
broken_config = """\
{
  "cron": {
    "enabled": true,
    "jobs": [
      {
        "name": "Daily Auto-Update",
        "schedule": "0 3 * * *",
        "timezone": "UTC",
        "session": "main",
        "notes": "THIS IS WRONG - kept here for reference only"
      }
    ]
  }
}
"""
with open(os.path.join(workspace, "services/worker/config/cron_config_broken.json"), "w") as f:
    f.write(broken_config)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")