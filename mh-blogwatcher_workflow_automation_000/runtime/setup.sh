#!/bin/bash
set -e

echo "Starting mock RSS/Atom feed HTTP server..."

# Write the Python HTTP server script
cat > /tmp/mock_feed_server.py << 'PYEOF'
#!/usr/bin/env python3
import http.server
import socketserver
import os
from pathlib import Path

FEEDS_DIR = Path("/workspace/mock_feeds")
PORT = 8765

class FeedHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        path = self.path.lstrip('/')
        # Route: /feeds/cloudnative -> cloudnative.xml, etc.
        if path.startswith("feeds/"):
            feed_name = path.split("/", 1)[1]
            feed_file = FEEDS_DIR / f"{feed_name}.xml"
            if feed_file.exists():
                content = feed_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/xml")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
        # Fallback: 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

with socketserver.TCPServer(("", PORT), FeedHandler) as httpd:
    print(f"Mock feed server running on port {PORT}", flush=True)
    httpd.serve_forever()
PYEOF

python3 /tmp/mock_feed_server.py &
SERVER_PID=$!
echo "Mock server PID: $SERVER_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:8765/feeds/cloudnative > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for mock server... ($i)"
    sleep 1
done

# Verify feeds are accessible
echo "Verifying feeds..."
curl -s http://localhost:8765/feeds/cloudnative | grep -q "CloudNative Weekly" && echo "Feed 1 OK" || echo "Feed 1 FAILED"
curl -s http://localhost:8765/feeds/devsecops | grep -q "DevSecOps Digest" && echo "Feed 2 OK" || echo "Feed 2 FAILED"
curl -s http://localhost:8765/feeds/platformeng | grep -q "PlatformEng Pulse" && echo "Feed 3 OK" || echo "Feed 3 FAILED"

echo "Setup complete."