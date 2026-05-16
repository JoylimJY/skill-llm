#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Pre-cache font info
fc-cache -f -v 2>/dev/null || true

echo "Setup complete. Workspace ready."
ls /workspace/decks/drafts/