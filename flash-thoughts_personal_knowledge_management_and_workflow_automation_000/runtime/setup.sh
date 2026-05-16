#!/usr/bin/env bash
set -e

# Make flash.py executable
chmod +x /workspace/skills/flash-thoughts/scripts/flash.py

# Ensure the home notes directory doesn't pre-exist (clean state)
rm -rf ~/notes/flash/

echo "Setup complete. flash.py is executable."
echo "Workspace contents:"
find /workspace -type f | sort