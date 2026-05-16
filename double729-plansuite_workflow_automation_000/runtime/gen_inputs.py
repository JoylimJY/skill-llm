import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create templates/ directory with template files (as per SKILL.md) ---
templates_dir = workspace / "templates"
templates_dir.mkdir(exist_ok=True)

(templates_dir / "task_plan.md").write_text(
"""# Task Plan

## Background & Objective

## Scope
### In Scope

### Out of Scope

## Risks & Rollback

## Milestones / Sub-Plans

### Milestone 1: [Name]
- **Input:**
- **Output:**
- **Acceptance Criteria:**
- **Estimated Tool Calls / File Changes:**
- **Risks & Rollback Point:**

""")

(templates_dir / "progress.md").write_text(
"""# Progress

## Done

## Next

## Blockers

""")

(templates_dir / "findings.md").write_text(
"""# Findings

## Key Decisions

## Issues / Pitfalls

## Verification Commands

## Rollback Steps

""")

# --- Create deeply nested distractor files ---
distractor_dirs = [
    "legacy_db/schemas/v1",
    "legacy_db/schemas/v2",
    "legacy_db/migrations/applied",
    "legacy_db/migrations/pending",
    "legacy_db/backups",
    "new_db/schemas",
    "new_db/seed_data",
    "scripts/etl",
    "scripts/validation",
    "docs/architecture",
    "docs/decisions",
    "infra/terraform",
    "infra/docker",
    "tests/unit",
    "tests/integration",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Legacy schema DDL files
(workspace / "legacy_db/schemas/v1/transactions.sql").write_text(
"""CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    acct_num VARCHAR(20),
    amount DECIMAL(15,2),
    txn_date TIMESTAMP,
    status CHAR(1),  -- 'P' pending, 'C' cleared, 'F' failed
    notes TEXT
);
""")

(workspace / "legacy_db/schemas/v1/accounts.sql").write_text(
"""CREATE TABLE accounts (
    acct_num VARCHAR(20) PRIMARY KEY,
    owner_name VARCHAR(100),
    opened_date DATE,
    balance DECIMAL(15,2),
    acct_type CHAR(1)  -- 'C' checking, 'S' savings
);
""")

(workspace / "legacy_db/schemas/v2/transactions_v2.sql").write_text(
"""CREATE TABLE transactions_v2 (
    txn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id BIGINT REFERENCES accounts_v2(id),
    amount_cents BIGINT NOT NULL,
    currency CHAR(3) DEFAULT 'USD',
    initiated_at TIMESTAMPTZ,
    settled_at TIMESTAMPTZ,
    state VARCHAR(20) CHECK (state IN ('pending','cleared','failed','reversed')),
    metadata JSONB
);
""")

(workspace / "legacy_db/schemas/v2/accounts_v2.sql").write_text(
"""CREATE TABLE accounts_v2 (
    id BIGSERIAL PRIMARY KEY,
    legacy_acct_num VARCHAR(20) UNIQUE,
    owner_id BIGINT REFERENCES customers(id),
    opened_at TIMESTAMPTZ,
    balance_cents BIGINT DEFAULT 0,
    account_type VARCHAR(20) CHECK (account_type IN ('checking','savings','credit'))
);
""")

(workspace / "legacy_db/migrations/applied/001_initial.sql").write_text(
"-- Applied: initial schema creation 2022-01-15\n")

(workspace / "legacy_db/migrations/applied/002_add_notes.sql").write_text(
"-- Applied: added notes column to transactions 2022-06-01\n")

(workspace / "legacy_db/migrations/pending/003_migrate_to_v2.sql").write_text(
"-- PENDING: full migration to v2 schema - NOT YET APPLIED\n-- Requires: data type conversion, UUID generation, balance recalculation\n")

(workspace / "legacy_db/backups/backup_manifest.txt").write_text(
"backup_2024_01_10.dump  size=4.2GB  checksum=a3f9d2\nbackup_2024_02_01.dump  size=4.3GB  checksum=b7e1c4\n")

(workspace / "new_db/schemas/customers.sql").write_text(
"""CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    kyc_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
""")

(workspace / "new_db/seed_data/currency_codes.csv").write_text(
"USD,US Dollar\nEUR,Euro\nGBP,British Pound\nJPY,Japanese Yen\n")

(workspace / "scripts/etl/extract_legacy.py").write_text(
"#!/usr/bin/env python3\n# TODO: implement legacy extraction\nprint('extract_legacy: not implemented')\n")

(workspace / "scripts/etl/transform_amounts.py").write_text(
"#!/usr/bin/env python3\n# Converts DECIMAL(15,2) dollar amounts to BIGINT cents\ndef to_cents(amount):\n    return int(round(amount * 100))\n")

(workspace / "scripts/validation/check_balances.py").write_text(
"#!/usr/bin/env python3\n# Validates that sum of transactions matches account balance\nprint('check_balances: stub')\n")

(workspace / "scripts/validation/row_count_check.sh").write_text(
"#!/bin/bash\n# Compare row counts between legacy and new tables\necho 'row_count_check: stub'\n")

(workspace / "docs/architecture/data_flow.txt").write_text(
"Legacy PG 12 --> ETL Pipeline --> New PG 15\nKey changes: UUID keys, cents-based amounts, JSONB metadata, stricter enums\n")

(workspace / "docs/decisions/adr_001_uuid_keys.txt").write_text(
"ADR-001: Use UUID for txn_id in v2\nStatus: Accepted\nReason: Globally unique, avoids sequence exhaustion\n")

(workspace / "docs/decisions/adr_002_cents.txt").write_text(
"ADR-002: Store monetary amounts as integer cents\nStatus: Accepted\nReason: Avoids floating-point rounding errors in financial calculations\n")

(workspace / "infra/terraform/main.tf").write_text(
"# Terraform config for RDS PostgreSQL 15 instance\n# provider = aws, region = us-east-1\n")

(workspace / "infra/docker/docker-compose.yml").write_text(
"""version: '3.8'
services:
  legacy_pg:
    image: postgres:12
    environment:
      POSTGRES_DB: ledger_legacy
  new_pg:
    image: postgres:15
    environment:
      POSTGRES_DB: ledger_new
""")

(workspace / "tests/unit/test_transform.py").write_text(
"import pytest\ndef test_cents_conversion():\n    from scripts.etl.transform_amounts import to_cents\n    assert to_cents(10.50) == 1050\n    assert to_cents(0.01) == 1\n")

(workspace / "tests/integration/test_migration_integrity.py").write_text(
"# Integration test: verify full row migration\n# Requires both DB instances running\nprint('integration tests: skipped in CI without DBs')\n")

# A messy notes file left by a previous engineer
(workspace / "docs/architecture/NOTES_SCRATCH.txt").write_text(
"""SCRATCH NOTES - DO NOT USE AS OFFICIAL PLAN

things to do maybe:
- migrate accounts first or transactions first? unclear
- what about foreign keys during migration? disable constraints?
- rollback if row counts dont match?
- need to handle NULL notes -> empty JSONB?
- balance recalculation: sum all cleared transactions or use stored balance?
- timeline: probably 3-4 weeks?
""")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")