#!/usr/bin/env bash
set -e

# Ensure lucky.py is executable
chmod +x /workspace/agency/tools/lucky.py

echo "Setup complete. lucky.py is at /workspace/agency/tools/lucky.py"
echo "Test invocation:"
python3 /workspace/agency/tools/lucky.py 嫁娶 马 | head -5