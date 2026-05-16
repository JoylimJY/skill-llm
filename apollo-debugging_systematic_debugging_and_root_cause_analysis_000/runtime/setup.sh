#!/bin/bash
set -e

cd /workspace

# Make scripts executable
chmod +x scripts/run_daily_recon.py scripts/export_report.sh

# Show initial test state so agent can see the failures immediately
echo "===== Initial test run (showing existing failures) ====="
pytest tests/ -v --tb=short 2>&1 | tail -40 || true

echo ""
echo "===== Git log (showing prior fix attempts) ====="
git log --oneline