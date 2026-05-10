import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# --- Create realistic distractor files ---

# Legacy schema notes (misleading/wrong patterns)
legacy_schema = """
-- OLD SCHEMA - DO NOT USE (archived)
-- This was the original schema from v1.0

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255),
  name VARCHAR(100),
  active BOOLEAN DEFAULT true,
  balance FLOAT,  -- money stored as float (WRONG but this is legacy)
  created TIMESTAMP
);

CREATE TABLE appointments (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  doctor_id INT,
  date TIMESTAMP,
  status VARCHAR(20),
  fee FLOAT
);

-- No indexes, no audit, no partitioning
"""
with open(os.path.join(WORKSPACE, "legacy", "schema_v1.sql"), "w") as f:
    f.write(legacy_schema)

# Misleading migration attempt (uses wrong patterns)
bad_migration = """
-- migration_001_add_indexes.sql
-- WARNING: This migration was NEVER applied. It has issues.

-- Bad: no CONCURRENTLY, will lock table in production
CREATE INDEX idx_users_email ON users(email);

-- Bad: wrong money type
ALTER TABLE appointments ADD COLUMN consultation_fee FLOAT;

-- Bad: full index on status instead of partial
CREATE INDEX idx_users_status_bad ON users(status);
"""
with open(os.path.join(WORKSPACE, "migrations", "migration_001_BROKEN.sql"), "w") as f:
    f.write(bad_migration)

# A partially correct but incomplete attempt
partial_attempt = """
-- migration_002_partial_attempt.sql  
-- Developer started this but gave up

ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;
-- TODO: add soft delete view
-- TODO: add audit trigger
-- TODO: partition appointments table
"""
with open(os.path.join(WORKSPACE, "migrations", "migration_002_INCOMPLETE.sql"), "w") as f:
    f.write(partial_attempt)

# Business requirements doc (this drives the task)
requirements = {
    "platform": "MediBook - Healthcare Appointment Booking Platform",
    "version": "2.0",
    "compliance": "HIPAA-adjacent audit trail required for all patient/provider record changes",
    "tables_needed": [
        {
            "name": "providers",
            "description": "Healthcare providers (doctors, therapists)",
            "columns": [
                "id BIGSERIAL PK",
                "email VARCHAR(255) UNIQUE NOT NULL - must validate format",
                "username VARCHAR(50) UNIQUE NOT NULL",
                "password_hash VARCHAR(255) NOT NULL",
                "first_name VARCHAR(100) NOT NULL",
                "last_name VARCHAR(100) NOT NULL",
                "specialty VARCHAR(100)",
                "license_number VARCHAR(50) UNIQUE",
                "status: active/inactive/suspended/pending (enum)",
                "email_verified BOOLEAN DEFAULT FALSE",
                "created_at TIMESTAMPTZ",
                "updated_at TIMESTAMPTZ",
                "deleted_at TIMESTAMPTZ (soft delete)"
            ],
            "constraints": [
                "email format validation",
                "first_name and last_name must not be empty/whitespace"
            ]
        },
        {
            "name": "appointments",
            "description": "Patient appointments - HIGH VOLUME, must be partitioned by month",
            "columns": [
                "id BIGSERIAL",
                "provider_id BIGINT NOT NULL FK->providers",
                "patient_email VARCHAR(255) NOT NULL",
                "appointment_date TIMESTAMPTZ NOT NULL",
                "status VARCHAR(20): scheduled/completed/cancelled/no_show",
                "consultation_fee DECIMAL(10,2) NOT NULL - NEVER float",
                "notes TEXT",
                "created_at TIMESTAMPTZ NOT NULL"
            ],
            "partitioning": "RANGE on created_at, monthly partitions for 2024-01, 2024-02, 2024-03"
        }
    ],
    "audit_requirements": {
        "description": "All INSERT/UPDATE/DELETE on providers table must be logged",
        "mechanism": "database trigger using audit_log table",
        "fields": "table_name, record_id, operation, old_values, new_values"
    },
    "indexing_requirements": [
        "providers.email: expression index on lower(email) for case-insensitive lookups",
        "providers.status: PARTIAL index only for non-active providers (performance optimization)",
        "providers.deleted_at: partial index for soft-delete filtering",
        "appointments: covering index on (provider_id, status) INCLUDE (consultation_fee, appointment_date) for dashboard queries",
        "appointments: partial index on (consultation_fee) WHERE status = 'completed' for revenue queries"
    ],
    "reporting_requirements": {
        "description": "Monthly revenue summary view needed for billing dashboard",
        "type": "materialized view",
        "name": "monthly_revenue_summary",
        "columns": "month (truncated), provider_id, appointment_count, total_revenue, avg_fee",
        "source": "appointments WHERE status = 'completed'",
        "refresh": "must support CONCURRENT refresh (requires unique index)"
    }
}

with open(os.path.join(WORKSPACE, "docs", "business_requirements.json"), "w") as f:
    json.dump(requirements, f, indent=2)

# Fake monitoring output suggesting slow queries (context clues)
slow_query_report = """
=== Slow Query Report - MediBook Production ===
Generated: 2024-03-15 09:00:00 UTC

TOP SLOW QUERIES (mean_exec_time > 100ms):
1. SELECT * FROM providers WHERE lower(email) = $1
   calls: 45231, mean_exec_time: 234ms, total: 10583s
   ISSUE: No expression index on lower(email)

2. SELECT * FROM providers WHERE status IN ('inactive','suspended')
   calls: 12000, mean_exec_time: 189ms
   ISSUE: Full table scan, partial index would help

3. SELECT p.id, COUNT(a.id), SUM(a.consultation_fee)
   FROM providers p JOIN appointments a ON p.id = a.provider_id
   WHERE a.status = 'completed'
   calls: 890, mean_exec_time: 4200ms
   ISSUE: No materialized view, fee column type is FLOAT (precision loss)

4. SELECT * FROM providers WHERE deleted_at IS NULL
   calls: 98000, mean_exec_time: 45ms
   ISSUE: Missing partial index for soft delete pattern
"""
with open(os.path.join(WORKSPACE, "monitoring", "slow_query_report.txt"), "w") as f:
    f.write(slow_query_report)

# Distractor: old Redis cache config (not needed for this task)
redis_config = {
    "host": "localhost",
    "port": 6379,
    "ttl_seconds": 300,
    "keys": ["providers:status:*", "appointments:provider:*"]
}
with open(os.path.join(WORKSPACE, "config", "redis_config.json"), "w") as f:
    json.dump(redis_config, f, indent=2)

# Distractor: EF Core migration notes (not needed)
ef_notes = """
# EF Core Migration Notes
Run: dotnet ef migrations add AddProviderFields -p src/Infrastructure -s src/Api
This is for the .NET team. SQL team handles raw migrations separately.
"""
with open(os.path.join(WORKSPACE, "docs", "ef_core_notes.md"), "w") as f:
    f.write(ef_notes)

# Distractor: connection pool config
pool_config = """
# Node.js pg Pool Configuration
max: 20
idleTimeoutMillis: 30000
connectionTimeoutMillis: 2000
maxUses: 7500
"""
with open(os.path.join(WORKSPACE, "config", "pool_config.yaml"), "w") as f:
    f.write(pool_config)

# Distractor: test data samples
test_patients = [
    {"patient_email": f"patient{i}@clinic.com", "provider_id": random.randint(1, 5),
     "fee": round(random.uniform(50, 500), 2), "month": random.choice(["2024-01", "2024-02", "2024-03"])}
    for i in range(20)
]
with open(os.path.join(WORKSPACE, "tests", "sample_patients.json"), "w") as f:
    json.dump(test_patients, f, indent=2)

# Distractor: archived old trigger (wrong approach)
old_trigger = """
-- ARCHIVED: Old trigger approach - DO NOT USE
-- This used a separate audit table per entity (wrong pattern)
CREATE OR REPLACE FUNCTION old_providers_audit()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO providers_audit_old (provider_id, changed_at, changed_by)
  VALUES (NEW.id, NOW(), current_user);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
with open(os.path.join(WORKSPACE, "archive", "old_trigger_DEPRECATED.sql"), "w") as f:
    f.write(old_trigger)

# Distractor: bloat monitoring query
bloat_query = """
-- Run this monthly to check table bloat
SELECT tablename,
  pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
  n_dead_tup, n_live_tup
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
"""
with open(os.path.join(WORKSPACE, "monitoring", "bloat_check.sql"), "w") as f:
    f.write(bloat_query)

# Distractor: unrelated schema for billing service
billing_schema = """
-- Billing microservice schema (separate database)
CREATE TABLE invoices (
  id BIGSERIAL PRIMARY KEY,
  amount DECIMAL(10,2),
  issued_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""
with open(os.path.join(WORKSPACE, "schema", "billing_schema_OTHERSERVICE.sql"), "w") as f:
    f.write(billing_schema)

# Distractor: N+1 detection notes
n1_notes = """
N+1 Detection Notes:
- providers listing page calls provider details one by one (N+1)
- Fix: use Include() in EF Core or JOIN in raw SQL
- See pg_stat_statements for query patterns
"""
with open(os.path.join(WORKSPACE, "docs", "n1_problem_notes.txt"), "w") as f:
    f.write(n1_notes)

# Distractor: rollback plan template
rollback_template = """
-- Rollback Plan Template
-- Always test rollback before applying migrations

-- Step 1: Take backup
pg_dump -Fc healthdb > backup_$(date +%Y%m%d).dump

-- Step 2: Apply migration
-- Step 3: Validate
-- Step 4: If issues, rollback:
-- dotnet ef database update PreviousMigrationName
"""
with open(os.path.join(WORKSPACE, "migrations", "rollback_template.txt"), "w") as f:
    f.write(rollback_template)

print("Workspace initialized successfully.")
print(f"Files created in {WORKSPACE}")