#!/bin/bash
set -e

# Set proper permissions on sensitive auth files
chmod 600 ~/.codex/auth.json
chmod 700 ~/.codex/accounts
chmod 600 ~/.codex/accounts/*.json
chmod 600 ~/.openclaw/agents/agent-alpha/agent/auth-profiles.json
chmod 600 ~/.openclaw/agents/agent-beta/agent/auth-profiles.json

# Make the skill script executable
chmod +x ~/skills/codex-account-switcher/scripts/codex-accounts.py

# Verify the structure is correct
echo "=== Codex Account Switcher Sandbox Ready ==="
echo "Active auth.json email: $(python3 -c "import json,pathlib; d=json.loads(pathlib.Path('~/.codex/auth.json').expanduser().read_text()); print(d.get('email','?'))")"
echo "Saved accounts: $(ls ~/.codex/accounts/)"
echo "OpenClaw agents: $(ls ~/.openclaw/agents/)"
echo "Skill script: $(ls ~/skills/codex-account-switcher/scripts/)"
echo "Quota snapshot: $(ls /workspace/quota_snapshot.json)"