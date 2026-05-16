#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "Agent should read /workspace/ai_project/specs/yubei_ai_requirements.txt and produce gpu_assessment_report.txt"