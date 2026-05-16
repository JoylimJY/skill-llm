import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "services/gateway/config",
    "services/gateway/logs",
    "services/auth/config",
    "services/auth/logs",
    "infra/terraform/modules",
    "infra/ansible/playbooks",
    "data/raw/2024",
    "data/processed/2024",
    "reports/weekly",
    "reports/monthly",
    "tmp/scratch",
    "docs/runbooks",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "services/gateway/config/gateway.yaml": "host: 0.0.0.0\nport: 8080\ntimeout: 30\n",
    "services/gateway/config/tls.conf": "ssl_cert=/etc/ssl/certs/gateway.crt\nssl_key=/etc/ssl/private/gateway.key\n",
    "services/gateway/logs/access.log": "2024-01-15 10:00:01 GET /api/v1/health 200\n2024-01-15 10:00:05 POST /api/v1/auth 401\n",
    "services/auth/config/auth.json": json.dumps({"provider": "ldap", "timeout": 5000, "retries": 3}, indent=2),
    "services/auth/logs/auth.log": "ERROR: failed login attempt from 192.168.1.100\nINFO: token issued for user admin\n",
    "infra/terraform/modules/main.tf": 'resource "aws_instance" "app" { ami = "ami-0abcdef" instance_type = "t3.medium" }\n',
    "infra/ansible/playbooks/deploy.yml": "---\n- hosts: all\n  tasks:\n    - name: restart app\n      service: name=myapp state=restarted\n",
    "data/raw/2024/transactions.csv": "id,amount,status\n1,100.00,ok\n2,250.50,failed\n3,75.00,ok\n",
    "data/processed/2024/summary.json": json.dumps({"total": 3, "ok": 2, "failed": 1, "sum": 425.50}, indent=2),
    "reports/weekly/week-03.md": "# Week 3 Report\n\n- Transactions processed: 3\n- Errors: 1\n",
    "reports/monthly/jan-2024.txt": "Monthly summary: 87 transactions, 5 failures\n",
    "tmp/scratch/test_output.txt": "ad-hoc test run output - ignore\n",
    "docs/runbooks/incident-response.md": "# Incident Response\n1. Page on-call\n2. Diagnose\n3. Fix\n4. Post-mortem\n",
}
for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── Partial/broken scripts directory (the automation skill's workspace) ──────
scripts_dir = workspace / "scripts"
for sub in ["templates", "custom", "logs"]:
    (scripts_dir / sub).mkdir(parents=True, exist_ok=True)

# Broken/incomplete config — agent must NOT use this; the skill tool manages it
bad_config = {
    "automation": {
        "enabled": False,           # wrong: should be true
        "logRetentionDays": 7,      # wrong: should be 30
        "maxRetries": 1,            # wrong: should be 3
        "retryDelay": 10,           # wrong: should be 60
        "notifications": {
            "onFailure": False,      # wrong
            "onSuccess": True
        }
    }
}
(scripts_dir / "config.conf").write_text(json.dumps(bad_config, indent=2))

# Stale/wrong template stubs to confuse the agent
(scripts_dir / "templates" / "monitor.sh").write_text(
    "#!/bin/bash\n# STUB: monitor template - do not use directly\necho 'monitor stub'\n"
)
(scripts_dir / "templates" / "backup.sh").write_text(
    "#!/bin/bash\n# STUB: backup template - do not use directly\necho 'backup stub'\n"
)
(scripts_dir / "templates" / "sync.sh").write_text(
    "#!/bin/bash\n# STUB: sync template\necho 'sync stub'\n"
)
(scripts_dir / "templates" / "report.sh").write_text(
    "#!/bin/bash\n# STUB: report template\necho 'report stub'\n"
)

# A deliberately mis-named existing script to test naming convention awareness
(scripts_dir / "custom" / "configsave.sh").write_text(
    "#!/bin/bash\n# old ad-hoc config save - NOT managed by automation skill\ncp -r /etc/myapp /tmp/configsave_$(date +%Y%m%d)\n"
)

# Orphaned log with wrong format
(scripts_dir / "logs" / "old-run.log").write_text(
    "ran at some point, result unknown\n"
)

print("Workspace scaffold created successfully.")
print(f"Directory tree rooted at: {workspace}")