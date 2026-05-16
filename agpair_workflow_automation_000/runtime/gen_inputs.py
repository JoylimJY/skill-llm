import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Project structure: payments microservice ---
dirs = [
    "payments_service/src/core",
    "payments_service/src/models",
    "payments_service/src/handlers",
    "payments_service/src/utils",
    "payments_service/tests/unit",
    "payments_service/tests/integration",
    "payments_service/config",
    "payments_service/migrations",
    "payments_service/.github/workflows",
    "payments_service/docs",
    "infra/terraform",
    "infra/docker",
    "scripts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Core payment processor (the file to be refactored) ---
(workspace / "payments_service/src/core/processor.py").write_text('''\
# Legacy payment processor - needs refactoring
import time, hashlib, random

class PaymentProcessor:
    def __init__(self):
        self.db = None  # TODO: inject
        self.cache = {}
    
    def process(self, amt, acct, method):
        # bad: no validation, no idempotency key
        tid = hashlib.md5(str(time.time()).encode()).hexdigest()
        if method == "card":
            r = self._charge_card(acct, amt)
        elif method == "ach":
            r = self._ach_transfer(acct, amt)
        else:
            r = False
        self.cache[tid] = r
        return tid, r

    def _charge_card(self, acct, amt):
        # simulate
        return random.random() > 0.1

    def _ach_transfer(self, acct, amt):
        return random.random() > 0.05
''')

(workspace / "payments_service/src/core/__init__.py").write_text("")
(workspace / "payments_service/src/models/__init__.py").write_text("")
(workspace / "payments_service/src/handlers/__init__.py").write_text("")
(workspace / "payments_service/src/utils/__init__.py").write_text("")

(workspace / "payments_service/src/models/transaction.py").write_text('''\
from dataclasses import dataclass, field
from typing import Optional
import uuid

@dataclass
class Transaction:
    amount: float
    account_id: str
    method: str
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
    idempotency_key: Optional[str] = None
''')

(workspace / "payments_service/src/handlers/webhook.py").write_text('''\
import json

def handle_stripe_webhook(payload: bytes, sig: str) -> dict:
    # TODO: verify signature
    data = json.loads(payload)
    return {"status": "received", "event": data.get("type")}
''')

(workspace / "payments_service/src/utils/retry.py").write_text('''\
import time
import functools

def with_retry(max_attempts=3, backoff=1.0):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(backoff * (2 ** attempt))
        return wrapper
    return decorator
''')

(workspace / "payments_service/src/utils/validation.py").write_text('''\
import re

CARD_PATTERN = re.compile(r"^\d{16}$")
ACH_PATTERN = re.compile(r"^\d{9,17}$")

def validate_account(acct: str, method: str) -> bool:
    if method == "card":
        return bool(CARD_PATTERN.match(acct))
    elif method == "ach":
        return bool(ACH_PATTERN.match(acct))
    return False
''')

(workspace / "payments_service/tests/unit/test_processor.py").write_text('''\
import pytest
from payments_service.src.core.processor import PaymentProcessor

def test_process_card():
    p = PaymentProcessor()
    tid, ok = p.process(100.0, "4111111111111111", "card")
    assert isinstance(tid, str)

def test_process_unknown_method():
    p = PaymentProcessor()
    tid, ok = p.process(50.0, "anything", "bitcoin")
    assert ok is False
''')

(workspace / "payments_service/tests/integration/test_e2e.py").write_text('''\
# Integration tests - require DB connection
# Skipped in CI without DATABASE_URL
import pytest

@pytest.mark.skip(reason="requires live DB")
def test_full_payment_flow():
    pass
''')

(workspace / "payments_service/config/settings.py").write_text('''\
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/payments_dev")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY", "")
MAX_RETRY_ATTEMPTS = 3
PAYMENT_TIMEOUT_SECONDS = 30
''')

(workspace / "payments_service/config/logging.yaml").write_text('''\
version: 1
formatters:
  standard:
    format: "%(asctime)s %(levelname)s %(name)s %(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
root:
  level: INFO
  handlers: [console]
''')

(workspace / "payments_service/migrations/001_initial.sql").write_text('''\
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY,
    account_id VARCHAR(64) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    method VARCHAR(32) NOT NULL,
    status VARCHAR(32) DEFAULT \'pending\',
    created_at TIMESTAMPTZ DEFAULT now()
);
''')

(workspace / "payments_service/migrations/002_idempotency.sql").write_text('''\
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128) UNIQUE;
''')

(workspace / "payments_service/.github/workflows/ci.yml").write_text('''\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest payments_service/tests/unit/
''')

(workspace / "payments_service/docs/architecture.md").write_text('''\
# Payments Service Architecture

## Components
- **Processor**: Core payment execution logic
- **Webhook Handler**: Stripe event ingestion
- **Transaction Model**: Domain object
- **Retry Utility**: Exponential backoff for transient failures

## Refactoring Goals (Q3)
- Add idempotency key support to PaymentProcessor
- Inject database dependency
- Add input validation before processing
- Replace md5 transaction ID with UUID
''')

(workspace / "payments_service/docs/runbook.md").write_text('''\
# On-Call Runbook

## Payment Failures
1. Check Stripe dashboard for gateway errors
2. Verify DATABASE_URL is reachable
3. Review logs: `kubectl logs deploy/payments-service --tail=100`

## Rollback
```bash
kubectl rollout undo deploy/payments-service
```
''')

(workspace / "infra/terraform/main.tf").write_text('''\
resource "aws_rds_instance" "payments" {
  identifier        = "payments-db"
  engine            = "postgres"
  engine_version    = "14.7"
  instance_class    = "db.t3.medium"
  allocated_storage = 100
}
''')

(workspace / "infra/docker/Dockerfile.payments").write_text('''\
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "payments_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
''')

(workspace / "scripts/seed_db.py").write_text('''\
#!/usr/bin/env python3
"""Seed development database with test transactions."""
import uuid, random, psycopg2

def seed(conn_str, n=100):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    for _ in range(n):
        cur.execute(
            "INSERT INTO transactions (id, account_id, amount, method) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), f"acct_{random.randint(1000,9999)}", round(random.uniform(1, 10000), 2), random.choice(["card","ach"]))
        )
    conn.commit()

if __name__ == "__main__":
    seed("postgresql://localhost/payments_dev")
''')

(workspace / "scripts/smoke_test.sh").write_text('''\
#!/bin/bash
set -e
echo "Running smoke tests..."
curl -sf http://localhost:8080/health || exit 1
echo "Smoke tests passed."
''')

# requirements.txt
(workspace / "requirements.txt").write_text('''\
fastapi>=0.100.0
uvicorn>=0.23.0
psycopg2-binary>=2.9.0
redis>=4.6.0
stripe>=5.0.0
pydantic>=2.0.0
''')

# Task description for the agent: the "ticket"
(workspace / "task_ticket.txt").write_text('''\
REFACTORING TICKET: PAY-2847
Title: Refactor PaymentProcessor for idempotency and dependency injection

Description:
The PaymentProcessor in payments_service/src/core/processor.py has several
critical issues identified in our Q3 architecture review:

1. Transaction IDs use MD5(timestamp) — collision-prone; replace with UUID4
2. No idempotency key support — duplicate charges possible under retry storms
3. Database dependency is not injected — impossible to unit test
4. No input validation — accepts malformed account numbers

Acceptance Criteria:
- PaymentProcessor.__init__ accepts a `db` parameter (injected)
- process() accepts an optional `idempotency_key: str` parameter  
- Transaction IDs generated with uuid.uuid4()
- validate_account() from utils.validation is called before processing
- All existing unit tests must still pass

Assigned to: Antigravity (automated refactoring backend)
Repo: /workspace/payments_service
Priority: HIGH
''')

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")