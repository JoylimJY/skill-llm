#!/bin/bash
set -e

echo "[*] Setting up mock services on localhost..."

# Start a simple HTTP server on port 8080 (simulating a custom fintech app)
python3 -c "
import http.server
import socketserver
import threading

class QuietHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Server', 'FinTechApp/2.1.3')
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body>Staging Portal</body></html>')

httpd = socketserver.TCPServer(('127.0.0.1', 8080), QuietHandler)
httpd.serve_forever()
" &

# Start SSH daemon (it may already be configured)
mkdir -p /run/sshd
/usr/sbin/sshd -D &
SSH_PID=$!
echo "SSH started with PID $SSH_PID"

# Start nginx on port 80
nginx -g 'daemon off;' &
NGINX_PID=$!
echo "Nginx started with PID $NGINX_PID"

# Start a raw TCP listener on port 3306 (simulating MySQL/DB service)
python3 -c "
import socket
import threading

def handle(conn):
    try:
        conn.send(b'\x4a\x00\x00\x00\x0a\x38\x2e\x30\x2e\x33\x35\x00')  # Fake MySQL greeting
        conn.close()
    except:
        pass

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('127.0.0.1', 3306))
s.listen(5)
while True:
    try:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()
    except:
        break
" &

# Give services time to start
sleep 3

echo "[*] Verifying services are listening..."
ss -tlnp | grep -E ':(22|80|3306|8080)' || true

echo "[*] Setup complete. Services running:"
echo "    - SSH on port 22"
echo "    - HTTP (nginx) on port 80"
echo "    - MySQL-like on port 3306"
echo "    - FinTechApp HTTP on port 8080"

# Ensure workspace has correct permissions
chmod -R 755 /workspace

echo "[*] Agent workspace ready at /workspace"