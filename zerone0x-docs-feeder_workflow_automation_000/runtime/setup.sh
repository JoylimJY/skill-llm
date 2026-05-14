#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"

# Start a local HTTP server to serve the mock meridian docs on port 9876
# It must serve /llms-full.txt from the mock-server-content directory
python3 -c "
import http.server
import socketserver
import os

os.chdir('/workspace/mock-server-content')

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Suppress access logs

with socketserver.TCPServer(('0.0.0.0', 9876), Handler) as httpd:
    httpd.serve_forever()
" &

echo "Mock docs server started on port 9876 (PID $!)"

# Give the server a moment to start
sleep 1

# Verify server is up
curl -sf http://localhost:9876/llms-full.txt > /dev/null && echo "Server verified: /llms-full.txt is accessible" || echo "WARNING: server check failed"

chmod +x /workspace/fetch-docs.js 2>/dev/null || true