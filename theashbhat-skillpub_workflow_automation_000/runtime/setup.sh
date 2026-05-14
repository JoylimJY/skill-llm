#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

echo "=== Setting up skill-publisher scripts ==="
chmod +x "${WORKSPACE}/skill-publisher/scripts/scaffold.sh"
chmod +x "${WORKSPACE}/skill-publisher/scripts/validate.sh"
chmod +x "${WORKSPACE}/skill-publisher/scripts/security-scan.sh"
chmod +x "${WORKSPACE}/skill-publisher/scripts/publish.sh"
chmod +x "${WORKSPACE}/skill-publisher/scripts/clawhub"

# Symlink clawhub to PATH
ln -sf "${WORKSPACE}/skill-publisher/scripts/clawhub" /usr/local/bin/clawhub

echo "=== Starting mock ClawHub server ==="
cat > /tmp/mock_clawhub_server.py << 'PYEOF'
#!/usr/bin/env python3
"""Minimal mock ClawHub API server for benchmark."""
import json, os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

VALID_TOKEN = "benchmark-token-xyz"
published_skills = {}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress noisy logs

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def do_POST(self):
        if self.path == "/api/login":
            body = json.loads(self._read_body())
            if body.get("user") == "ci-agent" and body.get("pass") == "benchmark":
                resp = json.dumps({"token": VALID_TOKEN}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)
            else:
                self.send_response(401)
                self.end_headers()
            return

        if self.path == "/api/publish":
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != VALID_TOKEN:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Unauthorized")
                return
            # Parse multipart form data minimally
            content_type = self.headers.get("Content-Type", "")
            body = self._read_body()
            # Extract slug and version from form fields
            slug, version = None, None
            for line in body.split(b"\r\n"):
                if b'name="slug"' in line:
                    slug = "NEXT"
                elif b'name="version"' in line:
                    version = "NEXT"
                elif slug == "NEXT":
                    slug = line.decode(errors="replace").strip()
                elif version == "NEXT":
                    version = line.decode(errors="replace").strip()
            if slug and version:
                published_skills[f"{slug}@{version}"] = True
                # Persist to disk for eval
                os.makedirs("/tmp/clawhub_registry", exist_ok=True)
                with open(f"/tmp/clawhub_registry/{slug}@{version}", "w") as f:
                    f.write(json.dumps({"slug": slug, "version": version}))
                resp = json.dumps({"status": "published", "slug": slug, "version": version}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing slug or version")
            return

        self.send_response(404)
        self.end_headers()

server = HTTPServer(("0.0.0.0", 7474), Handler)
print("Mock ClawHub server listening on :7474", flush=True)
server.serve_forever()
PYEOF

python3 /tmp/mock_clawhub_server.py &
sleep 1

# Quick health check
if curl -sf http://localhost:7474/api/login \
     -H "Content-Type: application/json" \
     -d '{"user":"ci-agent","pass":"benchmark"}' > /dev/null; then
  echo "Mock ClawHub server is healthy."
else
  echo "WARNING: Mock ClawHub server health check failed." >&2
fi

echo "=== Setup complete ==="