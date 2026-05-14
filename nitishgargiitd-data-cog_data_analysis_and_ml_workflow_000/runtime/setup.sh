#!/bin/bash
set -e

# ── Start a mock CellCog API server ───────────────────────────────────────
cat > /tmp/mock_cellcog_server.py << 'MOCK_SERVER_EOF'
from flask import Flask, request, jsonify
import json, os, time, threading
from pathlib import Path

app = Flask(__name__)
RECEIVED_CALLS = []

@app.route("/v1/chat", methods=["POST"])
def create_chat():
    data = request.get_json(force=True)
    RECEIVED_CALLS.append(data)
    # Persist the call for evaluation
    log_path = Path("/tmp/cellcog_calls.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps(data) + "\n")
    return jsonify({
        "session_id": "mock-session-abc123",
        "status": "queued",
        "message": "Task submitted. Daemon will notify when complete."
    }), 202

@app.route("/v1/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7341, debug=False)
MOCK_SERVER_EOF

python /tmp/mock_cellcog_server.py &
SERVER_PID=$!
echo "Mock CellCog server PID: $SERVER_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:7341/v1/health > /dev/null 2>&1; then
        echo "Mock server ready."
        break
    fi
    sleep 1
done

# ── Install a mock cellcog Python client that points to our local server ──
cat > /usr/local/lib/python3.11/site-packages/cellcog.py << 'CLIENT_EOF'
"""
Mock CellCog SDK - mirrors the real SDK interface described in SKILL.md.
Sends calls to the local mock server for evaluation.
"""
import requests
import json

CELLCOG_API_BASE = "http://localhost:7341"

class CellCogClient:
    def __init__(self, api_key: str = "local-dev", base_url: str = CELLCOG_API_BASE):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def create_chat(
        self,
        prompt: str,
        notify_session_key: str = None,
        task_label: str = None,
        chat_mode: str = "agent",
        **kwargs,
    ):
        payload = {
            "prompt": prompt,
            "chat_mode": chat_mode,
        }
        if notify_session_key is not None:
            payload["notify_session_key"] = notify_session_key
        if task_label is not None:
            payload["task_label"] = task_label
        payload.update(kwargs)

        resp = self.session.post(f"{self.base_url}/v1/chat", json=payload)
        resp.raise_for_status()
        return resp.json()

# Convenience singleton
client = CellCogClient()
CLIENT_EOF

echo "cellcog SDK installed."

# Clear any previous call logs
rm -f /tmp/cellcog_calls.jsonl
touch /tmp/cellcog_calls.jsonl

echo "Setup complete."