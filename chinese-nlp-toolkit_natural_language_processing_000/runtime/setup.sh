#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Pre-warm jieba's dictionary (avoids slow first-time load during agent execution)
python3 -c "import jieba; jieba.initialize()" 2>/dev/null || true

echo "Setup complete."