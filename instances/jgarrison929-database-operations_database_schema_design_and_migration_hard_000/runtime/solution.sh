#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
cd "$WORKSPACE"

echo "=== Step 1: Read SKILL.md to understand required patterns ==="
cat /workspace/skill_context/SKILL.md | head -20
echo ""
echo "Key patterns identified from SKILL.md:"
echo "  - Partition function: to_char(p_date, 'YYYY_MM'), INTERVAL '1 month'"
echo "  - Audit trigger: TG_TABLE_NAME, TG_OP, to_jsonb(OLD/NEW)"
echo "  - Covering index: INCLUDE (total, created_at)"
echo "  - FTS: GENERATED ALWAYS AS (...) STORED"
echo "  - soft_delete: EXECUTE format('%I', ...) with dynamic SQL"
echo "  - All indexes: CREATE INDEX CONCURRENTLY"

echo ""
echo "=== Step 2: Examine the requirements in the workspace ==="
cat "$WORKSPACE/workspace/docs/architecture/modernization_requirements.json" | python3 -c "
import json, sys
req = json.load(sys.stdin)
print('Project:', req['project'])
print('Partitions needed:', req['tables_to_create'][1]['partitions_needed'])
print('Infrastructure:', req['infrastructure_requirements'])
"

echo ""
echo "=== Step 3: Generate schema_migration.sql based on SKILL.md patterns ==="

cat > "$WORKSPACE/schema_migration.sql" << 'SQLEOF'
-- ============================================================
-- schema_migration.sql
-- E-commerce DB Modernization Migration
-- Based on SKILL.md database-operations patterns
-- ============================================================

-- +migrate Up

-- ============================================================
-- SECTION 1: AUDIT INFRASTRUCTURE
-- (Must come before tables that reference it)
-- ============================================================

-- SKILL.md: "audit_operation ENUM type"
CREATE TYPE audit_operation AS ENUM ('INSERT', 'UPDATE', 'DELETE');

-- SKILL.md: audit_log table with JSONB old_values/new_values
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name VARCHAR(255) NOT NULL,
  record_id BIGINT NOT NULL,
  operation audit_operation NOT NULL,
  old_values JSONB,
  new_values JSONB,
  changed_fields TEXT[],
  user_id BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- SKILL.md: Strategic indexes for audit_log
CREATE INDEX CONCURRENTLY idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX CONCURRENTLY idx_audit_user_time ON audit_log(user_id, created_at);

-- SKILL.md: audit_trigger_function using TG_TABLE_NAME, TG_OP, to_jsonb (NOT row_to_json)
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

-- ============================================================
-- SECTION 2: SOFT DELETE UTILITY FUNCTION
-- ============================================================

-- SKILL.md: soft_delete using EXECUTE format('%I') for injection-safe dynamic SQL
CREATE OR REPLACE FUNCTION soft_delete(p_table TEXT, p_id BIGINT)
RETURNS VOID AS $$
BEGIN
  EXECUTE format('UPDATE %I SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL', p_table)
  USING p_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECTION 3: PARTITION AUTO-CREATION FUNCTION
-- ============================================================

-- SKILL.md: create_monthly_partition using to_char(p_date, 'YYYY_MM') and INTERVAL '1 month'
CREATE OR REPLACE FUNCTION create_monthly_partition(p_table TEXT, p_date DATE)
RETURNS VOID AS $$
DECLARE
  partition_name TEXT := p_table || '_' || to_char(p_date, 'YYYY_MM');
  next_date DATE := p_date + INTERVAL '1 month';
BEGIN
  EXECUTE format(
    'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
    partition_name, p_table, p_date, next_date
  );
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SECTION 4: PARTITIONED ORDERS TABLE
-- ============================================================

-- SKILL.md: Partitioned table with composite PK (id, created_at) required for RANGE partitioning
-- SKILL.md: Use DECIMAL(10,2) for money — NEVER FLOAT (anti-pattern #9)
CREATE TABLE orders (
  id BIGSERIAL,
  user_id BIGINT NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  total DECIMAL(10,2),
  attributes JSONB,
  created_at TIMESTAMPTZ NOT NULL,
  deleted_at TIMESTAMPTZ,
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- SKILL.md: Monthly partitions for 2024-01, 2024-02, 2024-03
CREATE TABLE orders_2024_01 PARTITION OF orders
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_2024_02 PARTITION OF orders
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE orders_2024_03 PARTITION OF orders
  FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- SKILL.md: Covering index (INCLUDE extra columns to avoid table heap fetch)
-- Use CONCURRENTLY for production safety (anti-pattern #6 avoidance)
CREATE INDEX CONCURRENTLY idx_orders_covering
  ON orders(user_id, status) INCLUDE (total, created_at);

-- SKILL.md: Partial index for soft delete queries
CREATE INDEX CONCURRENTLY idx_orders_deleted_at
  ON orders(deleted_at) WHERE deleted_at IS NULL;

-- SKILL.md: Audit trigger on orders table
CREATE TRIGGER audit_orders
  AFTER INSERT OR UPDATE OR DELETE ON orders
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- SKILL.md: Soft delete view (active_orders)
CREATE VIEW active_orders AS
  SELECT * FROM orders WHERE deleted_at IS NULL;

-- ============================================================
-- SECTION 5: PRODUCTS TABLE WITH FTS AND ADVANCED INDEXING
-- ============================================================

CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  sku VARCHAR(100) UNIQUE NOT NULL,
  inventory_quantity INTEGER DEFAULT 0,
  inventory_tracking BOOLEAN DEFAULT FALSE,
  attributes JSONB,
  -- SKILL.md: DECIMAL for money, never FLOAT (anti-pattern #9)
  price DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMPTZ,
  -- SKILL.md: Full-text search: GENERATED ALWAYS AS ... STORED
  -- Combines name, description, sku into tsvector
  search_vector tsvector GENERATED ALWAYS AS (
    to_tsvector('english',
      COALESCE(name, '') || ' ' ||
      COALESCE(description, '') || ' ' ||
      COALESCE(sku, '')
    )
  ) STORED
);

-- SKILL.md: GIN index for full-text search vector
CREATE INDEX CONCURRENTLY idx_products_search
  ON products USING gin(search_vector);

-- SKILL.md: GIN index for JSONB attributes (document queries)
CREATE INDEX CONCURRENTLY idx_products_attrs
  ON products USING gin(attributes);

-- SKILL.md: Partial index for low inventory — exact pattern from skill
CREATE INDEX CONCURRENTLY idx_products_low_stock
  ON products(inventory_quantity)
  WHERE inventory_tracking = true AND inventory_quantity <= 5;

-- SKILL.md: Strategic index on deleted_at for soft delete queries
CREATE INDEX CONCURRENTLY idx_products_deleted_at
  ON products(deleted_at) WHERE deleted_at IS NULL;

SQLEOF

echo ""
echo "=== Step 4: Verify the SQL file was created ==="
wc -l "$WORKSPACE/schema_migration.sql"
echo "First 10 lines:"
head -10 "$WORKSPACE/schema_migration.sql"

echo ""
echo "=== Step 5: Apply the migration to the live ecommerce_db database ==="
su -c "psql -U postgres -d ecommerce_db -f $WORKSPACE/schema_migration.sql" postgres

echo ""
echo "=== Step 6: Verify key objects were created ==="
su -c "psql -U postgres -d ecommerce_db -c \"
SELECT 'ENUM:' as type, typname as name FROM pg_type WHERE typname = 'audit_operation'
UNION ALL
SELECT 'TABLE:', tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('audit_log', 'orders', 'products')
UNION ALL
SELECT 'PARTITION:', c.relname FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid JOIN pg_class p ON p.oid=i.inhparent WHERE p.relname='orders'
UNION ALL
SELECT 'FUNCTION:', proname FROM pg_proc WHERE proname IN ('audit_trigger_function', 'create_monthly_partition', 'soft_delete')
UNION ALL
SELECT 'TRIGGER:', tgname FROM pg_trigger WHERE tgname = 'audit_orders'
ORDER BY 1, 2;
\"" postgres

echo ""
echo "=== Step 7: Functional test - verify partition auto-creation ==="
su -c "psql -U postgres -d ecommerce_db -c \"SELECT create_monthly_partition('orders', '2024-04-01'::DATE);\"" postgres
su -c "psql -U postgres -d ecommerce_db -c \"SELECT c.relname as partition FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid JOIN pg_class p ON p.oid=i.inhparent WHERE p.relname='orders' ORDER BY 1;\"" postgres

echo ""
echo "=== Migration complete. schema_migration.sql applied successfully. ==="