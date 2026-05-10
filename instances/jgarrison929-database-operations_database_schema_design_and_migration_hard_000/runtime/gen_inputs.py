import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic distractor directory structure ---
dirs = [
    "workspace/legacy_schema",
    "workspace/app/models",
    "workspace/app/controllers",
    "workspace/app/services",
    "workspace/migrations/old",
    "workspace/migrations/drafts",
    "workspace/docs/architecture",
    "workspace/docs/runbooks",
    "workspace/infra/terraform",
    "workspace/infra/helm",
    "workspace/scripts/etl",
    "workspace/scripts/backup",
    "workspace/tests/integration",
    "workspace/tests/unit",
    "workspace/config/environments",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files (realistic but irrelevant) ---

# Old broken migration file
Path("workspace/migrations/old/001_initial_schema.sql").write_text("""
-- DEPRECATED: Do not use this migration
CREATE TABLE orders_flat (
  id INTEGER,
  user_id INTEGER,
  total FLOAT,  -- bad: should be DECIMAL
  status VARCHAR(20),
  created_at TIMESTAMP
);
-- NOTE: This was replaced by the partitioned approach
""")

Path("workspace/migrations/old/002_add_users.sql").write_text("""
-- Old migration - superseded
CREATE TABLE users_old (
  id SERIAL PRIMARY KEY,
  name TEXT,
  email TEXT
);
""")

Path("workspace/migrations/drafts/draft_partitioning.sql").write_text("""
-- DRAFT - INCOMPLETE - DO NOT USE
-- Attempt at partitioning, abandoned
CREATE TABLE orders_v2 (
  id BIGSERIAL,
  created_at TIMESTAMPTZ
) PARTITION BY RANGE (created_at);
-- TODO: Create partitions
-- TODO: Add indexes
""")

Path("workspace/docs/architecture/database_design.md").write_text("""
# Database Architecture Notes

## Current Problems
- orders table has 50M+ rows and queries are slow
- No audit trail for compliance (GDPR requirement)
- Search on product attributes using LIKE '%value%' is catastrophic
- No soft delete mechanism
- Foreign key columns not indexed

## Requirements (from architecture review 2024-03)
1. Monthly data partitioning for orders (2024-01, 2024-02, 2024-03)
2. Full audit logging for orders table changes
3. Proper indexing strategy:
   - user_id + status composite with covering columns (total, created_at)
   - JSONB attributes column needs proper index
   - Low inventory partial index (inventory_tracking=true AND quantity <= 5)
4. Soft delete support
5. Product full-text search capability

## IMPORTANT Business Rules
- Partition function must handle auto-creation for any given date
- Audit log must capture old AND new values for UPDATE operations
- All indexes must be safe for production (no locking)
- Money columns must NEVER be stored as FLOAT
""")

Path("workspace/docs/architecture/compliance_requirements.txt").write_text("""
COMPLIANCE NOTES - Legal & Engineering Review

Regulation: GDPR Article 30 - Records of Processing Activities
Requirement: All modifications to order records must be logged with:
  - The operation type (INSERT/UPDATE/DELETE)
  - Previous state of the record
  - New state of the record
  - Timestamp of the change

Implementation must use database-level triggers, not application-level.
The audit_log table must reference orders table via record_id.
""")

Path("workspace/docs/runbooks/slow_query_runbook.md").write_text("""
# Slow Query Investigation Runbook

## Step 1: Identify slow queries
Use pg_stat_statements to find queries with mean_exec_time > 100ms

## Step 2: Run EXPLAIN ANALYZE
Always use EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)

## Step 3: Check for missing indexes
Look for Seq Scans on large tables

## Known problem queries:
SELECT * FROM orders WHERE user_id = X AND status = 'pending'  -- needs composite index
SELECT * FROM products WHERE attributes @> '{"brand": "Nike"}' -- needs GIN index
SELECT * FROM products WHERE inventory_tracking = true AND inventory_quantity <= 5 -- needs partial index
""")

Path("workspace/app/models/order.py").write_text("""
# Python SQLAlchemy model - application layer
# NOTE: DB schema is managed separately via SQL migrations

class Order:
    id: int
    user_id: int
    total: float  # BUG: should use Decimal - pending fix
    status: str
    attributes: dict
    created_at: datetime
    deleted_at: datetime = None
""")

Path("workspace/app/models/product.py").write_text("""
class Product:
    id: int
    name: str
    description: str
    sku: str
    inventory_quantity: int
    inventory_tracking: bool
    attributes: dict  # JSONB in DB
    search_vector: object  # tsvector - generated column
""")

Path("workspace/app/controllers/order_controller.py").write_text("""
# WARNING: N+1 problem here - needs EF Core Include fix
def get_orders_with_items(user_id):
    orders = db.query("SELECT * FROM orders WHERE user_id = %s", user_id)
    for order in orders:
        # N+1: separate query per order!
        order.items = db.query("SELECT * FROM order_items WHERE order_id = %s", order.id)
    return orders
""")

Path("workspace/app/services/search_service.py").write_text("""
# Anti-pattern: using LIKE for search
def search_products(term):
    # BAD: Full table scan
    return db.query(f"SELECT * FROM products WHERE name LIKE '%{term}%'")
    # Should use: WHERE search_vector @@ to_tsquery('english', %s)
""")

Path("workspace/scripts/etl/import_orders.py").write_text("""
# ETL script for importing historical orders
# Assumes orders table exists with partitioning

import psycopg2
import csv

def import_from_csv(filepath, conn):
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Inserts will auto-route to correct partition
            cursor.execute(
                'INSERT INTO orders (user_id, total, status, created_at) VALUES (%s, %s, %s, %s)',
                (row['user_id'], row['total'], row['status'], row['created_at'])
            )
""")

Path("workspace/scripts/backup/pg_backup.sh").write_text("""#!/bin/bash
# Daily backup script
pg_dump -h localhost -U postgres -d ecommerce_db -f /backups/ecommerce_$(date +%Y%m%d).dump
""")

Path("workspace/infra/terraform/main.tf").write_text("""
resource "aws_db_instance" "ecommerce" {
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.r6g.xlarge"
  storage_type   = "gp3"
}
""")

Path("workspace/config/environments/production.env").write_text("""
DATABASE_URL=postgresql://app_user:secret@db.internal:5432/ecommerce_db
REDIS_URL=redis://cache.internal:6379/0
POOL_MAX=20
POOL_IDLE_TIMEOUT_MS=30000
POOL_CONNECTION_TIMEOUT_MS=2000
""")

Path("workspace/tests/integration/test_orders.py").write_text("""
# Integration tests - require partitioned orders table

def test_partition_routing():
    # Insert order in Jan 2024 - should land in orders_2024_01
    order = insert_order(created_at='2024-01-15')
    assert order is not None

def test_audit_trail():
    # Update an order - should create audit log entry
    update_order(id=1, status='shipped')
    log = get_audit_log('orders', 1)
    assert log.operation == 'UPDATE'
    assert log.old_values is not None
    assert log.new_values is not None
""")

Path("workspace/tests/unit/test_soft_delete.py").write_text("""
def test_soft_delete():
    # soft_delete('orders', 1) should set deleted_at, not remove row
    soft_delete('orders', 1)
    order = db.query('SELECT * FROM orders WHERE id = 1')
    assert order.deleted_at is not None
    assert db.query('SELECT * FROM active_orders WHERE id = 1') is None
""")

# --- THE MAIN PROBLEM FILE: messy requirements spec ---
# This is the primary input the agent must process

requirements = {
    "project": "ecommerce_db_modernization",
    "version": "2024-Q1",
    "database": {
        "engine": "PostgreSQL",
        "version": "15",
        "dbname": "ecommerce_db"
    },
    "tables_to_create": [
        {
            "name": "products",
            "columns": [
                {"name": "id", "type": "BIGSERIAL", "constraints": ["PRIMARY KEY"]},
                {"name": "name", "type": "VARCHAR(255)", "constraints": ["NOT NULL"]},
                {"name": "description", "type": "TEXT"},
                {"name": "sku", "type": "VARCHAR(100)", "constraints": ["UNIQUE", "NOT NULL"]},
                {"name": "inventory_quantity", "type": "INTEGER", "constraints": ["DEFAULT 0"]},
                {"name": "inventory_tracking", "type": "BOOLEAN", "constraints": ["DEFAULT FALSE"]},
                {"name": "attributes", "type": "JSONB"},
                {"name": "price", "type": "DECIMAL(10,2)", "constraints": ["NOT NULL"]},
                {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": ["DEFAULT CURRENT_TIMESTAMP"]},
                {"name": "deleted_at", "type": "TIMESTAMPTZ"}
            ],
            "special_features": [
                "full_text_search on (name, description, sku)",
                "gin_index on attributes",
                "partial_index on inventory_quantity WHERE inventory_tracking=true AND inventory_quantity<=5"
            ]
        },
        {
            "name": "orders",
            "partitioned_by": "created_at",
            "partition_strategy": "RANGE monthly",
            "partitions_needed": ["2024-01-01", "2024-02-01", "2024-03-01"],
            "columns": [
                {"name": "id", "type": "BIGSERIAL"},
                {"name": "user_id", "type": "BIGINT", "constraints": ["NOT NULL"]},
                {"name": "status", "type": "VARCHAR(50)", "constraints": ["NOT NULL", "DEFAULT 'pending'"]},
                {"name": "total", "type": "DECIMAL(10,2)"},
                {"name": "attributes", "type": "JSONB"},
                {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": ["NOT NULL"]},
                {"name": "deleted_at", "type": "TIMESTAMPTZ"}
            ],
            "primary_key": ["id", "created_at"],
            "indexes": [
                {
                    "type": "composite_covering",
                    "columns": ["user_id", "status"],
                    "include_columns": ["total", "created_at"],
                    "note": "Must support user+status lookups without table heap fetch"
                }
            ],
            "audit_required": True,
            "soft_delete_view": True
        }
    ],
    "infrastructure_requirements": [
        "audit_operation ENUM type must be created",
        "audit_log table must be created",
        "audit trigger on orders table",
        "partition auto-creation function",
        "soft_delete utility function"
    ],
    "anti_patterns_to_avoid": [
        "FLOAT for money columns",
        "Missing CONCURRENTLY on production indexes",
        "SELECT * in views",
        "LIKE for text search"
    ]
}

with open("workspace/docs/architecture/modernization_requirements.json", "w") as f:
    json.dump(requirements, f, indent=2)

# --- The schema file they need to produce: does NOT exist yet ---
# Agent must create: /workspace/schema_migration.sql

print("Workspace generated successfully.")
print("Distractor files created:", len(list(Path("workspace").rglob("*"))))