#!/usr/bin/env bash
set -euo pipefail

# Make note-taker available on PATH
chmod +x /workspace/scripts/note-taker
ln -sf /workspace/scripts/note-taker /usr/local/bin/note-taker

# Ensure project_notes dir exists and is writable (agent's target NOTE_TAKER_DIR)
mkdir -p /workspace/project_notes

echo "Setup complete. note-taker is on PATH."
note-taker version