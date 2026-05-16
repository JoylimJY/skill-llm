#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/event_monitor.py
chmod +x /workspace/scripts/sensor_cli.py
chmod +x /workspace/scripts/usb_receiver.py

# Create venv as referenced in SKILL.md
python3 -m venv /workspace/venv
/workspace/venv/bin/pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple -q
/workspace/venv/bin/pip install python-dateutil -i https://pypi.tuna.tsinghua.edu.cn/simple -q

# Ensure data directory is ready
mkdir -p /workspace/data

echo "Setup complete. Workspace ready."
echo "Scripts available at /workspace/scripts/"
echo "Data at /workspace/data/sensor_data.jsonl"
ls -la /workspace/data/