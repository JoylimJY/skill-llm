#!/bin/bash
set -e

# Ensure trash-cli binaries are available
which trash-put || (echo "trash-put not found" && exit 1)
which trash-list || (echo "trash-list not found" && exit 1)
which trash-restore || (echo "trash-restore not found" && exit 1)
which trash-rm || (echo "trash-rm not found" && exit 1)
which trash-empty || (echo "trash-empty not found" && exit 1)

# Ensure trash directory exists for current user
mkdir -p ~/.local/share/Trash/files
mkdir -p ~/.local/share/Trash/info

# Ensure workspace permissions are correct
chown -R root:root /workspace
chmod -R 755 /workspace

echo "Setup complete. Trash directory initialized."
echo "Workspace contents:"
find /workspace -type f | sort