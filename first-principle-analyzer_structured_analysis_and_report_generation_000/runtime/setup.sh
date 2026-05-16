#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying skill files are in place..."
ls /workspace/skills/first-principle-analyzer/
ls /workspace/projects/av-sensor-analysis/

echo "Setup complete."