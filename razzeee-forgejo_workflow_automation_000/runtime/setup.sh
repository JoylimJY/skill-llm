#!/bin/bash
set -e

echo "[setup] Starting mock Forgejo API server..."

cat > /tmp/mock_forgejo.py << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock Forgejo API server that mimics the Forgejo/Gitea REST API
relevant to the tea CLI commands used in this task.
"""
from flask import Flask, jsonify, request, Response
import json

app = Flask(__name__)

# --- Mock Data ---

ISSUES = [
    {
        "id": 1001,
        "number": 1,
        "title": "Kalman filter divergence under high-G maneuver",
        "state": "open",
        "user": {"login": "j.smith", "id": 10},
        "labels": [{"name": "severity:critical"}, {"name": "module:nav_core"}],
        "body": "Under sustained 6G maneuver the filter diverges after ~12 seconds. Reproducible in SIL test bench.",
        "created_at": "2024-04-02T09:15:00Z",
        "updated_at": "2024-04-10T14:22:00Z",
        "closed_at": None,
        "comments": 3,
        "html_url": "http://localhost:3000/aeroquality/nav-core/issues/1",
    },
    {
        "id": 1002,
        "number": 2,
        "title": "Unchecked return value in position_update()",
        "state": "open",
        "user": {"login": "a.lee", "id": 11},
        "labels": [{"name": "severity:high"}, {"name": "module:nav_core"}],
        "body": "Return value of compute_position() is never checked, can silently fail on sensor dropout.",
        "created_at": "2024-04-15T11:00:00Z",
        "updated_at": "2024-04-16T08:30:00Z",
        "closed_at": None,
        "comments": 1,
        "html_url": "http://localhost:3000/aeroquality/nav-core/issues/2",
    },
    {
        "id": 1003,
        "number": 3,
        "title": "Missing boundary check in altitude parser",
        "state": "open",
        "user": {"login": "b.jones", "id": 12},
        "labels": [{"name": "severity:high"}, {"name": "module:nav_core"}],
        "body": "Altitude parser does not validate input range, negative altitude accepted without error.",
        "created_at": "2024-05-01T16:45:00Z",
        "updated_at": "2024-05-03T10:00:00Z",
        "closed_at": None,
        "comments": 0,
        "html_url": "http://localhost:3000/aeroquality/nav-core/issues/3",
    },
    {
        "id": 1004,
        "number": 4,
        "title": "Race condition in telemetry flush (CLOSED - not relevant)",
        "state": "closed",
        "user": {"login": "j.smith", "id": 10},
        "labels": [{"name": "severity:medium"}],
        "body": "Fixed in v1.2.3",
        "created_at": "2024-03-10T08:00:00Z",
        "updated_at": "2024-03-25T12:00:00Z",
        "closed_at": "2024-03-25T12:00:00Z",
        "comments": 5,
        "html_url": "http://localhost:3000/aeroquality/nav-core/issues/4",
    },
]

PULLS = [
    {
        "id": 2001,
        "number": 1,
        "title": "Fix: add retry logic to telemetry sender",
        "state": "open",
        "user": {"login": "a.lee", "id": 11},
        "body": "Adds exponential backoff retry to telemetry transmit path.",
        "created_at": "2024-04-20T10:00:00Z",
        "updated_at": "2024-04-21T09:00:00Z",
        "merged": False,
        "merged_at": None,
        "base": {"label": "main"},
        "head": {"label": "fix/telemetry-retry"},
        "html_url": "http://localhost:3000/aeroquality/nav-core/pulls/1",
    },
    {
        "id": 2002,
        "number": 2,
        "title": "Feat: implement Kalman filter with DO-178C traceability",
        "state": "open",
        "user": {"login": "b.jones", "id": 12},
        "body": "Full Kalman filter implementation with requirement traceability matrix.",
        "created_at": "2024-05-05T14:30:00Z",
        "updated_at": "2024-05-10T11:15:00Z",
        "merged": False,
        "merged_at": None,
        "base": {"label": "main"},
        "head": {"label": "feat/kalman-filter"},
        "html_url": "http://localhost:3000/aeroquality/nav-core/pulls/2",
    },
    {
        "id": 2003,
        "number": 3,
        "title": "Fix: boundary validation in altitude parser",
        "state": "open",
        "user": {"login": "j.smith", "id": 10},
        "body": "Adds strict range validation for altitude input. Closes #3.",
        "created_at": "2024-05-20T09:45:00Z",
        "updated_at": "2024-05-21T16:00:00Z",
        "merged": False,
        "merged_at": None,
        "base": {"label": "main"},
        "head": {"label": "fix/altitude-boundary"},
        "html_url": "http://localhost:3000/aeroquality/nav-core/pulls/3",
    },
]

REPO_INFO = {
    "id": 9001,
    "name": "nav-core",
    "full_name": "aeroquality/nav-core",
    "description": "Navigation core module - DO-178C Level B",
    "private": True,
    "owner": {"login": "aeroquality", "id": 20},
    "html_url": "http://localhost:3000/aeroquality/nav-core",
    "clone_url": "http://localhost:3000/aeroquality/nav-core.git",
    "default_branch": "main",
    "open_issues_count": 3,
    "stars_count": 0,
    "forks_count": 0,
    "language": "C",
    "created_at": "2023-01-15T00:00:00Z",
    "updated_at": "2024-05-21T16:00:00Z",
}

USER_INFO = {
    "id": 10,
    "login": "aerospace-bot",
    "full_name": "Aerospace Bot",
    "email": "bot@aerospace.local",
    "is_admin": True,
}

# --- Auth middleware ---
def check_token():
    auth = request.headers.get("Authorization", "")
    token = request.args.get("token", "")
    if "test-token-aerospace-42" in auth or token == "test-token-aerospace-42":
        return True
    return False

# --- Routes ---

@app.route("/api/v1/user", methods=["GET"])
def get_user():
    return jsonify(USER_INFO)

@app.route("/api/v1/repos/search", methods=["GET"])
def search_repos():
    return jsonify({"data": [REPO_INFO], "ok": True})

@app.route("/api/v1/repos/<owner>/<repo>", methods=["GET"])
def get_repo(owner, repo):
    if owner == "aeroquality" and repo == "nav-core":
        return jsonify(REPO_INFO)
    return jsonify({"message": "Not found"}), 404

@app.route("/api/v1/repos/<owner>/<repo>/issues", methods=["GET"])
def get_issues(owner, repo):
    if owner != "aeroquality" or repo != "nav-core":
        return jsonify([]), 404
    state = request.args.get("state", "open")
    issue_type = request.args.get("type", "issues")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    
    if state == "open":
        result = [i for i in ISSUES if i["state"] == "open"]
    elif state == "closed":
        result = [i for i in ISSUES if i["state"] == "closed"]
    else:
        result = ISSUES
    
    # paginate
    start = (page - 1) * limit
    end = start + limit
    return jsonify(result[start:end])

@app.route("/api/v1/repos/<owner>/<repo>/issues/<int:index>", methods=["GET"])
def get_issue(owner, repo, index):
    if owner != "aeroquality" or repo != "nav-core":
        return jsonify({"message": "Not found"}), 404
    for issue in ISSUES:
        if issue["number"] == index:
            return jsonify(issue)
    return jsonify({"message": "Not found"}), 404

@app.route("/api/v1/repos/<owner>/<repo>/pulls", methods=["GET"])
def get_pulls(owner, repo):
    if owner != "aeroquality" or repo != "nav-core":
        return jsonify([]), 404
    state = request.args.get("state", "open")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    
    if state == "open":
        result = [p for p in PULLS if p["state"] == "open"]
    elif state == "closed":
        result = [p for p in PULLS if p["state"] == "closed"]
    else:
        result = PULLS
    
    start = (page - 1) * limit
    end = start + limit
    return jsonify(result[start:end])

@app.route("/api/v1/repos/<owner>/<repo>/pulls/<int:index>", methods=["GET"])
def get_pull(owner, repo, index):
    if owner != "aeroquality" or repo != "nav-core":
        return jsonify({"message": "Not found"}), 404
    for pull in PULLS:
        if pull["number"] == index:
            return jsonify(pull)
    return jsonify({"message": "Not found"}), 404

@app.route("/api/v1/repos/<owner>/<repo>/git/refs", methods=["GET"])
def get_refs(owner, repo):
    return jsonify([])

@app.route("/api/v1/repos/<owner>/<repo>/topics", methods=["GET"])
def get_topics(owner, repo):
    return jsonify({"topics": ["navigation", "do-178c", "aerospace"]})

@app.route("/api/v1/settings/api", methods=["GET"])
def get_settings():
    return jsonify({"max_response_items": 50, "default_paging_num": 20})

@app.route("/api/swagger", methods=["GET"])
def swagger():
    return jsonify({})

# Catch-all for debugging
@app.route("/api/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def catch_all(path):
    return jsonify({"message": f"endpoint /{path} not implemented in mock", "ok": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
MOCK_SERVER_EOF

chmod +x /tmp/mock_forgejo.py

# Start the mock server in background
python3 /tmp/mock_forgejo.py > /tmp/mock_forgejo.log 2>&1 &
MOCK_PID=$!
echo $MOCK_PID > /tmp/mock_forgejo.pid

# Wait for server to be ready
echo "[setup] Waiting for mock Forgejo server to start..."
for i in $(seq 1 20); do
    if curl -s http://localhost:3000/api/v1/settings/api > /dev/null 2>&1; then
        echo "[setup] Mock Forgejo server is up on port 3000 (PID: $MOCK_PID)"
        break
    fi
    sleep 1
done

# Verify tea is available
echo "[setup] Checking tea CLI..."
tea --version || echo "[setup] WARNING: tea not found in PATH"

echo "[setup] Setup complete."