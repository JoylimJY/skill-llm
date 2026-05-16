#!/bin/bash
set -e

chmod +x /workspace/cleaner.py
chmod +x /workspace/deploy/scripts/bootstrap.sh
chmod +x /workspace/deploy/scripts/deploy_release.sh
chmod +x /workspace/pipeline/stages/build/build.sh

echo "Setup complete. Workspace ready."