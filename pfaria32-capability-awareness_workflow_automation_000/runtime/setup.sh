#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/home/

echo "Workspace ready."
echo "Directory structure:"
find /workspace/home/node/.openclaw/workspace -type f | sort