#!/bin/bash
set -e

# Make checklist script executable
chmod +x /workspace/scripts/drawing_checklist.py

# Verify the script runs correctly
echo "Verifying drawing_checklist.py..."
cd /workspace
python scripts/drawing_checklist.py --type full --output /tmp/test_checklist.txt
if [ $? -eq 0 ]; then
    echo "Checklist script OK"
else
    echo "ERROR: Checklist script failed"
    exit 1
fi
rm -f /tmp/test_checklist.txt

echo "Setup complete. Workspace ready."
ls -R /workspace