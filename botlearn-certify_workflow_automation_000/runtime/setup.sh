#!/bin/bash
set -e

chmod +x /workspace/skills/botlearn-certify/scripts/check-assessment.sh

# Ensure results directory exists and is writable
mkdir -p /workspace/skills/botlearn-certify/results
chmod 777 /workspace/skills/botlearn-certify/results

echo "Setup complete."