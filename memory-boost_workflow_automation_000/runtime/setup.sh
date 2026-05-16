#!/bin/bash
set -e

# Ensure the memory directory has correct permissions
chmod -R 755 /workspace/memory/
chmod 644 /workspace/MEMORY.md
chmod 644 /workspace/MEMORY_INDEX.md

# Make the migration script executable (realistic environment)
chmod +x /workspace/scripts/db/migrate_postgres_to_mongo.py

echo "Setup complete. Workspace ready."
echo "Today's date: $(date +%Y-%m-%d)"