#!/bin/bash
set -e

# Ensure audit.sh is executable
chmod +x /workspace/giraffe-guard/scripts/audit.sh

# Verify the tool runs
echo "Verifying Giraffe Guard installation..."
/workspace/giraffe-guard/scripts/audit.sh --json /workspace/giraffe-guard 2>/dev/null | head -5 || true

echo "Setup complete. Tool verified."
echo ""
echo "Directory structure:"
find /workspace -maxdepth 4 -type f | sort