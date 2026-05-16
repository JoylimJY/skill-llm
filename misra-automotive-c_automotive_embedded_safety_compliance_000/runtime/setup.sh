#!/bin/bash
set -e

chmod +x /workspace/scripts/build.sh 2>/dev/null || true
chmod +x /workspace/tools/lint/run_lint.sh 2>/dev/null || true

echo "Workspace initialized."
echo "Target file: /workspace/firmware/brake_ctrl/src/brake_ctrl_core.c"