#!/bin/bash
set -e

# Ensure the registry directory and file have correct permissions
chmod 700 ~/.openclaw/registries/
chmod 600 ~/.openclaw/registries/application_registry.json

echo "Setup complete. Registry is readable."
echo "Registry contents:"
cat ~/.openclaw/registries/application_registry.json