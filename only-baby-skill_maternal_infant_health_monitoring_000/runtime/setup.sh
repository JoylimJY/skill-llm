#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. Workspace ready at /workspace"
ls /workspace