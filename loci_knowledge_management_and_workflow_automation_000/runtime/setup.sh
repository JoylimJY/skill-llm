#!/usr/bin/env bash
set -e

echo "=== Setting up loci environment ==="

# Verify loci scripts exist
ls /opt/loci/scripts/

# Make executable if needed
chmod +x /opt/loci/scripts/loci.mjs 2>/dev/null || true

# Create output dir
mkdir -p /workspace/output

# Test node is available
node --version
echo "Node.js available."

# Verify palace file exists
if [ -f /workspace/data/lab_palace.json ]; then
    echo "Palace seed file confirmed."
else
    echo "ERROR: Palace seed file missing!" >&2
    exit 1
fi

echo "=== Setup complete ==="