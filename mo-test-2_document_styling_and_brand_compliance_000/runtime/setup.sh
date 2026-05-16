#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying python-pptx installation..."
python3 -c "from pptx import Presentation; print('python-pptx OK')"

echo "Checking font availability..."
fc-list | grep -i poppins && echo "Poppins found" || echo "Poppins not found (fallback to Arial will be used)"
fc-list | grep -i lora && echo "Lora found" || echo "Lora not found (fallback to Georgia will be used)"

echo "Setup complete. Workspace ready."
ls -la /workspace/marketing/campaigns/q3_launch/