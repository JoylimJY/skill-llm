import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested directory structure for a financial analytics firm
dirs = [
    "workspace/agents/market_data",
    "workspace/agents/report_writer",
    "workspace/agents/audit_logger",
    "workspace/agents/risk_engine",
    "workspace/config/environments",
    "workspace/config/deprecated",
    "workspace/logs/archive/2024",
    "workspace/logs/current",
    "workspace/protocols/v0_legacy",
    "workspace/protocols/v1",
    "workspace/tasks/pending",
    "workspace/tasks/completed",
    "workspace/reports/drafts",
    "workspace/reports/published",
]
for d in dirs:
    os.makedirs(os.path.join("/", d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "workspace/agents/market_data/README_OLD.txt": "Legacy market data agent. Do not use this config.",
    "workspace/agents/report_writer/config.yaml": "version: 0.9\nmodel: gpt-3\ndeprecated: true\n",
    "workspace/agents/audit_logger/endpoint.txt": "http://internal-audit:9999/log  # DEPRECATED",
    "workspace/agents/risk_engine/manifest.json": json.dumps({"agentId": "risk-engine-001", "status": "offline", "capabilities": ["var_calc", "stress_test"]}),
    "workspace/config/environments/prod.env": "ENV=production\nSESSION_TIMEOUT=30\nMAX_RETRIES=3\n",
    "workspace/config/environments/staging.env": "ENV=staging\nSESSION_TIMEOUT=10\n",
    "workspace/config/deprecated/old_session_keys.json": json.dumps({
        "market_data_agent": "HARDCODED-KEY-DO-NOT-USE-abc123",
        "report_writer_agent": "HARDCODED-KEY-DO-NOT-USE-def456",
        "audit_logger_agent": "HARDCODED-KEY-DO-NOT-USE-ghi789",
        "note": "These keys are STALE and must NOT be used. Always fetch live keys from sessions_list."
    }),
    "workspace/logs/archive/2024/session_log_2024_01.jsonl": json.dumps({"ts": "2024-01-15T10:00:00Z", "event": "session_expired", "key": "expired-key-xyz"}) + "\n",
    "workspace/logs/current/active.log": "No active sessions logged yet.\n",
    "workspace/protocols/v0_legacy/messaging.md": "# Legacy Protocol v0\nUse direct RPC calls. DEPRECATED.\n",
    "workspace/protocols/v1/notes.txt": "See SKILL.md for current protocol. This folder is reserved for future examples.",
    "workspace/tasks/pending/coordination_request.txt": (
        "REQUEST FROM: Chief Analytics Officer\n"
        "DATE: 2025-01-20\n\n"
        "We need to coordinate three actions across our agent network:\n\n"
        "1. QUERY the MarketDataAgent to get the latest closing prices for AAPL, MSFT, GOOGL.\n"
        "   We need to WAIT for this data before proceeding.\n\n"
        "2. NOTIFY the AuditLoggerAgent that this data retrieval occurred (we don't need to wait for confirmation).\n\n"
        "3. DELEGATE to the ReportWriterAgent: generate a full end-of-day financial summary report "
        "using the market data retrieved in step 1. This will take a while, so it should run in the background.\n\n"
        "Please coordinate these agents accordingly and log your work in 'coordination_result.json'.\n"
        "Your agent identity: name='CoordinatorAgent', agentId='coordinator-main-007'\n"
    ),
    "workspace/tasks/completed/.gitkeep": "",
    "workspace/reports/drafts/.gitkeep": "",
    "workspace/reports/published/.gitkeep": "",
    "workspace/config/deprecated/session_cache.json": json.dumps({
        "warning": "DO NOT USE cached sessions",
        "cached_at": "2024-12-01T00:00:00Z",
        "sessions": []
    }),
}

for path, content in distractor_files.items():
    full_path = os.path.join("/", path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Mock server configuration (for reference, not a hint to the agent) ---
# The actual mock server is started in setup_script
# We write the server script here so it's available at runtime

mock_server_code = '''
import json
import os
import threading
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

LOG_DIR = "/workspace/mock_server_logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOCK = threading.Lock()

LIVE_SESSIONS = {
    "sessions": [
        {"agentName": "MarketDataAgent",   "agentId": "mda-live-9f3a",   "sessionKey": "sk-live-MARKET-f8c2e1a9"},
        {"agentName": "AuditLoggerAgent",  "agentId": "ala-live-7b2c",   "sessionKey": "sk-live-AUDIT-3d7f902b"},
        {"agentName": "ReportWriterAgent", "agentId": "rwa-live-4e1d",   "sessionKey": "sk-live-REPORT-a1b2c3d4"},
        {"agentName": "CoordinatorAgent",  "agentId": "coordinator-main-007", "sessionKey": "sk-live-COORD-00700700"},
    ]
}

def log_call(tool_name, payload):
    with LOCK:
        log_file = os.path.join(LOG_DIR, f"{tool_name}.jsonl")
        with open(log_file, "a") as f:
            entry = {"timestamp": time.time(), "tool": tool_name, "payload": payload}
            f.write(json.dumps(entry) + "\\n")

@app.route("/sessions_list", methods=["GET", "POST"])
def sessions_list():
    log_call("sessions_list", {})
    return jsonify(LIVE_SESSIONS)

@app.route("/sessions_send", methods=["POST"])
def sessions_send():
    data = request.get_json(force=True, silent=True) or {}
    log_call("sessions_send", data)
    # Simulate blocking response
    timeout = data.get("timeoutSeconds", 0)
    response_body = ""
    if timeout == 120:
        response_body = "AAPL: 189.50, MSFT: 415.20, GOOGL: 173.80 (as of market close)"
    return jsonify({"status": "ok", "response": response_body, "received": data})

@app.route("/sessions_spawn", methods=["POST"])
def sessions_spawn():
    data = request.get_json(force=True, silent=True) or {}
    log_call("sessions_spawn", data)
    import uuid
    run_id = "run-" + str(uuid.uuid4())[:8]
    child_key = "sk-child-" + str(uuid.uuid4())[:8]
    return jsonify({"status": "accepted", "runId": run_id, "childSessionKey": child_key})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7878, debug=False)
'''

with open("/workspace/mock_server.py", "w") as f:
    f.write(mock_server_code)

print("Workspace generated successfully.")
print("Key task file:", "/workspace/tasks/pending/coordination_request.txt")