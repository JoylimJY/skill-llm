#!/bin/bash
set -e

WORKSPACE="/workspace"
MOCK_BIN="$WORKSPACE/mock_bin"

# Create mock clawdbot binary
cat > "$MOCK_BIN/clawdbot" << 'MOCKEOF'
#!/bin/bash
# Mock clawdbot - logs all invocations
LOGFILE="/workspace/mock_bin/invocations.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log the full invocation
echo "CLAWDBOT_INVOKE|$TIMESTAMP|$*" >> "$LOGFILE"

# Simulate responses
if [[ "$1" == "--version" ]]; then
    echo "clawdbot v2026.1.10"
    exit 0
fi

if [[ "$1" == "cron" && "$2" == "add" ]]; then
    echo "Cron job registered successfully."
    # Parse and log all arguments as JSON-like for easy eval
    ARGS_STR="$*"
    echo "CRON_ADD|$TIMESTAMP|$ARGS_STR" >> "$LOGFILE"
    exit 0
fi

if [[ "$1" == "cron" && "$2" == "list" ]]; then
    echo "No cron jobs configured."
    exit 0
fi

if [[ "$1" == "cron" && "$2" == "remove" ]]; then
    echo "Cron job removed."
    exit 0
fi

if [[ "$1" == "doctor" ]]; then
    echo "All systems nominal."
    exit 0
fi

if [[ "$1" == "update" ]]; then
    echo "Clawdbot updated to v2026.1.10"
    exit 0
fi

echo "clawdbot: unknown command '$*'"
exit 1
MOCKEOF

# Create mock clawdhub binary
cat > "$MOCK_BIN/clawdhub" << 'MOCKEOF'
#!/bin/bash
# Mock clawdhub - logs all invocations
LOGFILE="/workspace/mock_bin/invocations.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "CLAWDHUB_INVOKE|$TIMESTAMP|$*" >> "$LOGFILE"

if [[ "$1" == "update" && "$2" == "--all" ]]; then
    if [[ "$3" == "--dry-run" ]]; then
        echo "Dry run: prd (2.0.3 -> 2.0.4), browser (1.2.0 -> 1.2.1), nano-banana-pro (3.1.0 -> 3.1.2)"
    else
        echo "Updated: prd 2.0.3 -> 2.0.4"
        echo "Updated: browser 1.2.0 -> 1.2.1"
        echo "Updated: nano-banana-pro 3.1.0 -> 3.1.2"
        echo "Already current: gemini, sag"
    fi
    exit 0
fi

if [[ "$1" == "list" ]]; then
    echo "prd@2.0.4  browser@1.2.1  nano-banana-pro@3.1.2  gemini@1.5.2  sag@0.9.1"
    exit 0
fi

echo "clawdhub: unknown command '$*'"
exit 1
MOCKEOF

chmod +x "$MOCK_BIN/clawdbot"
chmod +x "$MOCK_BIN/clawdhub"

# Prepend mock_bin to PATH system-wide
echo "export PATH=$MOCK_BIN:\$PATH" >> /etc/bash.bashrc
echo "export PATH=$MOCK_BIN:\$PATH" >> /root/.bashrc

# Also set PATH immediately for any direct execution
export PATH="$MOCK_BIN:$PATH"

# Verify mocks are accessible
echo "Mock binaries installed:"
ls -la "$MOCK_BIN/"
echo "PATH set. clawdbot location: $(which clawdbot 2>/dev/null || echo 'not in PATH yet - agent must use full path or source bashrc')"

# Make invocations.log writable
chmod 666 "$MOCK_BIN/invocations.log"

echo "Setup complete."