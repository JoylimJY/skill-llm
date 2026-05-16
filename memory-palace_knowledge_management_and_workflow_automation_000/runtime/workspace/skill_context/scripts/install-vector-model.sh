#!/bin/bash
set -e

echo "=========================================="
echo "Memory Palace - BGE Vector Model Installer"
echo "=========================================="

# Configuration
MODEL_NAME="${BGE_MODEL:-BAAI/bge-small-zh-v1.5}"
CACHE_DIR="${BGE_MODEL_CACHE_DIR:-/data/agent-memory-palace/model_cache}"
HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

echo ""
echo "Model: $MODEL_NAME"
echo "Cache: $CACHE_DIR"
echo ""

# Create cache directory
mkdir -p "$CACHE_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 first:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

echo "[1/4] Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    echo "[2/4] Installing pip..."
    python3 -m ensurepip --upgrade || python3 -m pip install --upgrade pip
fi

# Install sentence-transformers
echo "[2/4] Installing sentence-transformers..."
if ! python3 -c "import sentence_transformers" 2>/dev/null; then
    python3 -m pip install --quiet sentence-transformers numpy
    echo "sentence-transformers installed."
else
    echo "sentence-transformers already installed."
fi

# Download model
echo "[3/4] Downloading BGE model..."
echo "This may take a few minutes on first run..."

# Set HuggingFace mirror for China users
export HF_ENDPOINT="$HF_ENDPOINT"

# Use Python to download the model
python3 << EOF
import os
import sys

cache_dir = os.environ.get('BGE_MODEL_CACHE_DIR', '$CACHE_DIR')
model_name = os.environ.get('BGE_MODEL', '$MODEL_NAME')
hf_endpoint = os.environ.get('HF_ENDPOINT', 'https://hf-mirror.com')

os.environ['HF_ENDPOINT'] = hf_endpoint
os.makedirs(cache_dir, exist_ok=True)

print(f"Downloading model: {model_name}")
print(f"Cache directory: {cache_dir}")
print(f"HF_ENDPOINT: {hf_endpoint}")

try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name, cache_folder=cache_dir)
    dim = model.get_sentence_embedding_dimension()
    print(f"Model downloaded successfully!")
    print(f"Embedding dimension: {dim}")
except Exception as e:
    print(f"ERROR: Failed to download model: {e}", file=sys.stderr)
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "[4/4] Installation complete!"
    echo ""
    echo "=========================================="
    echo "BGE model installed successfully!"
    echo ""
    echo "You can now use Memory Palace with semantic search."
    echo "The model is cached at: $CACHE_DIR"
    echo "=========================================="
else
    echo ""
    echo "ERROR: Model download failed."
    echo "If you're in China, try setting HF_ENDPOINT:"
    echo "  export HF_ENDPOINT=https://hf-mirror.com"
    exit 1
fi
