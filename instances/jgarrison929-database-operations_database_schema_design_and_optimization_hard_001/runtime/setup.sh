#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting PostgreSQL service ==="
# Start PostgreSQL in the background
su -c "pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/pg.log start" postgres || true

# Wait for PostgreSQL to be ready
for i in $(seq 1 30); do
    if pg_isready -U healthadmin -d healthdb -q 2>/dev/null; then
        echo "PostgreSQL is ready."
        break
    fi
    echo "Waiting for PostgreSQL... ($i/30)"
    sleep 1
done

# Create the database and user if they don't exist
su -c "psql -U postgres -tc \"SELECT 1 FROM pg_database WHERE datname='healthdb'\" | grep -q 1 || psql -U postgres -c \"CREATE DATABASE healthdb;\"" postgres || true
su -c "psql -U postgres -tc \"SELECT 1 FROM pg_roles WHERE rolname='healthadmin'\" | grep -q 1 || psql -U postgres -c \"CREATE USER healthadmin WITH SUPERUSER PASSWORD 'health_secret_2024';\"" postgres || true
su -c "psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE healthdb TO healthadmin;\"" postgres || true

echo "=== Installing pg_stat_statements extension ==="
su -c "psql -U healthadmin -d healthdb -c \"CREATE EXTENSION IF NOT EXISTS pg_stat_statements;\"" postgres || true

echo "=== Workspace permissions ==="
chmod -R 777 /workspace
chown -R postgres:postgres /workspace 2>/dev/null || true

echo "=== Setup complete ==="