#!/usr/bin/env bash
set -e

echo "=== Setting up skillhub CLI ==="

# Install skillhub CLI from official source described in SKILL.md
# The install instructions are at: https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/skillhub.md
# We'll fetch and follow those instructions

INSTALL_SCRIPT_URL="https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh"
FALLBACK_URL="https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/skillhub.md"

# Try to fetch the install script directly
echo "Fetching skillhub install instructions..."

# Download the install markdown to understand the install process
curl -fsSL "$FALLBACK_URL" -o /tmp/skillhub_install.md 2>/dev/null || true

if [ -f /tmp/skillhub_install.md ]; then
    echo "Install doc fetched:"
    cat /tmp/skillhub_install.md
fi

# Try standard install script approach
if curl -fsSL "$INSTALL_SCRIPT_URL" -o /tmp/install_skillhub.sh 2>/dev/null; then
    chmod +x /tmp/install_skillhub.sh
    bash /tmp/install_skillhub.sh || true
fi

# Check if skillhub is now available
if command -v skillhub &>/dev/null; then
    echo "skillhub installed successfully: $(skillhub --version 2>/dev/null || echo 'version unknown')"
else
    # Fallback: try to find the binary from common locations
    POSSIBLE_PATHS=(
        "/usr/local/bin/skillhub"
        "$HOME/.local/bin/skillhub"
        "$HOME/bin/skillhub"
        "/usr/bin/skillhub"
    )
    for p in "${POSSIBLE_PATHS[@]}"; do
        if [ -f "$p" ]; then
            echo "Found skillhub at $p"
            ln -sf "$p" /usr/local/bin/skillhub 2>/dev/null || true
            break
        fi
    done
fi

# Also try the direct binary download if it exists
BINARY_URL="https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/skillhub-linux-x64"
if ! command -v skillhub &>/dev/null; then
    echo "Attempting direct binary download..."
    if curl -fsSL "$BINARY_URL" -o /usr/local/bin/skillhub 2>/dev/null; then
        chmod +x /usr/local/bin/skillhub
        echo "skillhub binary installed directly."
    fi
fi

# Final check
if command -v skillhub &>/dev/null; then
    echo "skillhub is ready."
    skillhub --version 2>/dev/null || true
else
    echo "WARNING: skillhub could not be installed automatically. Agent must install it."
fi

# Ensure ~/.openclaw/skills/ exists
mkdir -p ~/.openclaw/skills/

# Make sure scripts are executable
chmod +x /workspace/scripts/usage.sh 2>/dev/null || true

echo "=== Setup complete ==="