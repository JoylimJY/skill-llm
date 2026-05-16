#!/bin/bash
set -e

echo "Setting up CNC Quick Probe evaluation sandbox..."

# Ensure workspace permissions
chmod -R 755 /workspace

# Create output directory where agent should place response files
mkdir -p /workspace/inquiries/responses

echo "Setup complete. Agent should process files in /workspace/inquiries/incoming/ and write response files to /workspace/inquiries/responses/"
echo "SKILL.md is available at /workspace/skills/SKILL.md"