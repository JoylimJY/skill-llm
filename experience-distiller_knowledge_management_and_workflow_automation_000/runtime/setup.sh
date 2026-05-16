#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Ensure all reference files are readable
chmod -R 644 /workspace/references/
chmod -R 755 /workspace/memory/
chmod -R 755 /workspace/playbooks/
chmod -R 755 /workspace/skills/

echo "=== Setup complete ==="
tree /workspace --dirsfirst -L 3 2>/dev/null || find /workspace -type f | sort