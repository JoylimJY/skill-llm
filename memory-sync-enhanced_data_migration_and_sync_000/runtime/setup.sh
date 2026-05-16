#!/usr/bin/env bash
set -e

# Make scripts dir executable (stubs won't be called but permissions should be fine)
chmod -R 755 /workspace/scripts/ 2>/dev/null || true
chmod -R 755 /workspace/memory/ 2>/dev/null || true

echo "Setup complete. Workspace ready."