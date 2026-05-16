#!/bin/bash
set -e

# ── Start the mock scheduled-tasks MCP server ────────────────────────────────
cat > /tmp/mock_mcp_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock server for mcp__scheduled-tasks__ tool calls.
Stores tasks in /tmp/mock_scheduled_tasks.json
Records all API calls in /tmp/mock_mcp_calls.log
"""
from flask import Flask, request, jsonify
import json, os, datetime

app = Flask(__name__)
TASKS_FILE = "/tmp/mock_scheduled_tasks.json"
CALLS_LOG  = "/tmp/mock_mcp_calls.log"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def log_call(endpoint, payload, response):
    entry = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "payload": payload,
        "response": response
    }
    with open(CALLS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

@app.route("/create_scheduled_task", methods=["POST"])
def create_task():
    data = request.json or {}
    tasks = load_tasks()
    task_id = data.get("taskId") or data.get("task_id") or data.get("id")
    if not task_id:
        resp = {"error": "taskId required"}, 400
        log_call("create_scheduled_task", data, resp[0])
        return jsonify(resp[0]), resp[1]
    tasks[task_id] = {
        "taskId": task_id,
        "cronExpression": data.get("cronExpression") or data.get("cron_expression", ""),
        "prompt": data.get("prompt", ""),
        "description": data.get("description", ""),
        "enabled": data.get("enabled", True),
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    save_tasks(tasks)
    resp = {"success": True, "taskId": task_id, "task": tasks[task_id]}
    log_call("create_scheduled_task", data, resp)
    return jsonify(resp)

@app.route("/list_scheduled_tasks", methods=["GET", "POST"])
def list_tasks():
    tasks = load_tasks()
    resp = {"tasks": list(tasks.values())}
    log_call("list_scheduled_tasks", {}, resp)
    return jsonify(resp)

@app.route("/update_scheduled_task", methods=["POST"])
def update_task():
    data = request.json or {}
    tasks = load_tasks()
    task_id = data.get("taskId") or data.get("task_id") or data.get("id")
    if task_id not in tasks:
        resp = {"error": f"Task {task_id} not found"}
        log_call("update_scheduled_task", data, resp)
        return jsonify(resp), 404
    for k, v in data.items():
        if k not in ("taskId", "task_id", "id"):
            tasks[task_id][k] = v
    save_tasks(tasks)
    resp = {"success": True, "task": tasks[task_id]}
    log_call("update_scheduled_task", data, resp)
    return jsonify(resp)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7822, debug=False)
PYEOF

python3 /tmp/mock_mcp_server.py &
sleep 1

# ── Write a thin wrapper so agent can call the mock as "tool" commands ────────
cat > /usr/local/bin/mcp__scheduled-tasks__create_scheduled_task << 'SHEOF'
#!/bin/bash
# Usage: echo '<json>' | mcp__scheduled-tasks__create_scheduled_task
BODY=$(cat)
curl -s -X POST http://localhost:7822/create_scheduled_task \
     -H "Content-Type: application/json" \
     -d "$BODY"
SHEOF
chmod +x "/usr/local/bin/mcp__scheduled-tasks__create_scheduled_task"

cat > /usr/local/bin/mcp__scheduled-tasks__list_scheduled_tasks << 'SHEOF'
#!/bin/bash
curl -s http://localhost:7822/list_scheduled_tasks
SHEOF
chmod +x "/usr/local/bin/mcp__scheduled-tasks__list_scheduled_tasks"

cat > /usr/local/bin/mcp__scheduled-tasks__update_scheduled_task << 'SHEOF'
#!/bin/bash
BODY=$(cat)
curl -s -X POST http://localhost:7822/update_scheduled_task \
     -H "Content-Type: application/json" \
     -d "$BODY"
SHEOF
chmod +x "/usr/local/bin/mcp__scheduled-tasks__update_scheduled_task"

# ── Also expose as a Python-callable helper ───────────────────────────────────
cat > /usr/local/lib/python3.11/mcp_tools.py << 'PYEOF'
"""Helper module: call the local mock MCP server."""
import requests, json

BASE = "http://localhost:7822"

def create_scheduled_task(taskId, cronExpression, prompt, description, enabled=True):
    r = requests.post(f"{BASE}/create_scheduled_task", json={
        "taskId": taskId,
        "cronExpression": cronExpression,
        "prompt": prompt,
        "description": description,
        "enabled": enabled
    })
    return r.json()

def list_scheduled_tasks():
    r = requests.get(f"{BASE}/list_scheduled_tasks")
    return r.json()

def update_scheduled_task(taskId, **kwargs):
    payload = {"taskId": taskId, **kwargs}
    r = requests.post(f"{BASE}/update_scheduled_task", json=payload)
    return r.json()
PYEOF

echo "Mock MCP server started on :7822"
curl -s http://localhost:7822/health