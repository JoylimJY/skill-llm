#!/bin/bash
set -e

# Make sysinfo.py executable
chmod +x /workspace/skills/local-system-info/sysinfo.py

# Ensure uv is available and psutil is cached for uv
uv run --with psutil python3 -c "import psutil; print('psutil available:', psutil.__version__)" 2>/dev/null || true

echo "Setup complete."