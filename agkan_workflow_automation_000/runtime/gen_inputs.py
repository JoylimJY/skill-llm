import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic fintech project directory structure with distractor files
dirs = [
    "payment-service/src/handlers",
    "payment-service/src/models",
    "payment-service/src/middleware",
    "payment-service/tests/unit",
    "payment-service/tests/integration",
    "payment-service/config",
    "payment-service/migrations",
    "payment-service/docs",
    "infra/terraform",
    "infra/kubernetes",
    "scripts/deploy",
    "scripts/monitoring",
    ".github/workflows",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor source files
source_files = {
    "payment-service/src/handlers/payment_handler.py": """\
import stripe
from models.transaction import Transaction

class PaymentHandler:
    def process(self, amount, currency, card_token):
        # BUG: No idempotency key - causes duplicate charges on retry
        charge = stripe.Charge.create(amount=amount, currency=currency, source=card_token)
        return Transaction(charge_id=charge.id, status='pending')
""",
    "payment-service/src/handlers/refund_handler.py": """\
class RefundHandler:
    def refund(self, transaction_id, amount):
        # TODO: Validate amount does not exceed original charge
        pass
""",
    "payment-service/src/models/transaction.py": """\
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    charge_id: str
    status: str
    created_at: datetime = None
""",
    "payment-service/src/models/webhook.py": """\
class WebhookEvent:
    PAYMENT_SUCCESS = 'payment.success'
    PAYMENT_FAILED = 'payment.failed'
    REFUND_PROCESSED = 'refund.processed'
""",
    "payment-service/src/middleware/auth.py": """\
# WARNING: JWT secret hardcoded - security vulnerability
JWT_SECRET = 'super_secret_key_123'

def verify_token(token):
    import jwt
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
""",
    "payment-service/src/middleware/rate_limiter.py": """\
import time

class RateLimiter:
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
""",
    "payment-service/tests/unit/test_payment.py": """\
import pytest
from handlers.payment_handler import PaymentHandler

def test_process_payment():
    handler = PaymentHandler()
    # Test not implemented - needs mock stripe client
    assert True
""",
    "payment-service/tests/integration/test_webhook.py": """\
def test_webhook_signature_validation():
    # Integration test requires live Stripe webhook secret
    pass
""",
    "payment-service/config/production.yaml": """\
database:
  host: db.internal.fintech.io
  port: 5432
  name: payments_prod
stripe:
  api_version: '2023-10-16'
  webhook_tolerance: 300
""",
    "payment-service/config/staging.yaml": """\
database:
  host: db-staging.internal.fintech.io
  port: 5432
  name: payments_staging
""",
    "payment-service/migrations/001_create_transactions.sql": """\
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    charge_id VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
""",
    "payment-service/docs/api_spec.md": """\
# Payment Service API

## POST /payments
Creates a new payment.

### Request Body
- `amount` (int): Amount in cents
- `currency` (str): ISO 4217 currency code
- `card_token` (str): Tokenized card from frontend

## GET /payments/{id}
Retrieves payment status.
""",
    "infra/terraform/main.tf": """\
provider \"aws\" {
  region = \"us-east-1\"
}

resource \"aws_rds_instance\" \"payments_db\" {
  engine = \"postgres\"
  instance_class = \"db.t3.medium\"
}
""",
    "infra/kubernetes/deployment.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
""",
    "scripts/deploy/rollback.sh": """\
#!/bin/bash
echo \"Rolling back to previous version...\"
kubectl rollout undo deployment/payment-service
""",
    "scripts/monitoring/alert_rules.yaml": """\
groups:
  - name: payment_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(payment_errors_total[5m]) > 0.05
        for: 2m
""",
    ".github/workflows/ci.yaml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest payment-service/tests/
""",
}

for filepath, content in source_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Create the sprint planning input document (the "messy real-world data" the agent must process)
sprint_brief = """\
PAYMENT SERVICE SPRINT PLANNING BRIEF
=====================================
Sprint Goal: Stabilize and harden the payment service before Q3 launch.

ITEMS TO TRACK:

[EPIC] Payment Service Hardening
  Author: sprint-planner
  State: planning phase (not ready to work on yet - needs breakdown)

  SUBTASK 1: Fix duplicate charge bug (idempotency key missing in payment handler)
    - This is the most urgent item. Customers are being double-charged on retries.
    - Start immediately.
    - Category: defect/bug
    - Urgency: CRITICAL

  SUBTASK 2: Remove hardcoded JWT secret from middleware
    - Cannot ship with hardcoded secrets. Must be done before subtask 4.
    - Category: security vulnerability
    - Urgency: HIGH
    - NOTE: Subtask 3 cannot begin until this is resolved.

  SUBTASK 3: Add rate limiting to payment endpoints
    - Protects against abuse. Depends on auth middleware being secure first.
    - Category: improvement/enhancement
    - Urgency: HIGH

  SUBTASK 4: Write unit tests for PaymentHandler
    - Needed for CI pipeline confidence.
    - Category: testing
    - Urgency: MEDIUM
    - NOTE: Can only start after subtask 1 is fixed (need stable code to test).

WORKFLOW NOTES:
- The epic/parent task should remain in backlog for now (not started).
- Subtask 1 should be actively worked on (in progress).
- Subtask 2 should be ready to start (ready).  
- Subtasks 3 and 4 should be in backlog (not yet ready).
- The blocking chain: Subtask 1 blocks Subtask 4. Subtask 2 blocks Subtask 3.

DELIVERABLE:
After setting up all tasks in the tracking system, export the full task list 
(including done/closed tasks if any) as a JSON file named sprint_summary.json.
The JSON should contain the raw output from the task tracking system's JSON export.
"""

(workspace / "sprint_brief.md").write_text(sprint_brief)

# Create agkan config
agkan_config = "path: ./.agkan/data.db\n"
(workspace / ".agkan.yml").write_text(agkan_config)
(workspace / ".agkan").mkdir(exist_ok=True)

print("Workspace generated successfully.")
print(f"Files created: {len(source_files) + 2}")
print("Sprint brief available at: /workspace/sprint_brief.md")