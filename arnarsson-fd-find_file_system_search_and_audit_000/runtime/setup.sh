#!/usr/bin/env bash
set -e

# Ensure fd alias is available
if ! command -v fd &>/dev/null; then
    ln -sf /usr/bin/fdfind /usr/local/bin/fd
fi

# Confirm git repo state in studio/
cd /workspace/studio
git config user.email "ci@studio.local"
git config user.name "CI"
git add .gitignore
git commit -m "init" --allow-empty -q

echo "Setup complete. fd version: $(fd --version)"