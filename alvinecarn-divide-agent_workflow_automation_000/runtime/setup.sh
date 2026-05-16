#!/bin/bash
set -e

# Make tool scripts executable
chmod +x /workspace/tools/create_wiki_document.py
chmod +x /workspace/tools/submit_result.py

# Ensure output directories exist
mkdir -p /workspace/tools/wiki
mkdir -p /workspace/tools/submission

echo "Setup complete. Mock tools ready at:"
echo "  /workspace/tools/create_wiki_document.py"
echo "  /workspace/tools/submit_result.py"

# Verify tools are accessible
python3 /workspace/tools/create_wiki_document.py --help > /dev/null 2>&1 && echo "create_wiki_document.py: OK"
python3 /workspace/tools/submit_result.py --help > /dev/null 2>&1 && echo "submit_result.py: OK"