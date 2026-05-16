#!/bin/bash
set -e

echo "=== Setting up sandbox environment ==="

# Ensure the conversion script is executable
chmod +x /root/.openclaw/workspace/official-document-template/scripts/convert_to_docx.py

# Verify python-docx is installed
python3 -c "import docx; print('python-docx version:', docx.__version__)"

# Verify the input file exists
ls -la /workspace/water_resource_notice_raw.md

# Verify the conversion script exists
ls -la /root/.openclaw/workspace/official-document-template/scripts/convert_to_docx.py

echo "=== Setup complete ==="