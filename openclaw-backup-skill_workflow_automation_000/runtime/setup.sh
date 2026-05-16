#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Make all scripts executable
chmod +x "${WORKSPACE}/scripts/openclaw-backup.sh"
chmod +x "${WORKSPACE}/scripts/db_export.sh" 2>/dev/null || true

# Stub the `openclaw` CLI so the script's version capture doesn't fail
cat > /usr/local/bin/openclaw <<'EOF'
#!/usr/bin/env bash
case "${1:-}" in
  --version) echo "OpenClaw 3.2.1" ;;
  *) echo "OpenClaw CLI stub" ;;
esac
exit 0
EOF
chmod +x /usr/local/bin/openclaw

# Initialize cron service (needed for crontab -l inside backup script)
service cron start 2>/dev/null || true

# Ensure crontab is clear for test user
crontab -r 2>/dev/null || true

echo "Setup complete."