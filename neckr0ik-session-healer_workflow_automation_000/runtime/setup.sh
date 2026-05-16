#!/usr/bin/env bash
set -e

echo "=== Setting up neckr0ik-session-healer sandbox ==="

# Ensure the healer script is executable (gen_inputs already did this via Python,
# but double-confirm in case of permission reset)
chmod +x /usr/local/bin/neckr0ik-session-healer

# Verify it runs
neckr0ik-session-healer check --verbose || true

echo "=== Setup complete ==="
echo "Lock files in place, healer ready."