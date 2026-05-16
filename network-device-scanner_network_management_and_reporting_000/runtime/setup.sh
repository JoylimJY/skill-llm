#!/bin/bash
set -e

# Ensure the scan script is executable
chmod +x /workspace/skills/network-device-scanner/scripts/scan.py

# Verify structure
echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "=== scan.py sanity check ==="
python3 /workspace/skills/network-device-scanner/scripts/scan.py

echo "=== Setup complete ==="