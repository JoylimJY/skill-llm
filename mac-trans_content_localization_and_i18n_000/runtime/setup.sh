#!/bin/bash
set -e

# Verify translate-shell is available
if ! command -v trans &> /dev/null; then
    echo "trans not found, attempting fallback install..."
    wget -q https://raw.githubusercontent.com/soimort/translate-shell/gh-pages/trans -O /usr/local/bin/trans && chmod +x /usr/local/bin/trans
fi

# Verify trans works (quick smoke test, non-fatal)
echo "Checking trans availability..."
trans --version 2>/dev/null && echo "trans is available" || echo "trans version check failed, but continuing"

# List supported languages to warm up (non-fatal)
trans -R -e bing 2>/dev/null | head -5 || true

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete."