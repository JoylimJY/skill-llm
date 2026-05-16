#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/genos_dna.py 2>/dev/null || true

# Ensure the workspace Python path is accessible
cd /workspace

# Verify the mock model directory is intact
if [ ! -d "/workspace/models/Genos-1___2B" ]; then
    echo "ERROR: Model directory missing!"
    exit 1
fi

echo "Setup complete. Workspace ready at /workspace"
echo "Model directory: /workspace/models/Genos-1___2B"
echo "Input sequence: /workspace/data/raw_sequences/sample_GRCh38_chr1_ZJL2024.fasta"