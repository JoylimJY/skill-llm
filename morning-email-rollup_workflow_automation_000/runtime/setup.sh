#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"

echo "[setup] Installing mock CLI tools..."

# Mock 'gog' binary
cat > /usr/local/bin/gog << 'MOCK_GOG'
#!/usr/bin/env bash
# Mock gog CLI - records calls for evaluation
echo '[]' 
exit 0
MOCK_GOG
chmod +x /usr/local/bin/gog

# Mock 'gemini' binary
cat > /usr/local/bin/gemini << 'MOCK_GEMINI'
#!/usr/bin/env bash
# Mock gemini CLI
echo "This is a mock AI-generated summary of the email content."
exit 0
MOCK_GEMINI
chmod +x /usr/local/bin/gemini

# Mock 'cron' binary - records calls to a log file for eval
cat > /usr/local/bin/cron << 'MOCK_CRON'
#!/usr/bin/env bash
# Mock cron CLI - records invocation arguments for evaluation
CRON_CALLS_LOG="/workspace/.cron_calls.log"
echo "CALL: $@" >> "$CRON_CALLS_LOG"

# Parse subcommand
SUBCMD="${1:-}"
case "$SUBCMD" in
    add)
        echo "Cron job added successfully."
        ;;
    list)
        echo "job-abc123  Morning Email Rollup  0 8 * * *  America/Denver"
        ;;
    update)
        echo "Cron job updated."
        ;;
    runs)
        echo "Last run: success"
        ;;
    *)
        echo "Unknown subcommand: $SUBCMD"
        exit 1
        ;;
esac
exit 0
MOCK_CRON
chmod +x /usr/local/bin/cron

# Ensure workspace permissions
chmod -R 755 "$WORKSPACE/skills"

echo "[setup] Mock binaries installed: gog, gemini, cron"
echo "[setup] Setup complete."