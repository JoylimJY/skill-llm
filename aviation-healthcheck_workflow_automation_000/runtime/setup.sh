#!/usr/bin/env bash
set -e

# ── Create the mock `openclaw` CLI ────────────────────────────────────────────
cat > /usr/local/bin/openclaw << 'OPENCLAW_EOF'
#!/usr/bin/env bash

CMD="$1"
SUBCMD="$2"

case "$CMD" in
  status)
    echo "OpenClaw Service Status"
    echo "-----------------------"
    echo "Service:    openclaw-daemon"
    echo "State:      RUNNING"
    echo "PID:        1337"
    echo "Uptime:     14d 06h 22m"
    echo "Version:    2.4.1"
    ;;
  health)
    if [ "$SUBCMD" = "--json" ]; then
      cat << 'JSONEOF'
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "queue": "ok",
    "scheduler": "ok",
    "api": "ok"
  },
  "uptime_seconds": 1234567,
  "version": "2.4.1",
  "last_check": "2024-01-15T09:00:00Z"
}
JSONEOF
    else
      echo "Health: OK"
    fi
    ;;
  security)
    if [ "$SUBCMD" = "audit" ]; then
      echo "Security Audit Results"
      echo "----------------------"
      echo "CVE scan:        PASSED"
      echo "Config check:    PASSED"
      echo "Access logs:     PASSED"
      echo "Cert expiry:     89 days remaining"
      echo "Overall:         PASSED"
    fi
    ;;
  update)
    if [ "$SUBCMD" = "status" ]; then
      echo "Update Status"
      echo "-------------"
      echo "Current version:  2.4.1"
      echo "Latest version:   2.4.1"
      echo "Status:           UP TO DATE"
    fi
    ;;
  cron)
    echo "Cron operation: $SUBCMD"
    ;;
  *)
    echo "Usage: openclaw {status|health|security|update|cron} [options]"
    exit 1
    ;;
esac
OPENCLAW_EOF

chmod +x /usr/local/bin/openclaw

echo "Mock openclaw CLI installed."

# Verify mock works
openclaw status > /dev/null && echo "openclaw status: OK"
openclaw health --json > /dev/null && echo "openclaw health --json: OK"
openclaw security audit > /dev/null && echo "openclaw security audit: OK"
openclaw update status > /dev/null && echo "openclaw update status: OK"

echo "Setup complete."