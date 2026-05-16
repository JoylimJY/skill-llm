#!/bin/bash
set -e

# Create a mock 'openclaw' binary that captures all invocations to a log file
cat > /usr/local/bin/openclaw << 'MOCK_EOF'
#!/bin/bash
# Mock openclaw - records all invocations
LOGFILE="/workspace/.openclaw_invocations.log"
echo "INVOCATION: openclaw $@" >> "$LOGFILE"

# Parse subcommand
if [ "$1" = "cron" ] && [ "$2" = "add" ]; then
    # Extract all arguments and write them to a structured record
    echo "CRON_ADD_CALL: $@" >> "$LOGFILE"
    
    # Write the full argument list to a dedicated file for eval
    echo "$@" >> /workspace/.cron_add_calls.txt
    
    echo "Cron job registered successfully."
    exit 0
fi

echo "openclaw: command executed"
exit 0
MOCK_EOF

chmod +x /usr/local/bin/openclaw

# Create a mock 'clawdhub' binary (note: SKILL.md uses 'clawdhub')
cat > /usr/local/bin/clawdhub << 'MOCK_EOF2'
#!/bin/bash
LOGFILE="/workspace/.openclaw_invocations.log"
echo "INVOCATION: clawdhub $@" >> "$LOGFILE"
echo "clawdhub: command executed"
exit 0
MOCK_EOF2

chmod +x /usr/local/bin/clawdhub

# Initialize the invocation log
touch /workspace/.openclaw_invocations.log
touch /workspace/.cron_add_calls.txt

echo "Mock binaries installed and ready."