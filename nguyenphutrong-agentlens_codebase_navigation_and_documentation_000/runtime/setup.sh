#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Workspace ready. Structure:"
find /workspace/.agentlens -type f | sort
echo ""
echo "Source tree:"
find /workspace/src -type f | sort