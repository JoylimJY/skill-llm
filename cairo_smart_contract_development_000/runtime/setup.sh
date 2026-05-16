#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/script.sh

echo "Setup complete. Skill script is executable."
echo "Workspace contents:"
find /workspace -type f | sort