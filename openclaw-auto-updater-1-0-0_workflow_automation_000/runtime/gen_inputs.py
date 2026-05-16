import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested DevOps project structure with distractor files
dirs = [
    "infra/terraform/modules/networking",
    "infra/terraform/modules/compute",
    "infra/k8s/deployments",
    "infra/k8s/services",
    "scripts/maintenance",
    "scripts/backup",
    "config/environments/prod",
    "config/environments/staging",
    "config/environments/dev",
    "logs/archive",
    "tools/monitoring",
    "tools/alerting",
    ".clawdbot",
    ".clawdbot/skills",
    ".clawdbot/cache",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "infra/terraform/modules/networking/main.tf": """
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "main-vpc" }
}
""",
    "infra/terraform/modules/compute/variables.tf": """
variable "instance_type" {
  default = "t3.medium"
}
variable "ami_id" {
  description = "AMI for the EC2 instance"
}
""",
    "infra/k8s/deployments/ai-assistant.yaml": """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-assistant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-assistant
""",
    "infra/k8s/services/ai-assistant-svc.yaml": """
apiVersion: v1
kind: Service
metadata:
  name: ai-assistant-svc
spec:
  selector:
    app: ai-assistant
  ports:
    - port: 80
""",
    "scripts/maintenance/disk_cleanup.sh": """#!/bin/bash
# Clean up old logs
find /var/log -name "*.log" -mtime +30 -delete
echo "Disk cleanup complete"
""",
    "scripts/backup/db_backup.sh": """#!/bin/bash
# Backup database nightly
pg_dump mydb > /backups/mydb_$(date +%Y%m%d).sql
""",
    "config/environments/prod/app.json": json.dumps({
        "database": {"host": "prod-db.internal", "port": 5432},
        "cache": {"ttl": 3600},
        "logging": {"level": "warn"}
    }, indent=2),
    "config/environments/staging/app.json": json.dumps({
        "database": {"host": "staging-db.internal", "port": 5432},
        "cache": {"ttl": 300},
        "logging": {"level": "debug"}
    }, indent=2),
    "config/environments/dev/app.json": json.dumps({
        "database": {"host": "localhost", "port": 5432},
        "cache": {"ttl": 60},
        "logging": {"level": "debug"}
    }, indent=2),
    "tools/monitoring/prometheus.yml": """
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'ai-assistant'
    static_configs:
      - targets: ['localhost:8080']
""",
    "tools/alerting/rules.yml": """
groups:
  - name: ai-assistant-alerts
    rules:
      - alert: HighMemoryUsage
        expr: memory_usage > 0.85
""",
    "logs/archive/.gitkeep": "",
    ".clawdbot/cache/.gitkeep": "",
}

# A partial/broken clawdbot config that exists but lacks cron configuration
clawdbot_config = {
    "version": "2026.1.9",
    "gateway": {
        "port": 3142,
        "autostart": True
    },
    "skills_dir": "/home/user/.clawdbot/skills",
    "telemetry": False
    # NOTE: no "cron" key — agent must add it
}

distractor_files[".clawdbot/config.json"] = json.dumps(clawdbot_config, indent=2)

# Skills metadata (distractor showing installed skills)
skills_data = {
    "installed": [
        {"name": "prd", "version": "2.0.3", "enabled": True},
        {"name": "browser", "version": "1.2.0", "enabled": True},
        {"name": "nano-banana-pro", "version": "3.1.0", "enabled": True},
        {"name": "gemini", "version": "1.5.0", "enabled": True},
        {"name": "sag", "version": "0.9.2", "enabled": True},
        {"name": "himalaya", "version": "2.1.0", "enabled": True},
    ]
}
distractor_files[".clawdbot/skills/manifest.json"] = json.dumps(skills_data, indent=2)

# A misleading old cron-related script that uses WRONG flags (trap for agents using training data)
distractor_files["scripts/maintenance/old_cron_setup.sh"] = """#!/bin/bash
# DEPRECATED - DO NOT USE
# Old way of setting up cron - no longer works with new clawdbot versions
clawdbot schedule --daily --time "04:00" --task "update" --background
"""

# Another distractor: a systemd service file (wrong approach)
distractor_files["infra/k8s/deployments/updater-cronjob.yaml"] = """
apiVersion: batch/v1
kind: CronJob
metadata:
  name: clawdbot-updater
spec:
  schedule: "0 4 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: updater
            image: clawdbot:latest
            command: ["clawdbot", "update"]
"""

for fpath, content in distractor_files.items():
    full_path = os.path.join(workspace, fpath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Create the command log directory where mock binaries will write
os.makedirs(os.path.join(workspace, ".clawdbot/command_log"), exist_ok=True)
with open(os.path.join(workspace, ".clawdbot/command_log/.gitkeep"), "w") as f:
    f.write("")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")