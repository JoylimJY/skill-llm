#!/bin/bash
set -e

echo "=== Setting up Soul Memory System ==="

# Ensure the soul-memory repo is available
if [ ! -d "/opt/soul-memory" ]; then
    echo "Cloning soul-memory repository..."
    git clone https://github.com/kingofqin2026/Soul-Memory-.git /opt/soul-memory
fi

cd /opt/soul-memory

# Make scripts executable
chmod +x install.sh 2>/dev/null || true
chmod +x uninstall.sh 2>/dev/null || true

# Run install if available (non-interactive)
if [ -f "install.sh" ]; then
    echo "Running install.sh..."
    bash install.sh --clean 2>/dev/null || bash install.sh 2>/dev/null || true
fi

# Ensure Python path includes soul-memory
echo "export PYTHONPATH=/opt/soul-memory:\$PYTHONPATH" >> /etc/environment
export PYTHONPATH=/opt/soul-memory:$PYTHONPATH

# Create symlink to make cli.py accessible
ln -sf /opt/soul-memory/cli.py /usr/local/bin/soul-cli 2>/dev/null || true

# Verify core.py exists
if [ -f "/opt/soul-memory/core.py" ]; then
    echo "core.py found at /opt/soul-memory/core.py"
else
    echo "WARNING: core.py not found"
fi

# Verify cli.py exists
if [ -f "/opt/soul-memory/cli.py" ]; then
    echo "cli.py found at /opt/soul-memory/cli.py"
else
    echo "WARNING: cli.py not found"
fi

# Initialize workspace
cd /workspace
echo "=== Setup Complete ==="
echo "Soul Memory available at: /opt/soul-memory"
echo "Workspace: /workspace"