#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
SKILL_BASE="$WORKSPACE/skills/btc-sprint-stack"

echo "[setup] Setting up BTC Sprint Stack sandbox..."

# Ensure .venv exists and all deps are installed
cd "$WORKSPACE"

# Make the entrypoint executable
chmod +x "$SKILL_BASE/main.py"

# Ensure the venv python can find the skill
"$WORKSPACE/.venv/bin/python" -c "import json, pathlib, time, random, sys; print('[setup] venv Python OK')"

# Create a minimal simmer-sdk stub so the import chain doesn't break
# (The skill uses SimmerClient conceptually but the modules don't import it directly)
mkdir -p "$WORKSPACE/.venv/lib/python3.11/site-packages/simmer_sdk"
cat > "$WORKSPACE/.venv/lib/python3.11/site-packages/simmer_sdk/__init__.py" << 'STUB'
"""Minimal SimmerClient stub for dry-run sandbox testing."""

class SimmerClient:
    def __init__(self, *args, **kwargs):
        self._dry_run = kwargs.get("dry_run", True)

    def place_order(self, market, side, amount, dry_run=True):
        return {"status": "dry_run_ok" if dry_run else "submitted",
                "market": market, "side": side, "amount": amount}
STUB

echo "[setup] simmer-sdk stub installed at .venv/lib/python3.11/site-packages/simmer_sdk/"
echo "[setup] Workspace ready. Agent should run the entrypoint and verify outputs."
echo "[setup] Skill entrypoint: ./.venv/bin/python skills/btc-sprint-stack/main.py --once --dry-run --validate-real-path"