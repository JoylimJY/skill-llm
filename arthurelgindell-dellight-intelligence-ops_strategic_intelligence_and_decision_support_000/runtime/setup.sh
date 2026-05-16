#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the input files exist
echo "=== Verifying input files ==="
ls /workspace/intel/raw_signals/
ls /workspace/strategy/decisions/

echo "=== Setup complete. Agent may begin. ==="