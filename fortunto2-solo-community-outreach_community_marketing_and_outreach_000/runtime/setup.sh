#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Create docs directory if not already present (it should be from gen_inputs)
mkdir -p /workspace/docs

echo "Setup complete. Workspace ready."
echo "Key files:"
echo "  - /workspace/docs/product-brief.md (PRD)"
echo "  - /workspace/research/reddit/search_results.json"
echo "  - /workspace/research/hn/search_results.json"
echo "  - /workspace/research/producthunt/search_results.json"
echo "  - /workspace/research/keywords_searched.json"