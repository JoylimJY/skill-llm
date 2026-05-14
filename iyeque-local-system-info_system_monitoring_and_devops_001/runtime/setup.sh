#!/bin/bash
set -e

# Make sysinfo script executable
chmod +x /workspace/skills/local-system-info/sysinfo.py

# Ensure uv is available on PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Warm up psutil process CPU readings (first call always returns 0.0)
uv run --with psutil /workspace/skills/local-system-info/sysinfo.py processes --limit 5 > /dev/null 2>&1 || true

echo "Setup complete."