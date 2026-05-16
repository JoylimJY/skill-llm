import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create deeply nested distractor directory structure ---
dirs = [
    "infra/terraform/modules/vpc",
    "infra/terraform/modules/rds",
    "infra/terraform/envs/prod",
    "infra/terraform/envs/staging",
    "infra/ansible/roles/postgres",
    "infra/ansible/roles/monitoring",
    "migrations/v1/scripts",
    "migrations/v2/scripts",
    "migrations/v2/rollback",
    "migrations/legacy/dumps",
    "docs/adr",
    "docs/runbooks",
    "docs/postmortems",
    "src/etl/loaders",
    "src/etl/transformers",
    "src/api/routes",
    "src/api/models",
    "tests/integration",
    "tests/unit",
    "config/prod",
    "config/staging",
    "logs/migration",
    "scripts/maintenance",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }',
    "infra/terraform/modules/rds/main.tf": 'resource "aws_db_instance" "postgres" { engine = "postgres" engine_version = "14.5" }',
    "infra/terraform/envs/prod/terraform.tfvars": "region = \"us-east-1\"\ndb_instance_class = \"db.r6g.xlarge\"",
    "infra/terraform/envs/staging/terraform.tfvars": "region = \"us-east-1\"\ndb_instance_class = \"db.t3.medium\"",
    "infra/ansible/roles/postgres/tasks.yml": "- name: Install psql\n  apt:\n    name: postgresql-client",
    "infra/ansible/roles/monitoring/tasks.yml": "- name: Install pg_exporter\n  apt:\n    name: prometheus-postgres-exporter",
    "migrations/v1/scripts/001_initial_schema.sql": "CREATE TABLE shipments (id SERIAL PRIMARY KEY, status TEXT);",
    "migrations/v2/scripts/002_add_indexes.sql": "CREATE INDEX idx_status ON shipments(status);",
    "migrations/v2/rollback/002_rollback.sql": "DROP INDEX idx_status;",
    "migrations/legacy/dumps/dump_manifest.txt": "pg_dump --format=custom --compress=9 logistics_db > logistics_20230101.dump",
    "docs/adr/001_choose_aurora.md": "# ADR 001: Use Aurora PostgreSQL\n## Status: Accepted\n## Context: Need managed Postgres.",
    "docs/runbooks/db_failover.md": "# DB Failover Runbook\n1. Promote replica\n2. Update DNS\n3. Notify team",
    "docs/postmortems/2023_migration_outage.md": "# Postmortem: 4h outage during v1 migration\nRoot cause: missed FK constraints during dump.",
    "src/etl/loaders/pg_loader.py": "import psycopg2\ndef load(conn_str, data): pass",
    "src/etl/transformers/normalize.py": "def normalize_address(addr): return addr.strip().upper()",
    "src/api/routes/shipments.py": "from flask import Blueprint\nshipments_bp = Blueprint('shipments', __name__)",
    "src/api/models/shipment.py": "class Shipment:\n    def __init__(self, id, status): self.id = id; self.status = status",
    "tests/integration/test_db_connection.py": "def test_connection(): assert True",
    "tests/unit/test_normalize.py": "def test_normalize(): assert normalize_address(' abc ') == 'ABC'",
    "config/prod/db.conf": "host=prod-db.internal\nport=5432\ndbname=logistics_db\nuser=app_user",
    "config/staging/db.conf": "host=staging-db.internal\nport=5432\ndbname=logistics_db_stg\nuser=app_user",
    "logs/migration/migration_run_20230101.log": "[INFO] Starting migration\n[ERROR] FK constraint violation on orders table\n[INFO] Migration aborted",
    "scripts/maintenance/vacuum_analyze.sh": "#!/bin/bash\npsql -h $DB_HOST -U $DB_USER -c 'VACUUM ANALYZE;'",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM INPUT: A messy, incomplete project brief ---
brief_content = """
PROJECT BRIEF: LogiFlow Database Migration

Background:
Our logistics platform currently runs on 3 on-premise PostgreSQL 12 servers (shipments_db, inventory_db, orders_db).
We need to migrate all three to Amazon Aurora PostgreSQL 15 before the Q3 deadline.

Known issues from the last attempt (see postmortem):
- FK constraint violations were not caught before cutover
- DNS cutover was not coordinated with app teams
- No rollback procedure was tested

Scope:
- ~200 tables across 3 databases
- 6 microservices depending on these databases (see src/api/)
- External analytics pipeline (BigQuery) reads from a Postgres replica
- Estimated ~48 hours of total migration work
- Possible involvement of DBA sub-team for schema validation

Constraints:
- Zero-downtime migration required (max 15 min maintenance window)
- BigQuery pipeline cannot be broken
- All FK and trigger logic must be validated before cutover
- Staging migration must complete successfully before production

Current blockers:
- Aurora IAM auth not yet configured (security team dependency)
- Legacy dump from 2023 needs re-validation before use

Please produce a thorough execution plan for this migration.
The plan should be saved as: migration_plan.md
"""

with open(os.path.join(WORKSPACE, "project_brief.txt"), "w") as f:
    f.write(brief_content)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")