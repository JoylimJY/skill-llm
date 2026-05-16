import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create a realistic, deeply nested directory structure with distractor files ---

dirs = [
    "infra/terraform/modules/networking",
    "infra/terraform/modules/compute",
    "infra/terraform/environments/prod",
    "infra/terraform/environments/staging",
    "infra/ansible/playbooks",
    "infra/ansible/roles/common/tasks",
    "infra/ansible/roles/webserver",
    "services/api-gateway/src",
    "services/api-gateway/tests",
    "services/auth-service/src",
    "services/auth-service/config",
    "docs/architecture",
    "docs/architecture/decisions",
    "docs/runbooks",
    "scripts/ci",
    "scripts/deploy",
    ".github/workflows",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "infra/terraform/modules/networking/main.tf": """
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "main-vpc" }
}
""",
    "infra/terraform/modules/compute/main.tf": """
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}
""",
    "infra/terraform/environments/prod/terraform.tfvars": """
region       = "us-east-1"
environment  = "production"
instance_count = 3
""",
    "infra/terraform/environments/staging/terraform.tfvars": """
region       = "us-west-2"
environment  = "staging"
instance_count = 1
""",
    "infra/ansible/playbooks/site.yml": """
---
- name: Configure webservers
  hosts: webservers
  roles:
    - common
    - webserver
""",
    "infra/ansible/roles/common/tasks/main.yml": """
---
- name: Update apt cache
  apt: update_cache=yes
""",
    "services/api-gateway/src/main.py": """
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
""",
    "services/api-gateway/tests/test_health.py": """
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
""",
    "services/auth-service/src/auth.py": """
import jwt

def verify_token(token: str) -> dict:
    return jwt.decode(token, options={"verify_signature": False})
""",
    "services/auth-service/config/settings.yaml": """
jwt_secret: changeme
token_expiry: 3600
redis_url: redis://localhost:6379
""",
    "docs/architecture/system-overview.md": """
# System Architecture

## Components
- API Gateway: Routes requests to backend services
- Auth Service: Handles authentication and authorization
- Worker Pool: Processes async jobs

## Data Flow
Client -> API Gateway -> Auth Service -> Backend Services
""",
    "docs/runbooks/incident-response.md": """
# Incident Response Runbook

## Steps
1. Acknowledge alert in PagerDuty
2. Check service health dashboards
3. Review recent deployments
4. Escalate if not resolved in 15 minutes
""",
    "scripts/ci/run-tests.sh": """#!/bin/bash
set -e
pytest services/ --cov=services --cov-report=xml
""",
    "scripts/deploy/deploy.sh": """#!/bin/bash
set -e
echo "Deploying to $ENVIRONMENT"
terraform apply -auto-approve
ansible-playbook infra/ansible/playbooks/site.yml
""",
    ".github/workflows/ci.yml": """
name: CI Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: bash scripts/ci/run-tests.sh
""",
    "docs/architecture/decisions/adr-001-api-gateway.md": """
# ADR 001: Use API Gateway Pattern

## Status: Accepted

## Context
We need a single entry point for all client requests.

## Decision
Implement an API Gateway using FastAPI.

## Consequences
All traffic routes through the gateway, enabling centralized auth.
""",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.write_text(content.strip() + "\n")

# --- THE PROBLEM: A messy, incomplete, but active FOCUS.md representing an old project ---
# This is deliberately malformed: missing Sub-Agents section, Active State is vague,
# but the format is close enough to be recognizable. The agent must archive this.

focus_md_content = """# FOCUS — Database Migration to PostgreSQL
**Started:** 2024-11-15 09:00 UTC
**Status:** active
**Context:** Moving from MySQL 5.7 to PostgreSQL 14 to support JSON columns and better indexing

## Objective
Migrate all 12 production database tables from MySQL 5.7 to PostgreSQL 14 with zero data loss and minimal downtime using a blue-green deployment strategy.

## Plan
- [x] Step 1 — Audit all MySQL schemas and document column types
- [x] Step 2 — Set up PostgreSQL 14 RDS instance in staging
- [x] Step 3 — Write and test pgloader migration scripts for 8 of 12 tables
- [x] Step 4 — Migrate remaining 4 tables (orders, order_items, payments, refunds)
- [x] Step 5 — Run full integration test suite against PostgreSQL staging
- [x] Step 6 — Update all ORM models and connection strings in codebase
- [x] Step 7 — Deploy to production with blue-green cutover
- [x] Step 8 — Monitor error rates and query performance for 48 hours
- [ ] Step 9 — Decommission MySQL instance and remove legacy connection code

## Active State
All migration steps complete. Currently in 48-hour monitoring window post-cutover. Error rates nominal, p99 latency improved by 18%. Waiting for monitoring window to close before decommissioning MySQL.

## Blockers
None currently. Monitoring window ends 2024-11-17 14:00 UTC.
"""

(workspace / "FOCUS.md").write_text(focus_md_content.strip() + "\n")

# No FOCUS-LOG.md exists yet — agent must create it
# No hints or READMEs about what to do

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")