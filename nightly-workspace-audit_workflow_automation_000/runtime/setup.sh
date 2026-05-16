#!/usr/bin/env bash
set -e

# Ensure the cron mock is executable (gen_inputs already set it, but double-check)
chmod +x /usr/local/bin/cron

# Verify mock works
echo "--- cron list test ---"
cron list | head -5
echo "--- mock OK ---"

# Ensure workspace-audit skill references dir exists
mkdir -p /workspace/skills/workspace-audit/references

echo "Setup complete."