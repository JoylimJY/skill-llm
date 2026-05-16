#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path("/workspace")

def create_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# ── Initialize git repo ──────────────────────────────────────────────────────
os.chdir(WORKSPACE)
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "config", "user.email", "dev@fintech-example.local"], check=True)
subprocess.run(["git", "config", "user.name", "Dev Bot"], check=True)

# ── Distractor files: realistic fintech Python codebase ──────────────────────

create_file(WORKSPACE / "src" / "__init__.py", "# Transaction Processing Service\n")

create_file(WORKSPACE / "src" / "models" / "transaction.py", """\
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class TransactionType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    REFUND = "refund"


@dataclass
class Transaction:
    id: str
    amount: Decimal
    currency: str
    status: TransactionStatus
    tx_type: TransactionType
    merchant_id: str
    user_id: str
    created_at: datetime
    metadata: dict = None

    def is_high_value(self) -> bool:
        return self.amount > Decimal("10000.00")
""")

create_file(WORKSPACE / "src" / "models" / "user.py", """\
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    email: str
    tier: str  # "basic", "premium", "enterprise"
    kyc_verified: bool
    created_at: datetime
    risk_score: float = 0.0
""")

create_file(WORKSPACE / "src" / "models" / "__init__.py", 
    "from .transaction import Transaction, TransactionStatus, TransactionType\nfrom .user import User\n")

create_file(WORKSPACE / "src" / "services" / "processor.py", """\
import logging
from decimal import Decimal
from .ledger import LedgerService
from ..models.transaction import Transaction, TransactionStatus

logger = logging.getLogger(__name__)


class TransactionProcessor:
    def __init__(self, ledger: LedgerService):
        self.ledger = ledger

    def process(self, tx: Transaction) -> bool:
        if tx.amount <= Decimal("0"):
            logger.warning(f"Rejected zero/negative transaction {tx.id}")
            return False
        try:
            self.ledger.record(tx)
            tx.status = TransactionStatus.COMPLETED
            return True
        except Exception as e:
            logger.error(f"Processing failed for {tx.id}: {e}")
            tx.status = TransactionStatus.FAILED
            return False
""")

create_file(WORKSPACE / "src" / "services" / "ledger.py", """\
from ..models.transaction import Transaction


class LedgerService:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def record(self, tx: Transaction) -> None:
        # Writes transaction to the append-only ledger table
        pass

    def get_user_history(self, user_id: str, limit: int = 100):
        # Returns last N transactions for user
        pass

    def get_merchant_volume(self, merchant_id: str, window_hours: int = 24):
        # Returns total volume for merchant in time window
        pass
""")

create_file(WORKSPACE / "src" / "services" / "__init__.py", 
    "from .processor import TransactionProcessor\nfrom .ledger import LedgerService\n")

create_file(WORKSPACE / "src" / "api" / "routes.py", """\
from flask import Blueprint, request, jsonify
from ..services.processor import TransactionProcessor

bp = Blueprint("transactions", __name__, url_prefix="/api/v1/transactions")


@bp.route("/submit", methods=["POST"])
def submit_transaction():
    data = request.get_json()
    # TODO: validate, build Transaction object, call processor
    return jsonify({"status": "accepted"}), 202


@bp.route("/status/<tx_id>", methods=["GET"])
def get_status(tx_id: str):
    # TODO: look up transaction by ID
    return jsonify({"tx_id": tx_id, "status": "unknown"}), 200
""")

create_file(WORKSPACE / "src" / "api" / "__init__.py", "")

create_file(WORKSPACE / "src" / "config.py", """\
import os

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fintech_dev")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
MAX_TX_AMOUNT = 500_000  # cents
RATE_LIMIT_WINDOW = 60   # seconds
RATE_LIMIT_MAX_CALLS = 200
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
""")

create_file(WORKSPACE / "tests" / "test_processor.py", """\
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from src.services.processor import TransactionProcessor
from src.models.transaction import Transaction, TransactionStatus, TransactionType
from datetime import datetime


def make_tx(amount="100.00"):
    return Transaction(
        id="tx-001", amount=Decimal(amount), currency="USD",
        status=TransactionStatus.PENDING, tx_type=TransactionType.DEBIT,
        merchant_id="m-001", user_id="u-001", created_at=datetime.utcnow()
    )


def test_process_valid():
    ledger = MagicMock()
    proc = TransactionProcessor(ledger)
    tx = make_tx()
    assert proc.process(tx) is True
    assert tx.status == TransactionStatus.COMPLETED


def test_process_zero_amount():
    ledger = MagicMock()
    proc = TransactionProcessor(ledger)
    tx = make_tx("0.00")
    assert proc.process(tx) is False
""")

create_file(WORKSPACE / "tests" / "test_ledger.py", """\
import pytest
from src.services.ledger import LedgerService


def test_ledger_instantiation():
    svc = LedgerService("postgresql://localhost/test")
    assert svc.db_url == "postgresql://localhost/test"
""")

create_file(WORKSPACE / "tests" / "__init__.py", "")

create_file(WORKSPACE / "requirements.txt", """\
flask>=2.3.0
psycopg2-binary>=2.9.0
redis>=4.6.0
pydantic>=2.0.0
pytest>=7.4.0
pytest-cov>=4.1.0
python-dateutil>=2.8.0
""")

create_file(WORKSPACE / "pyproject.toml", """\
[project]
name = "fintech-tx-service"
version = "0.4.1"
description = "Transaction Processing Microservice"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"
""")

create_file(WORKSPACE / ".gitignore", """\
__pycache__/
*.py[cod]
.env
.venv/
dist/
*.egg-info/
.pytest_cache/
.coverage
""")

create_file(WORKSPACE / "CHANGELOG.md", """\
# Changelog

## [Unreleased]
- Investigating anomaly detection approaches

## [0.4.1] - 2024-11-15
- Fixed rate limiter off-by-one error
- Improved ledger error logging

## [0.4.0] - 2024-10-30
- Added refund transaction type
- Merchant volume aggregation endpoint

## [0.3.0] - 2024-09-12
- KYC verification integration
- Premium tier rate limits
""")

create_file(WORKSPACE / "docs" / "architecture.md", """\
# Architecture Overview

The service follows a layered architecture:

- **API Layer** (`src/api/`): Flask blueprints, request validation
- **Service Layer** (`src/services/`): Business logic, orchestration
- **Model Layer** (`src/models/`): Domain entities
- **Infrastructure**: PostgreSQL ledger, Redis for rate limiting

## Deployment

Deployed as a Docker container behind an nginx reverse proxy.
Single-region, vertical scaling currently. Multi-region is on the roadmap.
""")

create_file(WORKSPACE / "docs" / "adr" / "001-use-postgresql.md", """\
# ADR 001: Use PostgreSQL for Ledger Storage

## Status: Accepted

## Context
We need an append-only, ACID-compliant store for transaction records.

## Decision
Use PostgreSQL with a write-once trigger enforced at the DB level.

## Consequences
- Strong consistency guarantees
- Operational complexity of managing Postgres
""")

create_file(WORKSPACE / "docs" / "adr" / "002-redis-rate-limiting.md", """\
# ADR 002: Redis for Rate Limiting

## Status: Accepted

## Context
API endpoints need per-user and per-merchant rate limiting.

## Decision
Use Redis sliding window counters (ZADD/ZCOUNT pattern).

## Consequences
- Fast, low-latency rate checks
- Redis becomes a soft dependency (graceful degradation needed)
""")

# Messy feature notes — contradictory, incomplete, real-world chaos
create_file(WORKSPACE / "docs" / "notes" / "anomaly-ideas.txt", """\
ROUGH NOTES - anomaly detection brainstorm (NOT approved)
===========================================================

Idea A: rule-based
  - flag txns > 3x user's 30-day avg
  - flag velocity: >5 txns in 10 min from same user
  - flag cross-border if user has never done it before
  - CONS: lots of false positives, hard to tune thresholds
  - PROS: explainable, fast to ship

Idea B: ML scoring
  - train isolation forest on historical txns
  - real-time inference via a sidecar service
  - store anomaly scores in Postgres
  - CONS: needs labeled data we don't have yet, infra overhead
  - PROS: catches subtle patterns

Idea C: hybrid
  - rules as fast pre-filter, ML for borderline cases
  - CONS: complex to maintain both systems
  - PROS: best of both worlds?

Questions:
- Do we block flagged txns or just alert?
- Who reviews alerts? Ops team? automated?
- SLA for detection latency? real-time vs batch?
- Do we need explainability for regulatory compliance?
- What's the false-positive tolerance?

Possible data signals:
  - transaction amount vs user historical avg
  - txn velocity (count per time window)
  - geo/IP mismatch
  - merchant category mismatch
  - time-of-day deviation
  - device fingerprint (not yet collected)

TODO: get product sign-off before touching code
""")

create_file(WORKSPACE / "docs" / "notes" / "standup-2024-11-20.txt", """\
Standup notes 2024-11-20
------------------------
- Maria: finished ledger migration, needs review
- Dan: blocked on anomaly detection - no design yet, not starting until we have one
- Priya: working on merchant dashboard (unrelated)
- Action: someone needs to write the anomaly detection design doc before sprint end
""")

create_file(WORKSPACE / "scripts" / "migrate.sh", """\
#!/bin/bash
# Run Alembic migrations
set -e
alembic upgrade head
echo "Migrations complete."
""")

create_file(WORKSPACE / "scripts" / "seed_dev.py", """\
#!/usr/bin/env python3
\"\"\"Seed development database with test transactions.\"\"\"
import random
import string
from decimal import Decimal
from datetime import datetime, timedelta

NUM_USERS = 50
NUM_TXS_PER_USER = 200

print(f"Seeding {NUM_USERS} users with {NUM_TXS_PER_USER} transactions each...")
# (actual DB calls omitted for brevity)
print("Done.")
""")

# ── Initial git commit with the existing codebase ───────────────────────────
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "chore: initial codebase snapshot v0.4.1"], check=True)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")