#!/bin/bash
set -e

# Make deploy script executable (distractor)
chmod +x /workspace/scripts/deploy/deploy.sh

# Create a minimal mock 'clawdbot' binary so any agent attempts to run
# clawdbot commands don't hard-crash the shell (they just print args and exit 0)
cat > /usr/local/bin/clawdbot << 'MOCK_EOF'
#!/bin/bash
echo "[mock-clawdbot] called with args: $@"
exit 0
MOCK_EOF
chmod +x /usr/local/bin/clawdbot

echo "Setup complete. Mock clawdbot available at /usr/local/bin/clawdbot"