#!/bin/bash
set -e

WORKSPACE="/workspace"

# Make scripts executable
chmod +x "$WORKSPACE/skills/us-treasury-tracker/scripts/fetch_treasury.py"
chmod +x "$WORKSPACE/infra/mock_servers/mock_treasury_cnbc.py"

# Start the mock server on port 8888
cd "$WORKSPACE/infra/mock_servers"
python3 mock_treasury_cnbc.py 8888 > /tmp/mock_server.log 2>&1 &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID on port 8888"
sleep 2

# Verify mock server is running
if ! kill -0 $MOCK_PID 2>/dev/null; then
    echo "ERROR: Mock server failed to start"
    cat /tmp/mock_server.log
    exit 1
fi
echo "Mock server is running."

# Redirect CNBC and Treasury.gov to localhost mock server
echo "127.0.0.1 www.cnbc.com" >> /etc/hosts
echo "127.0.0.1 cnbc.com" >> /etc/hosts
echo "127.0.0.1 home.treasury.gov" >> /etc/hosts
echo "127.0.0.1 treasury.gov" >> /etc/hosts
echo "Hosts file updated for CNBC and Treasury.gov interception."

SCRIPT_PATH="$WORKSPACE/skills/us-treasury-tracker/scripts/fetch_treasury.py"

cat > /tmp/patch_header.py << 'PATCHEOF'
# AUTO-INJECTED TEST PATCH: redirects external URLs to local mock server
import requests as _requests_orig
_original_get = _requests_orig.get
def _patched_get(url, **kwargs):
    import re
    url = re.sub(r'https?://(www\.)?cnbc\.com', 'http://localhost:8888', url)
    url = re.sub(r'https?://home\.treasury\.gov', 'http://localhost:8888', url)
    url = re.sub(r'https?://(www\.)?treasury\.gov', 'http://localhost:8888', url)
    kwargs.pop('verify', None)
    return _original_get(url, **kwargs)
_requests_orig.get = _patched_get
# END PATCH
PATCHEOF

ORIGINAL_CONTENT=$(cat "$SCRIPT_PATH")
printf '%s\n%s\n' "$(cat /tmp/patch_header.py)" "$ORIGINAL_CONTENT" > "$SCRIPT_PATH"

echo "fetch_treasury.py patched to use local mock server."
echo "Setup complete. Ready for agent task."