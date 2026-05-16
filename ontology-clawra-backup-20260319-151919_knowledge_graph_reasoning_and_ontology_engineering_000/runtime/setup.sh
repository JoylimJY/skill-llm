#!/usr/bin/env bash
set -e

echo "=== Setting up ontology-clawra sandbox ==="

# Ensure the script is executable
chmod +x /workspace/scripts/ontology-clawra.py

# Verify Python dependencies
python3 -c "import yaml, json, pathlib, argparse; print('✅ Python dependencies OK')"

# Verify the CLI script parses correctly
python3 /workspace/scripts/ontology-clawra.py --help > /dev/null && echo "✅ CLI script parses OK"

# Ensure memory directory is writable
chmod -R 777 /workspace/memory/

echo "=== Setup complete. Workspace ready. ==="
echo ""
echo "Available CLI: python3 /workspace/scripts/ontology-clawra.py <command> [options]"
echo "Commands: create, reason, extract, validate, trace, extraction-history"
echo ""
echo "Task brief: cat /workspace/TASK_BRIEF.txt"
echo "Requirements: cat /workspace/task_requirements.json"