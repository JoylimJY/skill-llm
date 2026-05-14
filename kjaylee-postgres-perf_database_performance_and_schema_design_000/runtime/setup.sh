#!/bin/bash
set -e

# Start PostgreSQL in background
service postgresql start 2>/dev/null || true

# Wait for postgres to be ready
for i in $(seq 1 30); do
    pg_isready -U postgres && break
    sleep 1
done

# Set password and create DB
su -c "psql -c \"ALTER USER postgres WITH PASSWORD 'testpass';\"" postgres 2>/dev/null || true
su -c "createdb ecommerce 2>/dev/null || true" postgres

echo "PostgreSQL ready."