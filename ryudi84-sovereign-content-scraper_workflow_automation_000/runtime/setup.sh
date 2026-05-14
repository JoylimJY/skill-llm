#!/bin/bash
set -e

# Start the local mock HTTP server that serves all feed data
cat > /tmp/mock_feed_server.py << 'PYEOF'
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

WORKSPACE = Path("/workspace")

class MockFeedHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        if self.path == "/reddit_feed":
            data = (WORKSPACE / "raw_feeds" / "reddit_raw.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        elif self.path == "/twitter_feed":
            data = (WORKSPACE / "raw_feeds" / "twitter_raw.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        elif self.path == "/youtube_feed":
            data = (WORKSPACE / "raw_feeds" / "youtube_raw.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        elif self.path == "/rss_gamedeveloper":
            data = (WORKSPACE / "raw_feeds" / "rss_gamedeveloper.xml").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml")
            self.end_headers()
            self.wfile.write(data)

        elif self.path == "/rss_indiegames":
            data = (WORKSPACE / "raw_feeds" / "rss_indiegames.xml").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml")
            self.end_headers()
            self.wfile.write(data)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

server = HTTPServer(("localhost", 7331), MockFeedHandler)
print("Mock feed server running on port 7331", flush=True)
server.serve_forever()
PYEOF

python3 /tmp/mock_feed_server.py &
sleep 1

# Verify the server is up
curl -s http://localhost:7331/reddit_feed > /dev/null && echo "Mock server: OK" || echo "Mock server: FAILED"
echo "Setup complete."