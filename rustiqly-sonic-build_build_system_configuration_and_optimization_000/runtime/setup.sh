#!/bin/bash
set -e

echo "[setup] Initializing workspace permissions..."
chmod -R 755 /workspace/sonic-buildimage/

# Initialize a minimal git repo so submodule commands are structurally valid
cd /workspace/sonic-buildimage
if [ ! -d ".git" ]; then
    git init -q
    git config user.email "ci@example.com"
    git config user.name "CI Bot"
    # Register fake submodules so the git structure is realistic
    cat > .gitmodules << 'EOF'
[submodule "src/sonic-swss"]
    path = src/sonic-swss
    url = https://github.com/sonic-net/sonic-swss.git
[submodule "src/libswsscommon"]
    path = src/libswsscommon
    url = https://github.com/sonic-net/sonic-buildimage.git
[submodule "src/sonic-utilities"]
    path = src/sonic-utilities
    url = https://github.com/sonic-net/sonic-utilities.git
[submodule "src/sonic-sairedis"]
    path = src/sonic-sairedis
    url = https://github.com/sonic-net/sonic-sairedis.git
EOF
    git add . 2>/dev/null || true
    git commit -q -m "initial" --allow-empty 2>/dev/null || true
fi

echo "[setup] Done. Workspace ready."