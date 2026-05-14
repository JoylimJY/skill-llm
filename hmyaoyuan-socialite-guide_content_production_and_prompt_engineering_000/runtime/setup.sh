#!/usr/bin/env bash
set -e

# No mock servers needed. Ensure workspace permissions are correct.
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
ls /workspace