#!/bin/bash
set -euo pipefail

# Ensure tmux server is available (start a throwaway session to initialize the server)
tmux new-session -d -s _init_server -x 220 -y 50 2>/dev/null || true

# Ensure git global config is set
git config --global user.email "agent@test.local" 2>/dev/null || true
git config --global user.name "Agent Test" 2>/dev/null || true

# Ensure mock codex is executable
chmod +x /usr/local/bin/codex

# Verify project is properly initialized
cd /workspace/dna-qc-pipeline
git log --oneline | head -3

echo "Setup complete. tmux server running."
echo "Project branches: $(git branch)"
echo "Mock codex location: $(which codex)"