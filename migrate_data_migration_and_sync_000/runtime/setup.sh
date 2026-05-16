#!/bin/bash
set -e

echo "=== Setting up mock export.sh and import.sh scripts ==="

# Create scripts/export.sh — a realistic mock that:
# 1. Parses flags correctly
# 2. Creates a proper tar.gz with the right naming convention
# 3. Excludes the correct directories
# 4. Conditionally includes transcripts and credentials

cat > /workspace/scripts/export.sh << 'EXPORT_EOF'
#!/bin/bash
set -e

OUTPUT_DIR="."
WORKSPACE_PATH="$HOME/clawd"
INCLUDE_SESSIONS=false
INCLUDE_CREDENTIALS=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output|-o)
            OUTPUT_DIR="$2"; shift 2;;
        --workspace)
            WORKSPACE_PATH="$2"; shift 2;;
        --include-sessions)
            INCLUDE_SESSIONS=true; shift;;
        --include-credentials)
            INCLUDE_CREDENTIALS=true; shift;;
        *)
            echo "Unknown option: $1" >&2; exit 1;;
    esac
done

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="clawdbot-export-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${OUTPUT_DIR}/${ARCHIVE_NAME}"

mkdir -p "$OUTPUT_DIR"

# Build tar exclusion args
EXCLUDES=(
    "--exclude=*/node_modules"
    "--exclude=*/.next"
    "--exclude=*/.open-next"
    "--exclude=*/.vercel"
    "--exclude=*/.wrangler"
    "--exclude=*/.git"
    "--exclude=*/dist"
    "--exclude=*/build"
)

if [ "$INCLUDE_SESSIONS" = false ]; then
    EXCLUDES+=("--exclude=*/transcripts")
fi

if [ "$INCLUDE_CREDENTIALS" = false ]; then
    EXCLUDES+=("--exclude=*/credentials")
fi

echo "[export] Creating archive: $ARCHIVE_PATH"
echo "[export] Source workspace: $WORKSPACE_PATH"
echo "[export] Include sessions: $INCLUDE_SESSIONS"
echo "[export] Include credentials: $INCLUDE_CREDENTIALS"

tar -czf "$ARCHIVE_PATH" "${EXCLUDES[@]}" -C "$(dirname "$WORKSPACE_PATH")" "$(basename "$WORKSPACE_PATH")"

# Write manifest
MANIFEST_TMP=$(mktemp -d)
cat > "${MANIFEST_TMP}/manifest.json" << MANIFEST
{
  "exportedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sourceWorkspace": "${WORKSPACE_PATH}",
  "includesSessions": ${INCLUDE_SESSIONS},
  "includesCredentials": ${INCLUDE_CREDENTIALS},
  "archiveName": "${ARCHIVE_NAME}",
  "clawdbotVersion": "2.4.1"
}
MANIFEST

# Append manifest to archive
cd "$MANIFEST_TMP"
tar -rzf "$ARCHIVE_PATH" manifest.json 2>/dev/null || {
    # fallback: recreate with manifest
    tar -czf "${ARCHIVE_PATH}.tmp" "${EXCLUDES[@]}" -C "$(dirname "$WORKSPACE_PATH")" "$(basename "$WORKSPACE_PATH")" manifest.json 2>/dev/null || \
    tar -czf "${ARCHIVE_PATH}.tmp" "${EXCLUDES[@]}" -C "$(dirname "$WORKSPACE_PATH")" "$(basename "$WORKSPACE_PATH")"
    mv "${ARCHIVE_PATH}.tmp" "$ARCHIVE_PATH"
}
rm -rf "$MANIFEST_TMP"

echo "[export] Done. Archive: $ARCHIVE_PATH"
echo "[export] Size: $(du -sh "$ARCHIVE_PATH" | cut -f1)"
EXPORT_EOF

# Create scripts/import.sh — restores from archive to target workspace
cat > /workspace/scripts/import.sh << 'IMPORT_EOF'
#!/bin/bash
set -e

ARCHIVE="$1"
shift || true

TARGET_WORKSPACE="$HOME/clawd"
FORCE=false

if [ -z "$ARCHIVE" ]; then
    echo "Usage: import.sh <archive.tar.gz> [--workspace PATH] [--force]" >&2
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace)
            TARGET_WORKSPACE="$2"; shift 2;;
        --force|-f)
            FORCE=true; shift;;
        *)
            echo "Unknown option: $1" >&2; exit 1;;
    esac
done

if [ ! -f "$ARCHIVE" ]; then
    echo "[import] Archive not found: $ARCHIVE" >&2
    exit 1
fi

echo "[import] Archive: $ARCHIVE"
echo "[import] Target workspace: $TARGET_WORKSPACE"
echo "[import] Force overwrite: $FORCE"

if [ -d "$TARGET_WORKSPACE" ] && [ "$FORCE" = false ]; then
    echo "[import] Target directory exists. Use --force to overwrite." >&2
    exit 1
fi

mkdir -p "$(dirname "$TARGET_WORKSPACE")"

# Extract archive
EXTRACT_TMP=$(mktemp -d)
tar -xzf "$ARCHIVE" -C "$EXTRACT_TMP"

# Find the workspace directory inside the archive (first non-manifest directory)
ARCHIVE_WORKSPACE=$(find "$EXTRACT_TMP" -mindepth 1 -maxdepth 1 -type d | head -1)

if [ -z "$ARCHIVE_WORKSPACE" ]; then
    echo "[import] Could not find workspace directory in archive" >&2
    rm -rf "$EXTRACT_TMP"
    exit 1
fi

# Overwrite target
if [ -d "$TARGET_WORKSPACE" ]; then
    rm -rf "$TARGET_WORKSPACE"
fi

cp -r "$ARCHIVE_WORKSPACE" "$TARGET_WORKSPACE"

# Write import receipt
cat > "${TARGET_WORKSPACE}/.import-receipt.json" << RECEIPT
{
  "importedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sourceArchive": "$(basename "$ARCHIVE")",
  "targetWorkspace": "${TARGET_WORKSPACE}",
  "forced": ${FORCE}
}
RECEIPT

rm -rf "$EXTRACT_TMP"
echo "[import] Import complete. Workspace restored to: $TARGET_WORKSPACE"
IMPORT_EOF

chmod +x /workspace/scripts/export.sh
chmod +x /workspace/scripts/import.sh

echo "=== Scripts ready ==="
echo "  /workspace/scripts/export.sh"
echo "  /workspace/scripts/import.sh"

# Verify source workspace
echo ""
echo "=== Source workspace contents ==="
find /opt/clawd-source -maxdepth 3 -type f | sort | head -40
echo ""
echo "=== Setup complete ==="