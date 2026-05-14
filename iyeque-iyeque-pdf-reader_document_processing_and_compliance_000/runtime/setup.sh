#!/bin/bash
set -e

chmod +x /workspace/skills/pdf-reader/reader.py

# Verify PDFs exist
echo "=== Verifying PDF assets ==="
ls /workspace/data/raw/clinical_trials/

# Verify skill script is usable
echo "=== Smoke-testing reader.py ==="
python3 /workspace/skills/pdf-reader/reader.py metadata \
  /workspace/data/raw/clinical_trials/trial_CT2024_001.pdf | head -5

echo "=== Setup complete ==="