#!/bin/bash
set -e

# Make mock tools executable
chmod +x /workspace/tools/kimi_search
chmod +x /workspace/tools/kimi_fetch

# Add tools to PATH for the agent
echo 'export PATH="/workspace/tools:$PATH"' >> /etc/bash.bashrc
export PATH="/workspace/tools:$PATH"

# Create symlinks in /usr/local/bin so tools are available globally
ln -sf /workspace/tools/kimi_search /usr/local/bin/kimi_search
ln -sf /workspace/tools/kimi_fetch /usr/local/bin/kimi_fetch

# Verify tools work
echo "=== Testing kimi_search ==="
python3 /workspace/tools/kimi_search "顺达物流 统一社会信用代码" | head -20

echo "=== Testing kimi_fetch ==="
python3 /workspace/tools/kimi_fetch "http://www.gsxt.gov.cn/corp-query-entprise-info-100.html?id=shundawl001" | head -20

echo "=== Setup complete ==="