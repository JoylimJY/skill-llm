#!/usr/bin/env bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
test -f /workspace/platform/agents/data-sync-agent/logs/execution_log.jsonl || { echo "ERROR: execution log missing"; exit 1; }
test -f /workspace/platform/agents/data-sync-agent/metadata/capability_profile.json || { echo "ERROR: capability profile missing"; exit 1; }
test -f /workspace/platform/registry/published/data-sync-agent.json || { echo "ERROR: registry entry missing"; exit 1; }
test -f /workspace/platform/monitoring/baselines/data-sync-agent-baseline.json || { echo "ERROR: baseline missing"; exit 1; }

echo "Setup complete. Workspace ready for agent."
ls /workspace/platform/agents/data-sync-agent/