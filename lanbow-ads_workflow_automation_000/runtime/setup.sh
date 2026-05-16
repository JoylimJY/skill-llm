#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod -R 755 /workspace

echo "=== Verifying workspace structure ==="
find /workspace -type f | sort

echo "=== Setup complete ==="