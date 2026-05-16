#!/bin/bash
chmod -R 755 /workspace/scripts
echo "Workspace ready."
tree /workspace 2>/dev/null || find /workspace -type f | sort