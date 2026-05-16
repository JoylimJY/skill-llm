#!/bin/bash
set -e

# Write the mock OpenClaw cron server
cat > /workspace/mock_cron_server.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock OpenClaw Cron Service
Exposes a REST API mimicking the OpenClaw cron tool.
All state is persisted to /workspace/.cron_store.json
"""
import json
import uuid
import os
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
STORE_PATH = "/workspace/.cron_store.json"

def load_store():
    with open(STORE_PATH, "r") as f:
        return json.load(f)

def save_store(store):
    with open(STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)

def log_call(method, endpoint, body, response):
    store = load_store()
    store["call_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "endpoint": endpoint,
        "body": body,
        "response": response
    })
    save_store(store)

@app.route("/cron/list", methods=["GET"])
def cron_list():
    store = load_store()
    resp = {"jobs": store["jobs"]}
    log_call("GET", "/cron/list", {}, resp)
    return jsonify(resp)

@app.route("/cron/create", methods=["POST"])
def cron_create():
    body = request.json or {}
    store = load_store()
    
    # Validate required fields
    errors = []
    if "schedule" not in body:
        errors.append("missing 'schedule'")
    else:
        if "kind" not in body["schedule"]:
            errors.append("missing 'schedule.kind'")
        else:
            kind = body["schedule"]["kind"]
            if kind not in ("at", "cron"):
                errors.append(f"invalid schedule.kind: {kind}")
            if kind == "cron" and "expr" not in body["schedule"]:
                errors.append("cron schedule missing 'expr'")
            if kind == "at" and "time" not in body["schedule"]:
                errors.append("at schedule missing 'time'")
    
    if "sessionTarget" not in body:
        errors.append("missing 'sessionTarget'")
    if "payload" not in body:
        errors.append("missing 'payload'")
    else:
        if "kind" not in body["payload"]:
            errors.append("missing 'payload.kind'")
        if "text" not in body["payload"]:
            errors.append("missing 'payload.text'")
    
    if errors:
        resp = {"error": "; ".join(errors), "status": "failed"}
        log_call("POST", "/cron/create", body, resp)
        return jsonify(resp), 400
    
    job_id = "job_" + uuid.uuid4().hex[:8]
    job = {
        "jobId": job_id,
        "name": body.get("name", "unnamed"),
        "schedule": body["schedule"],
        "sessionTarget": body["sessionTarget"],
        "payload": body["payload"],
        "status": "active",
        "nextRun": body["schedule"].get("time", "computed")
    }
    store["jobs"].append(job)
    save_store(store)
    resp = {"jobId": job_id, "status": "created", "job": job}
    log_call("POST", "/cron/create", body, resp)
    return jsonify(resp), 201

@app.route("/cron/remove/<job_id>", methods=["DELETE"])
def cron_remove(job_id):
    store = load_store()
    original_count = len(store["jobs"])
    store["jobs"] = [j for j in store["jobs"] if j["jobId"] != job_id]
    
    if len(store["jobs"]) == original_count:
        resp = {"error": f"job {job_id} not found", "status": "failed"}
        log_call("DELETE", f"/cron/remove/{job_id}", {}, resp)
        return jsonify(resp), 404
    
    save_store(store)
    resp = {"status": "removed", "jobId": job_id}
    log_call("DELETE", f"/cron/remove/{job_id}", {}, resp)
    return jsonify(resp)

@app.route("/cron/disable/<job_id>", methods=["POST"])
def cron_disable(job_id):
    store = load_store()
    for job in store["jobs"]:
        if job["jobId"] == job_id:
            job["status"] = "disabled"
            save_store(store)
            resp = {"status": "disabled", "jobId": job_id}
            log_call("POST", f"/cron/disable/{job_id}", {}, resp)
            return jsonify(resp)
    resp = {"error": f"job {job_id} not found"}
    log_call("POST", f"/cron/disable/{job_id}", {}, resp)
    return jsonify(resp), 404

@app.route("/cron/enable/<job_id>", methods=["POST"])
def cron_enable(job_id):
    store = load_store()
    for job in store["jobs"]:
        if job["jobId"] == job_id:
            job["status"] = "active"
            save_store(store)
            resp = {"status": "enabled", "jobId": job_id}
            log_call("POST", f"/cron/enable/{job_id}", {}, resp)
            return jsonify(resp)
    resp = {"error": f"job {job_id} not found"}
    log_call("POST", f"/cron/enable/{job_id}", {}, resp)
    return jsonify(resp), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7291, debug=False)
PYEOF

chmod +x /workspace/mock_cron_server.py

# Start the mock cron server in background
cd /workspace
python3 mock_cron_server.py &
MOCK_PID=$!
echo "Mock cron server started with PID $MOCK_PID on port 7291"

# Wait for server to be ready
sleep 2

# Verify it's running
curl -sf http://localhost:7291/cron/list > /dev/null && echo "Cron server is healthy." || echo "WARNING: Cron server may not be ready."

echo "Setup complete."