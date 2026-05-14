#!/usr/bin/env python3
"""
Generate a realistic fintech payment gateway codebase workspace.
The workspace is messy and realistic — multiple file types, nested dirs,
distractor files. The agent must index it, record cognitive facts, search it.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "src/gateway",
    "src/gateway/processors",
    "src/gateway/validators",
    "src/gateway/models",
    "src/auth",
    "src/utils",
    "docs/architecture",
    "docs/decisions",
    "tests/unit",
    "tests/integration",
    "config",
    "scripts",
    "legacy",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Python source files ──────────────────────────────────────────────────────

(WORKSPACE / "src/gateway/__init__.py").write_text("""\
\"\"\"PayBridge Gateway — core payment routing engine.\"\"\"
from .router import PaymentRouter
from .processors.stripe_processor import StripeProcessor
from .processors.paypal_processor import PayPalProcessor

__version__ = "3.4.1"
__all__ = ["PaymentRouter", "StripeProcessor", "PayPalProcessor"]
""")

(WORKSPACE / "src/gateway/router.py").write_text("""\
\"\"\"
PaymentRouter: central routing logic for the PayBridge gateway.

Routes transactions to the appropriate payment processor based on:
- Currency (USD/EUR/JPY -> different processors)
- Transaction amount (micro-payments < $1 use FastLane)
- Merchant category code (MCC)
- Fraud score from RiskEngine
\"\"\"
import logging
from typing import Optional
from .processors.base import BaseProcessor
from .validators.transaction_validator import validate_transaction
from ..auth.token_manager import TokenManager

logger = logging.getLogger(__name__)

class PaymentRouter:
    \"\"\"Routes payments to processors using weighted round-robin with fallback.\"\"\"

    FALLBACK_CHAIN = ["stripe", "paypal", "fastlane"]

    def __init__(self, config: dict):
        self.config = config
        self.token_manager = TokenManager(config.get("auth", {}))
        self._processors: dict[str, BaseProcessor] = {}
        self._circuit_breakers: dict[str, int] = {}

    def register_processor(self, name: str, processor: BaseProcessor) -> None:
        \"\"\"Register a payment processor by name.\"\"\"
        self._processors[name] = processor
        self._circuit_breakers[name] = 0
        logger.info(f"Registered processor: {name}")

    def route(self, transaction: dict) -> dict:
        \"\"\"
        Route a transaction. Returns processor response dict.
        Raises RoutingError if all processors in fallback chain fail.
        \"\"\"
        validate_transaction(transaction)
        fraud_score = self._get_fraud_score(transaction)
        if fraud_score > 0.85:
            raise ValueError(f"Transaction blocked: fraud_score={fraud_score:.2f}")

        for processor_name in self.FALLBACK_CHAIN:
            if processor_name not in self._processors:
                continue
            if self._circuit_breakers.get(processor_name, 0) >= 5:
                logger.warning(f"Circuit breaker open for {processor_name}, skipping")
                continue
            try:
                result = self._processors[processor_name].process(transaction)
                self._circuit_breakers[processor_name] = 0
                return result
            except Exception as e:
                self._circuit_breakers[processor_name] += 1
                logger.error(f"Processor {processor_name} failed: {e}")

        raise RuntimeError("All processors exhausted in fallback chain")

    def _get_fraud_score(self, transaction: dict) -> float:
        \"\"\"Stub: integrate with RiskEngine via gRPC in production.\"\"\"
        amount = transaction.get("amount_cents", 0)
        return 0.1 if amount < 100000 else 0.3
""")

(WORKSPACE / "src/gateway/processors/__init__.py").write_text("")

(WORKSPACE / "src/gateway/processors/base.py").write_text("""\
\"\"\"Abstract base class for all payment processors.\"\"\"
from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    \"\"\"All processors must implement process() and health_check().\"\"\"

    @abstractmethod
    def process(self, transaction: dict) -> dict:
        \"\"\"Submit transaction. Returns response with status and processor_ref.\"\"\"
        ...

    @abstractmethod
    def health_check(self) -> bool:
        \"\"\"Return True if processor endpoint is reachable.\"\"\"
        ...
""")

(WORKSPACE / "src/gateway/processors/stripe_processor.py").write_text("""\
\"\"\"
Stripe processor integration for PayBridge.

Design decision: We use Stripe's /v1/payment_intents API (not charges).
This was chosen in ADR-007 because PaymentIntents support SCA/3DS2 natively,
which is mandatory for EU merchants post-PSD2.

Retry policy: exponential backoff, max 3 attempts, 2^n * 100ms delay.
\"\"\"
import time
import logging
from .base import BaseProcessor

logger = logging.getLogger(__name__)

class StripeProcessor(BaseProcessor):
    BASE_URL = "https://api.stripe.com/v1"
    MAX_RETRIES = 3

    def __init__(self, api_key: str, webhook_secret: str):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    def process(self, transaction: dict) -> dict:
        \"\"\"Create a PaymentIntent and confirm it.\"\"\"
        payload = {
            "amount": transaction["amount_cents"],
            "currency": transaction.get("currency", "usd"),
            "payment_method": transaction["payment_method_id"],
            "confirm": True,
            "return_url": transaction.get("return_url", "https://paybridge.io/return"),
        }
        for attempt in range(self.MAX_RETRIES):
            try:
                # Simulated HTTP call
                logger.info(f"Stripe attempt {attempt+1}: {payload}")
                return {"status": "succeeded", "processor_ref": "pi_simulated_001", "processor": "stripe"}
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                time.sleep((2 ** attempt) * 0.1)

    def health_check(self) -> bool:
        return True
""")

(WORKSPACE / "src/gateway/processors/paypal_processor.py").write_text("""\
\"\"\"PayPal Orders API v2 processor — used as secondary fallback.\"\"\"
from .base import BaseProcessor

class PayPalProcessor(BaseProcessor):
    \"\"\"
    Uses PayPal Orders API v2.
    Note: PayPal requires a two-step flow: CREATE order -> CAPTURE order.
    This is encapsulated in process() as a synchronous call.
    \"\"\"
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def process(self, transaction: dict) -> dict:
        order_id = self._create_order(transaction)
        return self._capture_order(order_id)

    def _create_order(self, transaction: dict) -> str:
        return "PAYPAL-ORDER-SIM-001"

    def _capture_order(self, order_id: str) -> dict:
        return {"status": "COMPLETED", "processor_ref": order_id, "processor": "paypal"}

    def health_check(self) -> bool:
        return True
""")

(WORKSPACE / "src/gateway/validators/__init__.py").write_text("")

(WORKSPACE / "src/gateway/validators/transaction_validator.py").write_text("""\
\"\"\"
Transaction validation layer.

Rules enforced:
- amount_cents must be integer > 0 and <= 99_999_999 (Stripe/PayPal max)
- currency must be ISO 4217 3-letter code
- payment_method_id must start with 'pm_' (Stripe) or 'PAYPAL-' (PayPal)
- merchant_id must be present and non-empty
\"\"\"
import re

CURRENCY_RE = re.compile(r'^[A-Z]{3}$')
AMOUNT_MAX = 99_999_999

def validate_transaction(tx: dict) -> None:
    \"\"\"Raise ValueError with descriptive message on validation failure.\"\"\"
    if not isinstance(tx.get("amount_cents"), int) or tx["amount_cents"] <= 0:
        raise ValueError("amount_cents must be a positive integer")
    if tx["amount_cents"] > AMOUNT_MAX:
        raise ValueError(f"amount_cents exceeds maximum {AMOUNT_MAX}")
    if not CURRENCY_RE.match(tx.get("currency", "")):
        raise ValueError("currency must be ISO 4217 (e.g. 'USD')")
    if not tx.get("merchant_id"):
        raise ValueError("merchant_id is required")
""")

(WORKSPACE / "src/gateway/models/__init__.py").write_text("")

(WORKSPACE / "src/gateway/models/transaction.py").write_text("""\
\"\"\"Pydantic models for transaction data.\"\"\"
from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"

class Transaction(BaseModel):
    transaction_id: str = Field(..., description="UUID v4")
    amount_cents: int = Field(..., gt=0, le=99_999_999)
    currency: str = Field(..., min_length=3, max_length=3)
    merchant_id: str
    payment_method_id: str
    status: TransactionStatus = TransactionStatus.PENDING
    processor: Optional[str] = None
    processor_ref: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

    @validator("currency")
    def currency_uppercase(cls, v):
        return v.upper()
""")

(WORKSPACE / "src/auth/__init__.py").write_text("")

(WORKSPACE / "src/auth/token_manager.py").write_text("""\
\"\"\"
TokenManager: handles JWT issuance and validation for merchant API access.

Architecture note: We use asymmetric RS256 signing (not HS256).
Rationale: Multiple microservices need to VERIFY tokens without knowing the secret.
Private key lives only in the gateway service. Public keys are distributed via JWKS endpoint.
Token TTL: 15 minutes for access tokens, 30 days for refresh tokens.
\"\"\"
import time

class TokenManager:
    def __init__(self, config: dict):
        self.config = config
        self._revocation_cache: set = set()

    def issue_token(self, merchant_id: str, scopes: list) -> dict:
        \"\"\"Issue JWT access + refresh token pair.\"\"\"
        now = int(time.time())
        return {
            "access_token": f"jwt_sim_{merchant_id}_{now}",
            "refresh_token": f"refresh_sim_{merchant_id}_{now}",
            "expires_in": 900,
            "token_type": "Bearer",
        }

    def verify_token(self, token: str) -> dict:
        \"\"\"Verify and decode JWT. Raises if expired/revoked/invalid.\"\"\"
        if token in self._revocation_cache:
            raise ValueError("Token has been revoked")
        return {"merchant_id": "sim_merchant", "scopes": ["payments:write"]}

    def revoke_token(self, token: str) -> None:
        \"\"\"Add token to revocation cache (in-process only — use Redis in prod).\"\"\"
        self._revocation_cache.add(token)
""")

(WORKSPACE / "src/utils/__init__.py").write_text("")

(WORKSPACE / "src/utils/idempotency.py").write_text("""\
\"\"\"
Idempotency key management.

Critical design: Idempotency keys are scoped per merchant+endpoint combo.
Collisions across merchants with same key string are NOT treated as duplicates.
Keys expire after 24 hours (86400 seconds).
Storage: Redis with TTL. Fall back to in-memory dict for testing.
\"\"\"
import time
import hashlib

class IdempotencyStore:
    def __init__(self, backend="memory"):
        self._store: dict = {}
        self.backend = backend

    def _make_key(self, merchant_id: str, endpoint: str, idempotency_key: str) -> str:
        raw = f"{merchant_id}:{endpoint}:{idempotency_key}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def check_and_store(self, merchant_id, endpoint, idempotency_key, response) -> tuple:
        \"\"\"Returns (is_duplicate, stored_response).\"\"\"
        key = self._make_key(merchant_id, endpoint, idempotency_key)
        now = time.time()
        if key in self._store:
            stored_at, stored_resp = self._store[key]
            if now - stored_at < 86400:
                return True, stored_resp
        self._store[key] = (now, response)
        return False, response
""")

# ── Markdown architecture docs ────────────────────────────────────────────────

(WORKSPACE / "docs/architecture/overview.md").write_text("""\
# PayBridge Architecture Overview

## System Components

PayBridge consists of four primary components:

1. **API Gateway** (`src/gateway/`) — Routes payment requests to processors
2. **Auth Service** (`src/auth/`) — Issues and validates merchant JWTs
3. **Risk Engine** — External gRPC service (not in this repo)
4. **Settlement Service** — Batch job, runs nightly at 02:00 UTC

## Data Flow

```
Merchant API Request
    -> Auth Middleware (JWT verify)
    -> Idempotency Check
    -> Transaction Validation
    -> Fraud Score (Risk Engine gRPC)
    -> Payment Router
    -> Processor (Stripe / PayPal / FastLane)
    -> Response + Webhook emit
```

## Scalability

The PaymentRouter uses **weighted round-robin** with **circuit breakers**.
Each processor has a failure threshold of 5 consecutive failures before the
circuit opens. Automatic reset happens after 30 seconds.

## Database

PostgreSQL 15 with read replicas. The `transactions` table is partitioned
by month (range partitioning on `created_at`).
""")

(WORKSPACE / "docs/architecture/processor_selection.md").write_text("""\
# Processor Selection Logic

## Decision Matrix

| Condition | Processor |
|-----------|-----------|
| EU merchant + amount > 0 | Stripe (SCA required) |
| amount_cents < 100 | FastLane (micro-payment) |
| Stripe circuit open | PayPal fallback |
| PayPal circuit open | FastLane |
| All circuits open | Reject with 503 |

## Why Stripe First?

ADR-007 (see docs/decisions/ADR-007-payment-intents.md) documents the decision
to use Stripe PaymentIntents over the legacy Charges API. The key driver was
PSD2/SCA compliance for European merchants, which became mandatory in 2021.

## FastLane Integration

FastLane is our internal micro-payment processor built on top of pre-authorized
wallet balances. It bypasses external network calls for sub-$1 transactions,
reducing latency from ~800ms to ~12ms.
""")

(WORKSPACE / "docs/decisions/ADR-007-payment-intents.md").write_text("""\
# ADR-007: Use Stripe PaymentIntents API (not Charges)

**Status**: Accepted  
**Date**: 2023-04-12  
**Deciders**: @alice-eng, @bob-arch, @carol-pm

## Context

The legacy integration used Stripe's `/v1/charges` endpoint. Post-PSD2 (Strong
Customer Authentication), EU card transactions require 3DS2 challenge flows.
The Charges API does not natively support 3DS2.

## Decision

Migrate all Stripe calls to `/v1/payment_intents`. PaymentIntents support SCA
natively via `confirm=True` + `return_url` for redirect-based 3DS2 flows.

## Consequences

- All existing Stripe integration tests must be updated
- `processor_ref` field now stores `pi_*` IDs instead of `ch_*` IDs
- Webhook handlers must listen for `payment_intent.succeeded` not `charge.succeeded`
""")

(WORKSPACE / "docs/decisions/ADR-012-rs256-tokens.md").write_text("""\
# ADR-012: Use RS256 for JWT Signing (not HS256)

**Status**: Accepted  
**Date**: 2023-09-01

## Context

Multiple downstream microservices (settlement, reporting, fraud) need to
validate merchant JWTs independently. HS256 requires sharing the secret
with every service that needs to verify tokens — a security anti-pattern.

## Decision

Use RS256 (RSA 2048-bit). Gateway holds private key for signing.
Public keys served via `/.well-known/jwks.json` endpoint.

## Consequences

- Key rotation requires JWKS cache invalidation across all consumers
- Token TTL set to 15 min (access) / 30 days (refresh) to limit exposure window
""")

# ── Plain-text decision logs (distractor + content) ──────────────────────────

(WORKSPACE / "docs/decisions/incident-2024-03-15.txt").write_text("""\
INCIDENT REPORT — 2024-03-15

Duration: 47 minutes (14:23 - 15:10 UTC)
Severity: P1 — payment processing degraded

Root cause: Stripe circuit breaker threshold set to 5 but counter was not
reset on deployment. After a rolling deploy, all instances had counter=4
from pre-deploy errors. First error post-deploy opened all circuits simultaneously.

Fix applied:
- Added circuit breaker state to Redis (was in-process memory, not shared)
- Added /internal/circuit-reset admin endpoint
- Counter now resets on healthy response, not just on explicit reset

Action items:
- Move ALL stateful components out of process memory before Q3
- Add circuit breaker dashboards to Grafana
""")

(WORKSPACE / "docs/decisions/tech-debt-notes.txt").write_text("""\
Tech debt items tracked here informally (formal tracking in Jira):

1. IdempotencyStore falls back to in-memory dict — NOT safe for multi-instance.
   Must migrate to Redis before scaling beyond 2 replicas.
   Owner: @dave-eng  ETA: Q2 2024

2. RiskEngine gRPC stub in PaymentRouter._get_fraud_score() returns hardcoded 0.1/0.3.
   Real integration blocked on Risk team API stability.
   Owner: @alice-eng  ETA: Q3 2024

3. No rate limiting on merchant API endpoints. Planned: token bucket per merchant_id.
   Owner: TBD  ETA: Q4 2024

4. FastLane processor not yet implemented — placeholder only.
   Owner: @frank-eng  ETA: Q1 2025
""")

# ── Test files (distractors) ─────────────────────────────────────────────────

(WORKSPACE / "tests/unit/test_validator.py").write_text("""\
import pytest
from src.gateway.validators.transaction_validator import validate_transaction

def test_valid_transaction():
    validate_transaction({
        "amount_cents": 5000,
        "currency": "USD",
        "merchant_id": "merch_001",
        "payment_method_id": "pm_test_001",
    })

def test_amount_zero_fails():
    with pytest.raises(ValueError):
        validate_transaction({"amount_cents": 0, "currency": "USD", "merchant_id": "m1"})

def test_currency_invalid():
    with pytest.raises(ValueError):
        validate_transaction({"amount_cents": 100, "currency": "usd", "merchant_id": "m1"})
""")

(WORKSPACE / "tests/integration/test_router_integration.py").write_text("""\
\"\"\"Integration tests — require live processor mocks.\"\"\"
import pytest

@pytest.mark.skip(reason="Requires mock processor server")
def test_stripe_primary_route():
    pass

@pytest.mark.skip(reason="Requires mock processor server")
def test_paypal_fallback_on_stripe_circuit_open():
    pass
""")

# ── Config files (distractors) ───────────────────────────────────────────────

(WORKSPACE / "config/processors.yaml").write_text("""\
processors:
  stripe:
    enabled: true
    priority: 1
    timeout_ms: 5000
  paypal:
    enabled: true
    priority: 2
    timeout_ms: 8000
  fastlane:
    enabled: false
    priority: 3
    timeout_ms: 500
""")

(WORKSPACE / "config/logging.yaml").write_text("""\
version: 1
formatters:
  json:
    format: '{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
handlers:
  console:
    class: logging.StreamHandler
    formatter: json
root:
  level: INFO
  handlers: [console]
""")

# ── Scripts (distractors) ────────────────────────────────────────────────────

(WORKSPACE / "scripts/migrate_db.sh").write_text("""\
#!/bin/bash
# Run Alembic migrations
set -e
alembic upgrade head
echo "Migrations complete"
""")

(WORKSPACE / "scripts/seed_dev_data.py").write_text("""\
\"\"\"Seed development database with test merchants and transactions.\"\"\"
import uuid
import random

MERCHANTS = [f"merch_{i:04d}" for i in range(1, 21)]

def seed():
    for m in MERCHANTS:
        print(f"Seeding merchant {m} with 50 transactions...")

if __name__ == "__main__":
    seed()
""")

# ── Legacy code (distractors) ─────────────────────────────────────────────────

(WORKSPACE / "legacy/old_charges_processor.py").write_text("""\
\"\"\"
DEPRECATED: Old Stripe Charges integration.
Replaced by StripeProcessor (PaymentIntents) per ADR-007.
Do NOT use in new code.
\"\"\"

def create_charge(amount, currency, source, description):
    \"\"\"Legacy Stripe /v1/charges call. DO NOT USE.\"\"\"
    raise DeprecationWarning("Use StripeProcessor.process() instead")
""")

(WORKSPACE / "legacy/README_LEGACY.txt").write_text("""\
This directory contains legacy code kept for reference only.
None of these files should be imported by production code.
""")

# ── A messy requirements file ─────────────────────────────────────────────────

(WORKSPACE / "requirements.txt").write_text("""\
pydantic>=2.0
fastapi>=0.100
uvicorn
httpx
redis>=4.0
python-jose[cryptography]
alembic
sqlalchemy>=2.0
pytest
pytest-asyncio
""")

# ── A broken/incomplete pyproject.toml ───────────────────────────────────────

(WORKSPACE / "pyproject.toml").write_text("""\
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
# TODO: fill in more config
""")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")