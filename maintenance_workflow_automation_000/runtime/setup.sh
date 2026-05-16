#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up maintenance skill environment ==="

# Attempt multiple install strategies for the 'maintenance' CLI tool
# Strategy 1: check if already on PATH
if command -v maintenance &>/dev/null; then
    echo "maintenance already installed: $(maintenance version 2>/dev/null || echo 'version unknown')"
    exit 0
fi

# Strategy 2: npm global install
if command -v npm &>/dev/null; then
    echo "Trying npm install..."
    npm install -g maintenance 2>/dev/null && \
        echo "Installed via npm" && \
        command -v maintenance && exit 0 || true
fi

# Strategy 3: pip install
if command -v pip3 &>/dev/null; then
    echo "Trying pip3 install..."
    pip3 install maintenance -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null && \
        echo "Installed via pip3" && \
        command -v maintenance && exit 0 || true
fi

# Strategy 4: clone from source and install
echo "Trying source install from GitHub..."
if [ -d /opt/ai-skills ]; then
    cd /opt/ai-skills
    if [ -f install.sh ]; then
        bash install.sh
    elif [ -f package.json ]; then
        npm install -g . 2>/dev/null || true
    fi
fi

# Strategy 5: Direct download of the script
echo "Trying direct download..."
curl -fsSL "https://raw.githubusercontent.com/bytesagain/ai-skills/main/maintenance/maintenance.sh" \
    -o /usr/local/bin/maintenance 2>/dev/null && \
    chmod +x /usr/local/bin/maintenance && \
    echo "Installed via direct download" && exit 0 || true

# Final check
if command -v maintenance &>/dev/null; then
    echo "maintenance is available"
    maintenance version 2>/dev/null || true
    maintenance status 2>/dev/null || true
else
    echo "WARNING: maintenance could not be installed via standard channels."
    echo "The agent will need to locate or install it."
fi

# Ensure data directory exists
mkdir -p ~/.local/share/maintenance/

echo "=== Setup complete ==="