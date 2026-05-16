#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod -R 755 /workspace

echo "=== Verifying raw interaction logs ==="
ls /workspace/logs/raw/

echo "=== Verifying USER.md exists ==="
cat /workspace/USER.md

echo "=== Setup complete ==="