#!/bin/bash
set -e

# Ensure workspace is ready
cd /workspace

# Run the input generation script
python3 /gen_inputs_script.py 2>/dev/null || python3 gen_inputs_script.py 2>/dev/null || true

# Make project_archive accessible
chmod -R 755 /workspace/project_archive

echo "Setup complete. Project archive is ready at /workspace/project_archive"
tree /workspace/project_archive -L 3 2>/dev/null || find /workspace/project_archive -maxdepth 3 | head -60