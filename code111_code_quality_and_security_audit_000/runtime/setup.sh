#!/bin/bash
set -e

chmod -R 755 /workspace/finpay/
chmod +x /workspace/finpay/scripts/deploy.sh

echo "Workspace initialized. Files ready for review."
ls -la /workspace/finpay/backend/api/
ls -la /workspace/finpay/frontend/src/services/