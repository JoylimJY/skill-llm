#!/bin/bash
set -e

# Clone claw-compactor into a known location
cd /opt
git clone https://github.com/aeromomo/claw-compactor.git claw-compactor 2>&1 || {
    echo "Primary clone failed, retrying..."
    sleep 3
    git clone https://github.com/aeromomo/claw-compactor.git claw-compactor
}

chmod +x /opt/claw-compactor/scripts/mem_compress.py 2>/dev/null || true

# Ensure workspace exists
mkdir -p /agent-workspace/memory/sessions

# Make the claw-compactor scripts accessible
echo "Claw-compactor installed at: /opt/claw-compactor"
echo "Workspace at: /agent-workspace"
echo "Usage: python3 /opt/claw-compactor/scripts/mem_compress.py /agent-workspace <command>"

# Verify key script exists
python3 /opt/claw-compactor/scripts/mem_compress.py /agent-workspace estimate 2>&1 | head -5 || true