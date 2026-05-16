#!/bin/bash
set -e

# Make migration and validator scripts executable
chmod +x /workspace/scripts/migration/migrate_v1_to_v2.py
chmod +x /workspace/scripts/validators/schema_check.py

echo "Setup complete. Workspace ready."
ls /workspace/