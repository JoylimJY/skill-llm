#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the scenario brief is readable
echo "=== Workspace ready ==="
echo "Key input file:"
cat /workspace/openclaw/config/channel_brief.txt
echo ""
echo "=== Directory structure ==="
tree /workspace || find /workspace -type f | sort