import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic, deeply nested distractor directory structure
dirs = [
    "infra/scripts/deploy",
    "infra/scripts/backup",
    "infra/config/nginx",
    "infra/config/postgres",
    "audit/reports/2023",
    "audit/reports/2024",
    "audit/logs",
    "security/policies",
    "security/certs",
    "src/app/utils",
    "src/app/models",
    "src/tests",
    "docs/runbooks",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files — realistic but irrelevant
distractor_files = {
    "infra/scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "infra/scripts/backup/backup.sh": "#!/bin/bash\ntar -czf /tmp/backup.tar.gz /data\n",
    "infra/config/nginx/nginx.conf": "server { listen 80; }\n",
    "infra/config/postgres/pg_hba.conf": "# PostgreSQL HBA config\nlocal all all trust\n",
    "audit/reports/2023/q4_summary.txt": "Q4 2023 Security Summary\nNo critical findings.\n",
    "audit/reports/2024/q1_summary.txt": "Q1 2024 Audit\nMinor misconfiguration in /etc/cron.d\n",
    "audit/logs/access.log": "2024-01-10 10:00:01 root LOGIN OK\n2024-01-10 10:05:22 appuser LOGIN FAIL\n",
    "security/policies/password_policy.md": "# Password Policy\nMin 12 chars, must include special character.\n",
    "security/certs/README.txt": "Store only PEM-encoded certs here.\n",
    "src/app/utils/helpers.py": "def sanitize(s): return s.strip()\n",
    "src/app/models/user.py": "class User: pass\n",
    "src/tests/test_helpers.py": "def test_sanitize(): assert True\n",
    "docs/runbooks/incident_response.md": "# Incident Response\nStep 1: Isolate affected host.\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# THE ACTUAL TASK FILE: a legacy permissions audit manifest with messy, mixed-format entries
# The agent must process each entry and produce a structured reference document

permissions_manifest = """\
# Legacy System Permissions Audit Manifest
# Finance Core Infrastructure — DO NOT MODIFY
# Last updated: 2019-03-14 by sysadmin@corp.internal
#
# Format: LABEL | PERMISSION_STRING | DESCRIPTION
#
ENTRY_A | rwsr-xr-x | Setuid binary used by billing daemon
ENTRY_B | rwxr-sr-x | Shared group executable for report generation
ENTRY_C | rwxr-xr-t | Shared directory with sticky bit for temp uploads
ENTRY_D | rw-r--r-- | Standard config file
ENTRY_E | 4750      | Privileged audit script (owner=root, group=auditors)
ENTRY_F | 2640      | Group-writable log file with setgid
ENTRY_G | 1777      | World-writable sticky temp directory
ENTRY_H | rwSr--r-- | Config with setuid but owner has NO execute
"""

manifest_path = os.path.join(workspace, "audit", "legacy_permissions_manifest.txt")
with open(manifest_path, "w") as f:
    f.write(permissions_manifest)

print("Workspace generated successfully.")
print(f"Manifest written to: {manifest_path}")