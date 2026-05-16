#!/usr/bin/env bash
set -euo pipefail

# Make the splitxch script executable
chmod +x /workspace/scripts/splitxch.sh

# -------------------------------------------------------
# Start a local mock SplitXCH API server
# -------------------------------------------------------
cat > /tmp/mock_splitxch_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock SplitXCH API server.
- Validates that points sum to exactly 9850
- Validates all addresses start with xch1
- Validates all addresses are unique
- Validates each recipient's points > 0
- Returns deterministic addresses based on payload content
- Records all calls to /tmp/splitxch_calls.jsonl for eval inspection
"""
import json
import hashlib
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

CALLS_LOG = "/tmp/splitxch_calls.jsonl"

def make_address(payload_str: str, call_index: int) -> str:
    """Generate a deterministic fake xch1 address from payload hash."""
    h = hashlib.sha256(f"{call_index}:{payload_str}".encode()).hexdigest()
    # xch1 followed by 58 chars of the hash (bech32-like, lowercase hex is fine for testing)
    return "xch1" + h[:58]

class Handler(BaseHTTPRequestHandler):
    call_count = 0

    def log_message(self, format, *args):
        pass  # suppress default logging

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/compute/fast":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            self._error(400, f"Invalid JSON: {e}")
            return

        recipients = payload.get("recipients", [])
        if not isinstance(recipients, list) or len(recipients) == 0:
            self._error(400, "recipients must be a non-empty list")
            return

        if len(recipients) > 128:
            self._error(400, f"Too many recipients: {len(recipients)} > 128")
            return

        addresses = []
        total_points = 0
        for r in recipients:
            addr = r.get("address", "")
            pts = r.get("points", 0)

            if not isinstance(addr, str) or not addr.startswith("xch1"):
                self._error(400, f"Invalid address: {addr}")
                return
            if not isinstance(pts, int) or pts <= 0:
                self._error(400, f"Points must be > 0, got: {pts}")
                return
            addresses.append(addr)
            total_points += pts

        if len(set(addresses)) != len(addresses):
            self._error(400, "Duplicate addresses in split")
            return

        if total_points != 9850:
            self._error(400, f"Points must sum to 9850, got: {total_points}")
            return

        # All good - generate deterministic address
        Handler.call_count += 1
        call_idx = Handler.call_count
        result_address = make_address(body, call_idx)
        split_id = hashlib.md5(f"{call_idx}:{body}".encode()).hexdigest()

        response = {
            "id": split_id,
            "message": "Saved",
            "pctProgress": 100,
            "address": result_address
        }

        # Log the call
        log_entry = {
            "call_index": call_idx,
            "request": payload,
            "response": response
        }
        with open(CALLS_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        self._respond(200, response)

    def _respond(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, message):
        self._respond(code, {"message": message})

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8766), Handler)
    print(f"Mock SplitXCH API listening on http://127.0.0.1:8766", flush=True)
    server.serve_forever()
PYEOF

python3 /tmp/mock_splitxch_server.py &
SERVER_PID=$!
echo $SERVER_PID > /tmp/mock_server.pid

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://127.0.0.1:8766/api/compute/fast -X POST \
        -H "Content-Type: application/json" \
        -d '{"recipients":[{"name":"test","address":"xch1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","points":9850,"id":1}]}' \
        | grep -q "address"; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

# Point the splitxch script to the local mock server
export SPLITXCH_API_URL="http://127.0.0.1:8766/api/compute/fast"

# Persist the env var for all future shells / agent processes
echo "export SPLITXCH_API_URL=http://127.0.0.1:8766/api/compute/fast" >> /etc/environment
echo "export SPLITXCH_API_URL=http://127.0.0.1:8766/api/compute/fast" >> /root/.bashrc
echo "export SPLITXCH_API_URL=http://127.0.0.1:8766/api/compute/fast" >> /root/.profile

# Also write it to a file the agent can source if needed
echo "SPLITXCH_API_URL=http://127.0.0.1:8766/api/compute/fast" > /workspace/.env

echo "Setup complete. Mock server PID: $SERVER_PID"