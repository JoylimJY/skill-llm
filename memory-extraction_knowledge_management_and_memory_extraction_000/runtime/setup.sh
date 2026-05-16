#!/bin/bash
set -e

cd /workspace

# Ensure scripts directory is importable
touch scripts/__init__.py

# Ensure memory directory exists
mkdir -p memory

# Verify the knowledge graph manager script exists
if [ ! -f "scripts/knowledge_graph_manager.py" ]; then
    echo "ERROR: scripts/knowledge_graph_manager.py not found"
    exit 1
fi

# Verify the transcript exists
if [ ! -f "data/raw/onboarding_transcript.txt" ]; then
    echo "ERROR: data/raw/onboarding_transcript.txt not found"
    exit 1
fi

echo "Setup complete. Workspace ready."
echo "Transcript content:"
cat data/raw/onboarding_transcript.txt