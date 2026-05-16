#!/bin/bash
set -e

# Ensure analyze.py is executable
chmod +x /workspace/scripts/analyze.py

# Verify PDDL files exist
echo "Verifying workspace setup..."
ls -la /workspace/pipeline/
ls -la /workspace/scripts/

# Quick sanity check on analyze.py
python3 /workspace/scripts/analyze.py /workspace/pipeline/domain.pddl /workspace/pipeline/problem.pddl > /dev/null 2>&1 && echo "analyze.py: OK" || echo "analyze.py: WARNING - check manually"

echo "Setup complete."