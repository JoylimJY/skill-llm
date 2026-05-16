#!/bin/bash
set -e

echo "=== Setting up deep-research sandbox ==="

# Ensure all scripts are executable
chmod +x /workspace/skills/deep-research/scripts/run-research.sh
chmod +x /workspace/skills/deep-research/scripts/fetch-and-extract.sh
chmod +x /workspace/skills/deep-research/scripts/check-sourcing.sh
chmod +x /workspace/skills/deep-research/scripts/extract-from-pdf.py

# Verify workspace integrity
echo "Source cards present:"
ls /workspace/skills/deep-research/sources/

echo "Current config:"
cat /workspace/skills/deep-research/config/research-config.yaml

echo "Reports dir (should be empty):"
ls /workspace/skills/deep-research/reports/ 2>/dev/null || echo "  (empty — correct)"

echo "=== Setup complete ==="