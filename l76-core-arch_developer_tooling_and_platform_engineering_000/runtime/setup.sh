#!/bin/bash
set -e

# Make distractor deploy script executable
chmod +x /workspace/platform/ci/pipelines/deploy/deploy.sh 2>/dev/null || true
chmod +x /workspace/tools/linters/md_lint.sh 2>/dev/null || true

echo "Sandbox setup complete."