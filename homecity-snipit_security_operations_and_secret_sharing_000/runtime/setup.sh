#!/bin/bash
set -e

# ---------------------------------------------------------------
# Start a local mock snipit.sh API server on port 9341
# The CLI tool reads SNIPIT_API_URL env var or defaults to https://snipit.sh
# We'll intercept by overriding /etc/hosts and using a self-signed local server,
# OR by patching the environment variable that snipit-sh CLI respects.
# ---------------------------------------------------------------

cat > /tmp/mock_snipit_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock snipit.sh server. Validates requests and returns deterministic responses.
Records all requests to /tmp/snipit_requests.jsonl for evaluation.
"""
import json
import uuid
import time
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)
REQUESTS_LOG = "/tmp/snipit_requests.jsonl"
SNIPPETS_STORE = "/tmp/snipit_snippets.json"

def log_request(data):
    with open(REQUESTS_LOG, "a") as f:
        f.write(json.dumps(data) + "\n")

def save_snippet(snippet_id, snippet_data):
    try:
        with open(SNIPPETS_STORE, "r") as f:
            store = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        store = {}
    store[snippet_id] = snippet_data
    with open(SNIPPETS_STORE, "w") as f:
        json.dump(store, f)

def load_snippet(snippet_id):
    try:
        with open(SNIPPETS_STORE, "r") as f:
            store = json.load(f)
        return store.get(snippet_id)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

@app.route("/api/snippets", methods=["POST"])
def create_snippet():
    body = request.get_json(force=True, silent=True) or {}
    snippet_id = "snip_" + uuid.uuid4().hex[:10]
    
    record = {
        "event": "create",
        "id": snippet_id,
        "timestamp": time.time(),
        "body": body,
        "headers": dict(request.headers),
    }
    log_request(record)
    
    snippet_data = dict(body)
    snippet_data["id"] = snippet_id
    save_snippet(snippet_id, snippet_data)
    
    response = {
        "id": snippet_id,
        "url": f"http://localhost:9341/s/{snippet_id}",
        "expiresAt": None,
        "burnAfterRead": body.get("burnAfterRead", False),
    }
    return jsonify(response), 201

@app.route("/api/snippets/<snippet_id>", methods=["GET"])
def get_snippet(snippet_id):
    password = request.args.get("password") or request.headers.get("X-Password")
    
    snippet = load_snippet(snippet_id)
    
    record = {
        "event": "get",
        "id": snippet_id,
        "timestamp": time.time(),
        "password_provided": password,
        "headers": dict(request.headers),
    }
    log_request(record)
    
    if not snippet:
        return jsonify({"error": "Snippet not found"}), 404
    
    # Check password if set
    if snippet.get("password") and snippet.get("password") != password:
        return jsonify({"error": "Invalid password"}), 403
    
    response = {
        "id": snippet_id,
        "content": snippet.get("content", ""),
        "language": snippet.get("language", "text"),
        "title": snippet.get("title", ""),
        "burnAfterRead": snippet.get("burnAfterRead", False),
        "expires": snippet.get("expires"),
    }
    return jsonify(response), 200

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "mock-snipit"}), 200

if __name__ == "__main__":
    import os
    open(REQUESTS_LOG, "w").close()
    app.run(host="0.0.0.0", port=9341, debug=False)
PYEOF

chmod +x /tmp/mock_snipit_server.py
python3 /tmp/mock_snipit_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"
echo $MOCK_PID > /tmp/mock_server.pid

# Wait for server to be ready
for i in $(seq 1 20); do
    if curl -sf http://localhost:9341/ > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

# Override the snipit CLI to point to our local mock
# snipit-sh respects SNIPIT_API_URL environment variable
# Add to /etc/environment so all shells pick it up
echo 'export SNIPIT_API_URL=http://localhost:9341' >> /etc/bash.bashrc
echo 'export SNIPIT_API_URL=http://localhost:9341' >> /root/.bashrc
echo 'SNIPIT_API_URL=http://localhost:9341' >> /etc/environment

# Also create a wrapper that ensures the env var is always set
# Find where snipit binary is
SNIPIT_BIN=$(which snipit 2>/dev/null || echo "")
if [ -n "$SNIPIT_BIN" ]; then
    REAL_SNIPIT=$(readlink -f "$SNIPIT_BIN" 2>/dev/null || echo "$SNIPIT_BIN")
    # Create a wrapper script
    cat > /usr/local/bin/snipit << WRAPEOF
#!/bin/bash
export SNIPIT_API_URL=http://localhost:9341
exec $REAL_SNIPIT "\$@"
WRAPEOF
    chmod +x /usr/local/bin/snipit
    echo "Snipit wrapper created at /usr/local/bin/snipit -> $REAL_SNIPIT"
else
    echo "snipit not found in PATH, will rely on env var"
fi

# Also intercept curl to snipit.sh by adding hosts entry
echo "127.0.0.1 snipit.sh" >> /etc/hosts

# Start a thin HTTPS redirect on 443 is complex; instead redirect at the app layer.
# The curl fallback in the task will use the local URL explicitly.
# We provide instructions via a task file.

cat > /workspace/TASK.md << 'TASKEOF'
# Security Operations: Secure Credential Distribution Task

## Background
During an ongoing incident response drill, you need to securely share two sensitive artifacts
with the on-call team. The sharing service endpoint is: http://localhost:9341

## Task 1: Share the Production DB Credentials File
File: secrets/prod_db_credentials.env

Share this file with the following security requirements:
- It must be password-protected using the password: `DrillP@ss2024!`
- It must self-destruct after being read (burn-after-read)
- It must expire in exactly 1 week
- Title it: "Prod DB Creds - Incident Drill"

## Task 2: Share the Remediation Script via Direct HTTP API
File: src/workers/reset_pool.py

Share this script using the direct HTTP API (curl) with:
- Language set to: python
- Burn-after-read enabled
- No password required

## Output
Save both snippet IDs to a file called `snippet_ids.txt` in the workspace root.
Format:
```
CREDS_SNIPPET_ID=<id from task 1>
SCRIPT_SNIPPET_ID=<id from task 2>
```
TASKEOF

echo "Setup complete. Task file written to /workspace/TASK.md"