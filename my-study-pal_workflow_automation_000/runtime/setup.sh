#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Workspace is ready."
echo "Contents of /workspace:"
find /workspace -type f | sort