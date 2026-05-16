#!/usr/bin/env bash
set -euo pipefail

# Make scripts executable
chmod +x /workspace/scripts/git_sync_daemon.sh
chmod +x /workspace/scripts/git_sync_ctl.sh

# Ensure git global config is set for root user
git config --global user.email "ci@genomics-lab.org"
git config --global user.name "CI Bot"
git config --global init.defaultBranch main

echo "[setup] Scripts are executable and git config is ready."
echo "[setup] Repos available under /opt/genomics-repos/"
ls /opt/genomics-repos/