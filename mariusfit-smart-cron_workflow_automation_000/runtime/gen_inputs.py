import os
import json
import random
import hashlib
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "infrastructure/monitoring",
    "infrastructure/alerts",
    "infrastructure/backups",
    "services/payment-gateway/logs",
    "services/fraud-detection/config",
    "services/reporting/templates",
    "devops/ansible/roles",
    "devops/terraform/modules",
    "ci-cd/pipelines",
    "docs/runbooks",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "infrastructure/monitoring/prometheus.yml": """global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'payment-api'
    static_configs:
      - targets: ['localhost:8080']
""",
    "infrastructure/monitoring/grafana-dashboard.json": json.dumps({
        "title": "Fintech Dashboard",
        "panels": [{"type": "graph", "title": "Transaction Volume"}]
    }, indent=2),
    "infrastructure/alerts/pagerduty-config.yaml": """service_key: REDACTED
escalation_policy: P1-critical
silence_window: 300
""",
    "infrastructure/backups/backup-policy.txt": """Retention: 90 days
Frequency: Daily at 2am UTC
Target: s3://fintech-backups-prod
Encryption: AES-256
""",
    "services/payment-gateway/logs/2024-01-15.log": "\n".join([
        f"[2024-01-15 {h:02d}:00:00] INFO Transaction processed: TXN{random.randint(10000,99999)}"
        for h in range(24)
    ]),
    "services/fraud-detection/config/thresholds.json": json.dumps({
        "velocity_limit": 50,
        "amount_threshold": 10000,
        "geo_distance_km": 500
    }, indent=2),
    "services/reporting/templates/monthly-report.html": "<html><body><h1>Monthly Financial Report</h1></body></html>",
    "devops/ansible/roles/deploy.yml": """- name: Deploy services
  hosts: production
  tasks:
    - name: Restart payment service
      service: name=payment-api state=restarted
""",
    "devops/terraform/modules/vpc.tf": """resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
""",
    "ci-cd/pipelines/deploy.sh": "#!/bin/bash\necho 'Deploying to production...'\ndocker-compose up -d\n",
    "docs/runbooks/incident-response.md": """# Incident Response Runbook
1. Page on-call engineer
2. Assess severity
3. Initiate war room
""",
    "docs/runbooks/escalation-matrix.json": json.dumps({
        "P1": {"response_time": "5min", "contact": "cto@fintech.io"},
        "P2": {"response_time": "30min", "contact": "devops@fintech.io"}
    }, indent=2),
    "services/fraud-detection/config/model-metadata.txt": "Model: fraud-detector-v3.2\nAccuracy: 0.9987\nLastRetrained: 2024-01-01\n",
}

for path, content in distractors.items():
    full_path = workspace / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- THE PROBLEM: Business requirements document (messy, business-language only) ---
requirements_content = """
AUTOMATED TASK SCHEDULING REQUIREMENTS
Fintech Infrastructure Team — Q1 2025
======================================

We need to set up several recurring automated tasks on our production backend server.
The DevOps lead has identified the following requirements after the Q4 post-mortem:

JOBS TO SCHEDULE:
-----------------

JOB A: "check all APIs and alert if any is down"
  - Should run every 5 minutes, all day every day
  - CRITICAL: Must run on European time (Romania)
  - Priority: HIGH

JOB B: "generate monthly financial reconciliation report"
  - Should run on the first day of each month at 9am
  - No special timezone needed (default is fine)
  - Priority: HIGH

JOB C: "scan and quarantine suspicious transactions"
  - Should run every weekday at 6pm
  - CRITICAL: Must run on European time (Romania)
  - Priority: MEDIUM

JOB D: "archive old payment logs and compress audit trail"
  - Should run every weekend at noon
  - No special timezone needed (default is fine)  
  - Priority: LOW

JOB E: "sync fraud model weights from model registry"
  - Should run every hour
  - No special timezone needed (default is fine)
  - Priority: MEDIUM

LIFECYCLE REQUIREMENTS:
-----------------------
- Jobs C and D are not needed until next quarter. They should be SCHEDULED but immediately SUSPENDED (not deleted).
- All other jobs should remain active.

ALERTING REQUIREMENTS:
----------------------
- The team uses Telegram for all infrastructure alerts (not email, not Slack, not WhatsApp).
- Alerts should fire on any job failure.
- Log retention should be set to 60 days (compliance requirement).
- Default timezone for the scheduler should be Europe/Bucharest.

DELIVERABLE:
------------
- All jobs scheduled and configured as described above.
- A file named 'scheduled_jobs_report.json' capturing a summary of what was configured,
  including job IDs, their schedule descriptions, their status (active/paused), and
  the alert channel configured.
"""

(workspace / "docs" / "runbooks" / "scheduling-requirements.txt").write_text(requirements_content)

# Also place a copy in workspace root for visibility
(workspace / "SCHEDULING-REQUIREMENTS.txt").write_text(requirements_content)

print("Workspace initialized successfully.")
print(f"Structure created at: {workspace}")