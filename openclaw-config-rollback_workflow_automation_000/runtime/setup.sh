#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up OpenClaw Config Rollback Sandbox ==="

# Ensure all scripts are executable
chmod +x ~/.openclaw/scripts/*.sh
chmod +x ~/.openclaw/workspace/skills/config-rollback/scripts/*.sh

# Create a mock 'openclaw' binary that does nothing (so "openclaw gateway restart" doesn't fail)
mkdir -p /usr/local/bin
cat > /usr/local/bin/openclaw <<'MOCKEOF'
#!/usr/bin/env bash
# Mock openclaw binary for sandbox testing
SUBCOMMAND="${1:-}"
ACTION="${2:-}"
case "$SUBCOMMAND" in
    gateway)
        case "$ACTION" in
            restart) echo "[mock] Gateway restarted." ;;
            start)   echo "[mock] Gateway started." ;;
            stop)    echo "[mock] Gateway stopped." ;;
            status)  echo "[mock] Gateway status: running" ;;
            *)       echo "[mock] Unknown gateway action: $ACTION" ;;
        esac
        ;;
    skills)
        echo "[mock] Skills: $*" ;;
    *)
        echo "[mock] openclaw $*" ;;
esac
exit 0
MOCKEOF
chmod +x /usr/local/bin/openclaw

# Start cron daemon so crontab commands work
service cron start 2>/dev/null || cron 2>/dev/null || true

echo "=== Setup complete ==="
echo "Available scripts:"
ls -la ~/.openclaw/scripts/
echo ""
echo "Initial openclaw.json:"
cat ~/.openclaw/openclaw.json