import os
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure for a fintech payment processing codebase ---
dirs = [
    "src/gateway",
    "src/fraud",
    "src/ledger",
    "src/notifications",
    "src/common/middleware",
    "src/common/models",
    "src/common/utils",
    "src/config",
    "src/jobs",
    "tests/unit/gateway",
    "tests/unit/fraud",
    "tests/integration",
    "migrations",
    "scripts",
    "docs/runbooks",
    "docs/api",
    ".github/workflows",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Source files ---

files = {}

files["src/gateway/__init__.py"] = ""

files["src/gateway/router.py"] = '''\
"""
Payment Gateway Router
Entry point for all incoming payment requests.
"""
from .validator import validate_payment_request
from .dispatcher import dispatch_to_processor
from src.fraud.engine import FraudEngine
from src.ledger.ledger_service import LedgerService
from src.notifications.notifier import Notifier
from src.common.models.payment import PaymentRequest, PaymentResult
from src.common.middleware.auth import require_auth
from src.common.middleware.rate_limit import RateLimiter


class PaymentRouter:
    """Routes incoming payment requests through validation, fraud check, ledger posting, and notification."""

    def __init__(self, config):
        self.fraud_engine = FraudEngine(config.fraud)
        self.ledger = LedgerService(config.ledger)
        self.notifier = Notifier(config.notifications)
        self.rate_limiter = RateLimiter(config.rate_limit)

    @require_auth
    def handle_payment(self, request: PaymentRequest) -> PaymentResult:
        """Main handler. Validates, fraud-checks, posts to ledger, and notifies."""
        validated = validate_payment_request(request)
        fraud_result = self.fraud_engine.evaluate(validated)
        if fraud_result.is_blocked:
            self.notifier.send_fraud_alert(request, fraud_result)
            return PaymentResult(status="declined", reason=fraud_result.reason)
        ledger_entry = self.ledger.post(validated)
        self.notifier.send_confirmation(request, ledger_entry)
        return PaymentResult(status="approved", ledger_id=ledger_entry.id)
'''

files["src/gateway/validator.py"] = '''\
"""
Request Validator: checks schema, currency codes, and amount limits.
"""
from src.common.models.payment import PaymentRequest
from src.config.limits import MAX_TRANSACTION_AMOUNT


def validate_payment_request(request: PaymentRequest) -> PaymentRequest:
    """Validates a PaymentRequest against schema and business rules. Raises ValidationError on failure."""
    if request.amount <= 0:
        raise ValueError("Amount must be positive")
    if request.amount > MAX_TRANSACTION_AMOUNT:
        raise ValueError(f"Amount exceeds maximum: {MAX_TRANSACTION_AMOUNT}")
    if not request.currency in ("USD", "EUR", "GBP"):
        raise ValueError(f"Unsupported currency: {request.currency}")
    return request
'''

files["src/gateway/dispatcher.py"] = '''\
"""
Dispatcher: routes validated payment to the correct processor adapter (Stripe, ACH, Wire).
"""
from src.common.utils.registry import ProcessorRegistry


def dispatch_to_processor(request, registry: ProcessorRegistry):
    """Selects the appropriate payment processor and dispatches the request."""
    processor = registry.get_processor(request.method)
    return processor.submit(request)
'''

files["src/fraud/__init__.py"] = ""

files["src/fraud/engine.py"] = '''\
"""
Fraud Detection Engine: applies rule-based and ML scoring to flag risky transactions.
"""
from .rules import RuleSet
from .scorer import MLScorer
from src.common.models.fraud import FraudResult


class FraudEngine:
    """Orchestrates fraud detection: runs RuleSet first, then MLScorer if rules pass."""

    def __init__(self, config):
        self.rules = RuleSet(config.rules)
        self.scorer = MLScorer(config.model_path)
        self.threshold = config.block_threshold

    def evaluate(self, request) -> FraudResult:
        """Evaluate a payment request for fraud risk. Returns FraudResult with is_blocked and reason."""
        rule_result = self.rules.check(request)
        if rule_result.triggered:
            return FraudResult(is_blocked=True, reason=rule_result.rule_name, score=1.0)
        score = self.scorer.score(request)
        is_blocked = score >= self.threshold
        return FraudResult(is_blocked=is_blocked, reason="ml_score" if is_blocked else None, score=score)
'''

files["src/fraud/rules.py"] = '''\
"""
Rule-based fraud filters: velocity checks, blacklist lookups, geographic restrictions.
"""
from src.common.models.fraud import RuleResult


class RuleSet:
    """Applies a configurable list of deterministic fraud rules."""

    def __init__(self, rules_config):
        self.rules_config = rules_config

    def check(self, request) -> RuleResult:
        """Check request against all rules. Returns first triggered rule or a pass result."""
        if request.amount > self.rules_config.get("max_single_transaction", 50000):
            return RuleResult(triggered=True, rule_name="max_single_transaction")
        if request.merchant_id in self.rules_config.get("blacklisted_merchants", []):
            return RuleResult(triggered=True, rule_name="blacklisted_merchant")
        return RuleResult(triggered=False, rule_name=None)
'''

files["src/fraud/scorer.py"] = '''\
"""
ML-based fraud scorer: loads a trained model and returns a risk score [0.0, 1.0].
"""
import pickle


class MLScorer:
    """Wraps a serialized ML model for real-time fraud scoring."""

    def __init__(self, model_path: str):
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

    def score(self, request) -> float:
        """Returns a fraud probability score between 0.0 (safe) and 1.0 (fraudulent)."""
        features = self._extract_features(request)
        return float(self.model.predict_proba([features])[0][1])

    def _extract_features(self, request):
        return [request.amount, request.merchant_id, request.user_id]
'''

files["src/ledger/__init__.py"] = ""

files["src/ledger/ledger_service.py"] = '''\
"""
Ledger Service: double-entry bookkeeping for all approved transactions.
"""
from .entry_builder import build_entry
from .db_writer import write_to_db
from src.common.models.ledger import LedgerEntry


class LedgerService:
    """Creates and persists double-entry ledger records for approved payments."""

    def __init__(self, config):
        self.db_config = config.database

    def post(self, request) -> LedgerEntry:
        """Build a double-entry record and persist it to the database."""
        entry = build_entry(request)
        return write_to_db(entry, self.db_config)
'''

files["src/ledger/entry_builder.py"] = '''\
"""
Entry Builder: constructs debit/credit pairs for a transaction.
"""
from src.common.models.ledger import LedgerEntry
import uuid
from datetime import datetime, timezone


def build_entry(request) -> LedgerEntry:
    """Constructs a LedgerEntry with debit/credit lines and a unique transaction ID."""
    return LedgerEntry(
        id=str(uuid.uuid4()),
        debit_account=request.source_account,
        credit_account=request.destination_account,
        amount=request.amount,
        currency=request.currency,
        timestamp=datetime.now(timezone.utc),
    )
'''

files["src/ledger/db_writer.py"] = '''\
"""
DB Writer: persists LedgerEntry to PostgreSQL using a connection pool.
"""
import psycopg2


def write_to_db(entry, db_config) -> "LedgerEntry":
    """Insert the ledger entry into the PostgreSQL ledger table and return with server-assigned ID."""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ledger_entries (id, debit, credit, amount, currency, ts) VALUES (%s,%s,%s,%s,%s,%s)",
        (entry.id, entry.debit_account, entry.credit_account, entry.amount, entry.currency, entry.timestamp)
    )
    conn.commit()
    return entry
'''

files["src/notifications/__init__.py"] = ""

files["src/notifications/notifier.py"] = '''\
"""
Notifier: sends confirmation emails and fraud alerts via async queues.
"""
from .email_sender import EmailSender
from .queue_publisher import QueuePublisher


class Notifier:
    """Dispatches notification events to email and message queue."""

    def __init__(self, config):
        self.email = EmailSender(config.smtp)
        self.queue = QueuePublisher(config.queue_url)

    def send_confirmation(self, request, ledger_entry):
        """Send payment confirmation email and publish event to the message queue."""
        self.email.send(to=request.user_email, subject="Payment Confirmed", body=f"Ledger ID: {ledger_entry.id}")
        self.queue.publish("payment.confirmed", {"ledger_id": ledger_entry.id})

    def send_fraud_alert(self, request, fraud_result):
        """Publish a fraud alert event and optionally notify the user."""
        self.queue.publish("payment.fraud_alert", {"score": fraud_result.score, "reason": fraud_result.reason})
'''

files["src/notifications/email_sender.py"] = '''\
"""
Email Sender: wraps SMTP connection for sending transactional emails.
"""
import smtplib


class EmailSender:
    def __init__(self, smtp_config):
        self.host = smtp_config["host"]
        self.port = smtp_config["port"]

    def send(self, to, subject, body):
        """Send a plain-text email via configured SMTP server."""
        pass  # implementation omitted for brevity
'''

files["src/notifications/queue_publisher.py"] = '''\
"""
Queue Publisher: publishes domain events to a RabbitMQ exchange.
"""


class QueuePublisher:
    def __init__(self, queue_url):
        self.queue_url = queue_url

    def publish(self, event_type, payload):
        """Publish an event payload to the configured queue exchange."""
        pass  # implementation omitted for brevity
'''

files["src/common/__init__.py"] = ""
files["src/common/middleware/__init__.py"] = ""

files["src/common/middleware/auth.py"] = '''\
"""
Auth middleware: validates Bearer tokens on incoming requests.
"""


def require_auth(handler):
    """Decorator that extracts and validates the Bearer token before calling the handler."""
    def wrapper(self, request, *args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise PermissionError("Missing auth token")
        return handler(self, request, *args, **kwargs)
    return wrapper
'''

files["src/common/middleware/rate_limit.py"] = '''\
"""
Rate Limiter: sliding-window rate limiting per user ID using Redis.
"""


class RateLimiter:
    def __init__(self, config):
        self.window_seconds = config.get("window_seconds", 60)
        self.max_requests = config.get("max_requests", 100)

    def check(self, user_id: str) -> bool:
        """Returns True if user is within rate limit, False if exceeded."""
        return True  # Redis integration omitted
'''

files["src/common/models/__init__.py"] = ""

files["src/common/models/payment.py"] = '''\
"""
Payment domain models.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentRequest:
    user_id: str
    user_email: str
    merchant_id: str
    amount: float
    currency: str
    method: str
    source_account: str
    destination_account: str
    headers: dict = None


@dataclass
class PaymentResult:
    status: str
    reason: Optional[str] = None
    ledger_id: Optional[str] = None
'''

files["src/common/models/fraud.py"] = '''\
"""
Fraud domain models.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class FraudResult:
    is_blocked: bool
    score: float
    reason: Optional[str] = None


@dataclass
class RuleResult:
    triggered: bool
    rule_name: Optional[str]
'''

files["src/common/models/ledger.py"] = '''\
"""
Ledger domain models.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LedgerEntry:
    id: str
    debit_account: str
    credit_account: str
    amount: float
    currency: str
    timestamp: datetime
'''

files["src/common/utils/__init__.py"] = ""

files["src/common/utils/registry.py"] = '''\
"""
Processor Registry: maps payment method strings to processor adapter instances.
"""


class ProcessorRegistry:
    def __init__(self):
        self._registry = {}

    def register(self, method: str, processor):
        """Register a processor adapter for a payment method."""
        self._registry[method] = processor

    def get_processor(self, method: str):
        """Retrieve the adapter for the given payment method. Raises KeyError if not found."""
        if method not in self._registry:
            raise KeyError(f"No processor registered for method: {method}")
        return self._registry[method]
'''

files["src/config/__init__.py"] = ""

files["src/config/limits.py"] = '''\
"""
Global transaction limits and business rule constants.
"""
MAX_TRANSACTION_AMOUNT = 100_000  # USD equivalent
MIN_TRANSACTION_AMOUNT = 0.01
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]
FRAUD_BLOCK_THRESHOLD = 0.85
'''

files["src/config/app_config.py"] = '''\
"""
Application configuration loader: reads from environment variables and config.yaml.
"""
import os
import yaml


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load and merge YAML config with environment variable overrides."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    cfg["fraud"]["block_threshold"] = float(os.getenv("FRAUD_THRESHOLD", cfg["fraud"]["block_threshold"]))
    return cfg
'''

files["src/jobs/__init__.py"] = ""

files["src/jobs/reconciliation.py"] = '''\
"""
Reconciliation Job: nightly batch job comparing ledger entries against processor settlement files.
"""


class ReconciliationJob:
    """Runs nightly to detect and flag mismatches between internal ledger and processor reports."""

    def run(self, ledger_entries, settlement_file):
        """Compare ledger with settlement data. Returns list of discrepancies."""
        discrepancies = []
        settlement_ids = {r["transaction_id"] for r in settlement_file}
        for entry in ledger_entries:
            if entry.id not in settlement_ids:
                discrepancies.append(entry)
        return discrepancies
'''

# Tests (distractor files)
files["tests/__init__.py"] = ""
files["tests/unit/__init__.py"] = ""
files["tests/unit/gateway/__init__.py"] = ""
files["tests/unit/fraud/__init__.py"] = ""

files["tests/unit/gateway/test_validator.py"] = '''\
import pytest
from src.gateway.validator import validate_payment_request


def test_negative_amount_rejected():
    pass  # TODO
'''

files["tests/unit/fraud/test_engine.py"] = '''\
import pytest


def test_blocked_merchant():
    pass  # TODO
'''

files["tests/integration/test_payment_flow.py"] = '''\
"""Integration test for end-to-end payment flow."""
pass
'''

files["migrations/001_initial_ledger.sql"] = '''\
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY,
    debit VARCHAR(64),
    credit VARCHAR(64),
    amount NUMERIC(18,4),
    currency CHAR(3),
    ts TIMESTAMPTZ
);
'''

files["scripts/seed_dev_data.py"] = '''\
"""Seed script for development environment."""
print("Seeding dev data...")
'''

files["docs/runbooks/incident_response.md"] = '''\
# Incident Response Runbook
1. Page on-call engineer
2. Check dashboards
3. Escalate if unresolved in 15 minutes
'''

files["docs/api/payment_api.md"] = '''\
# Payment API Reference
POST /v1/payments
Authorization: Bearer <token>
'''

files[".github/workflows/ci.yml"] = '''\
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/
'''

files["config/config.yaml"] = '''\
fraud:
  block_threshold: 0.85
  rules:
    max_single_transaction: 50000
    blacklisted_merchants: []
  model_path: models/fraud_model.pkl
ledger:
  database:
    host: localhost
    port: 5432
    dbname: payments_ledger
    user: ledger_user
    password: secret
notifications:
  smtp:
    host: smtp.internal
    port: 587
  queue_url: amqp://guest:guest@rabbitmq:5672/
rate_limit:
  window_seconds: 60
  max_requests: 100
'''

files["pyproject.toml"] = '''\
[tool.poetry]
name = "payment-processor"
version = "0.4.2"
description = "Fintech payment processing pipeline"

[tool.poetry.dependencies]
python = "^3.11"
pyyaml = "^6.0"
psycopg2 = "^2.9"
'''

# Write all files
for rel_path, content in files.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print("Files created:")
for rel_path in sorted(files.keys()):
    print(f"  {rel_path}")