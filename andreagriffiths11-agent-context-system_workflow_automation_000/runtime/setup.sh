#!/usr/bin/env bash
set -e

cd /workspace

# Ensure git is configured
git config user.email "agent@test.local" 2>/dev/null || true
git config user.name "Agent Test" 2>/dev/null || true

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

echo "Setup complete. Workspace ready for agent."
echo "Project: Genomics ETL Pipeline"
echo "Task: Set up persistent agent context system"