#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify key input files exist
echo "Checking workspace structure..."
ls /workspace/
ls /workspace/references/
ls /workspace/competitors/raw/
ls /workspace/opportunities/threads/

echo "Setup complete. Agent workspace is ready."