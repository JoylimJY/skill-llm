#!/usr/bin/env python3
"""
Generate a realistic DevOps sandbox workspace for a microservice migration project.
The agent must use the openclaw workflow skill to produce an auditable execution trail.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Distractor directory structure ─────────────────────────────────────────
dirs = [
    "services/auth-service/src",
    "services/auth-service/tests",
    "services/payment-service/src",
    "services/payment-service/config",
    "services/notification-service/src",
    "infra/terraform/modules/vpc",
    "infra/terraform/modules/rds",
    "infra/k8s/overlays/staging",
    "infra/k8s/overlays/production",
    "docs/architecture",
    "docs/runbooks",
    "scripts/migrations",
    "scripts/rollback",
    ".github/workflows",
    "monitoring/grafana/dashboards",
    "monitoring/alerts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "services/auth-service/src/main.py": '# Auth service entry point\nprint("auth running")\n',
    "services/auth-service/tests/test_auth.py": '# placeholder tests\nassert True\n',
    "services/payment-service/src/handler.js": 'module.exports = () => console.log("payment");\n',
    "services/payment-service/config/env.example": 'DB_HOST=localhost\nDB_PORT=5432\nSECRET=changeme\n',
    "services/notification-service/src/sender.py": '# sends emails\npass\n',
    "infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }\n',
    "infra/terraform/modules/rds/variables.tf": 'variable "db_name" { default = "appdb" }\n',
    "infra/k8s/overlays/staging/kustomization.yaml": 'apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n',
    "infra/k8s/overlays/production/kustomization.yaml": 'apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n',
    "docs/architecture/overview.md": '# Monolith → Microservices\nMigration planned for Q3.\n',
    "docs/runbooks/incident_response.md": '# Incident Response\n1. Page on-call\n2. Assess blast radius\n',
    "scripts/migrations/001_create_users.sql": 'CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT NOT NULL);\n',
    "scripts/migrations/002_create_orders.sql": 'CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT REFERENCES users(id));\n',
    "scripts/rollback/rollback_001.sql": 'DROP TABLE IF EXISTS users;\n',
    ".github/workflows/ci.yml": 'name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n',
    "monitoring/grafana/dashboards/services.json": json.dumps({"title": "Services Overview", "panels": []}, indent=2) + "\n",
    "monitoring/alerts/cpu_high.yaml": 'alert: CpuHigh\nexpr: cpu_usage > 0.9\nfor: 5m\n',
}

for rel_path, content in distractor_files.items():
    file_path = WORKSPACE / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)

# ─── The actual task brief ───────────────────────────────────────────────────
# This is the PROBLEM document the agent must act upon.
# It is NOT a README or hint — it is raw project intake data.
task_brief = """\
PROJECT INTAKE FORM
===================
Project ID  : msvc-decomp-2024
Project Name: Monolith Decomposition — Phase 1
Owner       : Platform Engineering Team
Priority    : HIGH

Phases identified:
  1. Audit existing monolith endpoints
  2. Define service boundaries
  3. Scaffold new microservices
  4. Deploy to staging
  5. Validate integration tests

Disaster Recovery Note:
  Mid-project context snapshots are MANDATORY before any compaction event.
  Snapshot must record: task name, current findings, and remaining work.

Compliance Note:
  All workflow state changes must be formally logged through the
  approved state management tooling. Skipping states is not permitted.

Delegation Check:
  At the DELEGATING phase, a context percentage of 42 must be evaluated.
"""

(WORKSPACE / "project_intake.txt").write_text(task_brief)

# ─── Erroneous prior attempt artifacts (messy real-world data) ───────────────
# Simulates a failed/incomplete previous attempt that the agent should NOT rely on
bad_tracker = {
    "task": "msvc-decomp-2024",
    "steps": ["1. Audit", "2. Boundaries", "3. Scaffold"],  # wrong format, incomplete
    "status": "abandoned",
    "note": "Do not use this file — previous attempt was aborted"
}
(WORKSPACE / "scripts/migrations/.tracker_abandoned.json").write_text(
    json.dumps(bad_tracker, indent=2) + "\n"
)

bad_state = {
    "task_id": "msvc-decomp-2024",
    "state": "EXECUTING",  # mid-state, invalid starting point
    "note": "Stale state file from aborted run — ignore"
}
(WORKSPACE / "infra/.stale_state.json").write_text(
    json.dumps(bad_state, indent=2) + "\n"
)

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))}")