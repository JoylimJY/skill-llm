#!/bin/bash
set -e

echo "=== Setting up hex-vetter tool ==="
cd /workspace

# Clone hex-vetter
if [ ! -d "hex-vetter" ]; then
    git clone https://github.com/Matrix-Meta/hex-vetter.git
fi

cd /workspace/hex-vetter
npm install

echo "=== hex-vetter installed ==="
node vet.js --help 2>/dev/null || echo "vet.js ready (no --help flag needed)"

# Verify key scripts exist
for script in vet.js scan_all.js verify.js starfragment.js; do
    if [ -f "/workspace/hex-vetter/$script" ]; then
        echo "  ✓ $script present"
    else
        echo "  ✗ $script MISSING"
    fi
done

echo "=== Workspace ready ==="
ls /workspace/