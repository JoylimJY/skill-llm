#!/usr/bin/env bash
set -euo pipefail

cd /workspace

# Ensure all scripts are executable
chmod +x scripts/trae_agent_dispatch.py
chmod +x scripts/code_map_generator.py
chmod +x scripts/project_understanding.py
chmod +x scripts/spec_tools.py

# Verify Python can import the scripts
python3 -c "import sys; sys.path.insert(0, 'scripts')" 2>/dev/null || true

echo "✅ Setup complete. Workspace ready."
echo "Available scripts:"
ls -la scripts/
echo ""
echo "Project structure:"
find src -name "*.py" | head -20