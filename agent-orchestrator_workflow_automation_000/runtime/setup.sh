#!/usr/bin/env bash
set -e

echo "=== Setup: making scripts executable ==="
chmod +x /workspace/scripts/create_agent.py
chmod +x /workspace/scripts/dissolve_agents.py

echo "=== Verifying script syntax ==="
python3 -c "import ast; ast.parse(open('/workspace/scripts/create_agent.py').read()); print('create_agent.py OK')"
python3 -c "import ast; ast.parse(open('/workspace/scripts/dissolve_agents.py').read()); print('dissolve_agents.py OK')"

echo "=== Workspace tree ==="
find /workspace -maxdepth 4 -not -path '*/__pycache__/*' | sort

echo "=== Setup complete ==="