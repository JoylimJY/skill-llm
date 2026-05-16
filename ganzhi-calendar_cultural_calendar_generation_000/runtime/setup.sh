#!/bin/bash
set -e

chmod +x /workspace/scripts/calendar.py

# Ensure lunarcalendar is available
pip install lunarcalendar -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

echo "Setup complete."