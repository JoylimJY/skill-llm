#!/usr/bin/env python3
"""
Generate the sandbox workspace: a realistic fintech microservice project
with messy, incomplete code that needs a new feature developed end-to-end.
"""

import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

def makedirs(path):
    os.makedirs(path, exist_ok=True)

def write_file(path, content):
    makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(content)

# ── Project structure ──────────────────────────────────────────────────────────

write_file(f"{WORKSPACE}/finpay-service/src/main.py", '''\
"""FinPay microservice entry point."""
from flask import Flask
from api.payments import payments_bp
from api.accounts import accounts_bp

app = Flask(__name__)
app.register_blueprint(payments_bp)
app.register_blueprint(accounts_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
''')

write_file(f"{WORKSPACE}/finpay-service/src/api/__init__.py", "")

write_file(f"{WORKSPACE}/finpay-service/src/api/payments.py", '''\
"""Payment processing endpoints."""
from flask import Blueprint, request, jsonify
from services.payment_service import PaymentService

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")
_svc = PaymentService()

@payments_bp.route("/submit", methods=["POST"])
def submit_payment():
    data = request.get_json()
    # TODO: add transaction validation before processing
    result = _svc.process(data)
    return jsonify(result)

@payments_bp.route("/status/<txn_id>", methods=["GET"])
def payment_status(txn_id):
    status = _svc.get_status(txn_id)
    return jsonify(status)
''')

write_file(f"{WORKSPACE}/finpay-service/src/api/accounts.py", '''\
"""Account management endpoints."""
from flask import Blueprint, request, jsonify

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")

@accounts_bp.route("/balance/<account_id>", methods=["GET"])
def get_balance(account_id):
    # stub
    return {"account_id": account_id, "balance": 0.0}
''')

write_file(f"{WORKSPACE}/finpay-service/src/services/__init__.py", "")

write_file(f"{WORKSPACE}/finpay-service/src/services/payment_service.py", '''\
"""Core payment processing logic."""
import uuid
import time

_store = {}

class PaymentService:
    def process(self, data: dict) -> dict:
        txn_id = str(uuid.uuid4())
        _store[txn_id] = {
            "id": txn_id,
            "amount": data.get("amount"),
            "currency": data.get("currency", "USD"),
            "status": "PENDING",
            "created_at": time.time(),
        }
        # BUG: no validation, no fraud check, no idempotency
        _store[txn_id]["status"] = "COMPLETED"
        return _store[txn_id]

    def get_status(self, txn_id: str) -> dict:
        return _store.get(txn_id, {"error": "not found"})
''')

write_file(f"{WORKSPACE}/finpay-service/src/models/__init__.py", "")

write_file(f"{WORKSPACE}/finpay-service/src/models/transaction.py", '''\
"""Transaction data model."""
from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    status: str = "PENDING"
    created_at: float = field(default_factory=time.time)
    merchant_id: Optional[str] = None
    # missing: risk_score, validation_result, idempotency_key
''')

write_file(f"{WORKSPACE}/finpay-service/src/utils/__init__.py", "")

write_file(f"{WORKSPACE}/finpay-service/src/utils/currency.py", '''\
"""Currency utilities."""
SUPPORTED = {"USD", "EUR", "GBP", "JPY", "CNY"}

def normalize(amount: float, currency: str) -> float:
    if currency not in SUPPORTED:
        raise ValueError(f"Unsupported currency: {currency}")
    return round(amount, 2)
''')

write_file(f"{WORKSPACE}/finpay-service/src/utils/logging_config.py", '''\
"""Logging setup."""
import logging

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
''')

write_file(f"{WORKSPACE}/finpay-service/tests/__init__.py", "")

write_file(f"{WORKSPACE}/finpay-service/tests/test_payments.py", '''\
"""Existing payment tests (partial coverage)."""
import pytest
from src.services.payment_service import PaymentService

def test_basic_payment():
    svc = PaymentService()
    result = svc.process({"amount": 100.0, "currency": "USD"})
    assert result["status"] == "COMPLETED"
    assert "id" in result

# TODO: test validation, fraud detection, idempotency
''')

write_file(f"{WORKSPACE}/finpay-service/tests/test_accounts.py", '''\
"""Account endpoint tests."""
# stub — no tests yet
''')

write_file(f"{WORKSPACE}/finpay-service/requirements.txt", '''\
flask>=2.3.0
pytest>=7.4.0
requests>=2.31.0
''')

write_file(f"{WORKSPACE}/finpay-service/pyproject.toml", '''\
[project]
name = "finpay-service"
version = "0.1.0"
requires-python = ">=3.11"
''')

write_file(f"{WORKSPACE}/finpay-service/.env.example", '''\
DATABASE_URL=postgresql://localhost:5432/finpay
REDIS_URL=redis://localhost:6379
SECRET_KEY=change_me
FRAUD_SERVICE_URL=http://fraud-svc:9090
''')

write_file(f"{WORKSPACE}/finpay-service/docker-compose.yml", '''\
version: "3.9"
services:
  finpay:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=${DATABASE_URL}
  redis:
    image: redis:7-alpine
''')

write_file(f"{WORKSPACE}/finpay-service/Makefile", '''\
test:
\tpytest tests/ -v

run:
\tpython src/main.py

lint:
\tflake8 src/ tests/
''')

# Distractor files
write_file(f"{WORKSPACE}/finpay-service/docs/api_spec.md", '''\
# FinPay API

## POST /payments/submit
Submit a new payment transaction.

**TODO**: Add transaction validation endpoint spec.
''')

write_file(f"{WORKSPACE}/finpay-service/docs/architecture.md", '''\
# Architecture

FinPay is a microservice handling payment processing.
Missing: transaction validation layer, risk scoring module.
''')

write_file(f"{WORKSPACE}/finpay-service/.github/workflows/ci.yml", '''\
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest tests/
''')

write_file(f"{WORKSPACE}/finpay-service/migrations/001_initial.sql", '''\
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    amount DECIMAL(18,4) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL
    -- TODO: add risk_score, idempotency_key columns
);
''')

write_file(f"{WORKSPACE}/finpay-service/scripts/seed_data.py", '''\
"""Seed test data."""
# stub
''')

write_file(f"{WORKSPACE}/finpay-service/scripts/migrate.sh", '''\
#!/bin/bash
echo "Running migrations..."
# stub
''')

# ── Mock ACP tool infrastructure ───────────────────────────────────────────────
# These are the mock implementations of ACP tools. They will be installed as
# executable commands that the agent can call. They log all invocations to
# /workspace/call_log.jsonl for evaluation.

makedirs(f"{WORKSPACE}/.acp_mock")

write_file(f"{WORKSPACE}/.acp_mock/sessions_spawn.py", r'''#!/usr/bin/env python3
"""Mock sessions_spawn tool."""
import sys, json, time, uuid, os

LOG_FILE = "/workspace/call_log.jsonl"
STATE_FILE = "/workspace/.acp_mock/state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"sessions": [], "spawn_count": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log_call(params, result):
    entry = {"tool": "sessions_spawn", "params": params, "result": result, "ts": time.time()}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    raw = sys.stdin.read().strip()
    try:
        params = json.loads(raw) if raw else {}
    except Exception:
        if len(sys.argv) > 1:
            try:
                params = json.loads(sys.argv[1])
            except Exception:
                params = {}
        else:
            params = {}

    state = load_state()
    count = state["spawn_count"]
    state["spawn_count"] = count + 1

    agent_id = params.get("agentId", "unknown")
    child_key = f"agent:{agent_id}:acp:{uuid.uuid4()}"
    session_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    # Determine which stage this is for mock response
    task_text = params.get("task", "")
    resume_id = params.get("resumeSessionId")

    # Build session record
    session_record = {
        "sessionKey": child_key,
        "sessionId": session_id,
        "agentId": agent_id,
        "spawnIndex": count,
        "resumeSessionId": resume_id,
        "task": task_text,
        "params_snapshot": params,
    }
    state["sessions"].append(session_record)
    save_state(state)

    result = {
        "status": "spawned",
        "childSessionKey": child_key,
        "runId": run_id,
        "mode": "run",
        "streamLogPath": f"/tmp/acp/{run_id}.log",
        "note": "Agent will be delivered task once ready.",
    }
    log_call(params, result)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
''')

write_file(f"{WORKSPACE}/.acp_mock/sessions_list.py", r'''#!/usr/bin/env python3
"""Mock sessions_list tool."""
import sys, json, time, os

LOG_FILE = "/workspace/call_log.jsonl"
STATE_FILE = "/workspace/.acp_mock/state.json"

def log_call(params, result):
    entry = {"tool": "sessions_list", "params": params, "result": result, "ts": time.time()}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    raw = sys.stdin.read().strip()
    try:
        params = json.loads(raw) if raw else {}
    except Exception:
        params = {}

    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)

    sessions = state.get("sessions", [])

    result = {"sessions": sessions}
    log_call(params, result)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
''')

write_file(f"{WORKSPACE}/.acp_mock/sessions_yield.py", r'''#!/usr/bin/env python3
"""Mock sessions_yield tool. Simulates async completion notifications."""
import sys, json, time, os

LOG_FILE = "/workspace/call_log.jsonl"
STATE_FILE = "/workspace/.acp_mock/state.json"

MOCK_OUTPUTS = {
    0: {
        "agent": "claude",
        "contentTruncated": True,
        "content": "## Transaction Validation Architecture Plan\n\n### Phase 1: Analysis\nThe existing PaymentService lacks: (1) input validation layer, (2) idempotency key support, (3) risk scoring integration. The Transaction model needs risk_score and idempotency_key fields.\n\n### Phase 2: Design\n- New module: src/validation/transaction_validator.py\n- New model field: Transaction.risk_score, Transaction.idempotency_key\n- Integration point: payments_bp submit endpoint\n\n[CONTENT TRUNCATED - full plan exceeds context window]",
    },
    1: {
        "agent": "claude",
        "contentTruncated": False,
        "content": "## Full Transaction Validation Architecture Plan\n\n### Problems Identified\n1. No input sanitization on /payments/submit\n2. No idempotency — duplicate requests cause duplicate charges\n3. No risk scoring hook\n4. Transaction model incomplete\n\n### Solution Design\n1. Create src/validation/ module with TransactionValidator class\n2. Add idempotency_key to Transaction dataclass\n3. Add risk_score field (0.0-1.0)\n4. Wire validator into PaymentService.process()\n5. Write unit tests covering: valid payment, invalid currency, duplicate idempotency_key, high-risk score rejection\n\n### File Changes\n- src/models/transaction.py: add fields\n- src/validation/__init__.py: new\n- src/validation/transaction_validator.py: new\n- src/services/payment_service.py: integrate validator\n- tests/test_validation.py: new test file",
    },
    2: {
        "agent": "codex",
        "contentTruncated": False,
        "content": "## Implementation Complete\n\nCreated src/validation/transaction_validator.py with TransactionValidator class. Added idempotency_key and risk_score to Transaction model. Updated PaymentService to call validator before processing. Wrote tests/test_validation.py with 6 test cases covering all specified scenarios. All tests pass.",
    },
    3: {
        "agent": "claude",
        "contentTruncated": False,
        "content": "## Code Review Complete\n\nThe implementation correctly addresses all planned requirements. TransactionValidator properly handles edge cases. Idempotency logic is sound. Risk scoring hook is extensible. Minor suggestion: add type hints to validator public methods. Overall quality: APPROVED.",
    },
}

def log_call(params, result):
    entry = {"tool": "sessions_yield", "params": params, "result": result, "ts": time.time()}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    raw = sys.stdin.read().strip()
    try:
        params = json.loads(raw) if raw else {}
    except Exception:
        params = {}

    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)

    yield_count = state.get("yield_count", 0)
    state["yield_count"] = yield_count + 1
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    mock = MOCK_OUTPUTS.get(yield_count, {"agent": "unknown", "contentTruncated": False, "content": ""})
    agent = mock["agent"]

    # Simulate the stream of notifications the orchestrator would see
    notifications = [
        f"[{time.strftime('%H:%M:%S')}] Started {agent} session agent:{agent}:acp:xxx. Streaming progress updates to parent session.",
        f"[{time.strftime('%H:%M:%S')}] {agent}: Working on task...",
        f"[{time.strftime('%H:%M:%S')}] Background task done: ACP background task (run abcd1234).",
        f"[{time.strftime('%H:%M:%S')}] {agent} run completed.",
    ]

    result = {
        "notifications": notifications,
        "completed_agent": agent,
        "yield_index": yield_count,
    }
    log_call(params, result)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
''')

write_file(f"{WORKSPACE}/.acp_mock/sessions_history.py", r'''#!/usr/bin/env python3
"""Mock sessions_history tool."""
import sys, json, time, os

LOG_FILE = "/workspace/call_log.jsonl"
STATE_FILE = "/workspace/.acp_mock/state.json"

HISTORY_BY_CALL_INDEX = {
    0: {
        "messages": [{"role": "assistant", "content": "## Transaction Validation Architecture Plan\n\n[CONTENT TRUNCATED]"}],
        "contentTruncated": True,
    },
    1: {
        "messages": [{"role": "assistant", "content": "## Full Transaction Validation Architecture Plan\n\n### Problems Identified\n1. No input sanitization on /payments/submit\n2. No idempotency key support\n3. No risk scoring integration\n\n### Solution Design\n[full plan delivered via resumeSessionId]"}],
        "contentTruncated": False,
    },
    2: {
        "messages": [{"role": "assistant", "content": "## Implementation Complete\n\nAll files created and tests passing."}],
        "contentTruncated": False,
    },
    3: {
        "messages": [{"role": "assistant", "content": "## Review Complete — APPROVED with minor suggestions."}],
        "contentTruncated": False,
    },
}

def log_call(params, result):
    entry = {"tool": "sessions_history", "params": params, "result": result, "ts": time.time()}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    raw = sys.stdin.read().strip()
    try:
        params = json.loads(raw) if raw else {}
    except Exception:
        if len(sys.argv) > 1:
            try:
                params = json.loads(sys.argv[1])
            except Exception:
                params = {}
        else:
            params = {}

    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)

    history_count = state.get("history_count", 0)
    state["history_count"] = history_count + 1
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    result = HISTORY_BY_CALL_INDEX.get(history_count, {"messages": [], "contentTruncated": False})
    log_call(params, result)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
''')

# Create an empty call_log.jsonl
write_file(f"{WORKSPACE}/call_log.jsonl", "")

# Initial ACP state
write_file(f"{WORKSPACE}/.acp_mock/state.json", json.dumps({
    "sessions": [],
    "spawn_count": 0,
    "yield_count": 0,
    "history_count": 0,
}, indent=2))

print("Workspace generated successfully.")
print("Project: /workspace/finpay-service")
print("Mock ACP tools: /workspace/.acp_mock/")
print("Call log: /workspace/call_log.jsonl")