#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"

# ── Make the check-quota.sh executable ──────────────────────────────────────
chmod +x "$WORKSPACE/skills/token-monitor/scripts/check-quota.sh"

# ── Create a mock `openclaw` CLI ─────────────────────────────────────────────
# This mock reads a snapshot file determined by OPENCLAW_SNAPSHOT env var.
# It also handles `openclaw cron wake` silently.

mkdir -p "$WORKSPACE/.openclaw/bin"

cat > "$WORKSPACE/.openclaw/bin/openclaw" << 'MOCK_EOF'
#!/usr/bin/env bash
# Mock openclaw CLI for token-monitor sandbox

SNAPSHOT_FILE="${OPENCLAW_SNAPSHOT:-/workspace/.openclaw/bin/snapshot1.txt}"
WAKE_LOG="${OPENCLAW_WAKE_LOG:-/workspace/.openclaw/bin/wake.log}"

case "$1" in
  models)
    case "$2" in
      status)
        if [[ -f "$SNAPSHOT_FILE" ]]; then
          cat "$SNAPSHOT_FILE"
        else
          echo "Error: snapshot file not found: $SNAPSHOT_FILE" >&2
          exit 1
        fi
        ;;
      *)
        echo "Unknown models subcommand: $2" >&2
        exit 1
        ;;
    esac
    ;;
  cron)
    case "$2" in
      wake)
        # Collect all remaining args and log them
        shift 2
        echo "[WAKE] $*" >> "$WAKE_LOG"
        ;;
      list)
        echo "No cron jobs registered."
        ;;
      *)
        echo "Unknown cron subcommand: $2" >&2
        exit 1
        ;;
    esac
    ;;
  *)
    echo "Unknown openclaw command: $1" >&2
    exit 1
    ;;
esac
MOCK_EOF

chmod +x "$WORKSPACE/.openclaw/bin/openclaw"

# Put mock openclaw on PATH via a wrapper in /usr/local/bin
ln -sf "$WORKSPACE/.openclaw/bin/openclaw" /usr/local/bin/openclaw

# Ensure wake log is clean at start
rm -f "$WORKSPACE/.openclaw/bin/wake.log"

echo "Setup complete. Mock openclaw installed at /usr/local/bin/openclaw"
echo "Snapshot files:"
echo "  Run 1: $WORKSPACE/.openclaw/bin/snapshot1.txt"
echo "  Run 2: $WORKSPACE/.openclaw/bin/snapshot2.txt"