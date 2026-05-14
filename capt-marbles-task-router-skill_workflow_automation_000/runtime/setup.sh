#!/usr/bin/env bash
set -e

# Ensure the mock CLI is executable
chmod +x /home/agent/.local/bin/task

# Verify it runs
/home/agent/.local/bin/task router status || true

echo "Setup complete. Task router mock CLI ready."