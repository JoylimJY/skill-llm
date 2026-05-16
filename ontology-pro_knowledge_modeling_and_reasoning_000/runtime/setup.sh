#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/graph_visualize.py
chmod +x /workspace/scripts/memory_manager.py

# Ensure output directories exist
mkdir -p /workspace/data/processed
mkdir -p /workspace/reports/2024Q4

echo "Setup complete. Workspace ready."
echo "Key files:"
echo "  /workspace/data/raw/pharma_graph_session1.json  — existing knowledge graph (session 1)"
echo "  /workspace/data/raw/q4_2024_intelligence_brief.txt  — new intelligence brief to process"