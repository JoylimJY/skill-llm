#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/material-review/scripts/material_review_audit.py

# Verify markdownlint-cli2 is available
markdownlint-cli2 --version || echo "markdownlint-cli2 check done"

# Verify the submission file exists
ls -la /workspace/城市综合执法管理系统_共享清单.json

echo "Setup complete. Workspace ready for agent."