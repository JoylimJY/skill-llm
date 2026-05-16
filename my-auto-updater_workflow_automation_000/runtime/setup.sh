#!/bin/bash
set -e

# Make scripts/maintenance directory writable and usable
chmod 755 /workspace/scripts/maintenance

# Make existing scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Create mock clawdbot CLI that records calls and simulates behavior
mkdir -p /usr/local/bin

cat > /usr/local/bin/clawdbot << 'CLAWDBOT_EOF'
#!/bin/bash
# Mock clawdbot CLI for testing
LOG=/tmp/clawdbot_calls.log
echo "clawdbot called with args: $@" >> "$LOG"

CMD="$1"
shift

case "$CMD" in
  "cron")
    SUBCMD="$1"
    shift
    case "$SUBCMD" in
      "add")
        # Parse and record the flags
        ARGS="$@"
        echo "cron add called with: $ARGS" >> "$LOG"
        # Store the full command for evaluation
        echo "clawdbot cron add $ARGS" >> /tmp/clawdbot_cron_add_calls.log
        echo "Cron job added successfully."
        ;;
      "list")
        echo "Daily Auto-Update  |  0 4 * * *  |  America/Los_Angeles"
        ;;
      "remove")
        echo "Cron job removed."
        ;;
      *)
        echo "Unknown cron subcommand: $SUBCMD"
        exit 1
        ;;
    esac
    ;;
  "--version")
    echo "clawdbot v2026.1.10"
    ;;
  "doctor")
    echo "Doctor check passed. All migrations applied."
    ;;
  "update")
    echo "Clawdbot updated to latest version."
    ;;
  *)
    echo "Unknown command: $CMD"
    exit 1
    ;;
esac
CLAWDBOT_EOF
chmod +x /usr/local/bin/clawdbot

# Create mock clawdhub CLI
cat > /usr/local/bin/clawdhub << 'CLAWDHUB_EOF'
#!/bin/bash
# Mock clawdhub CLI for testing
LOG=/tmp/clawdhub_calls.log
echo "clawdhub called with args: $@" >> "$LOG"

CMD="$1"
shift

case "$CMD" in
  "update")
    echo "Checking all skills..."
    echo "prd: 2.0.3 -> 2.0.4 (updated)"
    echo "browser: 1.2.0 -> 1.2.1 (updated)"
    echo "nano-banana-pro: 3.1.0 -> 3.1.2 (updated)"
    echo "gemini: already current"
    echo "sag: already current"
    ;;
  "list")
    echo "prd@2.0.4"
    echo "browser@1.2.1"
    echo "gemini@1.0.5"
    ;;
  *)
    echo "Unknown command: $CMD"
    exit 1
    ;;
esac
CLAWDHUB_EOF
chmod +x /usr/local/bin/clawdhub

echo "Mock CLIs installed successfully."
echo "Setup complete."