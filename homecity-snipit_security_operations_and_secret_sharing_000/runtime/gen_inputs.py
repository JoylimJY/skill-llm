import os
import random
import string

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor structure
dirs = [
    "ops/incidents/2024-Q1",
    "ops/incidents/2024-Q2",
    "ops/runbooks",
    "ops/alerts",
    "infra/terraform/modules/vpc",
    "infra/terraform/modules/rds",
    "infra/ansible/roles/webserver",
    "infra/ansible/roles/dbserver",
    "src/api/handlers",
    "src/api/middleware",
    "src/workers",
    "logs/archive",
    "logs/current",
    "secrets/old",
    "secrets/staging",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "ops/incidents/2024-Q1/incident-001.md": "# Incident 001\nDatabase outage on Jan 15. Root cause: misconfigured firewall.\n",
    "ops/incidents/2024-Q1/incident-002.md": "# Incident 002\nMemory leak in worker process. Resolved by rolling restart.\n",
    "ops/incidents/2024-Q2/postmortem.md": "# Q2 Postmortem\nMultiple alerts missed due to PagerDuty misconfiguration.\n",
    "ops/runbooks/db-failover.md": "# DB Failover Runbook\n1. Check replication lag\n2. Promote replica\n3. Update DNS\n",
    "ops/runbooks/deploy-rollback.md": "# Deploy Rollback\nUse `git revert` and re-trigger pipeline.\n",
    "ops/alerts/thresholds.yaml": "cpu_threshold: 85\nmemory_threshold: 90\ndisk_threshold: 80\n",
    "infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n',
    "infra/terraform/modules/rds/variables.tf": 'variable "db_instance_class" {\n  default = "db.t3.medium"\n}\n',
    "infra/ansible/roles/webserver/tasks.yaml": "- name: Install nginx\n  apt:\n    name: nginx\n    state: present\n",
    "infra/ansible/roles/dbserver/tasks.yaml": "- name: Install postgres\n  apt:\n    name: postgresql\n    state: present\n",
    "src/api/handlers/health.py": "def health_check():\n    return {'status': 'ok'}\n",
    "src/api/middleware/auth.py": "def authenticate(token):\n    # TODO: validate JWT\n    pass\n",
    "src/workers/cleanup.py": "import os\ndef cleanup_old_logs(days=30):\n    pass\n",
    "logs/archive/app-2024-01.log.gz": "binary-placeholder",
    "logs/current/app.log": "[2024-06-01 10:00:01] INFO  Service started\n[2024-06-01 10:00:02] INFO  Connected to database\n[2024-06-01 10:05:33] WARN  Slow query detected: 2300ms\n[2024-06-01 10:10:11] ERROR Connection pool exhausted\n",
    "secrets/old/db_creds_v1.env": "# DEPRECATED - do not use\nDB_HOST=old-db.internal\nDB_USER=admin\nDB_PASS=hunter2\n",
    "secrets/staging/api_keys.txt": "# Staging only - not for production\nSTRIPE_KEY=sk_test_abc123\nSENDGRID_KEY=SG.fake_key_here\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# THE ACTUAL PROBLEM FILES

# 1. The sensitive DB credentials file the agent must share securely (burn + expire 1w + password)
db_creds_content = """# Production Database Credentials - CONFIDENTIAL
DB_HOST=prod-db-primary.internal.corp
DB_PORT=5432
DB_NAME=payments_db
DB_USER=payments_svc
DB_PASSWORD=xK9#mP2$vL8@nQ4
DB_SSL_MODE=require
DB_SSL_CERT=/etc/ssl/certs/prod-db.crt
REPLICA_HOST=prod-db-replica.internal.corp
REPLICA_PORT=5432
"""

creds_path = os.path.join(workspace, "secrets", "prod_db_credentials.env")
with open(creds_path, "w") as f:
    f.write(db_creds_content)

# 2. A Python remediation script to share via curl API fallback (burn after read, language=python)
python_script_content = '''#!/usr/bin/env python3
"""
Incident Remediation Script - Connection Pool Reset
Run this during production incidents when pool exhaustion is detected.
"""
import psycopg2
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_connection_pool(host, port, dbname, user, password):
    """Terminate idle connections older than 10 minutes."""
    conn = psycopg2.connect(host=host, port=port, dbname=dbname,
                            user=user, password=password)
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s
          AND state = 'idle'
          AND query_start < NOW() - INTERVAL '10 minutes'
          AND pid <> pg_backend_pid();
    """, (dbname,))
    
    count = cur.rowcount
    logger.info(f"Terminated {count} idle connections")
    cur.close()
    conn.close()
    return count

if __name__ == "__main__":
    import os
    reset_connection_pool(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
'''

script_path = os.path.join(workspace, "src", "workers", "reset_pool.py")
with open(script_path, "w") as f:
    f.write(python_script_content)

print("Workspace generated successfully.")
print(f"Key files:")
print(f"  - {creds_path}")
print(f"  - {script_path}")