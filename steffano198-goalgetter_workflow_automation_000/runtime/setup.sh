#!/bin/bash
set -e

# Ensure HOME is set and base directories exist for the user
export HOME="${HOME:-/root}"

# Remove any stale goalgetter state that might have been left from image build
if [ -d "$HOME/.openclaw/goalgetter" ]; then
    rm -rf "$HOME/.openclaw/goalgetter"
fi

echo "Setup complete. Home directory: $HOME"
echo "No pre-existing goalgetter data. Agent must initialize from scratch."