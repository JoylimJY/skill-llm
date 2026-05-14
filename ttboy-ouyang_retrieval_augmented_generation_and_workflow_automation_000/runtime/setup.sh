#!/usr/bin/env bash
set -e

echo "=== Setting up jasper-recall environment ==="

# Run the jasper-recall setup to create venv and ChromaDB
npx jasper-recall setup || echo "Setup may have partially completed"

# Ensure the PATH includes the CLI scripts
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /root/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /root/.profile

# Verify CLI tools are available
which recall || echo "recall not found in PATH yet"
which index-digests || echo "index-digests not found in PATH yet"

# Make sure permissions are correct on any installed scripts
chmod +x "$HOME/.local/bin/recall" 2>/dev/null || true
chmod +x "$HOME/.local/bin/index-digests" 2>/dev/null || true
chmod +x "$HOME/.local/bin/digest-sessions" 2>/dev/null || true

# Pre-download the embedding model to avoid cold-start during agent task
python3 -c "
from sentence_transformers import SentenceTransformer
print('Pre-loading embedding model...')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('Model ready.')
" || echo "Model pre-load skipped"

echo "=== Setup complete ==="
echo "Memory files location: /workspace/legal-memory/"
echo "Agent task request: /workspace/audit-request.txt"