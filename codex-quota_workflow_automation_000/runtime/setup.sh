#!/bin/bash
set -e

# Make the skill script executable
chmod +x /workspace/codex-quota/codex-quota.py

# Ensure the stub codex binary is available
if [ ! -f /usr/local/bin/codex ]; then
    echo '#!/bin/bash' > /usr/local/bin/codex
    echo 'exit 0' >> /usr/local/bin/codex
    chmod +x /usr/local/bin/codex
fi

# Print environment info for debugging
echo "=== Setup complete ==="
echo "Python: $(python3 --version)"
echo "codex stub: $(which codex)"
echo "Workspace: /workspace"
echo "Sessions dir:"
ls -laR ~/.codex/sessions/ 2>/dev/null || echo "(empty or missing)"