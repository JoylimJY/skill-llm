#!/bin/bash
set -e

# ── 1. Ensure /etc/hosts is writable by the current user (Linux setup) ───────
chown "$(whoami):$(whoami)" /etc/hosts
chmod 644 /etc/hosts

# ── 2. Start the mock hosts HTTP server in the background ────────────────────
cat > /workspace/mock_hosts_server/server.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock HTTP server serving a synthetic hosts file for DNS fix testing."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path

HOSTS_DATA_PATH = Path("/workspace/mock_hosts_server/hosts_data.txt")
PORT = 18080


class HostsHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress access logs

    def do_GET(self):
        if self.path == "/hosts":
            content = HOSTS_DATA_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), HostsHandler)
    print(f"Mock hosts server running on port {PORT}", flush=True)
    server.serve_forever()
PYEOF

chmod +x /workspace/mock_hosts_server/server.py
nohup python3 /workspace/mock_hosts_server/server.py > /workspace/mock_hosts_server/server.log 2>&1 &

# Wait for server to be ready
sleep 2

# Verify server is running
if curl -s "http://localhost:18080/hosts" | grep -q "github.com"; then
    echo "Mock server is up and serving hosts data."
else
    echo "WARNING: Mock server may not be ready yet."
fi

echo "Setup complete."
echo "Skill path: /workspace/skills/github-dns-helper"
echo "Mock hosts URL: http://localhost:18080/hosts"