#!/usr/bin/env bash
set -e

# ---------------------------------------------------------------------------
# Create the `openclaw` CLI stub that records invocations for later evaluation
# ---------------------------------------------------------------------------
cat > /usr/local/bin/openclaw << 'STUB'
#!/usr/bin/env bash
# OpenClaw CLI stub — records sub-command invocations
LOG_FILE="/tmp/openclaw_invocations.log"
echo "$@" >> "$LOG_FILE"

if [ "$1" = "gateway" ] && [ "$2" = "restart" ]; then
  echo "[openclaw] Gateway restarted successfully."
  exit 0
fi

echo "[openclaw] Unknown command: $*" >&2
exit 1
STUB

chmod +x /usr/local/bin/openclaw

echo "[setup] openclaw CLI stub installed at /usr/local/bin/openclaw"
echo "[setup] Invocations will be logged to /tmp/openclaw_invocations.log"