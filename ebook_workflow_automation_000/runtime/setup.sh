#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/script.sh

# Ensure the ~/.ebook directory exists
mkdir -p "$HOME/.ebook"
touch "$HOME/.ebook/data.jsonl"

echo "Setup complete. Script is executable."
echo "Testing script invocation:"
bash /workspace/scripts/script.sh version