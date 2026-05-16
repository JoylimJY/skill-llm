#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# ── Create mock scripts that the SKILL.md references ──────────────────────────

# session_status: reports context usage. We set it to 82% (in the 75-90% band)
# so the agent must do selective archiving (not force-skip everything).
cat > "${WORKSPACE}/scripts/session_status.sh" << 'EOF'
#!/usr/bin/env bash
echo "context_usage=82%"
echo "total_memory_entries=47"
echo "session_id=s-current-2024-01-11"
echo "status=WARNING: context above threshold"
EOF
chmod +x "${WORKSPACE}/scripts/session_status.sh"

# Also create a symlink/wrapper so agent can call it as `session_status`
cat > "${WORKSPACE}/session_status" << 'EOF'
#!/usr/bin/env bash
exec bash "$(dirname "$0")/scripts/session_status.sh" "$@"
EOF
chmod +x "${WORKSPACE}/session_status"

# memory_search: accepts a query keyword and returns matching memory file paths
cat > "${WORKSPACE}/scripts/memory_search.sh" << 'EOF'
#!/usr/bin/env bash
QUERY="${1:-}"
WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MEMORY_DIR="${WORKSPACE_DIR}/memory"

if [ -z "$QUERY" ]; then
    echo "Usage: memory_search <query>"
    exit 1
fi

# Search memory files for the query term
grep -ril "$QUERY" "$MEMORY_DIR" 2>/dev/null || true
EOF
chmod +x "${WORKSPACE}/scripts/memory_search.sh"

cat > "${WORKSPACE}/memory_search" << 'EOF'
#!/usr/bin/env bash
exec bash "$(dirname "$0")/scripts/memory_search.sh" "$@"
EOF
chmod +x "${WORKSPACE}/memory_search"

# shrink.sh: performs the actual archive operation.
# It moves files listed in stdin (one per line) to memory/archive/
# and appends a manifest entry to memory/archive/manifest.json
cat > "${WORKSPACE}/scripts/shrink.sh" << 'EOF'
#!/usr/bin/env bash
# Usage: echo "memory/file.json" | bash scripts/shrink.sh
# Or:    bash scripts/shrink.sh memory/file1.json memory/file2.json
WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE_DIR="${WORKSPACE_DIR}/memory/archive"
MANIFEST="${ARCHIVE_DIR}/manifest.json"

mkdir -p "$ARCHIVE_DIR"

# Initialize manifest if needed
if [ ! -f "$MANIFEST" ]; then
    echo "[]" > "$MANIFEST"
fi

ARCHIVED=0

archive_file() {
    local filepath="$1"
    # Normalize: strip leading workspace path if present
    local relpath="${filepath#${WORKSPACE_DIR}/}"
    local fullpath="${WORKSPACE_DIR}/${relpath}"

    if [ -f "$fullpath" ]; then
        local basename
        basename="$(basename "$fullpath")"
        local timestamp
        timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        cp "$fullpath" "${ARCHIVE_DIR}/${basename}"
        rm "$fullpath"
        # Append to manifest
        local tmp
        tmp="$(mktemp)"
        python3 -c "
import json, sys
with open('${MANIFEST}') as f:
    data = json.load(f)
data.append({'file': '${relpath}', 'archived_at': '${timestamp}', 'basename': '${basename}'})
with open('${MANIFEST}', 'w') as f:
    json.dump(data, f, indent=2)
"
        echo "Archived: ${relpath}"
        ARCHIVED=$((ARCHIVED + 1))
    else
        echo "SKIP (not found): ${filepath}"
    fi
}

# Accept args or stdin
if [ "$#" -gt 0 ]; then
    for f in "$@"; do
        archive_file "$f"
    done
else
    while IFS= read -r line; do
        [ -n "$line" ] && archive_file "$line"
    done
fi

echo "shrink.sh: archived ${ARCHIVED} file(s)"
EOF
chmod +x "${WORKSPACE}/scripts/shrink.sh"

# PATH convenience wrapper
cat > "${WORKSPACE}/shrink" << 'EOF'
#!/usr/bin/env bash
exec bash "$(dirname "$0")/scripts/shrink.sh" "$@"
EOF
chmod +x "${WORKSPACE}/shrink"

# Add workspace to PATH for the agent
echo "export PATH=\"${WORKSPACE}:\$PATH\"" >> /etc/bash.bashrc || true
echo "export PATH=\"${WORKSPACE}:\$PATH\"" >> /root/.bashrc || true

echo "Setup complete. Mock scripts ready:"
ls -la "${WORKSPACE}/scripts/"
echo ""
echo "session_status output preview:"
bash "${WORKSPACE}/scripts/session_status.sh"