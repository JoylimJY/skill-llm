import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create realistic distractor directory structure
dirs = [
    "ops/monitoring/configs",
    "ops/monitoring/logs",
    "ops/alerting/rules",
    "ops/alerting/templates",
    "infra/terraform/modules",
    "infra/ansible/playbooks",
    "infra/ansible/roles",
    "services/api/src",
    "services/worker/src",
    "dashboards/grafana",
    "reports/weekly",
    "reports/incidents",
    "scripts/maintenance",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "ops/monitoring/configs/prometheus.yml": """global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
""",
    "ops/monitoring/configs/alert_thresholds.json": json.dumps({
        "cpu_critical": 90,
        "cpu_warning": 75,
        "memory_critical": 85,
        "disk_critical": 80,
        "process_count_max": 500
    }, indent=2),
    "ops/monitoring/logs/collector.log": "\n".join([
        "2024-01-15 10:00:01 INFO Collector started",
        "2024-01-15 10:00:05 INFO Metrics scraped successfully",
        "2024-01-15 10:01:05 WARN High CPU detected: 78%",
        "2024-01-15 10:02:05 INFO Metrics scraped successfully",
    ]),
    "ops/alerting/rules/cpu_rules.yaml": """groups:
  - name: cpu_alerts
    rules:
      - alert: HighCPU
        expr: cpu_percent > 80
        for: 5m
""",
    "ops/alerting/templates/email_template.txt": "ALERT: {{ alert_name }} triggered on {{ host }} at {{ timestamp }}",
    "infra/terraform/modules/compute.tf": """resource "aws_instance" "app" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.medium"
}
""",
    "infra/ansible/playbooks/deploy.yml": """---
- hosts: all
  tasks:
    - name: ensure service running
      service: name=myapp state=started
""",
    "infra/ansible/roles/monitoring.yml": "# Monitoring role placeholder\n",
    "services/api/src/main.py": "# API service - placeholder\n",
    "services/worker/src/worker.py": "# Background worker - placeholder\n",
    "dashboards/grafana/system_overview.json": json.dumps({
        "title": "System Overview",
        "panels": ["CPU", "Memory", "Disk"]
    }, indent=2),
    "reports/weekly/week_2024_03.md": "# Weekly Report\n\n- No incidents this week\n",
    "reports/incidents/INC-001.md": "# Incident 001\n\n**Date:** 2024-01-10\n**Severity:** P2\n",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\nfind /tmp -mtime +7 -delete\n",
    # Partial/stale health report that looks like a hint but is intentionally wrong format
    "reports/weekly/old_health_snapshot.json": json.dumps({
        "timestamp": "2024-01-01",
        "note": "STALE - do not use",
        "ram_used_pct": 77.3,
        "disk_used_pct": 55.1,
    }, indent=2),
}

for rel_path, content in distractor_files.items():
    fp = workspace / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# Create a README-free task description only in the task brief (not workspace)
# The agent should NOT have a readme pointing it to the solution.

# Create a brief that describes the business requirement (no hints about how)
brief = {
    "request_id": "DEVOPS-2024-447",
    "requester": "SRE Team Lead",
    "priority": "HIGH",
    "description": (
        "We need a consolidated system health snapshot for our automated alerting pipeline. "
        "The snapshot must include: the top 5 CPU-consuming processes, current memory utilization, "
        "and current disk utilization. Save it as system_health_report.json."
    ),
    "destination": "Root of the workspace",
    "format": "JSON",
    "process_limit": 5
}
(workspace / "ops" / "monitoring" / "configs" / "health_check_request.json").write_text(
    json.dumps(brief, indent=2)
)

print("Workspace initialized successfully.")