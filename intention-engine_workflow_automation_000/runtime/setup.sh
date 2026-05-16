#!/usr/bin/env bash
set -e

# Make workspace files readable
chmod -R 644 /workspace/requests/*.json
chmod -R 644 /workspace/context/**/*.json
chmod 644 /workspace/USER.md

echo "Setup complete. Workspace is ready."
ls /workspace/