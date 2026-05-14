#!/bin/bash
set -e

# Write the mock OpenTask.ai server
cat > /workspace/mock_opentask_server.py << 'PYEOF'
from flask import Flask, request, jsonify
import json, threading, time, os

app = Flask(__name__)

# --- Shared State ---
state = {
    "registered": False,
    "token": "ot_mock_neuralbridge_abc123xyz",
    "bids": {},
    "contracts": {},
    "submissions": {},
    "payout_set": False,
    "notifications_fetched": False,
}

TASKS = [
    {
        "id": "task_alpha_001",
        "title": "Python Data Pipeline for CSV Aggregation",
        "budgetText": "200 USDC",
        "budget_usdc": 200,
        "skillsTags": ["python", "data-analysis", "automation"],
        "description": "Build a Python script that aggregates 10 CSV files into a single summary report.",
    },
    {
        "id": "task_beta_002",
        "title": "Market Research Report on AI Tools",
        "budgetText": "120 USDC",
        "budget_usdc": 120,
        "skillsTags": ["research", "writing"],
        "description": "Produce a 2000-word market research report on the top 10 AI productivity tools.",
    },
    {
        "id": "task_gamma_003",
        "title": "Logo Design for Startup",
        "budgetText": "300 USDC",
        "budget_usdc": 300,
        "skillsTags": ["design", "illustrator"],
        "description": "Create a logo. NOT relevant to our agent skills.",
    },
    {
        "id": "task_delta_004",
        "title": "Fix React Frontend Bug",
        "budgetText": "30 USDC",
        "budget_usdc": 30,
        "skillsTags": ["javascript", "react"],
        "description": "Below minimum budget threshold.",
    },
    {
        "id": "task_epsilon_005",
        "title": "Competitive Analysis: Data Platforms 2024",
        "budgetText": "150 USDC",
        "budget_usdc": 150,
        "skillsTags": ["research", "data-analysis"],
        "description": "Deep competitive analysis of 5 data platforms.",
    },
]

def verify_token(req):
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {state['token']}"

@app.route("/api/agent/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["email", "password", "handle", "displayName"]
    for field in required:
        if not data or field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    state["registered"] = True
    state["registered_email"] = data["email"]
    state["registered_handle"] = data["handle"]
    return jsonify({
        "success": True,
        "tokenValue": state["token"],
        "agent": {"handle": data["handle"], "email": data["email"]}
    }), 201

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    sort = request.args.get("sort", "new")
    return jsonify({"tasks": TASKS, "sort": sort}), 200

@app.route("/api/agent/tasks/<task_id>/bids", methods=["POST"])
def place_bid(task_id):
    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    errors = []

    # Validate priceText format: must be "X USDC"
    price_text = data.get("priceText", "")
    try:
        parts = price_text.strip().split()
        assert len(parts) == 2 and parts[1] == "USDC"
        bid_amount = float(parts[0])
        budget = task["budget_usdc"]
        ratio = bid_amount / budget
        if not (0.30 <= ratio <= 0.50):
            errors.append(f"priceText bid ratio {ratio:.2f} not in [0.30, 0.50] of budget {budget}")
    except Exception as e:
        errors.append(f"priceText format invalid: '{price_text}' — {e}")

    # Validate etaDays == 1
    eta = data.get("etaDays")
    if eta != 1:
        errors.append(f"etaDays must be 1, got {eta!r}")

    # Validate approach contains 'Plan:' and 'Verification:'
    approach = data.get("approach", "")
    if "Plan:" not in approach:
        errors.append("approach must contain 'Plan:'")
    if "Verification:" not in approach:
        errors.append("approach must contain 'Verification:'")

    if errors:
        return jsonify({"error": "Bid validation failed", "details": errors}), 422

    bid_id = f"bid_{task_id}_001"
    contract_id = f"contract_{task_id}_001"
    state["bids"][bid_id] = {
        "task_id": task_id, "priceText": price_text,
        "etaDays": eta, "approach": approach
    }
    state["contracts"][contract_id] = {
        "task_id": task_id, "bid_id": bid_id, "status": "active"
    }
    state["pending_notifications"] = state.get("pending_notifications", 0) + 1

    return jsonify({
        "success": True,
        "bid": {"id": bid_id, "status": "submitted"},
        "contract": {"id": contract_id, "status": "active"}
    }), 201

@app.route("/api/agent/notifications/unread-count", methods=["GET"])
def unread_count():
    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401
    count = len(state.get("contracts", {}))
    return jsonify({"unreadCount": count}), 200

@app.route("/api/agent/notifications", methods=["GET"])
def notifications():
    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401
    unread_only = request.args.get("unreadOnly")
    if unread_only != "1":
        return jsonify({"error": "Must use unreadOnly=1"}), 400
    state["notifications_fetched"] = True
    notifs = []
    for cid, c in state["contracts"].items():
        notifs.append({
            "id": f"notif_{cid}",
            "type": "contract_created",
            "contractId": cid,
            "taskId": c["task_id"],
            "message": f"Your bid was accepted. Contract {cid} is active."
        })
    return jsonify({"notifications": notifs}), 200

@app.route("/api/agent/contracts/<contract_id>/submissions", methods=["POST"])
def submit_deliverable(contract_id):
    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    if contract_id not in state["contracts"]:
        return jsonify({"error": "Contract not found"}), 404

    data = request.get_json()
    errors = []

    deliverable_url = data.get("deliverableUrl", "")
    if not deliverable_url.startswith("http"):
        errors.append(f"deliverableUrl must be a valid URL, got: '{deliverable_url}'")

    notes = data.get("notes", "")
    if len(notes.strip()) < 20:
        errors.append("notes field too short — must describe what changed, how to verify, and known limitations")

    if errors:
        return jsonify({"error": "Submission validation failed", "details": errors}), 422

    state["submissions"][contract_id] = {
        "deliverableUrl": deliverable_url,
        "notes": notes,
        "status": "submitted"
    }

    return jsonify({
        "success": True,
        "submission": {"contractId": contract_id, "status": "submitted", "deliverableUrl": deliverable_url}
    }), 201

@app.route("/api/agent/me/payout-methods", methods=["POST"])
def set_payout():
    if not verify_token(request):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    required = ["denomination", "network", "address"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing: {field}"}), 400
    state["payout_set"] = True
    state["payout_data"] = data
    return jsonify({"success": True, "payoutMethod": data}), 201

@app.route("/api/internal/state", methods=["GET"])
def get_state():
    """Eval endpoint — not part of the public API."""
    return jsonify(state), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8787, debug=False)
PYEOF

python /workspace/mock_opentask_server.py &
SERVER_PID=$!
echo "Mock OpenTask server started with PID $SERVER_PID"

# Wait until the server is ready
for i in $(seq 1 20); do
    if curl -s http://localhost:8787/api/tasks?sort=new > /dev/null 2>&1; then
        echo "Server is ready."
        break
    fi
    echo "Waiting for server... ($i)"
    sleep 1
done