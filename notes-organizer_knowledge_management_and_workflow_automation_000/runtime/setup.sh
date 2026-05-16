#!/bin/bash
set -e

# Ensure workspace exists
mkdir -p /workspace

# The notes-organizer skill scripts should already be present per the spec.
# We ensure the workspace has correct permissions.
chmod -R 755 /workspace

echo "Setup complete. Notes directory ready at /workspace/dev_notes"
ls /workspace/dev_notes/