#!/bin/bash
set -e

echo "Setting up sandbox environment..."

# Ensure directories exist and have correct permissions
mkdir -p ~/.openclaw/extensions/acp/src
mkdir -p ~/.openclaw/identities
mkdir -p ~/.acp-storage/AIDs
mkdir -p ~/.acp-storage/sessions

# Make the ACP plugin entry point readable
chmod 644 ~/.openclaw/extensions/acp/index.ts 2>/dev/null || true

# Make config files writable
chmod 644 ~/.openclaw/openclaw.json 2>/dev/null || true
chmod 644 ~/.openclaw/identities/33ca5434ab12ef78901234567890abcd.json 2>/dev/null || true

echo "Setup complete."
echo ""
echo "Note: openclaw.json currently has configuration issues that need to be resolved."
echo "Log file at ~/projects/logs/openclaw.log may contain hints about errors."