#!/usr/bin/env bash
set -e

# Make all bundled scripts executable
chmod +x /workspace/workspace-template/scripts/write_memory_entry.py
chmod +x /workspace/workspace-template/scripts/build_publish_package.py
chmod +x /workspace/workspace-template/scripts/save_publish_package.py
chmod +x /workspace/workspace-template/scripts/publish_approved_note.py

echo "Setup complete. All scripts are executable."
echo "Workspace root: /workspace"