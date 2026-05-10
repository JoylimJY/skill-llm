#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting PostgreSQL ==="
# Start PostgreSQL service in background
su -c "pg_ctlcluster 15 main start || true" postgres 2>/dev/null || \
  su -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/15/main start" postgres 2>/dev/null || \
  service postgresql start || true

sleep 3

# Wait for PostgreSQL to be ready
for i in {1..20}; do
    if su -c "psql -U postgres -c 'SELECT 1;'" postgres >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    echo "Waiting for PostgreSQL... attempt $i"
    sleep 2
done

# Create the ecommerce_db
su -c "psql -U postgres -c \"CREATE DATABASE ecommerce_db;\" 2>/dev/null || true" postgres
su -c "psql -U postgres -d ecommerce_db -c \"CREATE EXTENSION IF NOT EXISTS pg_trgm;\" 2>/dev/null || true" postgres
su -c "psql -U postgres -d ecommerce_db -c \"CREATE EXTENSION IF NOT EXISTS btree_gin;\" 2>/dev/null || true" postgres

# Create the users table (prerequisite - audit_log references it)
su -c "psql -U postgres -d ecommerce_db -c \"
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending');
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  status user_status DEFAULT 'active',
  email_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMPTZ
);
\"" postgres 2>/dev/null || true

echo "=== Setup Complete ==="
echo "PostgreSQL running, ecommerce_db created, users table pre-loaded."
echo "Agent must create: /workspace/schema_migration.sql"
echo "Then apply it to the database."