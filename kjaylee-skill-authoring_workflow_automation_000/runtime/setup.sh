#!/bin/bash
set -e

# Make workspace writable
chmod -R 755 /workspace

echo "Setup complete. Workspace ready at /workspace"
echo "Agent task input: /workspace/tmp/scratch/jordan_backup_notes.txt"