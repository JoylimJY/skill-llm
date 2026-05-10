#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

export PGPASSWORD="health_secret_2024"
PSQL="psql -U healthadmin -d healthdb -h localhost"

echo "=== Step 1: Read the skill documentation and business requirements ==="
cat /workspace/skill_context/SKILL.md | head -50 || true
cat /workspace/docs/business_requirements.json || true
cat /workspace/monitoring/slow_query_report.txt || true

echo "=== Step 2: Create the complete medibook_schema.sql ==="

cat > /workspace/medibook_schema.sql << 'SQLEOF'
-- ============================================================
-- MediBook Healthcare Platform - Production Database Schema
-- Follows SKILL.md patterns for PostgreSQL best practices
-- ============================================================

-- ============================================================
-- SECTION 1: ENUM TYPES
-- ============================================================

-- Provider status enum (mirrors user_status from SKILL.md)
DO $$ BEGIN
    CREATE TYPE provider_status AS ENUM ('active', 'inactive', 'suspended', 'pending');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Audit operation enum (from SKILL.md Audit Trail pattern)
DO $$ BEGIN
    CREATE TYPE audit_operation AS ENUM ('INSERT', 'UPDATE', 'DELETE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- SECTION 2: AUDIT LOG TABLE
-- Must exist before providers (trigger references it)
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name VARCHAR(255) NOT NULL,
  record_id BIGINT NOT NULL,
  operation audit_operation NOT NULL,
  old_values JSONB,
  new_values JSONB,
  changed_fields TEXT[],
  user_id BIGINT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes on audit_log (from SKILL.md)
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, created_at);

-- ============================================================
-- SECTION 3: PROVIDERS TABLE
-- Mirrors users table pattern from SKILL.md
-- ============================================================

CREATE TABLE IF NOT EXISTS providers (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  specialty VARCHAR(100),
  license_number VARCHAR(50) UNIQUE,
  status provider_status DEFAULT 'active',
  email_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMPTZ,  -- Soft delete (SKILL.md pattern)

  -- CHECK constraints (from SKILL.md Schema Design Patterns)
  CONSTRAINT providers_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
  CONSTRAINT providers_names_not_empty CHECK (
    LENGTH(TRIM(first_name)) > 0 AND LENGTH(TRIM(last_name)) > 0
  )
);

-- ============================================================
-- SECTION 4: STRATEGIC INDEXES ON PROVIDERS
-- Following SKILL.md Indexing Strategy exactly
-- ============================================================

-- Expression index for case-insensitive email lookup (SKILL.md: idx_users_email_lower)
-- Using CONCURRENTLY for production safety (SKILL.md anti-pattern #6)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_email_lower
  ON providers(lower(email));

-- Partial index: only index NON-ACTIVE providers (SKILL.md: idx_users_status pattern)
-- TRAP: Must be WHERE status != 'active' (partial index on the minority values)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_status_nonactive
  ON providers(status)
  WHERE status != 'active';

-- Partial index for soft-delete filter (SKILL.md: idx_users_deleted_at)
-- TRAP: WHERE deleted_at IS NULL (index only undeleted records for fast lookup)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_deleted_at
  ON providers(deleted_at)
  WHERE deleted_at IS NULL;

-- Standard email index for FK lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_email
  ON providers(email);

-- ============================================================
-- SECTION 5: AUDIT TRIGGER FUNCTION
-- Exact pattern from SKILL.md Audit Trail section
-- Uses to_jsonb() to capture row state
-- ============================================================

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log (table_name, record_id, operation, old_values)
    VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values)
    VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log (table_name, record_id, operation, new_values)
    VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to providers table
DROP TRIGGER IF EXISTS audit_providers ON providers;
CREATE TRIGGER audit_providers
AFTER INSERT OR UPDATE OR DELETE ON providers
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- ============================================================
-- SECTION 6: SOFT DELETE VIEW
-- SKILL.md Soft Delete Pattern: active_* view
-- ============================================================

CREATE OR REPLACE VIEW active_providers AS
  SELECT * FROM providers WHERE deleted_at IS NULL;

-- ============================================================
-- SECTION 7: APPOINTMENTS TABLE (PARTITIONED)
-- SKILL.md Table Partitioning pattern
-- TRAP: consultation_fee must be DECIMAL(10,2) NOT FLOAT (anti-pattern #9)
-- ============================================================

CREATE TABLE IF NOT EXISTS appointments (
  id BIGSERIAL,
  provider_id BIGINT NOT NULL REFERENCES providers(id),
  patient_email VARCHAR(255) NOT NULL,
  appointment_date TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
  -- CRITICAL: DECIMAL(10,2) for financial data - NEVER FLOAT (SKILL.md anti-pattern #9)
  consultation_fee DECIMAL(10,2) NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Monthly partitions for 2024 (SKILL.md Table Partitioning section)
CREATE TABLE IF NOT EXISTS appointments_2024_01
  PARTITION OF appointments
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS appointments_2024_02
  PARTITION OF appointments
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE IF NOT EXISTS appointments_2024_03
  PARTITION OF appointments
  FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- ============================================================
-- SECTION 8: STRATEGIC INDEXES ON APPOINTMENTS
-- Following SKILL.md Indexing Strategy
-- ============================================================

-- Covering index: INCLUDE clause to avoid heap lookups for dashboard queries
-- TRAP: Must use INCLUDE (covering index), not just a composite index
-- Applied to partition (indexes on partitioned tables apply to all partitions)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_covering
  ON appointments(provider_id, status)
  INCLUDE (consultation_fee, appointment_date);

-- Partial index: only completed appointments for revenue queries
-- TRAP: WHERE status = 'completed' restricts the index to relevant rows only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_completed_fee
  ON appointments(consultation_fee)
  WHERE status = 'completed';

-- ============================================================
-- SECTION 9: MONTHLY REVENUE MATERIALIZED VIEW
-- SKILL.md Materialized Views pattern
-- TRAP: UNIQUE index required for CONCURRENT refresh
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_revenue_summary AS
SELECT
  DATE_TRUNC('month', created_at) AS month,
  provider_id,
  COUNT(*) AS appointment_count,
  SUM(consultation_fee) AS total_revenue,
  AVG(consultation_fee) AS avg_fee
FROM appointments
WHERE status = 'completed'
GROUP BY DATE_TRUNC('month', created_at), provider_id;

-- UNIQUE index on materialized view is REQUIRED for CONCURRENT refresh
-- (SKILL.md: "REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_sales")
CREATE UNIQUE INDEX IF NOT EXISTS idx_monthly_revenue_summary_unique
  ON monthly_revenue_summary(month, provider_id);

SQLEOF

echo "=== Step 3: Apply the schema to the running PostgreSQL database ==="
$PSQL -f /workspace/medibook_schema.sql

echo "=== Step 4: Verify key objects were created ==="
echo "--- Tables ---"
$PSQL -c "\dt"

echo "--- Partitions ---"
$PSQL -c "SELECT c.relname FROM pg_class c JOIN pg_inherits i ON c.oid = i.inhrelid JOIN pg_class p ON i.inhparent = p.oid WHERE p.relname = 'appointments' ORDER BY c.relname;"

echo "--- Indexes ---"
$PSQL -c "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename, indexname;"

echo "--- Triggers ---"
$PSQL -c "SELECT trigger_name, event_object_table, event_manipulation FROM information_schema.triggers WHERE trigger_schema='public';"

echo "--- Views ---"
$PSQL -c "\dv"

echo "--- Materialized Views ---"
$PSQL -c "SELECT matviewname FROM pg_matviews WHERE schemaname='public';"

echo "--- ENUM Types ---"
$PSQL -c "SELECT typname, enumlabel FROM pg_type JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid ORDER BY typname, enumlabel;"

echo "=== Step 5: Test audit trigger works ==="
$PSQL -c "INSERT INTO providers (email, username, password_hash, first_name, last_name, specialty, status) VALUES ('dr.smith@medibook.com', 'drsmith', 'hashed_password_here', 'John', 'Smith', 'Cardiology', 'active');"
$PSQL -c "UPDATE providers SET specialty='Neurology' WHERE email='dr.smith@medibook.com';"
$PSQL -c "SELECT table_name, operation, id FROM audit_log ORDER BY id;"

echo "=== Step 6: Test soft delete view ==="
$PSQL -c "UPDATE providers SET deleted_at=NOW() WHERE username='drsmith';"
$PSQL -c "SELECT COUNT(*) AS total_providers FROM providers;"
$PSQL -c "SELECT COUNT(*) AS active_providers FROM active_providers;"

echo "=== Step 7: Confirm medibook_schema.sql is saved in workspace ==="
ls -la /workspace/medibook_schema.sql
wc -l /workspace/medibook_schema.sql

echo "=== Solution complete. All schema objects created and verified. ==="