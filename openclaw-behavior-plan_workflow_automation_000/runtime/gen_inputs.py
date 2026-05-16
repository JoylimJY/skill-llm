import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# === Create realistic distractor directory structure ===
dirs = [
    "incident_response/logs/2024-01",
    "incident_response/logs/2024-02",
    "incident_response/reports",
    "incident_response/scripts",
    "devops/monitoring",
    "devops/alerts/config",
    "devops/runbooks",
    "team/slack_templates",
    "team/oncall_schedule",
    "docs/architecture",
    "docs/postmortems",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# === Distractor files ===
(WORKSPACE / "incident_response/logs/2024-01/app.log").write_text(
    "2024-01-10 02:11:00 ERROR OOMKilled\n2024-01-10 02:12:00 INFO restarted\n"
)
(WORKSPACE / "incident_response/logs/2024-02/app.log").write_text(
    "2024-02-05 14:22:00 ERROR DiskFull\n2024-02-05 14:23:00 WARN low space\n"
)
(WORKSPACE / "incident_response/scripts/parse_logs.sh").write_text(
    "#!/bin/bash\ngrep ERROR $1 | tail -n 50\n"
)
(WORKSPACE / "incident_response/reports/template.txt").write_text(
    "Report Title:\nDate:\nErrors Found:\nActions:\n"
)
(WORKSPACE / "devops/monitoring/prometheus.yml").write_text(
    "global:\n  scrape_interval: 15s\nscrape_configs: []\n"
)
(WORKSPACE / "devops/alerts/config/alertmanager.yml").write_text(
    "route:\n  receiver: 'slack'\nreceivers:\n  - name: 'slack'\n"
)
(WORKSPACE / "devops/runbooks/disk_full.md").write_text(
    "# Disk Full Runbook\n1. Check df -h\n2. Remove old logs\n"
)
(WORKSPACE / "team/slack_templates/incident_msg.txt").write_text(
    "🚨 Incident Alert:\nTitle: {title}\nSeverity: {severity}\n"
)
(WORKSPACE / "team/oncall_schedule/schedule.csv").write_text(
    "week,engineer\n1,alice\n2,bob\n3,carol\n"
)
(WORKSPACE / "docs/architecture/overview.md").write_text(
    "# System Architecture\nMicroservices deployed on Kubernetes.\n"
)
(WORKSPACE / "docs/postmortems/2024-02-05.md").write_text(
    "# Postmortem 2024-02-05\nDisk exhaustion on node-3.\n"
)

# === The actual task context file ===
(WORKSPACE / "incident_response/task_request.txt").write_text(
    """SRE Task Request
=================
We need to automate our incident response pipeline for log-based alerts.

The goal:
1. Scan the ./incident_response/logs directory for ERROR-level entries across all log files.
2. Extract a structured list of unique error types and their occurrence counts.
3. Write a remediation report to ./incident_response/reports/remediation_report.md.
4. Post a summary Slack message to the #sre-alerts channel with the top errors found.

Please produce an OpenClaw behavior plan that our agent can execute for this workflow.
Save the plan as: incident_response_plan.md
"""
)

print("Workspace initialized.")