#!/bin/bash
set -euo pipefail

echo "=== Setting up sandbox environment ==="

# Prepend mock_bin to PATH so mock tmux is found first
export PATH="/workspace/mock_bin:$PATH"
echo 'export PATH="/workspace/mock_bin:$PATH"' >> /etc/profile
echo 'export PATH="/workspace/mock_bin:$PATH"' >> /root/.bashrc
echo 'export PATH="/workspace/mock_bin:$PATH"' >> /root/.profile

# Also create a persistent PATH injection for non-login shells
cat >> /etc/environment << 'EOF'
PATH="/workspace/mock_bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EOF

# Verify mock tmux is active
which tmux || echo "WARNING: tmux not found in PATH"
tmux --version 2>/dev/null || echo "INFO: mock tmux active (no --version output is fine)"

# Initialize the tmux audit log
touch /tmp/tmux_audit.log
chmod 666 /tmp/tmux_audit.log

# Ensure git is configured globally
git config --global user.email "agent@sandbox.local"
git config --global user.name "Agent"
git config --global init.defaultBranch main

# Verify the patient-pipeline repo is healthy
cd /workspace/patient-pipeline
git log --oneline -1
git branch
echo "Current branch: $(git branch --show-current)"

# Confirm MEMORY.md exists
ls -la /workspace/MEMORY.md

echo "=== Sandbox ready ==="
echo "PATH=$PATH"
echo "Mock tmux location: $(which tmux)"