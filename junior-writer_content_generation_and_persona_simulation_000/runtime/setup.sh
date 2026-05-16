#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying task files exist..."
ls /workspace/tasks/
ls /workspace/skill_config/

echo "Setup complete."