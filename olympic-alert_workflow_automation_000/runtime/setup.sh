#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make check_olympic.py executable
chmod +x "$WORKSPACE/skills/olympic-alert/scripts/check_olympic.py"

# Clear any pre-existing state file so alerts don't fire unexpectedly
mkdir -p "$HOME/.config/olympic-alert"
echo '{"notified": []}' > "$HOME/.config/olympic-alert/state.json"

echo "Setup complete."