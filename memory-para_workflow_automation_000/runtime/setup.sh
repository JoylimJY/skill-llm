#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace/.openclaw/

echo "Setup complete. Workspace ready at /workspace/.openclaw/workspace/"
echo "Daily logs present:"
ls /workspace/.openclaw/workspace/memory/