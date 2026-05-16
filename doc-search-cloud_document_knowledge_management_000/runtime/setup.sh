#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Ensure the workspace python path is correct
cd /workspace

# Verify key files exist
echo "Checking key files..."
ls -la /workspace/chromadb_document_vectorizer_simple.py
ls -la /workspace/contracts/active/

echo "=== Setup complete ==="