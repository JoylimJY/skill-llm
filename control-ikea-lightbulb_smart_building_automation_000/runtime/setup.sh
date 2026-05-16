#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up skill environment ==="

SKILL_ROOT="/workspace/skills/control-ikea-lightbulb"

# Make all scripts executable
chmod +x "$SKILL_ROOT/scripts/run_control_kasa.sh"
chmod +x "$SKILL_ROOT/scripts/run_test_light_show.sh"
chmod +x "$SKILL_ROOT/scripts/control_kasa_light.py"
chmod +x "$SKILL_ROOT/scripts/light_show.py"

# Initialize the uv virtual environment and install dependencies for the skill
cd "$SKILL_ROOT"
uv sync --project "$SKILL_ROOT" 2>&1 || {
    echo "uv sync failed, trying uv pip install..."
    uv pip install --project "$SKILL_ROOT" python-kasa>=0.10.2 2>&1 || true
}

# Create the kasa log file with open permissions
touch /tmp/kasa_calls.jsonl
chmod 666 /tmp/kasa_calls.jsonl

echo "=== Setup complete ==="
echo "Skill scripts available at: $SKILL_ROOT/scripts/"
echo "uv version: $(uv --version)"