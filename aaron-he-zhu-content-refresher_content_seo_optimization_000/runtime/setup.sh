#!/usr/bin/env bash
set -e

# Ensure workspace memory directories are writable
chmod -R 777 /workspace/memory/

# Create the content-refresher audit directory (it should not pre-exist; agent must create it)
# Actually we ensure it does NOT exist so agent must create it
rm -rf /workspace/memory/audits/content-refresher

echo "Setup complete. Workspace ready."
ls -la /workspace/