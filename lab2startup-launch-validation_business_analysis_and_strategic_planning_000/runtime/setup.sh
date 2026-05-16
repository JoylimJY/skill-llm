#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying project_data.json exists..."
if [ -f "/workspace/project_data.json" ]; then
    echo "project_data.json found."
    python3 -c "import json; d=json.load(open('/workspace/project_data.json')); print('JSON valid, project:', d['project_name'])"
else
    echo "ERROR: project_data.json not found!"
    exit 1
fi

echo "Setup complete."