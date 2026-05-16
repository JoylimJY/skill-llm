import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create a realistic fintech project directory structure (distractor files) ---
dirs = [
    "payments-service/src/handlers",
    "payments-service/src/models",
    "payments-service/tests/unit",
    "payments-service/tests/integration",
    "payments-service/config",
    "fraud-detection/src/rules",
    "fraud-detection/src/ml",
    "fraud-detection/tests",
    "fraud-detection/config",
    "shared/proto",
    "shared/utils",
    "infra/k8s",
    "infra/terraform",
    "docs/adr",
    "logs/archive",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic fintech content
files = {
    "payments-service/src/handlers/payment_handler.py": """\
class PaymentHandler:
    def process(self, amount, currency, merchant_id):
        # TODO: add idempotency key check
        pass
""",
    "payments-service/src/models/transaction.py": """\
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    created_at: datetime
    status: str  # pending | settled | failed
""",
    "payments-service/tests/unit/test_handler.py": """\
def test_process_payment():
    # placeholder
    assert True
""",
    "payments-service/config/settings.yaml": """\
db_host: postgres-payments
db_port: 5432
retry_limit: 3
timeout_ms: 5000
""",
    "fraud-detection/src/rules/velocity_check.py": """\
def check_velocity(user_id, window_seconds=60):
    # Check number of transactions in window
    return True
""",
    "fraud-detection/src/ml/model_loader.py": """\
import pickle
def load_model(path):
    with open(path, 'rb') as f:
        return pickle.load(f)
""",
    "fraud-detection/config/thresholds.json": json.dumps({
        "high_risk_score": 0.85,
        "medium_risk_score": 0.55,
        "velocity_limit": 10,
        "amount_limit_usd": 50000
    }, indent=2),
    "shared/utils/currency.py": """\
SUPPORTED = ['USD', 'EUR', 'GBP', 'JPY']
def normalize(amount, currency):
    if currency not in SUPPORTED:
        raise ValueError(f'Unsupported: {currency}')
    return round(amount, 2)
""",
    "shared/proto/payment.proto": """\
syntax = "proto3";
message PaymentRequest {
  string merchant_id = 1;
  double amount = 2;
  string currency = 3;
}
""",
    "infra/k8s/payments-deployment.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-service
spec:
  replicas: 3
""",
    "infra/terraform/main.tf": """\
provider "aws" {
  region = "us-east-1"
}
resource "aws_rds_instance" "payments_db" {
  engine = "postgres"
}
""",
    "docs/adr/001-use-postgres.md": """\
# ADR 001: Use PostgreSQL for payments
Status: Accepted
Context: Need ACID compliance for financial transactions.
""",
    "logs/archive/payments-2024-01-15.log": """\
2024-01-15T10:00:01Z INFO Payment processed txn_001 amount=150.00 USD
2024-01-15T10:00:03Z INFO Payment processed txn_002 amount=299.99 USD
2024-01-15T10:00:07Z ERROR Payment failed txn_003 reason=insufficient_funds
""",
    "logs/archive/fraud-2024-01-15.log": """\
2024-01-15T10:00:02Z INFO Score=0.12 user=u_001 ALLOW
2024-01-15T10:00:04Z WARN Score=0.72 user=u_002 REVIEW
2024-01-15T10:00:08Z CRIT Score=0.91 user=u_003 BLOCK
""",
}

for path, content in files.items():
    full = workspace / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

# --- Create the fake-claude responder script ---
# This script simulates Claude Code behavior inside a tmux pane.
# It runs as a loop: reads stdin, prints a ❯ echo then a ⏺ response.
fake_claude_script = r"""#!/bin/bash
# Fake Claude Code simulator for testing
# Prints initial conversation history then waits for input

SESSION_NAME="$1"

# Print some initial conversation history to simulate ongoing work
echo "Claude Code v1.2.0"
echo "Working in project: ${SESSION_NAME}"
echo ""
echo "❯ What is the current structure of the payment handler?"
echo ""
echo "⏺ The payment handler in src/handlers/payment_handler.py currently"
echo "  defines a PaymentHandler class with a process() method. The method"  
echo "  accepts amount, currency, and merchant_id parameters but the body"
echo "  is a stub with a TODO comment for idempotency key checking."
echo ""
echo "❯ Should we add retry logic at the handler level or the service level?"
echo ""
echo "⏺ I recommend implementing retry logic at the service level rather than"
echo "  the handler level. This keeps the handler focused on request parsing"
echo "  and validation while the service layer handles transient failures."
echo "  The config already has retry_limit: 3 which supports this approach."
echo ""

# Now enter interactive mode
while IFS= read -r line; do
    # Echo back what was received with the user marker
    echo ""
    echo "❯ ${line}"
    echo ""
    # Simulate thinking delay
    sleep 0.5
    # Respond based on content
    if echo "$line" | grep -q "/compact"; then
        echo "⏺ Compacting conversation memory..."
        echo "  Summarized 847 tokens → 203 tokens."
        echo "  Context window freed: 644 tokens."
    else
        echo "⏺ Understood. Processing your request regarding: ${line}"
        echo "  This has been noted and I will proceed accordingly."
        echo "  Let me know if you need any clarification."
    fi
    echo ""
done
"""

fake_claude_path = workspace / "fake_claude.sh"
fake_claude_path.write_text(fake_claude_script)
os.chmod(fake_claude_path, 0o755)

# --- Create a decoy tmux-notes file (distractor) ---
(workspace / "tmux-notes.txt").write_text("""\
Old notes - IGNORE
sessions: dev, staging, prod
""")

# --- Create the task brief for the agent ---
# This is NOT a hint file - it's a business context document
task_brief = """\
Project: Fintech AI Assistant Monitoring
Date: 2024-01-16
Author: Platform Engineering

Two AI coding assistant processes have been running overnight on separate projects.
Sessions: 'payments' (payments-service) and 'fraud' (fraud-detection).
Action required per ops runbook - see session_report.json output spec below.
"""
(workspace / "ops_brief.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")