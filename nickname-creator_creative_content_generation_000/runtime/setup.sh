#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key files exist..."
ls /workspace/clients/active/CLI-2024-089_transcript.txt
ls /workspace/clients/active/CLI-2024-089_intake.txt

echo "Setup complete. Agent task is ready."
echo ""
echo "Workspace overview:"
find /workspace -type f | sort