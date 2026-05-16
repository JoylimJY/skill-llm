#!/bin/bash
set -e

# Ensure all files are readable
chmod -R 644 /workspace/pipeline/ingestion/incoming_payload.txt
chmod -R 755 /workspace/pipeline
chmod -R 755 /workspace/archive
chmod -R 755 /workspace/config
chmod -R 755 /workspace/logs
chmod -R 755 /workspace/docs
chmod -R 755 /workspace/scratch

echo "Sandbox initialized. Ready for agent."