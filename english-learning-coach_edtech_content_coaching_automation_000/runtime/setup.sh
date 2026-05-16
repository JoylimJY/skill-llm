#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace/

echo "Setup complete. Workspace ready."
ls -la /workspace/platform/submissions/batch_2024_01/
ls -la /workspace/platform/assets/reading/
ls -la /workspace/platform/config/