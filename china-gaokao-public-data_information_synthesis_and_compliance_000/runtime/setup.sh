#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod -R 755 /workspace

echo "=== Verifying task input file ==="
if [ -f "/workspace/queries/incoming/parent_batch_query_20240615.txt" ]; then
    echo "Task input file found."
    wc -l /workspace/queries/incoming/parent_batch_query_20240615.txt
else
    echo "ERROR: Task input file missing!"
    exit 1
fi

echo "=== Setup complete ==="