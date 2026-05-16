#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
LOG_DIR="$WORKSPACE/.opencode_logs"
mkdir -p "$LOG_DIR"

# ── Mock opencode binary ───────────────────────────────────────────────────────
# This mock records every invocation (with full args and cwd) to a JSONL log,
# then returns realistic fake outputs so the agent can proceed through the workflow.

cat > /usr/local/bin/opencode << 'MOCK_EOF'
#!/usr/bin/env bash
# Mock opencode binary for evaluation purposes.

LOG_DIR="${WORKSPACE:-/workspace}/.opencode_logs"
mkdir -p "$LOG_DIR"
LOGFILE="$LOG_DIR/invocations.jsonl"

# Parse arguments
CMD="${1:-}"         # should be "run"
INSTRUCTIONS="${2:-}"
AGENT_FLAG=""
CONTINUE_FLAG="false"

shift 2 2>/dev/null || true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent)
            AGENT_FLAG="$2"
            shift 2
            ;;
        --continue)
            CONTINUE_FLAG="true"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CWD=$(pwd)

# Append invocation record to JSONL log
python3 -c "
import json, sys
record = {
    'timestamp': '$TIMESTAMP',
    'cwd': '$CWD',
    'command': '$CMD',
    'instructions': sys.argv[1],
    'agent': '$AGENT_FLAG',
    'continue_flag': $CONTINUE_FLAG
}
with open('$LOGFILE', 'a') as f:
    f.write(json.dumps(record) + '\n')
" "$INSTRUCTIONS"

# ── Return realistic mock output depending on agent type ──────────────────────
if [[ "$AGENT_FLAG" == "plan" ]]; then
    cat << 'PLAN_OUT'
[opencode/plan] Analyzing repository structure...

Repository: inventory-service (Flask microservice)

PLAN:
1. Add a new route `GET /health` to `app/routes.py` inside `create_app()`.
   - The endpoint should return JSON: `{"status": "ok"}` with HTTP 200.
2. Add a corresponding test `test_health` in `tests/test_items.py` (or a new file)
   that asserts the response status is 200 and body contains `{"status": "ok"}`.

No clarification questions. The plan is complete.
PLAN_OUT

elif [[ "$AGENT_FLAG" == "build" ]]; then
    # Simulate actual code changes
    REPO_DIR="$CWD"

    # Inject /health route into routes.py
    python3 - << 'PYEOF'
import os, re

repo = os.getcwd()
routes_path = os.path.join(repo, "app", "routes.py")

with open(routes_path, "r") as f:
    content = f.read()

health_route = (
    "\n"
    "    @app.route(\"/health\", methods=[\"GET\"])\n"
    "    def health_check():\n"
    "        return jsonify({\"status\": \"ok\"}), 200\n"
)

# Insert before `return app`
if "/health" not in content:
    content = content.replace("    return app\n", health_route + "\n    return app\n")
    with open(routes_path, "w") as f:
        f.write(content)

# Write test file
tests_health_path = os.path.join(repo, "tests", "test_health.py")
test_content = (
    '"""Tests for /health endpoint."""\n'
    'import pytest\n'
    'from app.routes import create_app\n'
    '\n'
    '\n'
    '@pytest.fixture\n'
    'def client():\n'
    '    app = create_app()\n'
    '    app.config["TESTING"] = True\n'
    '    with app.test_client() as c:\n'
    '        yield c\n'
    '\n'
    '\n'
    'def test_health(client):\n'
    '    rv = client.get("/health")\n'
    '    assert rv.status_code == 200\n'
    '    data = rv.get_json()\n'
    '    assert data.get("status") == "ok"\n'
)
with open(tests_health_path, "w") as f:
    f.write(test_content)

print("[opencode/build] Implementation complete.")
print("Modified: app/routes.py  (added GET /health)")
print("Created:  tests/test_health.py")
PYEOF

else
    echo "[opencode] Unknown agent: $AGENT_FLAG. Use --agent plan or --agent build."
    exit 1
fi
MOCK_EOF

chmod +x /usr/local/bin/opencode

echo "Mock opencode binary installed at /usr/local/bin/opencode"
echo "Invocation log will be written to: $WORKSPACE/.opencode_logs/invocations.jsonl"