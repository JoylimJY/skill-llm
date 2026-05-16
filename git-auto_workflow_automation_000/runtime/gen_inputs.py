import os
import subprocess
import random
import stat

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "src/payments",
    "src/payments/auth",
    "src/payments/processing",
    "src/payments/reporting",
    "src/users",
    "src/users/profile",
    "src/notifications",
    "src/notifications/email",
    "config",
    "tests/unit/payments",
    "tests/unit/users",
    "tests/integration",
    "docs/api",
    "docs/internal",
    "scripts",
    "infra/k8s",
    "infra/terraform",
    ".github/workflows",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── helper to write files ────────────────────────────────────────────────────
def write(path, content):
    full = os.path.join(WORKSPACE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ── initial committed files (will become "baseline") ────────────────────────
write("src/payments/auth/token_validator.py", '''\
"""Token validation for payment auth."""

def validate_token(token: str) -> bool:
    """Validate bearer token."""
    if not token or len(token) < 16:
        return False
    return token.startswith("Bearer ")
''')

write("src/payments/auth/session_manager.py", '''\
"""Session management for authenticated payment flows."""

SESSIONS = {}

def create_session(user_id: str, token: str) -> str:
    import uuid
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {"user_id": user_id, "token": token, "active": True}
    return sid

def invalidate_session(sid: str) -> bool:
    if sid in SESSIONS:
        SESSIONS[sid]["active"] = False
        return True
    return False
''')

write("src/payments/processing/charge.py", '''\
"""Core charge processing module."""

def process_charge(amount: float, currency: str, token: str) -> dict:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {"status": "pending", "amount": amount, "currency": currency}
''')

write("src/payments/processing/refund.py", '''\
"""Refund processing logic."""

def process_refund(charge_id: str, amount: float) -> dict:
    return {"status": "refund_pending", "charge_id": charge_id, "amount": amount}
''')

write("src/payments/reporting/ledger.py", '''\
"""Ledger reporting utilities."""

def get_ledger_entries(start_date: str, end_date: str) -> list:
    return []
''')

write("src/users/profile/kyc.py", '''\
"""KYC verification module."""

def verify_kyc(user_id: str, documents: list) -> bool:
    return len(documents) >= 2
''')

write("src/notifications/email/sender.py", '''\
"""Email notification sender."""

def send_email(to: str, subject: str, body: str) -> bool:
    print(f"Email to {to}: {subject}")
    return True
''')

write("config/app.yaml", '''\
app:
  name: fintech-payment-service
  version: 2.1.0
  environment: staging
database:
  host: db.internal
  port: 5432
  name: payments_db
''')

write("config/feature_flags.json", '''\
{
  "enable_3ds_auth": true,
  "enable_crypto_payments": false,
  "max_retry_attempts": 3
}
''')

write("tests/unit/payments/test_charge.py", '''\
"""Unit tests for charge processing."""
import pytest

def test_positive_charge():
    assert True

def test_negative_charge_raises():
    assert True
''')

write("tests/unit/users/test_kyc.py", '''\
"""Unit tests for KYC."""
def test_kyc_with_documents():
    assert True
''')

write("tests/integration/test_payment_flow.py", '''\
"""Integration tests for end-to-end payment flow."""
def test_full_payment_cycle():
    pass
''')

write("docs/api/openapi.yaml", '''\
openapi: 3.0.0
info:
  title: Payment API
  version: 2.1.0
paths:
  /charge:
    post:
      summary: Process a charge
''')

write("docs/internal/architecture.md", '''\
# Architecture Notes
Payment service uses microservice architecture with JWT auth.
''')

write("scripts/deploy.sh", '''\
#!/bin/bash
echo "Deploying payment service..."
kubectl apply -f infra/k8s/
''')

write("infra/k8s/deployment.yaml", '''\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 3
''')

write(".github/workflows/ci.yaml", '''\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python3 -m pytest tests/
''')

# ── Initialise git repo and make first commit ────────────────────────────────
os.chdir(WORKSPACE)
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "chore: initial project scaffold"], check=True)

# ── NOW introduce messy working-tree changes ─────────────────────────────────

# 1. SECURITY BUG FIX – these are the files the agent MUST commit
write("src/payments/auth/token_validator.py", '''\
"""Token validation for payment auth — PATCHED CVE-2024-0042."""

import hashlib
import hmac

SECRET_KEY = b"payment-service-secret-v2"

def validate_token(token: str) -> bool:
    """Validate bearer token with HMAC verification."""
    if not token or len(token) < 32:
        return False
    if not token.startswith("Bearer "):
        return False
    raw = token[len("Bearer "):]
    parts = raw.split(".")
    if len(parts) != 2:
        return False
    payload, sig = parts
    expected = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)

def revoke_token(token: str) -> bool:
    """Add token to revocation list."""
    # TODO: implement Redis-backed revocation
    return True
''')

write("src/payments/auth/session_manager.py", '''\
"""Session management — hardened against session fixation."""

import uuid
import time

SESSIONS: dict = {}
SESSION_TTL = 3600  # 1 hour

def create_session(user_id: str, token: str) -> str:
    """Create a new session, invalidating any existing one for the user."""
    # Invalidate old sessions for this user (prevent session fixation)
    for sid, data in list(SESSIONS.items()):
        if data["user_id"] == user_id:
            del SESSIONS[sid]
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "user_id": user_id,
        "token": token,
        "active": True,
        "created_at": time.time(),
    }
    return sid

def invalidate_session(sid: str) -> bool:
    if sid in SESSIONS:
        del SESSIONS[sid]
        return True
    return False

def is_session_valid(sid: str) -> bool:
    if sid not in SESSIONS:
        return False
    session = SESSIONS[sid]
    if not session["active"]:
        return False
    if time.time() - session["created_at"] > SESSION_TTL:
        del SESSIONS[sid]
        return False
    return True
''')

# 2. UNRELATED config change – should NOT be committed in this round
write("config/app.yaml", '''\
app:
  name: fintech-payment-service
  version: 2.2.0
  environment: production
database:
  host: db-prod.internal
  port: 5432
  name: payments_db
  pool_size: 20
''')

# 3. UNRELATED new feature file – should NOT be committed
write("src/payments/processing/fraud_detector.py", '''\
"""Fraud detection module — WIP, not ready for release."""

def score_transaction(tx: dict) -> float:
    """Returns a fraud risk score between 0 and 1."""
    # Placeholder — ML model integration pending
    return 0.0
''')

# 4. UNRELATED test update – should NOT be committed
write("tests/unit/payments/test_charge.py", '''\
"""Unit tests for charge processing — updated."""
import pytest

def test_positive_charge():
    from src.payments.processing.charge import process_charge
    result = process_charge(100.0, "USD", "tok_test")
    assert result["status"] == "pending"

def test_negative_charge_raises():
    from src.payments.processing.charge import process_charge
    with pytest.raises(ValueError):
        process_charge(-10.0, "USD", "tok_test")
''')

# 5. New untracked infrastructure file – should NOT be committed
write("infra/terraform/main.tf", '''\
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "payment_logs" {
  bucket = "fintech-payment-logs-prod"
}
''')

# 6. Another unrelated docs update
write("docs/api/openapi.yaml", '''\
openapi: 3.0.0
info:
  title: Payment API
  version: 2.2.0
paths:
  /charge:
    post:
      summary: Process a charge
  /refund:
    post:
      summary: Process a refund
  /fraud/score:
    post:
      summary: Get fraud score for a transaction
''')

print("Workspace generation complete.")
print("Files with security fixes (must be committed):")
print("  src/payments/auth/token_validator.py")
print("  src/payments/auth/session_manager.py")
print("Files modified but must NOT be committed:")
print("  config/app.yaml")
print("  tests/unit/payments/test_charge.py")
print("  docs/api/openapi.yaml")
print("New untracked files that must NOT be committed:")
print("  src/payments/processing/fraud_detector.py")
print("  infra/terraform/main.tf")