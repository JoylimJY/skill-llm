#!/bin/bash
set -e

# Ensure the wrapper is executable
chmod +x /home/openclaw/.openclaw/workspace/governance/governance_wrapper.py

# Ensure evidence directory is writable
mkdir -p /home/openclaw/.openclaw/workspace/evidence
chmod 777 /home/openclaw/.openclaw/workspace/evidence

# Ensure the main log file does not pre-exist (clean audit start)
rm -f /home/openclaw/.openclaw/workspace/evidence/execution-evidence.log

echo "[setup] Governance workspace initialized. Evidence log cleared for clean audit run."