#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace/workspace/

# Create the reports directory where the agent should save output
mkdir -p /workspace/workspace/reports

echo "Setup complete. Workspace ready."
echo "Contract to review: /workspace/workspace/contracts/pending/TSC-2024-0892_service_agreement.txt"