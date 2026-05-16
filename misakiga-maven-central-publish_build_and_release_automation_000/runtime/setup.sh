#!/bin/bash
set -e

echo "=== Setting up sandbox runtime ==="

# Ensure GPG directories exist with correct permissions
mkdir -p ~/.gnupg
chmod 700 ~/.gnupg

# Ensure .m2 directory exists
mkdir -p ~/.m2

# Generate a GPG key non-interactively for the agent to use (provides a real key environment)
# The agent must still configure loopback pinentry properly
cat > /tmp/gpg-keygen-params <<EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: FintechOSS Bot
Name-Email: bot@fintechoss.io
Expire-Date: 0
%commit
EOF

gpg --batch --gen-key /tmp/gpg-keygen-params 2>/dev/null || true
rm -f /tmp/gpg-keygen-params

echo "=== GPG keys available ==="
gpg --list-keys 2>/dev/null || echo "(no keys yet)"

# Make scripts executable
chmod +x /workspace/currencykit-sdk/scripts/*.sh 2>/dev/null || true

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -type f | sort