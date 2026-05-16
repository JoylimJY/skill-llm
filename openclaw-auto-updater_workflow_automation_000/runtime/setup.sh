#!/bin/bash
set -e

# Create a mock `openclaw` binary that:
# 1. Records exactly what arguments it was called with
# 2. Writes them to /workspace/openclaw_call_log.txt
# 3. Exits 0 (success)

cat > /usr/local/bin/openclaw << 'MOCKEOF'
#!/bin/bash
# Mock openclaw binary - records all arguments verbatim
LOGFILE="/workspace/openclaw_call_log.txt"
echo "CALL: openclaw $@" >> "$LOGFILE"

# Also write a structured record of just the args
echo "ARGS_START" >> "$LOGFILE"
for arg in "$@"; do
    echo "$arg" >> "$LOGFILE"
done
echo "ARGS_END" >> "$LOGFILE"

# If 'cron add' subcommand, capture the --name and --message for validation
if [[ "$1" == "cron" && "$2" == "add" ]]; then
    echo "CRON_ADD_INVOKED=true" >> "$LOGFILE"
fi

echo "openclaw: cron job scheduled successfully."
exit 0
MOCKEOF

chmod +x /usr/local/bin/openclaw

# Also create a clawdhub mock (in case agent tries to call it directly)
cat > /usr/local/bin/clawdhub << 'MOCKEOF2'
#!/bin/bash
echo "clawdhub: $@"
exit 0
MOCKEOF2

chmod +x /usr/local/bin/clawdhub

# Ensure workspace permissions
chmod -R 777 /workspace

echo "Mock binaries installed: openclaw, clawdhub"
echo "Setup complete."