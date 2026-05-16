#!/bin/bash
set -e

WORKSPACE=/workspace

# ── 1. Create a mock `wrangler` binary that logs invocations ──────────────
MOCK_WRANGLER=/usr/local/bin/wrangler
cat > "$MOCK_WRANGLER" << 'WRANGLER_MOCK'
#!/bin/bash
# Mock wrangler: log every invocation, simulate success

LOG_FILE="/tmp/wrangler_calls.log"
echo "CALL: wrangler $*" >> "$LOG_FILE"

# Parse sub-commands
if [[ "$1" == "r2" && "$2" == "object" && "$3" == "put" ]]; then
    OBJECT_PATH="$4"
    LOCAL_FILE=""
    HAS_REMOTE=false

    # Parse remaining args
    i=5
    while [[ $i -le $# ]]; do
        arg="${!i}"
        if [[ "$arg" == "--file" ]]; then
            i=$((i+1))
            LOCAL_FILE="${!i}"
        elif [[ "$arg" == "--remote" ]]; then
            HAS_REMOTE=true
        fi
        i=$((i+1))
    done

    echo "PUT: bucket_path=$OBJECT_PATH file=$LOCAL_FILE remote=$HAS_REMOTE" >> "$LOG_FILE"

    if [[ -z "$OBJECT_PATH" ]]; then
        echo "Error: missing object path" >&2
        exit 1
    fi
    echo "Uploaded successfully: $OBJECT_PATH"
    exit 0

elif [[ "$1" == "r2" && "$2" == "object" && "$3" == "list" ]]; then
    echo "[]"
    exit 0

elif [[ "$1" == "r2" && "$2" == "object" && "$3" == "delete" ]]; then
    echo "Deleted: $4"
    exit 0
else
    echo "mock wrangler: unhandled command: $*" >> "$LOG_FILE"
    echo "mock wrangler: $*"
    exit 0
fi
WRANGLER_MOCK

chmod +x "$MOCK_WRANGLER"

# ── 2. Create the real r2-upload.sh script (as documented in SKILL.md) ────
cat > "$WORKSPACE/scripts/r2-upload.sh" << 'R2_UPLOAD'
#!/bin/bash
# r2-upload.sh: Upload a file or directory to Cloudflare R2

set -e

CONFIG="$HOME/.config/cloudflare/r2.json"

if [[ ! -f "$CONFIG" ]]; then
    echo "Error: R2 config not found at $CONFIG" >&2
    exit 1
fi

export CLOUDFLARE_ACCOUNT_ID="$(jq -r .accountId "$CONFIG")"
export CLOUDFLARE_API_TOKEN="$(jq -r .apiToken "$CONFIG")"
BUCKET=$(jq -r .bucket "$CONFIG")

LOCAL="$1"
REMOTE_PREFIX="$2"

if [[ -z "$LOCAL" ]]; then
    echo "Usage: r2-upload.sh <local-file-or-dir> [remote-path]" >&2
    exit 1
fi

if [[ -d "$LOCAL" ]]; then
    # Batch upload directory
    if [[ -z "$REMOTE_PREFIX" ]]; then
        echo "Error: remote prefix required for directory upload" >&2
        exit 1
    fi
    find "$LOCAL" -type f | sort | while read -r FILE; do
        RELATIVE="${FILE#$LOCAL/}"
        REMOTE_PATH="${REMOTE_PREFIX%/}/${RELATIVE}"
        echo "Uploading $FILE -> $BUCKET/$REMOTE_PATH"
        wrangler r2 object put "$BUCKET/$REMOTE_PATH" --file "$FILE" --remote
    done
else
    # Single file upload
    if [[ -z "$REMOTE_PREFIX" ]]; then
        REMOTE_PATH="$(basename "$LOCAL")"
    else
        REMOTE_PATH="$REMOTE_PREFIX"
    fi
    echo "Uploading $LOCAL -> $BUCKET/$REMOTE_PATH"
    wrangler r2 object put "$BUCKET/$REMOTE_PATH" --file "$LOCAL" --remote
fi
R2_UPLOAD

chmod +x "$WORKSPACE/scripts/r2-upload.sh"

# ── 3. Clear any stale wrangler logs ──────────────────────────────────────
rm -f /tmp/wrangler_calls.log

echo "Setup complete. Mock wrangler at $MOCK_WRANGLER"
echo "r2-upload.sh ready at $WORKSPACE/scripts/r2-upload.sh"