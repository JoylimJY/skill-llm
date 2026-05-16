#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/root/workspace}"

# Ensure openclaw symlink is established
mkdir -p ~/.openclaw
if [ ! -L ~/.openclaw/workspace ]; then
    ln -s "$WORKSPACE" ~/.openclaw/workspace
fi

# Make scripts executable
chmod +x "$WORKSPACE/skills/living-room-air-monitor/scripts/query_data.py"
chmod +x "$WORKSPACE/skills/living-room-air-monitor/scripts/generate_chart.py"
chmod +x "$WORKSPACE/skills/living-room-air-monitor/scripts/send_report.py"

# Ensure /tmp/air_charts directory exists
mkdir -p /tmp/air_charts

echo "[setup] Environment ready. DB path: $WORKSPACE/skills/living-room-air-monitor/data/air_quality.db"
echo "[setup] Symlink: ~/.openclaw/workspace -> $WORKSPACE"