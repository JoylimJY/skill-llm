#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Workspace ready. Competition problem and research notes available."
echo "Directory structure:"
find /workspace -type f | sort