#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the main input file exists
if [ ! -f /workspace/incoming_emails.json ]; then
    echo "ERROR: incoming_emails.json not found!"
    exit 1
fi

echo "Setup complete. Workspace ready."
echo "Main input file: /workspace/incoming_emails.json"
ls -la /workspace/