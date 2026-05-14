import os
import random

random.seed(42)

base = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "payments/core",
    "payments/adapters",
    "payments/adapters/legacy",
    "payments/adapters/stripe",
    "payments/adapters/internal",
    "payments/models",
    "payments/utils",
    "settlements/batch",
    "settlements/reporting",
    "audit/logs",
    "audit/compliance",
    "config",
    "scripts",
    "tests/unit",
    "tests/integration",
    "infra/k8s",
    "infra/terraform",
    "docs/archive",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── helper to write files ────────────────────────────────────────────────────
def write(path, content):
    full = os.path.join(base, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ════════════════════════════════════════════════════════════════════════════
# CORE PAYMENT ENGINE  (messy, mixed ownership, unclear entry points)
# ════════════════════════════════════════════════════════════════════════════
write("payments/core/engine.py", '''\
# TODO: refactor – originally written by @alice (2019), last touched by @bob (2022)
# WARNING: do not call process_payment() directly from outside this module
import hashlib, time, os

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]
_INTERNAL_FEE_RATE = 0.0025   # undocumented magic number

def _hash_txn(txn_id: str) -> str:
    return hashlib.sha256(txn_id.encode()).hexdigest()[:16]

def process_payment(amount: float, currency: str, txn_id: str):
    """Entry point used by adapter layer. NOT for direct use."""
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency}")
    fee = amount * _INTERNAL_FEE_RATE
    record = {
        "txn_hash": _hash_txn(txn_id),
        "net": amount - fee,
        "currency": currency,
        "ts": time.time(),
    }
    # FIXME: writes to /tmp – not production safe
    with open(f"/tmp/{record[\'txn_hash\']}.json", "w") as fh:
        import json; json.dump(record, fh)
    return record

def _legacy_retry(txn_id, retries=3):
    """Dead code – superseded by adapters/legacy/retry.py"""
    pass
''')

write("payments/core/validator.py", '''\
# Owner: @carol  ETA: originally promised Q1 2023, still incomplete
# Validates payment requests before they reach the engine
import re

CARD_REGEX = re.compile(r"^\\d{16}$")

def validate_card(card_number: str) -> bool:
    return bool(CARD_REGEX.match(card_number))

def validate_amount(amount) -> bool:
    try:
        return float(amount) > 0
    except (TypeError, ValueError):
        return False

# NOTE: validate_currency is missing – engine.py does it inline (tech debt)
''')

write("payments/core/__init__.py", "from .engine import process_payment\n")

# ── adapters ─────────────────────────────────────────────────────────────────
write("payments/adapters/stripe/client.py", '''\
# Owner: @dave
# Wraps Stripe SDK – currently using API v2019-09-09 (outdated, flagged by security)
import os

STRIPE_API_VERSION = "2019-09-09"   # MUST be updated to 2023-10-16

def charge(amount_cents: int, token: str, idempotency_key: str):
    """Primary Stripe entrypoint used by checkout service."""
    # Stub – real impl calls stripe.Charge.create(...)
    return {"status": "ok", "charge_id": f"ch_{idempotency_key[:8]}"}
''')

write("payments/adapters/legacy/retry.py", '''\
# Supersedes engine._legacy_retry()
# Owner: @bob   Last updated: 2021-03-14
import time

MAX_RETRIES = 5
BACKOFF_BASE = 2   # seconds (exponential)

def retry_payment(fn, *args, max_retries=MAX_RETRIES, **kwargs):
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(BACKOFF_BASE ** attempt)
''')

write("payments/adapters/internal/ledger_sync.py", '''\
# Syncs approved transactions to internal ledger service
# Owner: @alice   Status: BROKEN – ledger endpoint changed 2023-11-01
LEDGER_ENDPOINT = "http://ledger-svc.internal/v1/post"  # stale URL

def post_to_ledger(record: dict):
    import urllib.request, json
    data = json.dumps(record).encode()
    # This will fail in prod – endpoint decommissioned
    req = urllib.request.Request(LEDGER_ENDPOINT, data=data,
                                  method="POST",
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.read()
''')

# ── models ────────────────────────────────────────────────────────────────────
write("payments/models/transaction.py", '''\
# Owner: @carol
from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class Transaction:
    txn_id: str
    amount: float
    currency: str
    card_last4: str
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    stripe_charge_id: Optional[str] = None
    ledger_posted: bool = False

    def is_complete(self):
        return self.status == "settled" and self.ledger_posted
''')

# ── settlements ───────────────────────────────────────────────────────────────
write("settlements/batch/runner.py", '''\
# Nightly batch settlement runner
# Owner: @eve   Cron: 02:00 UTC daily
# KNOWN BUG: skips transactions with amount > 50000 (silent truncation)
import glob, json, os

def run_settlement(txn_dir="/tmp"):
    files = glob.glob(os.path.join(txn_dir, "*.json"))
    total = 0.0
    skipped = 0
    for fpath in files:
        with open(fpath) as f:
            rec = json.load(f)
        if rec.get("net", 0) > 50000:   # BUG: should be 500000
            skipped += 1
            continue
        total += rec.get("net", 0)
    return {"total_settled": total, "skipped_large": skipped}
''')

write("settlements/reporting/daily_report.py", '''\
# Owner: @frank   Status: orphaned – no caller found in codebase
def generate_daily_report(date_str: str):
    """Generates CSV report for given date. Currently not called anywhere."""
    return f"date,total\\n{date_str},0.00\\n"
''')

# ── audit ─────────────────────────────────────────────────────────────────────
write("audit/compliance/pci_check.py", '''\
# PCI-DSS compliance checker stub
# Owner: @grace   Required before any prod deployment
# Status: incomplete – card masking not implemented
def check_pci_compliance(transaction_dict: dict) -> dict:
    issues = []
    if "card_number" in transaction_dict:
        issues.append("CRITICAL: raw card_number exposed in record")
    if not transaction_dict.get("txn_hash"):
        issues.append("WARNING: transaction not hashed")
    return {"compliant": len(issues) == 0, "issues": issues}
''')

write("audit/logs/log_config.py", '''\
# Logging is misconfigured – logs to stdout only, no rotation, no structured format
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger("payments")
''')

# ── config ────────────────────────────────────────────────────────────────────
write("config/settings.py", '''\
# Mixed env config – secrets hardcoded (security violation)
DB_HOST = "prod-db.internal"
DB_PASSWORD = "S3cr3tPa$$w0rd!"   # SECURITY VIOLATION
STRIPE_SECRET_KEY = "STRIPE_PLACEHOLDER_NOT_A_REAL_KEY"   # placeholder but pattern is live
REDIS_URL = "redis://localhost:6379"
DEBUG = True   # should be False in prod
MAX_WORKERS = 4
''')

write("config/feature_flags.yaml", '''\
flags:
  new_ledger_sync: false      # blocked on ledger_sync.py fix
  pci_v2_validation: false    # blocked on pci_check.py completion
  stripe_api_v2023: false     # blocked on stripe client update
  high_value_txn_fix: false   # blocked on batch/runner.py bug fix
''')

# ── scripts ───────────────────────────────────────────────────────────────────
write("scripts/migrate_ledger.sh", '''\
#!/usr/bin/env bash
# One-time migration script – run once, then archive
# Owner: @alice
# STATUS: NEVER RUN IN PROD WITHOUT DBA APPROVAL
set -e
echo "Migrating ledger records..."
# psql $DB_HOST -c "INSERT INTO ledger SELECT * FROM legacy_ledger WHERE migrated=false;"
echo "Done. Verify with: SELECT count(*) FROM ledger WHERE migrated=true;"
''')

write("scripts/backfill_hashes.py", '''\
# Backfill txn_hash for records created before 2022-06-01
# Owner: @bob  Status: tested in staging, not yet run in prod
import hashlib

def backfill(records):
    for r in records:
        if not r.get("txn_hash"):
            r["txn_hash"] = hashlib.sha256(r["txn_id"].encode()).hexdigest()[:16]
    return records
''')

# ── tests (sparse / incomplete) ───────────────────────────────────────────────
write("tests/unit/test_validator.py", '''\
from payments.core.validator import validate_card, validate_amount

def test_valid_card():
    assert validate_card("4111111111111111")

def test_invalid_amount():
    assert not validate_amount(-1)
# Missing: tests for validate_currency, process_payment, retry logic
''')

write("tests/integration/test_stripe.py", '''\
# Integration tests require live Stripe sandbox key – skipped in CI
import pytest

@pytest.mark.skip(reason="requires STRIPE_TEST_KEY env var")
def test_stripe_charge():
    pass
''')

# ── infra ─────────────────────────────────────────────────────────────────────
write("infra/k8s/payments-deployment.yaml", '''\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: payments
        image: payments:latest
        env:
        - name: DB_PASSWORD
          value: "S3cr3tPa$$w0rd!"   # hardcoded – must move to Secret
''')

write("infra/terraform/main.tf", '''\
# Terraform for payments infra – last applied 2022-08-10
# Owner: @henry   Status: drift detected, not synced with prod
resource "aws_rds_instance" "payments_db" {
  allocated_storage = 100
  engine            = "postgres"
  instance_class    = "db.t3.micro"   # undersized for current load
}
''')

# ── docs archive (noise) ──────────────────────────────────────────────────────
write("docs/archive/original_design_2018.md", '''\
# Original Payment System Design (2018)
This document is obsolete. The system has been rewritten twice since.
''')

write("docs/archive/api_v1_deprecated.md", '''\
# API v1 – DEPRECATED
All endpoints removed 2021-Q2. Do not use.
''')

# ── orphan/distractor files ───────────────────────────────────────────────────
write("payments/utils/currency_convert.py", '''\
# Utility – not wired into any payment flow yet
RATES = {"EUR": 1.08, "GBP": 1.26}
def to_usd(amount, currency):
    return amount * RATES.get(currency, 1.0)
''')

write("payments/adapters/internal/__init__.py", "")
write("payments/adapters/stripe/__init__.py", "")
write("payments/adapters/legacy/__init__.py", "")

print("Workspace generated successfully.")
print("Files created:")
for root, _, files in os.walk(base):
    for fname in files:
        rel = os.path.relpath(os.path.join(root, fname), base)
        print(f"  {rel}")