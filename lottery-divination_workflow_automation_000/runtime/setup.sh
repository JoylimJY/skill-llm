#!/usr/bin/env bash
set -e

# Ensure divination.py is executable
chmod +x /workspace/scripts/divination.py

# Verify the script works
echo "Verifying divination.py..."
python3 /workspace/scripts/divination.py dlt 2026-07-18-20 > /tmp/verify_output.json 2>&1
if [ $? -eq 0 ]; then
    echo "divination.py verification passed."
else
    echo "WARNING: divination.py verification failed:"
    cat /tmp/verify_output.json
fi

# Create output directory if not present
mkdir -p /workspace/output

echo "Setup complete."