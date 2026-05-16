#!/bin/bash
set -e

# Ensure fd symlink is in place
if ! command -v fd &>/dev/null; then
    ln -sf /usr/bin/fdfind /usr/local/bin/fd
fi

echo "fd version: $(fd --version)"
echo "Setup complete."