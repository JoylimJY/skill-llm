#!/usr/bin/env bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/search.py
chmod +x /workspace/scripts/fetch_thread.py
chmod +x /workspace/scripts/chain_tracker.py
chmod +x /workspace/scripts/relevance_gate.py

# Ensure invocation log directory exists and is clean
mkdir -p /workspace/logs
# Remove any stale invocation log so evaluation sees only agent-generated calls
rm -f /workspace/logs/search_invocations.jsonl

# Verify scripts run without error (smoke test)
python3 /workspace/scripts/search.py "smoke test" --mode fast --intent factual > /dev/null
echo "[setup] All scripts verified."

echo "[setup] Workspace ready. Agent task begins now."