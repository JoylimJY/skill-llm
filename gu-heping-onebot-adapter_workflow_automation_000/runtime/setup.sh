#!/bin/bash
set -e

# Start a local mock OneBot HTTP server using Flask
cat > /tmp/mock_onebot_server.py << 'PYEOF'
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
DISPATCH_LOG = "/workspace/data/processed/dispatch_log.jsonl"

@app.route("/send_private_msg", methods=["POST"])
def send_private_msg():
    data = request.get_json()
    record = {
        "action": "send_private_msg",
        "user_id": data.get("user_id"),
        "group_id": None,
        "message": data.get("message"),
        "status": "ok"
    }
    with open(DISPATCH_LOG, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return jsonify({"status": "ok", "retcode": 0, "data": {"message_id": 9001}})

@app.route("/send_group_msg", methods=["POST"])
def send_group_msg():
    data = request.get_json()
    record = {
        "action": "send_group_msg",
        "user_id": None,
        "group_id": data.get("group_id"),
        "message": data.get("message"),
        "status": "ok"
    }
    with open(DISPATCH_LOG, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return jsonify({"status": "ok", "retcode": 0, "data": {"message_id": 9002}})

@app.route("/get_login_info", methods=["POST"])
def get_login_info():
    return jsonify({"status": "ok", "data": {"user_id": 10086, "nickname": "TestBot"}})

@app.route("/get_friend_list", methods=["POST"])
def get_friend_list():
    return jsonify({"status": "ok", "data": []})

@app.route("/get_group_list", methods=["POST"])
def get_group_list():
    return jsonify({"status": "ok", "data": []})

@app.route("/set_group_kick", methods=["POST"])
def set_group_kick():
    return jsonify({"status": "ok", "retcode": 0})

if __name__ == "__main__":
    os.makedirs("/workspace/data/processed", exist_ok=True)
    # Clear any previous dispatch log
    open(DISPATCH_LOG, "w").close()
    app.run(host="127.0.0.1", port=3000, debug=False)
PYEOF

python /tmp/mock_onebot_server.py &
MOCK_PID=$!
echo "Mock OneBot HTTP server started with PID $MOCK_PID on port 3000"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s -X POST http://127.0.0.1:3000/get_login_info -H "Content-Type: application/json" -d '{}' > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

# Set environment variables for the agent
export ONEBOT_HTTP_URL="http://127.0.0.1:3000"
export ONEBOT_WS_URL="ws://127.0.0.1:3001"
export ONEBOT_TOKEN=""

# Persist env vars for the agent session
echo 'export ONEBOT_HTTP_URL="http://127.0.0.1:3000"' >> /etc/environment
echo 'export ONEBOT_WS_URL="ws://127.0.0.1:3001"' >> /etc/environment
echo 'export ONEBOT_TOKEN=""' >> /etc/environment

# Also write to a sourced profile
echo 'export ONEBOT_HTTP_URL="http://127.0.0.1:3000"' >> /root/.bashrc
echo 'export ONEBOT_WS_URL="ws://127.0.0.1:3001"' >> /root/.bashrc
echo 'export ONEBOT_TOKEN=""' >> /root/.bashrc

chmod +x /workspace/scripts/onebot_client.py 2>/dev/null || true
chmod +x /workspace/scripts/onebot_ws_listener.py 2>/dev/null || true

echo "Setup complete. Workspace ready at /workspace"