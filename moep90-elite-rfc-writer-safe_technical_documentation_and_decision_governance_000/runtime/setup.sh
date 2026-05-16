#!/bin/bash
set -e

chmod +x /workspace/scripts/migrate_jobs.py 2>/dev/null || true

echo "Setup complete. Workspace is ready."
ls -la /workspace/