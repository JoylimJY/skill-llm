#!/usr/bin/env bash
set -e

# Ensure the validator is executable
chmod +x /workspace/scripts/validate-mmd

# Verify Node / mmdc available (mmdc used optionally by advanced agents)
echo "Node version: $(node --version 2>/dev/null || echo 'not found')"
echo "mmdc available: $(which mmdc 2>/dev/null || echo 'not found')"

echo "Setup complete."