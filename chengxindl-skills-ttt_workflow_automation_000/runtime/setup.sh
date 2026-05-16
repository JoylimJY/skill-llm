#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/init_skill.py
chmod +x /workspace/scripts/quick_validate.py
chmod +x /workspace/archive/old-scripts/convert_hl7.py
chmod +x /workspace/tools/ci/run_tests.sh

echo "Setup complete. Scripts are executable."
echo "Workspace contents:"
ls /workspace/scripts/