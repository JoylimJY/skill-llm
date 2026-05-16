import os
import json
import random
import time
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure (distractor files) ──────────────────────────────────
dirs = [
    "infra/terraform/modules/vpc",
    "infra/terraform/modules/rds",
    "infra/k8s/manifests",
    "infra/k8s/helm",
    "services/api-gateway/src",
    "services/api-gateway/tests",
    "services/payment-processor/src",
    "services/auth/src",
    "ops/runbooks",
    "ops/dashboards",
    "ops/scripts/legacy",
    "monitoring/alerts",
    "monitoring/grafana",
    "logs/archive",
    "config/environments",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }',
    "infra/terraform/modules/rds/variables.tf": 'variable "db_password" { type = string }',
    "infra/k8s/manifests/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-gateway",
    "infra/k8s/helm/values.yaml": "replicaCount: 3\nimage:\n  tag: latest",
    "services/api-gateway/src/index.js": "const express = require('express');\nconst app = express();\napp.listen(3000);",
    "services/api-gateway/tests/health.test.js": "describe('health', () => { it('returns 200', () => {}); });",
    "services/payment-processor/src/processor.py": "def process(txn):\n    return {'status': 'ok', 'txn': txn}",
    "services/auth/src/jwt_handler.py": "import jwt\ndef verify(token): pass",
    "ops/runbooks/database_failover.md": "# DB Failover\n1. Promote replica\n2. Update DNS",
    "ops/dashboards/latency_p99.json": json.dumps({"dashboard": "latency", "threshold_ms": 200}),
    "ops/scripts/legacy/restart_all.sh": "#!/bin/bash\necho 'DEPRECATED: use nexus-safe instead'",
    "monitoring/alerts/high_cpu.yaml": "alert: HighCPU\nexpr: cpu_usage > 90\nfor: 5m",
    "monitoring/grafana/datasources.yaml": "apiVersion: 1\ndatasources:\n  - name: Prometheus",
    "logs/archive/api-gateway-2024-01-15.log": "[2024-01-15 03:12:01] ERROR payment route timeout\n[2024-01-15 03:12:45] FATAL worker crash\n",
    "config/environments/production.env": "NODE_ENV=production\nPORT=3000\nDB_HOST=prod-db.internal",
    "config/environments/staging.env": "NODE_ENV=staging\nPORT=3001\nDB_HOST=staging-db.internal",
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
# Skill: Nexus-Safe (V1.3.0)

Autonomous local System Reliability Agent for OpenClaw.

## 🛡️ Privacy & Security Policy
- **Runtime Privacy**: Strictly 100% local. No metrics, logs, or system data ever leave your server. No outbound network calls are performed by the script.
- **Setup Notice**: An internet connection is required **only during initial setup** to install the `psutil` dependency via `pip`.
- **Safe-by-default**: Recovery actions are locked until explicitly enabled.

## 📋 Capabilities
- **/nexus-safe status** : Real-time system health (CPU, RAM, Disk, Load).
- **/nexus-safe logs <service>** : Diagnostic log retrieval (Docker/PM2).
- **/nexus-safe recover <service>** : Policy-controlled service restart.

## ⚙️ Logic & Enforcement
- **Allowlist Required**: Restarts only work for services in `NEXUS_SAFE_ALLOWED_DOCKER/PM2`.
  - Set environment variable `NEXUS_SAFE_ALLOWED_PM2` as a comma-separated list of PM2 service names (e.g. `export NEXUS_SAFE_ALLOWED_PM2="api-gateway,worker"`).
  - Set environment variable `NEXUS_SAFE_ALLOWED_DOCKER` as a comma-separated list of Docker container names.
- **Logs-First Policy**: The tool blocks recovery if logs haven't been reviewed within the last 5 minutes.
- **Rate Limiting**: Sliding window protection (Max 3 restarts per hour).

## 🚀 Installation
1. `pip install psutil`
2. Ensure `docker` and `pm2` are installed and in your PATH.

## 💻 Usage Examples

```bash
# Check overall system health
nexus-safe status

# Retrieve recent logs for a PM2-managed service
nexus-safe logs api-gateway

# Recover (restart) a service after reviewing logs
nexus-safe recover api-gateway
```

## 📄 Output Behavior
- All commands print structured output to stdout.
- `nexus-safe recover` exits with code 0 on successful restart, code 1 on policy violation or failure.
- On successful recover, a JSON summary is printed to stdout with keys: `service`, `action`, `status`, `timestamp`.
"""
(workspace / "SKILL.md").write_text(skill_md)

# ── Incident context file (simulates a PagerDuty-style alert dump) ───────────
incident_ctx = {
    "incident_id": "INC-20240312-0047",
    "severity": "P1",
    "title": "api-gateway PM2 process unresponsive – payment throughput dropped to 0",
    "reported_at": "2024-03-12T14:22:00Z",
    "affected_service": "api-gateway",
    "runtime": "pm2",
    "last_known_good": "2024-03-12T13:55:00Z",
    "on_call_engineer": "agent",
    "instructions": (
        "Use the installed local reliability tooling (see SKILL.md) to perform a "
        "proper diagnostic review of the affected service and then trigger an "
        "authorized restart. Record the full incident response outcome in a file "
        "named incident_report.json at the workspace root."
    ),
}
(workspace / "incident_context.json").write_text(json.dumps(incident_ctx, indent=2))

# ── State directory used by the nexus-safe mock ───────────────────────────────
state_dir = workspace / ".nexus_safe_state"
state_dir.mkdir(exist_ok=True)
# Start with an EMPTY state (no prior logs reviewed, no prior restarts)
(state_dir / "restart_log.json").write_text(json.dumps([]))
# No logs_reviewed file exists yet → forces agent to run logs first

print("Workspace generated successfully.")