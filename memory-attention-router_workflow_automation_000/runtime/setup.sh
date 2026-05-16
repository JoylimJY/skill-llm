#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace
SKILL_DIR="$WORKSPACE/skills/memory-attention-router"
SCRIPTS_DIR="$SKILL_DIR/scripts"
REFS_DIR="$SKILL_DIR/references"

echo "=== Installing memory-attention-router skill ==="

# Clone from PyPI / GitHub — try pip-installable package first
# The skill is distributed as a pip package; install and locate the scripts
pip install memory-attention-router -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true

# If pip install succeeded, the scripts may be in site-packages; copy them to skill dir
SITE_SCRIPTS=$(python3 -c "
import importlib.util, pathlib
try:
    spec = importlib.util.find_spec('memory_attention_router')
    if spec and spec.submodule_search_locations:
        p = pathlib.Path(list(spec.submodule_search_locations)[0])
        print(p)
    else:
        print('')
except Exception:
    print('')
" 2>/dev/null || echo "")

# Try to locate memory_router.py in common places
ROUTER_FOUND=""
for candidate in \
    "$SCRIPTS_DIR/memory_router.py" \
    "$SITE_SCRIPTS/scripts/memory_router.py" \
    "$(python3 -c 'import sys; print(sys.prefix)' 2>/dev/null)/scripts/memory_router.py" \
    "/usr/local/lib/python3.11/dist-packages/memory_attention_router/scripts/memory_router.py" \
    "/usr/local/lib/python3.11/site-packages/memory_attention_router/scripts/memory_router.py"
do
    if [ -f "$candidate" ]; then
        ROUTER_FOUND="$candidate"
        echo "Found router at: $ROUTER_FOUND"
        break
    fi
done

# If not found via pip, try cloning from GitHub
if [ -z "$ROUTER_FOUND" ]; then
    echo "Router not found via pip, attempting git clone..."
    TMP_CLONE=$(mktemp -d)
    git clone --depth=1 https://github.com/openclaw/memory-attention-router "$TMP_CLONE/mar" 2>/dev/null || \
    git clone --depth=1 https://github.com/acodercat/memory-attention-router "$TMP_CLONE/mar" 2>/dev/null || \
    true

    if [ -f "$TMP_CLONE/mar/skills/memory-attention-router/scripts/memory_router.py" ]; then
        cp -r "$TMP_CLONE/mar/skills/memory-attention-router/." "$SKILL_DIR/"
        ROUTER_FOUND="$SKILLS_DIR/memory_router.py"
        echo "Installed from git clone."
    elif [ -f "$TMP_CLONE/mar/scripts/memory_router.py" ]; then
        cp -r "$TMP_CLONE/mar/scripts/." "$SCRIPTS_DIR/"
        ROUTER_FOUND="$SCRIPTS_DIR/memory_router.py"
        echo "Installed scripts from git clone."
    fi
fi

# Fallback: search system-wide
if [ -z "$ROUTER_FOUND" ]; then
    ROUTER_FOUND=$(find / -name "memory_router.py" 2>/dev/null | head -1 || echo "")
fi

if [ -z "$ROUTER_FOUND" ]; then
    echo "ERROR: memory_router.py not found. Cannot proceed."
    exit 1
fi

# Ensure canonical location exists and is populated
if [ "$ROUTER_FOUND" != "$SCRIPTS_DIR/memory_router.py" ]; then
    ROUTER_PARENT=$(dirname "$ROUTER_FOUND")
    echo "Copying scripts from $ROUTER_PARENT to $SCRIPTS_DIR"
    cp -r "$ROUTER_PARENT/." "$SCRIPTS_DIR/" 2>/dev/null || cp "$ROUTER_FOUND" "$SCRIPTS_DIR/memory_router.py"
fi

chmod +x "$SCRIPTS_DIR/memory_router.py" 2>/dev/null || true

# Export canonical env for the agent
echo "export SKILL_BASE_DIR=$SKILL_DIR" >> /etc/environment
echo "export MAR_DB_PATH=/tmp/platform-memory-test.sqlite3" >> /etc/environment
echo "export ROUTER=$SCRIPTS_DIR/memory_router.py" >> /etc/environment

# Also write a sourcing script the agent can reference
cat > /workspace/env.sh <<'ENVEOF'
export SKILL_BASE_DIR=/workspace/skills/memory-attention-router
export MAR_DB_PATH=/tmp/platform-memory-test.sqlite3
export ROUTER=/workspace/skills/memory-attention-router/scripts/memory_router.py
ENVEOF
chmod +x /workspace/env.sh

echo "=== Setup complete ==="
echo "  Router: $SCRIPTS_DIR/memory_router.py"
echo "  Run: python3 $SCRIPTS_DIR/memory_router.py init"