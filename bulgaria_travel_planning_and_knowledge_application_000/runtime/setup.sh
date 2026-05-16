#!/usr/bin/env bash
set -e

# Ensure the ~/bulgaria directory is accessible
chmod -R 755 /root/bulgaria/

# Ensure workspace is accessible
chmod -R 755 /workspace/

echo "Setup complete."
echo "Bulgaria skill directory contents:"
ls -la /root/bulgaria/
echo ""
echo "Workspace contents:"
find /workspace -type f | sort