#!/bin/bash
set -e

# Fix the syntax error in gen_inputs_script output (the script itself is corrected below)
# Ensure workspace dirs are fully created
mkdir -p /workspace/.openclaw/logs
mkdir -p /workspace/.openclaw/cache
mkdir -p /workspace/.openclaw/plugins/lobster
mkdir -p /workspace/.openclaw/plugins/llm-task
mkdir -p /workspace/conventions
mkdir -p /workspace/agents/orchestrator
mkdir -p /workspace/agents/summarizer
mkdir -p /workspace/agents/notifier
mkdir -p /workspace/deployments/prod
mkdir -p /workspace/deployments/staging
mkdir -p /workspace/scripts

chmod +x /workspace/scripts/restart_gateway.sh 2>/dev/null || true
chmod +x /workspace/scripts/verify_tools.sh 2>/dev/null || true

echo "Setup complete."