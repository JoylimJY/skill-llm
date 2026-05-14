#!/usr/bin/env bash
set -e

echo "[setup] Making scripts executable..."
chmod +x /workspace/dividend-premium-tracker/scripts/update_dividend_premium.py
chmod +x /workspace/dividend-premium-tracker/scripts/monitor_dividend_premium.py

echo "[setup] Starting mock data server..."
cat > /tmp/mock_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock server for H30269 dividend yield XLS and bond yield JSON.
Serves on port 18765.
"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

MOCK_DATA_DIR = Path("/workspace/mock_server_data")

class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Suppress noisy access logs
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.lstrip('/')
        query = parse_qs(parsed.query)

        if path == "H30269indicator.xls":
            xls_file = MOCK_DATA_DIR / "H30269indicator.xls"
            if xls_file.exists():
                data = xls_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.ms-excel")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")

        elif path == "bond_yield":
            bond_file = MOCK_DATA_DIR / "bond_yields.json"
            if bond_file.exists():
                all_yields = json.loads(bond_file.read_text())
                start = query.get("start", [None])[0]
                end = query.get("end", [None])[0]
                if start and end:
                    filtered = {
                        k: v for k, v in all_yields.items()
                        if start <= k <= end
                    }
                else:
                    filtered = all_yields
                body = json.dumps(filtered).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 18765), MockHandler)
    print("[mock_server] Listening on port 18765...")
    server.serve_forever()
PYEOF

python3 /tmp/mock_server.py &
MOCK_PID=$!
echo "[setup] Mock server PID: $MOCK_PID"

# Wait for server to be ready
sleep 2

# Verify server is up
curl -s -o /dev/null -w "%{http_code}" http://localhost:18765/H30269indicator.xls | grep -q "200" && \
    echo "[setup] Mock server confirmed: XLS endpoint OK" || \
    echo "[setup] WARNING: XLS endpoint check failed"

curl -s -o /dev/null -w "%{http_code}" "http://localhost:18765/bond_yield?start=2026-01-14&end=2026-01-14" | grep -q "200" && \
    echo "[setup] Mock server confirmed: bond_yield endpoint OK" || \
    echo "[setup] WARNING: bond_yield endpoint check failed"

echo "[setup] Setup complete. Working directory structure:"
find /workspace/dividend-premium-tracker -type f | sort