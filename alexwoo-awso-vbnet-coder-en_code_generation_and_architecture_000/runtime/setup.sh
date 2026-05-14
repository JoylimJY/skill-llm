#!/bin/bash
set -e

chmod +x /workspace/scripts/build.sh

echo "Workspace ready."
tree /workspace --charset=ascii 2>/dev/null || find /workspace -type f | sort