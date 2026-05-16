#!/bin/bash
set -e

echo "Setting up PayStream threat modeling workspace..."

# Ensure workspace permissions
chmod -R 755 /workspace/paystream

echo "Workspace ready. Agent may begin threat modeling task."