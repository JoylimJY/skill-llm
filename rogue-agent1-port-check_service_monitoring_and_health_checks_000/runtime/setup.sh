#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

echo "[setup] Starting mock services for health gate task..."

# ── Port 5432: open TCP (simulates PostgreSQL) ────────────────────────────────
socat TCP-LISTEN:5432,reuseaddr,fork PIPE &
echo "[setup] TCP listener on :5432 (postgres mock)"

# ── Port 8080: HTTP 200 (finpay-api) ─────────────────────────────────────────
python3 -c "
import http.server, socketserver, threading

class H200(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *a): pass

with socketserver.TCPServer(('', 8080), H200) as s:
    s.serve_forever()
" &
echo "[setup] HTTP 200 server on :8080 (finpay-api mock)"

# ── Port 8081: HTTP 500 (payment-svc known issue) ────────────────────────────
python3 -c "
import http.server, socketserver

class H500(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500)
        self.end_headers()
        self.wfile.write(b'Internal Server Error')
    def log_message(self, *a): pass

with socketserver.TCPServer(('', 8081), H500) as s:
    s.serve_forever()
" &
echo "[setup] HTTP 500 server on :8081 (payment-svc mock)"

# Ports 6379 and 9999 are intentionally NOT started — they should appear closed.

sleep 2
echo "[setup] Mock services ready."