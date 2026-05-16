#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Workspace is ready."
echo "Files in workspace root:"
ls -la /workspace/