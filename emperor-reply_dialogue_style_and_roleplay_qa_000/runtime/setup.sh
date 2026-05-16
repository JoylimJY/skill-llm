#!/bin/bash
set -e

# No mock servers needed for this text-based skill task.
# Ensure workspace permissions are correct.
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
ls /workspace