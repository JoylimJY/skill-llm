#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"

# ── 1. Create the skills directory structure ──────────────────────────────────
mkdir -p "$WORKSPACE/skills/leak-buy/scripts"

# ── 2. Create the mock `leak` binary ─────────────────────────────────────────
# This mock validates argument safety rules from SKILL.md and simulates download.
cat > /usr/local/bin/leak << 'LEAK_MOCK_EOF'
#!/usr/bin/env bash
# Mock leak CLI — validates SKILL.md argument conventions and simulates download

LOG_FILE="/workspace/tmp/leak_invocation.log"
mkdir -p /workspace/tmp

# Record full invocation for eval
echo "ARGS: $*" >> "$LOG_FILE"
echo "CMD: leak $*" > /workspace/tmp/last_command.log

# Parse arguments
SUBCOMMAND=""
URL=""
BUYER_KEY_FILE=""
DOWNLOAD_CODE=""
OUT_PATH=""
BASENAME_VAL=""
RAW_KEY_DETECTED=0
NPXISH=0

if [[ "${1:-}" == "buy" ]]; then
    SUBCOMMAND="buy"
    shift
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --buyer-private-key-file)
            BUYER_KEY_FILE="$2"
            shift 2
            ;;
        --private-key|--key|--raw-key|--stdin-key)
            RAW_KEY_DETECTED=1
            shift 2
            ;;
        --download-code)
            DOWNLOAD_CODE="$2"
            shift 2
            ;;
        --out)
            OUT_PATH="$2"
            shift 2
            ;;
        --basename)
            BASENAME_VAL="$2"
            shift 2
            ;;
        http://*|https://*)
            URL="$1"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Safety: reject raw key mode
if [[ "$RAW_KEY_DETECTED" -eq 1 ]]; then
    echo "ERROR: Raw key argument mode is blocked. Use --buyer-private-key-file <path>." >&2
    exit 2
fi

# Require subcommand
if [[ "$SUBCOMMAND" != "buy" ]]; then
    echo "ERROR: expected 'buy' subcommand." >&2
    exit 1
fi

# Require URL
if [[ -z "$URL" ]]; then
    echo "ERROR: No URL provided." >&2
    exit 1
fi

# Detect URL type
IS_DOWNLOAD_URL=0
if [[ "$URL" == */download || "$URL" == */download/ ]]; then
    IS_DOWNLOAD_URL=1
fi

# For /download URLs: require download code
if [[ "$IS_DOWNLOAD_URL" -eq 1 ]] && [[ -z "$DOWNLOAD_CODE" ]]; then
    echo "ERROR: This seller requires a download code. Provide --download-code <code>." >&2
    exit 3
fi

# Require buyer key file
if [[ -z "$BUYER_KEY_FILE" ]]; then
    echo "ERROR: Buyer private key file is required. Use --buyer-private-key-file <path>." >&2
    exit 4
fi

# Validate key file: must exist, be readable, be a regular file (not symlink)
if [[ ! -e "$BUYER_KEY_FILE" ]]; then
    echo "ERROR: Key file does not exist: $BUYER_KEY_FILE" >&2
    exit 5
fi
if [[ -L "$BUYER_KEY_FILE" ]]; then
    echo "ERROR: Key file must not be a symlink: $BUYER_KEY_FILE" >&2
    exit 6
fi
if [[ ! -f "$BUYER_KEY_FILE" ]]; then
    echo "ERROR: Key file is not a regular file: $BUYER_KEY_FILE" >&2
    exit 7
fi
if [[ ! -r "$BUYER_KEY_FILE" ]]; then
    echo "ERROR: Key file is not readable: $BUYER_KEY_FILE" >&2
    exit 8
fi

# Reject key paths with whitespace
if [[ "$BUYER_KEY_FILE" =~ [[:space:]] ]]; then
    echo "ERROR: Key file path contains whitespace." >&2
    exit 9
fi

# Simulate x402 payment / download-code flow
echo "leak: Connecting to $URL"
if [[ "$IS_DOWNLOAD_URL" -eq 1 ]]; then
    echo "leak: Access mode: download-code"
    echo "leak: Verifying download code: $DOWNLOAD_CODE"
fi
echo "leak: Verifying buyer identity from key file..."
echo "leak: Payment/auth successful."
echo "leak: Downloading content..."

# Determine output path
if [[ -n "$OUT_PATH" ]]; then
    DEST="$OUT_PATH"
elif [[ -n "$BASENAME_VAL" ]]; then
    DEST="/workspace/downloads/$BASENAME_VAL"
else
    DEST="/workspace/downloads/leak_download_$(date +%s).bin"
fi

mkdir -p "$(dirname "$DEST")"

# Write fake downloaded content
FAKE_CONTENT="LEAK_CONTENT_V1\nURL=$URL\nCODE=$DOWNLOAD_CODE\nKEY_FILE=$BUYER_KEY_FILE\nDATA=$(head -c 512 /dev/urandom | base64 | head -c 256)"
printf "%b" "$FAKE_CONTENT" > "$DEST"

BYTES=$(wc -c < "$DEST")
echo "leak: Saved to $DEST ($BYTES bytes)"

# Record success details for eval
echo "SUCCESS" > /workspace/tmp/leak_result.log
echo "DEST=$DEST" >> /workspace/tmp/leak_result.log
echo "BYTES=$BYTES" >> /workspace/tmp/leak_result.log
echo "URL=$URL" >> /workspace/tmp/leak_result.log
echo "DOWNLOAD_CODE=$DOWNLOAD_CODE" >> /workspace/tmp/leak_result.log
echo "BUYER_KEY_FILE=$BUYER_KEY_FILE" >> /workspace/tmp/leak_result.log
echo "IS_DOWNLOAD_URL=$IS_DOWNLOAD_URL" >> /workspace/tmp/leak_result.log

exit 0
LEAK_MOCK_EOF

chmod +x /usr/local/bin/leak

# ── 3. Create the buy.sh wrapper script (as SKILL.md prescribes it exists) ───
cat > "$WORKSPACE/skills/leak-buy/scripts/buy.sh" << 'BUY_SH_EOF'
#!/usr/bin/env bash
# skills/leak-buy/scripts/buy.sh
# Thin wrapper: validates 'leak' is on PATH, then delegates to it.
set -euo pipefail

if ! command -v leak &>/dev/null; then
    echo "ERROR: 'leak' binary not found on PATH. Install: npm i -g leak-cli" >&2
    exit 1
fi

exec leak buy "$@"
BUY_SH_EOF

chmod +x "$WORKSPACE/skills/leak-buy/scripts/buy.sh"

# ── 4. Ensure downloads dir exists and tmp dir exists ─────────────────────────
mkdir -p "$WORKSPACE/downloads"
mkdir -p "$WORKSPACE/tmp"

echo "Setup complete. Mock 'leak' binary installed at /usr/local/bin/leak"
echo "buy.sh wrapper at $WORKSPACE/skills/leak-buy/scripts/buy.sh"
leak --version 2>/dev/null || echo "(mock leak ready)"