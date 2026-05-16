#!/bin/bash
set -e

echo "=== Starting MariaDB ==="
# Initialize and start MariaDB
service mariadb start || mysqld_safe --datadir=/var/lib/mysql &
sleep 5

# Ensure MariaDB is running
for i in $(seq 1 10); do
    if mariadb -u root -e "SELECT 1;" > /dev/null 2>&1; then
        echo "MariaDB is up."
        break
    fi
    echo "Waiting for MariaDB... attempt $i"
    sleep 2
done

# Create the pharmacy database with proper charset
mariadb -u root <<'EOF'
CREATE DATABASE IF NOT EXISTS pharmacy
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user for the agent to use
CREATE USER IF NOT EXISTS 'pharma_agent'@'localhost' IDENTIFIED BY 'agent_pass_2024';
GRANT ALL PRIVILEGES ON pharmacy.* TO 'pharma_agent'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "=== MariaDB setup complete. Database 'pharmacy' created. ==="
echo "=== Agent credentials: user=pharma_agent, password=agent_pass_2024, db=pharmacy ==="

# Make workspace writable
chmod -R 777 /workspace

echo "=== Setup complete ==="