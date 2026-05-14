#!/bin/bash
set -e

# Write and start the mock Restate server that records incoming requests
cat > /tmp/mock_restate_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock Restate server. Listens on 127.0.0.1:8080 and records all
POST requests to /AppFactory/buildFeature/send into a log file.
"""
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
LOG_FILE = "/tmp/restate_requests.jsonl"

@app.route("/AppFactory/buildFeature/send", methods=["POST"])
def build_feature():
    entry = {
        "method": request.method,
        "path": request.path,
        "content_type": request.content_type,
        "body": request.get_json(force=True, silent=True),
        "raw_body": request.get_data(as_text=True),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return jsonify({"status": "accepted", "taskId": "mock-task-001"}), 202

@app.route("/<path:any_path>", methods=["GET", "POST", "PUT", "DELETE"])
def catch_all(any_path):
    # Record wrong-path attempts too so eval can detect them
    entry = {
        "method": request.method,
        "path": "/" + any_path,
        "content_type": request.content_type,
        "body": request.get_json(force=True, silent=True),
        "raw_body": request.get_data(as_text=True),
        "wrong_path": True,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return jsonify({"error": "wrong endpoint"}), 404

if __name__ == "__main__":
    # Clear previous log
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    app.run(host="127.0.0.1", port=8080, debug=False)
PYEOF

chmod +x /tmp/mock_restate_server.py
python3 /tmp/mock_restate_server.py &
SERVER_PID=$!
echo $SERVER_PID > /tmp/mock_restate_server.pid

# Wait until port 8080 is up (max 10 seconds)
for i in $(seq 1 20); do
    if nc -z 127.0.0.1 8080 2>/dev/null; then
        echo "Mock Restate server is up on port 8080 (PID=$SERVER_PID)"
        break
    fi
    sleep 0.5
done

echo "Setup complete."