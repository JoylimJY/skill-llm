#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Setup complete. Task inputs are in /workspace/workspace/community/threads/active/"
ls /workspace/workspace/community/threads/active/