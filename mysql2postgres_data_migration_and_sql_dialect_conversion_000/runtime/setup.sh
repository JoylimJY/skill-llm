#!/bin/bash
set -e
echo "Setup complete. No background services needed."
chmod +x /workspace/scripts/deploy.sh /workspace/scripts/backup_db.sh 2>/dev/null || true