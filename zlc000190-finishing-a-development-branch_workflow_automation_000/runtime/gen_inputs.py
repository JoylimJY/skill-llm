#!/usr/bin/env python3
"""
Generate the sandbox workspace for the finishing-a-development-branch skill evaluation.
Creates a realistic fintech microservice repo with a feature branch in a git worktree.
"""

import os
import subprocess
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── 1. Create the main git repository ────────────────────────────────────────
REPO = WORKSPACE / "payments-service"
REPO.mkdir()

def git(cmd, cwd=None):
    cwd = cwd or REPO
    result = subprocess.run(
        ["git"] + cmd,
        cwd=str(cwd),
        capture_output=True, text=True
    )
    if result.returncode != 0 and "already exists" not in result.stderr:
        print(f"git {cmd} stderr: {result.stderr}")
    return result.stdout.strip()

git(["init"])
git(["checkout", "-b", "main"])

# ── 2. Create the base project structure (distractor files) ───────────────────

# Core service files
(REPO / "pyproject.toml").write_text("""\
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "payments-service"
version = "2.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100",
    "pydantic>=2.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
""")

(REPO / "Makefile").write_text("""\
.PHONY: test lint build

test:
\tpytest tests/ -v

lint:
\tflake8 src/

build:
\tdocker build -t payments-service .
""")

(REPO / "Dockerfile").write_text("""\
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
""")

(REPO / ".gitignore").write_text("""\
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.pytest_cache/
""")

# Source package
src = REPO / "src"
src.mkdir()
(src / "__init__.py").write_text('__version__ = "2.1.0"\n')

(src / "main.py").write_text("""\
\"\"\"Payments Service - Main application entry point.\"\"\"
from fastapi import FastAPI
from .processor import PaymentProcessor
from .models import PaymentRequest

app = FastAPI(title="Payments Service", version="2.1.0")
processor = PaymentProcessor()


@app.post("/payments/process")
async def process_payment(request: PaymentRequest):
    result = processor.process(request)
    return result


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.1.0"}
""")

(src / "models.py").write_text("""\
\"\"\"Domain models for payment processing.\"\"\"
from pydantic import BaseModel, field_validator
from decimal import Decimal
from typing import Optional


class PaymentRequest(BaseModel):
    transaction_id: str
    amount: Decimal
    currency: str
    merchant_id: str
    customer_id: str
    metadata: Optional[dict] = None

    @field_validator("currency")
    @classmethod
    def currency_must_be_iso(cls, v):
        if len(v) != 3 or not v.isupper():
            raise ValueError("Currency must be 3-letter ISO code")
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
""")

(src / "processor.py").write_text("""\
\"\"\"Core payment processing logic.\"\"\"
from decimal import Decimal


class PaymentProcessor:
    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "AUD"}
    MAX_TRANSACTION_AMOUNT = Decimal("50000.00")

    def process(self, request):
        if request.currency not in self.SUPPORTED_CURRENCIES:
            return {"status": "rejected", "reason": "unsupported_currency"}
        if request.amount > self.MAX_TRANSACTION_AMOUNT:
            return {"status": "rejected", "reason": "exceeds_limit"}
        return {
            "status": "approved",
            "transaction_id": request.transaction_id,
            "amount": str(request.amount),
            "currency": request.currency,
        }
""")

(src / "config.py").write_text("""\
\"\"\"Service configuration.\"\"\"
import os


class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/payments")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
""")

(src / "exceptions.py").write_text("""\
\"\"\"Custom exceptions for payments service.\"\"\"


class PaymentError(Exception):
    \"\"\"Base exception for payment errors.\"\"\"


class ValidationError(PaymentError):
    \"\"\"Raised when payment validation fails.\"\"\"


class ProcessingError(PaymentError):
    \"\"\"Raised when payment processing fails.\"\"\"


class CurrencyNotSupportedError(PaymentError):
    \"\"\"Raised when currency is not supported.\"\"\"
    def __init__(self, currency: str):
        self.currency = currency
        super().__init__(f"Currency {currency!r} is not supported")
""")

# Tests directory (on main branch — baseline tests)
tests = REPO / "tests"
tests.mkdir()
(tests / "__init__.py").write_text("")

(tests / "conftest.py").write_text("""\
\"\"\"Shared test fixtures for payments service.\"\"\"
import pytest
from decimal import Decimal
from src.models import PaymentRequest
from src.processor import PaymentProcessor


@pytest.fixture
def processor():
    return PaymentProcessor()


@pytest.fixture
def valid_payment():
    return PaymentRequest(
        transaction_id="TXN-001",
        amount=Decimal("99.99"),
        currency="USD",
        merchant_id="MERCH-001",
        customer_id="CUST-001",
    )
""")

(tests / "test_processor.py").write_text("""\
\"\"\"Tests for PaymentProcessor.\"\"\"
from decimal import Decimal
import pytest
from src.models import PaymentRequest
from src.processor import PaymentProcessor


def test_approve_valid_payment(processor, valid_payment):
    result = processor.process(valid_payment)
    assert result["status"] == "approved"
    assert result["transaction_id"] == "TXN-001"


def test_reject_unsupported_currency(processor):
    req = PaymentRequest(
        transaction_id="TXN-002",
        amount=Decimal("50.00"),
        currency="CNY",
        merchant_id="MERCH-001",
        customer_id="CUST-002",
    )
    result = processor.process(req)
    assert result["status"] == "rejected"
    assert result["reason"] == "unsupported_currency"


def test_reject_exceeds_limit(processor):
    req = PaymentRequest(
        transaction_id="TXN-003",
        amount=Decimal("100000.00"),
        currency="USD",
        merchant_id="MERCH-001",
        customer_id="CUST-003",
    )
    result = processor.process(req)
    assert result["status"] == "rejected"
    assert result["reason"] == "exceeds_limit"


def test_currency_validation():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PaymentRequest(
            transaction_id="TXN-004",
            amount=Decimal("10.00"),
            currency="usd",  # lowercase - invalid
            merchant_id="MERCH-001",
            customer_id="CUST-004",
        )
""")

(tests / "test_models.py").write_text("""\
\"\"\"Tests for domain models.\"\"\"
from decimal import Decimal
import pytest
from pydantic import ValidationError
from src.models import PaymentRequest


def test_valid_payment_request():
    req = PaymentRequest(
        transaction_id="TXN-100",
        amount=Decimal("250.00"),
        currency="EUR",
        merchant_id="MERCH-EU-001",
        customer_id="CUST-EU-001",
    )
    assert req.amount == Decimal("250.00")
    assert req.currency == "EUR"


def test_negative_amount_rejected():
    with pytest.raises(ValidationError):
        PaymentRequest(
            transaction_id="TXN-101",
            amount=Decimal("-1.00"),
            currency="USD",
            merchant_id="MERCH-001",
            customer_id="CUST-001",
        )


def test_zero_amount_rejected():
    with pytest.raises(ValidationError):
        PaymentRequest(
            transaction_id="TXN-102",
            amount=Decimal("0"),
            currency="USD",
            merchant_id="MERCH-001",
            customer_id="CUST-001",
        )


def test_optional_metadata():
    req = PaymentRequest(
        transaction_id="TXN-103",
        amount=Decimal("10.00"),
        currency="GBP",
        merchant_id="MERCH-GB-001",
        customer_id="CUST-GB-001",
        metadata={"order_ref": "ORD-555", "channel": "web"},
    )
    assert req.metadata["channel"] == "web"
""")

# Additional distractor files
(REPO / "CHANGELOG.md").write_text("""\
# Changelog

## [2.1.0] - 2024-01-15
### Added
- Multi-currency support
- Transaction limit validation

## [2.0.0] - 2023-11-01
### Breaking Changes
- New API schema for payment requests
""")

(REPO / ".env.example").write_text("""\
DATABASE_URL=postgresql://localhost/payments_dev
REDIS_URL=redis://localhost:6379
MAX_RETRY_ATTEMPTS=3
LOG_LEVEL=DEBUG
ENVIRONMENT=development
""")

docs = REPO / "docs"
docs.mkdir()
(docs / "architecture.md").write_text("""\
# Architecture Overview

## Components
- **API Layer**: FastAPI-based REST endpoints
- **Processor**: Core business logic
- **Models**: Pydantic data validation

## Deployment
Deployed as Docker containers on Kubernetes.
""")

(docs / "api-reference.md").write_text("""\
# API Reference

## POST /payments/process
Process a payment transaction.

### Request Body
```json
{
  "transaction_id": "TXN-001",
  "amount": "99.99",
  "currency": "USD",
  "merchant_id": "MERCH-001",
  "customer_id": "CUST-001"
}
```
""")

scripts = REPO / "scripts"
scripts.mkdir()
(scripts / "migrate.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Database migration helper.\"\"\"
import sys

def run_migrations():
    print("Running migrations...")
    # placeholder
    return 0

if __name__ == "__main__":
    sys.exit(run_migrations())
""")

(scripts / "seed_data.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Seed test data into development database.\"\"\"

SEED_MERCHANTS = [
    {"id": "MERCH-001", "name": "Acme Corp"},
    {"id": "MERCH-002", "name": "Globex Ltd"},
]

def seed():
    for m in SEED_MERCHANTS:
        print(f"Seeding merchant: {m['name']}")

if __name__ == "__main__":
    seed()
""")

ci = REPO / ".github" / "workflows"
ci.mkdir(parents=True)
(ci / "test.yml").write_text("""\
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pytest pydantic fastapi
      - run: pytest tests/ -v
""")

# ── 3. Initial commit on main ─────────────────────────────────────────────────
git(["add", "."])
git(["commit", "-m", "feat: initial payments service implementation"])

# ── 4. Create the feature branch and its worktree ────────────────────────────
FEATURE_BRANCH = "feature/transaction-validator"
WORKTREE_PATH = WORKSPACE / "transaction-validator-worktree"

git(["branch", FEATURE_BRANCH])
subprocess.run(
    ["git", "worktree", "add", str(WORKTREE_PATH), FEATURE_BRANCH],
    cwd=str(REPO),
    check=True
)

# ── 5. Add feature work in the worktree ──────────────────────────────────────

# New validator module
(WORKTREE_PATH / "src" / "validator.py").write_text("""\
\"\"\"Transaction validation with fraud detection heuristics.\"\"\"
from decimal import Decimal
from .models import PaymentRequest


class TransactionValidator:
    \"\"\"Validates payment transactions before processing.\"\"\"

    HIGH_RISK_MERCHANTS = {"MERCH-RISK-001", "MERCH-RISK-002"}
    VELOCITY_LIMIT = 5  # max transactions per minute per customer

    def validate(self, request: PaymentRequest) -> dict:
        \"\"\"Returns validation result with risk score.\"\"\"
        issues = []
        risk_score = 0

        if request.merchant_id in self.HIGH_RISK_MERCHANTS:
            issues.append("high_risk_merchant")
            risk_score += 40

        if request.amount > Decimal("10000.00"):
            issues.append("large_transaction")
            risk_score += 25

        if request.metadata and request.metadata.get("ip_country") != \
                request.metadata.get("card_country"):
            issues.append("geo_mismatch")
            risk_score += 35

        return {
            "valid": len(issues) == 0 or risk_score < 50,
            "risk_score": risk_score,
            "issues": issues,
        }
""")

# New tests for the validator
(WORKTREE_PATH / "tests" / "test_validator.py").write_text("""\
\"\"\"Tests for TransactionValidator.\"\"\"
from decimal import Decimal
import pytest
from src.models import PaymentRequest
from src.validator import TransactionValidator


@pytest.fixture
def validator():
    return TransactionValidator()


def test_clean_transaction_passes(validator):
    req = PaymentRequest(
        transaction_id="TXN-V-001",
        amount=Decimal("150.00"),
        currency="USD",
        merchant_id="MERCH-001",
        customer_id="CUST-001",
    )
    result = validator.validate(req)
    assert result["valid"] is True
    assert result["risk_score"] == 0


def test_high_risk_merchant_flagged(validator):
    req = PaymentRequest(
        transaction_id="TXN-V-002",
        amount=Decimal("50.00"),
        currency="USD",
        merchant_id="MERCH-RISK-001",
        customer_id="CUST-001",
    )
    result = validator.validate(req)
    assert "high_risk_merchant" in result["issues"]
    assert result["risk_score"] == 40


def test_large_transaction_flagged(validator):
    req = PaymentRequest(
        transaction_id="TXN-V-003",
        amount=Decimal("15000.00"),
        currency="USD",
        merchant_id="MERCH-001",
        customer_id="CUST-001",
    )
    result = validator.validate(req)
    assert "large_transaction" in result["issues"]
    assert result["risk_score"] == 25
    assert result["valid"] is True  # below 50 threshold


def test_geo_mismatch_with_high_risk_fails(validator):
    req = PaymentRequest(
        transaction_id="TXN-V-004",
        amount=Decimal("5000.00"),
        currency="USD",
        merchant_id="MERCH-RISK-001",
        customer_id="CUST-001",
        metadata={"ip_country": "US", "card_country": "RU"},
    )
    result = validator.validate(req)
    assert result["risk_score"] == 75
    assert result["valid"] is False
""")

# Commit feature work
wt_git = lambda cmd: subprocess.run(
    ["git"] + cmd, cwd=str(WORKTREE_PATH),
    capture_output=True, text=True
)
wt_git(["add", "."])
subprocess.run(
    ["git", "commit", "-m", "feat(validator): add TransactionValidator with fraud detection"],
    cwd=str(WORKTREE_PATH), capture_output=True, text=True
)

# ── 6. Write a record file so eval knows branch/worktree names ────────────────
(WORKSPACE / ".task_meta.json").write_text(
    '{"repo": "payments-service", "feature_branch": "feature/transaction-validator", '
    '"worktree_path": "transaction-validator-worktree", "base_branch": "main"}'
)

print("✓ Workspace generated successfully.")
print(f"  Repo:           {REPO}")
print(f"  Feature branch: {FEATURE_BRANCH}")
print(f"  Worktree path:  {WORKTREE_PATH}")