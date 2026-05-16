#!/bin/bash
set -e

echo "=== Setting up milb-tracker ==="

# Install milb-tracker from the workspace base directory
pip install -e /opt/milb-tracker -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || {
    echo "Primary install path failed, trying alternatives..."
    # Try to find the package
    find / -name "setup.py" -path "*/milb-tracker/*" 2>/dev/null | head -1 | xargs -I{} dirname {} | xargs pip install -e 2>/dev/null || true
    find / -name "pyproject.toml" -path "*/milb*" 2>/dev/null | head -1 | xargs -I{} dirname {} | xargs pip install -e 2>/dev/null || true
}

# Verify installation
milb-tracker --help > /dev/null 2>&1 && echo "milb-tracker installed successfully" || echo "WARNING: milb-tracker not found in PATH"

# Set up environment
mkdir -p /workspace/data
export DB_PATH=/workspace/data/bids.db

# Initialize the system (register director)
cd /workspace
milb-tracker init --name "王总监" && echo "Director initialized" || echo "Init may have already run"

# Add team members that match the announcements
milb-tracker adduser --user-id mgr_zhang --name "张经理" --contact "138-1111-2222" 2>/dev/null || true
milb-tracker adduser --user-id mgr_li --name "李经理" --contact "138-3333-4444" 2>/dev/null || true

echo "=== Setup complete ==="