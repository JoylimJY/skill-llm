#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Ensure all reference files are readable
chmod -R 644 /workspace/references/
chmod -R 644 /workspace/task/

echo "=== Setup complete ==="
ls -la /workspace/
ls -la /workspace/references/
ls -la /workspace/task/