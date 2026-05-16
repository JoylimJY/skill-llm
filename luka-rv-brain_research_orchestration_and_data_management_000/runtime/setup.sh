#!/usr/bin/env bash
set -euo pipefail

export PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

echo "=== Setting up ResearchVault ==="

cd /workspace

# Clone the researchvault repository
if [ ! -d "researchvault" ]; then
    git clone https://github.com/agoloborodko/researchvault.git researchvault || \
    git clone https://github.com/andrewgolborodko/researchvault.git researchvault || \
    {
        echo "Primary clone failed, attempting pip-based fallback..."
        mkdir -p researchvault/scripts
        
        # Install via pip if git clone unavailable
        uv pip install researchvault 2>/dev/null || true
    }
fi

# If cloned successfully, set up the environment
if [ -d "researchvault" ] && [ -f "researchvault/pyproject.toml" ]; then
    cd /workspace/researchvault
    uv venv 2>/dev/null || python -m venv .venv
    uv pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
        .venv/bin/pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo "ResearchVault installed from source."
    cd /workspace
fi

# Verify uv is available
uv --version && echo "uv is available" || echo "WARNING: uv not found"

# Make legacy scripts executable
chmod +x /workspace/scripts/legacy/migrate_v1.sh 2>/dev/null || true

echo "=== Setup complete ==="
echo "Workspace contents:"
ls /workspace/