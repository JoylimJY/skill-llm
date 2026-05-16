#!/bin/bash
set -e

WORKSPACE="/workspace"
STATE_FILE="$WORKSPACE/opengoat_state.json"
SERVER_LOG="$WORKSPACE/opengoat_server.log"

# Write the mock OpenGoat server
cat > /tmp/opengoat_server.py << 'PYEOF'
import json
import sys
import copy
from flask import Flask, request, jsonify

app = Flask(__name__)
STATE_FILE = "/workspace/opengoat_state.json"

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_all_reportees(state, agent_id):
    """Return all direct and indirect reportees of agent_id."""
    result = set()
    queue = list(state["agents"].get(agent_id, {}).get("directReports", []))
    while queue:
        r = queue.pop()
        result.add(r)
        queue.extend(state["agents"].get(r, {}).get("directReports", []))
    return result

@app.route("/tool/<tool_name>", methods=["POST"])
def handle_tool(tool_name):
    state = load_state()
    params = request.json or {}

    if tool_name == "opengoat_agent_info":
        agent_id = params.get("agentId")
        if agent_id not in state["agents"]:
            return jsonify({"error": f"Agent '{agent_id}' not found"}), 404
        agent = copy.deepcopy(state["agents"][agent_id])
        reportees = get_all_reportees(state, agent_id)
        agent["allReportees"] = list(reportees)
        return jsonify({"agent": agent})

    elif tool_name == "opengoat_task_list":
        assignee = params.get("assignee")
        tasks = [t for t in state["tasks"].values() if t["assignedTo"] == assignee]
        return jsonify({"tasks": tasks})

    elif tool_name == "opengoat_task_get":
        task_id = params.get("taskId")
        if task_id not in state["tasks"]:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404
        return jsonify({"task": state["tasks"][task_id]})

    elif tool_name == "opengoat_task_create":
        actor_id = params.get("actorId")
        assigned_to = params.get("assignedTo")
        title = params.get("title", "")
        description = params.get("description", "")
        project = params.get("project", "")

        if actor_id not in state["agents"]:
            return jsonify({"error": f"Actor '{actor_id}' not found"}), 403

        valid_assignees = get_all_reportees(state, actor_id) | {actor_id}
        if assigned_to not in valid_assignees:
            return jsonify({"error": f"Cannot assign to '{assigned_to}': not in your reportee tree"}), 403

        task_id = f"TASK-{state['task_id_counter']:03d}"
        state["task_id_counter"] += 1
        task = {
            "taskId": task_id,
            "title": title,
            "description": description,
            "status": "todo",
            "assignedTo": assigned_to,
            "project": project,
            "blockers": [],
            "artifacts": [],
            "worklogs": [],
            "createdBy": actor_id,
        }
        state["tasks"][task_id] = task
        save_state(state)
        return jsonify({"task": task})

    elif tool_name == "opengoat_task_update_status":
        actor_id = params.get("actorId")
        task_id = params.get("taskId")
        status = params.get("status")
        reason = params.get("reason", "")
        valid_statuses = {"todo", "doing", "blocked", "pending", "done"}
        if status not in valid_statuses:
            return jsonify({"error": f"Invalid status '{status}'. Must be one of: {valid_statuses}"}), 400
        if task_id not in state["tasks"]:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404
        state["tasks"][task_id]["status"] = status
        if reason:
            state["tasks"][task_id].setdefault("statusHistory", []).append({"status": status, "reason": reason})
        save_state(state)
        return jsonify({"task": state["tasks"][task_id]})

    elif tool_name == "opengoat_task_add_blocker":
        task_id = params.get("taskId")
        blocker = params.get("blocker", "")
        if task_id not in state["tasks"]:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404
        state["tasks"][task_id]["blockers"].append(blocker)
        save_state(state)
        return jsonify({"task": state["tasks"][task_id]})

    elif tool_name == "opengoat_task_add_artifact":
        task_id = params.get("taskId")
        content = params.get("content", "")
        if task_id not in state["tasks"]:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404
        state["tasks"][task_id]["artifacts"].append(content)
        save_state(state)
        return jsonify({"task": state["tasks"][task_id]})

    elif tool_name == "opengoat_task_add_worklog":
        task_id = params.get("taskId")
        content = params.get("content", "")
        if task_id not in state["tasks"]:
            return jsonify({"error": f"Task '{task_id}' not found"}), 404
        state["tasks"][task_id]["worklogs"].append(content)
        save_state(state)
        return jsonify({"task": state["tasks"][task_id]})

    else:
        return jsonify({"error": f"Unknown tool: {tool_name}"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7890)
PYEOF

# Write the opengoat tool wrapper that agents will call as a function
cat > /workspace/opengoat_tool.py << 'PYEOF'
"""
OpenGoat tool proxy — agents use this module to call tools.
Usage: from opengoat_tool import call_tool
       result = call_tool("opengoat_task_create", {...})
"""
import requests
import json

OPENGOAT_BASE = "http://localhost:7890/tool"

def call_tool(tool_name: str, params: dict) -> dict:
    resp = requests.post(f"{OPENGOAT_BASE}/{tool_name}", json=params, timeout=10)
    try:
        return resp.json()
    except Exception:
        return {"error": resp.text, "status_code": resp.status_code}
PYEOF

# Also write a shell-callable wrapper so agents can invoke via process if they prefer
cat > /workspace/opengoat << 'SHEOF'
#!/usr/bin/env python3
"""
CLI shim — NOT the preferred way per SKILL.md. Calls the REST proxy.
"""
import sys
import json
import requests

if len(sys.argv) < 3:
    print("Usage: opengoat <tool_name> '<json_params>'")
    sys.exit(1)

tool = sys.argv[1]
params = json.loads(sys.argv[2])
resp = requests.post(f"http://localhost:7890/tool/{tool}", json=params, timeout=10)
print(resp.text)
SHEOF
chmod +x /workspace/opengoat

# Start the mock server in background
nohup python3 /tmp/opengoat_server.py > "$SERVER_LOG" 2>&1 &
echo "OpenGoat mock server starting..."
sleep 2

# Verify server is up
for i in $(seq 1 10); do
    if curl -s http://localhost:7890/tool/opengoat_agent_info -X POST -H 'Content-Type: application/json' -d '{"agentId":"amazon-senior-manager"}' | grep -q "amazon-senior-manager"; then
        echo "OpenGoat server is up."
        break
    fi
    sleep 1
done

echo "Setup complete."