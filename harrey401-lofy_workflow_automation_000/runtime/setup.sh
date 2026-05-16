#!/bin/bash
set -e

echo "Setting up lofy workspace evaluation environment..."

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify template files exist
if [ ! -d "/workspace/skills/lofy/assets/templates" ]; then
    echo "ERROR: Template directory missing"
    exit 1
fi

echo "Templates available:"
ls /workspace/skills/lofy/assets/templates/

echo "Setup complete."