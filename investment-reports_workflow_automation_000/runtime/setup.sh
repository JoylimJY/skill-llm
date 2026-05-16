#!/bin/bash
set -e

# Start PostgreSQL service
service postgresql start
sleep 3

# Create database and user
sudo -u postgres psql -c "CREATE USER investage_user WITH PASSWORD 'investage_pass';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE investage OWNER investage_user;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE investage TO investage_user;" 2>/dev/null || true

# Export environment variables for the agent
export PGHOST=localhost
export PGDATABASE=investage
export PGUSER=investage_user
export PGPASSWORD=investage_pass

# Write a .env file so the agent can source it
cat > /workspace/config/db.env << 'EOF'
PGHOST=localhost
PGDATABASE=investage
PGUSER=investage_user
PGPASSWORD=investage_pass
EOF

echo "PostgreSQL ready. Database 'investage' created for user 'investage_user'."
echo "DB credentials written to /workspace/config/db.env"