#!/bin/bash
set -e

cd /workspace

# Ensure scripts are executable
chmod +x scripts/nightly_summary.sh
chmod +x scripts/top_price_alert.sh
chmod +x scripts/push_report.sh

# Make sure git is properly initialised and has at least one commit
git config user.email "ci@openclaw.io"
git config user.name "CI Bot"
git add -A
git commit -m "initial: project scaffold" --allow-empty -q || true

echo "Setup complete."