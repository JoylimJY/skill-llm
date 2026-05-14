#!/bin/bash
set -e

echo "=== DCG Guard Sandbox Setup ==="

# Make scripts executable
chmod +x /workspace/scripts/deploy.sh || true
chmod +x /workspace/scripts/setup_env.sh || true
chmod +x /workspace/scripts/legacy_guard.sh || true

# Ensure node modules path exists
mkdir -p /workspace/plugins/dcg-guard/node_modules

# Pre-install the DCG binary so the agent can discover it at the default path
# Install to ~/.local/bin/dcg (the default path per SKILL.md)
echo "Installing DCG binary..."
mkdir -p ~/.local/bin

# Try to install DCG via the official installer
if curl -sSL --max-time 30 https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/master/install.sh -o /tmp/dcg_install.sh 2>/dev/null; then
    chmod +x /tmp/dcg_install.sh
    bash /tmp/dcg_install.sh 2>/dev/null || true
fi

# Verify or create a functional DCG binary
# The DCG binary reads a command from stdin and outputs whether it's dangerous
# If the real binary didn't install, create a reliable mock that matches the SKILL.md behavior
DCG_PATH="$HOME/.local/bin/dcg"
if [ ! -f "$DCG_PATH" ] || [ ! -x "$DCG_PATH" ]; then
    echo "Creating DCG binary mock at $DCG_PATH"
    cat > "$DCG_PATH" << 'DCGEOF'
#!/usr/bin/env python3
"""
DCG (Dangerous Command Guard) - mock implementation matching SKILL.md behavior.
Reads command from stdin, exits 0 if safe, exits non-zero and prints DANGEROUS if blocked.
"""
import sys
import re

DANGEROUS_PATTERNS = [
    # rm -rf variants
    r'rm\s+.*-[a-zA-Z]*r[a-zA-Z]*\s+.*-[a-zA-Z]*f',
    r'rm\s+.*-[a-zA-Z]*f[a-zA-Z]*\s+.*-[a-zA-Z]*r',
    r'rm\s+-rf',
    r'rm\s+-fr',
    # git dangerous operations
    r'git\s+push\s+.*--force',
    r'git\s+push\s+-f\b',
    r'git\s+reset\s+--hard',
    r'git\s+clean\s+.*-f',
    r'git\s+branch\s+-D\b',
    # Windows dangerous
    r'Remove-Item\s+.*-Recurse.*-Force',
    r'rd\s+/s\s+/q',
    r'del\s+/s',
    r'Format-Volume',
    r'reg\s+delete\s+HKLM',
]

def is_dangerous(cmd):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False

cmd = sys.stdin.read().strip()
if is_dangerous(cmd):
    print("DANGEROUS: command blocked by DCG")
    sys.exit(1)
else:
    sys.exit(0)
DCGEOF
    chmod +x "$DCG_PATH"
fi

echo "DCG binary at: $DCG_PATH"
"$DCG_PATH" <<< "ls -la" && echo "DCG binary test (safe): PASS" || echo "DCG binary test (safe): unexpected block"
"$DCG_PATH" <<< "rm -rf ~" && echo "DCG binary test (dangerous): missed block" || echo "DCG binary test (dangerous): PASS (correctly blocked)"

# Add ~/.local/bin to PATH system-wide
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /etc/bash.bashrc
export PATH="$HOME/.local/bin:$PATH"

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -type f | sort