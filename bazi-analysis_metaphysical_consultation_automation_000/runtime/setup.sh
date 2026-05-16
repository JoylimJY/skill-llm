#!/usr/bin/env bash
set -e

# Make the bazi_chart.py script executable
chmod +x /workspace/skills/bazi-analysis/scripts/bazi_chart.py

# Verify Python can run it
python /workspace/skills/bazi-analysis/scripts/bazi_chart.py --date 1990-01-01 --time 12:00 --gender male --format json > /dev/null && echo "bazi_chart.py OK"

echo "Setup complete."