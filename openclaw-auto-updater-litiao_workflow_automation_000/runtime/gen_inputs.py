import os
import random
import json
import stat

random.seed(42)

workspace = "/workspace"

# --- Deep distractor directory structure ---
dirs = [
    "platform/gateway/config",
    "platform/gateway/logs",
    "platform/gateway/backups",
    "platform/skills/installed",
    "platform/skills/disabled",
    "platform/monitoring/alerts",
    "platform/monitoring/dashboards",
    "ops/runbooks",
    "ops/schedules/legacy",
    "ops/schedules/active",
    "ops/reports/2024",
    "ops/reports/2025",
    "infra/terraform/modules",
    "infra/ansible/playbooks",
    "docs/internal",
    "docs/external",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "platform/gateway/config/gateway.yaml": """\
gateway:
  port: 8443
  tls: true
  timeout: 30s
  max_connections: 1000
""",
    "platform/gateway/config/routing.conf": """\
# Gateway routing configuration
# DO NOT EDIT MANUALLY
upstream backend { server 127.0.0.1:9000; }
""",
    "platform/gateway/logs/gateway.log": """\
2025-06-01 03:00:01 INFO  Gateway started
2025-06-01 03:00:02 INFO  Skills loaded: 15
2025-06-01 03:00:03 WARN  Skill 'legacy-auth' using deprecated API
""",
    "platform/gateway/backups/gateway_2025-05-31.tar.gz.manifest": """\
backup_date: 2025-05-31
files: 142
size_mb: 38
""",
    "platform/skills/installed/skills_registry.json": json.dumps({
        "skills": [
            {"name": "data-sync", "version": "1.2.3", "enabled": True},
            {"name": "audit-logger", "version": "2.0.1", "enabled": True},
            {"name": "rate-limiter", "version": "0.9.7", "enabled": True},
            {"name": "legacy-auth", "version": "1.0.0", "enabled": False},
        ]
    }, indent=2),
    "platform/skills/disabled/notes.txt": """\
# Disabled skills
# legacy-auth: deprecated, pending removal
# old-metrics: replaced by monitoring/dashboards
""",
    "platform/monitoring/alerts/alert_rules.yaml": """\
alerts:
  - name: high_latency
    threshold_ms: 500
    severity: warning
  - name: gateway_down
    threshold_ms: 0
    severity: critical
""",
    "platform/monitoring/dashboards/main.json": json.dumps({
        "dashboard": "Main Operations",
        "panels": ["latency", "throughput", "error_rate", "skill_health"]
    }, indent=2),
    "ops/runbooks/update_procedure.md": """\
# Update Procedure (MANUAL)

1. Notify team in #ops-alerts channel
2. Wait for off-peak window (03:00–05:00 Berlin time)
3. Run update on staging first
4. Monitor for 10 minutes
5. Apply to production

NOTE: This procedure is being superseded by automated scheduling.
""",
    "ops/schedules/legacy/old_cron.txt": """\
# OLD CRON - DO NOT USE
# 0 2 * * * /usr/local/bin/update_gateway.sh
# This script no longer exists
""",
    "ops/schedules/active/.keep": "",
    "ops/reports/2024/q4_summary.txt": """\
Q4 2024 Update Summary
======================
Updates applied: 47
Skills updated: 31
Failures: 2
""",
    "ops/reports/2025/q1_summary.txt": """\
Q1 2025 Update Summary
======================
Updates applied: 52
Skills updated: 38
Failures: 0
""",
    "infra/terraform/modules/gateway_module.tf": """\
resource "aws_instance" "gateway" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium"
}
""",
    "infra/ansible/playbooks/deploy.yml": """\
---
- name: Deploy Gateway
  hosts: gateway
  tasks:
    - name: Restart service
      systemd:
        name: openclaw-gateway
        state: restarted
""",
    "docs/internal/architecture.md": """\
# Platform Architecture

The gateway manages all skill routing and update orchestration.
Updates must be scheduled during off-hours to avoid disruption.
Berlin timezone is standard for all scheduled operations.
""",
    "docs/external/api_reference.md": """\
# External API Reference
See internal wiki for full details.
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- A misleading/broken legacy update report for distraction ---
with open(os.path.join(workspace, "ops/reports/2025/last_update_run.txt"), "w") as f:
    f.write("""\
Last update run: 2025-06-10 02:15 UTC
Status: PARTIAL
openclaw: no change
skills: 1 updated, 14 unchanged, 1 FAILED (rate-limiter: checksum mismatch)
""")

# --- A fake partial cron record that is WRONG (missing flags, wrong time) ---
with open(os.path.join(workspace, "ops/schedules/active/attempted_schedule.txt"), "w") as f:
    f.write("""\
# Attempted setup - DO NOT USE, missing required parameters
# openclaw cron add --name "nightly-update" --cron "0 2 * * *"
# Missing: --tz, --session, --wake, --deliver, --message
# Wrong time: should be 03:30 Berlin, not 02:00
""")

print("Workspace initialized with distractor files.")
print(f"Files created: {len(distractor_files) + 2}")