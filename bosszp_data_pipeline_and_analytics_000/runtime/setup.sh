#!/bin/bash
set -e

echo "=== Setting up MySQL ==="
service mariadb start || service mysql start || true
sleep 3

# Create the bosszp database and user
mysql -u root -e "CREATE DATABASE IF NOT EXISTS bosszp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'bosszp'@'localhost' IDENTIFIED BY 'bosszp123';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON bosszp.* TO 'bosszp'@'localhost'; FLUSH PRIVILEGES;" 2>/dev/null || true

echo "MySQL ready. Database 'bosszp' created."
echo "=== Workspace structure ==="
find /workspace -type f | head -30