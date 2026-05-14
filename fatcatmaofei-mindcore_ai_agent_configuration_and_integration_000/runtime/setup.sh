#!/bin/bash
set -e

echo "=== MindCore Sandbox Setup ==="

MINDCORE="/workspace/mindcore"

# Install mindcore dependencies if requirements.txt exists
if [ -f "$MINDCORE/requirements.txt" ]; then
    echo "Installing MindCore dependencies..."
    pip install -r "$MINDCORE/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
fi

# Make scripts executable
find "$MINDCORE" -name "*.py" -exec chmod +x {} \;

# Pre-download the sentence-transformer model to avoid cold-start timeout during eval
echo "Pre-caching NLP model (all-MiniLM-L6-v2)..."
python3 -c "
from sentence_transformers import SentenceTransformer
import os
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Model cached successfully.')
" || echo "Model pre-cache attempted (may already exist or will download on first run)"

# Create data directory if it doesn't exist
mkdir -p "$MINDCORE/data"

echo "=== Setup complete ==="
echo "Workspace layout:"
find /workspace -maxdepth 3 -type f | sort | head -40