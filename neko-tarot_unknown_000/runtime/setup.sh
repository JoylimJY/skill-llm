#!/bin/bash
set -e

# Make neko.py executable
chmod +x /workspace/neko.py

# Verify the CLI tool works correctly
cd /workspace
python neko.py list > /dev/null 2>&1 && echo "neko.py list: OK"
python neko.py list --json > /dev/null 2>&1 && echo "neko.py list --json: OK"

# Quick smoke test for compose
python neko.py compose --spread timeline --cards 9,16,3 --revs true,false,true --json > /dev/null 2>&1 && echo "neko.py compose: OK"

echo "Setup complete. Workspace ready."