#!/usr/bin/env bash
set -euo pipefail

# Ensure the search script in workspace is executable
chmod +x /workspace/scripts/search-registry.sh
chmod +x /tmp/agent-failure-registry/scripts/search-registry.sh

# Verify registry structure
echo "Registry structure:"
find /tmp/agent-failure-registry -type f | sort

echo ""
echo "Workspace structure:"
find /workspace -type f | sort

echo ""
echo "Setup complete. Search script ready at /workspace/scripts/search-registry.sh"