#!/bin/bash
set -e

# Make pdf_parser.py executable
chmod +x /workspace/scripts/pdf_parser.py

# Ensure output directory exists
mkdir -p /workspace/output

echo "Setup complete. Workspace ready."
echo "PDF reports available at /workspace/clients/shenzhen_mingyuan/"
ls -la /workspace/clients/shenzhen_mingyuan/