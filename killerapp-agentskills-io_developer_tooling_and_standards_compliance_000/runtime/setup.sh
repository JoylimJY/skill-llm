#!/bin/bash
set -e

export PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Make scripts executable
chmod +x /workspace/agent-marketplace/scripts/publish.sh 2>/dev/null || true
chmod +x /workspace/Fraud_Detection_Workflow/scripts/analyze.py 2>/dev/null || true

# Pre-warm uvx tool cache so agent doesn't have to wait
echo "Pre-warming skills-ref tool cache..."
uvx --from git+https://github.com/agentskills/agentskills#subdirectory=skills-ref skills-ref --help > /dev/null 2>&1 || true

echo "Setup complete."