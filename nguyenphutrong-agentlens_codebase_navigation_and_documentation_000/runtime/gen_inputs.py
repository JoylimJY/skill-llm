import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ─── Source tree ──────────────────────────────────────────────────────────────

src_files = {
    # ── transaction module ──────────────────────────────────────────────────
    "src/transaction/__init__.py": """\
from .processor import TransactionProcessor
from .validator import TransactionValidator
from .models import Transaction, TransactionStatus
""",

    "src/transaction/processor.py": "\n".join(
        [f"# line {i}" for i in range(1, 50)]
        + ["class TransactionProcessor:"]
        + [f"    # line {i}" for i in range(51, 110)]
        + ["    def process(self, txn):"]
        + [f"        # line {i}" for i in range(112, 200)]
        + ["    def rollback(self, txn_id):"]
        + [f"        # line {i}" for i in range(202, 280)]
        + ["    def _validate_amount(self, amount):"]
        + [f"        # line {i}" for i in range(282, 340)]
        + ["    def _apply_fees(self, txn):"]
        + [f"        # line {i}" for i in range(342, 420)]
        + ["    def get_status(self, txn_id):"]
        + [f"        # line {i}" for i in range(422, 510)]
        + ["    def batch_process(self, txns):"]
        + [f"        # line {i}" for i in range(512, 560)]
    ),

    "src/transaction/validator.py": "\n".join(
        [f"# line {i}" for i in range(1, 30)]
        + ["class TransactionValidator:"]
        + [f"    # line {i}" for i in range(32, 80)]
        + ["    def validate(self, txn):"]
        + [f"        # line {i}" for i in range(82, 140)]
        + ["    def check_limits(self, txn):"]
        + [f"        # line {i}" for i in range(142, 190)]
    ),

    "src/transaction/models.py": """\
from dataclasses import dataclass
from enum import Enum

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    status: TransactionStatus
    merchant_id: str
""",

    # ── fraud module ────────────────────────────────────────────────────────
    "src/fraud/__init__.py": """\
from .detector import FraudDetector
from .rules import RuleEngine
from .scorer import RiskScorer
""",

    "src/fraud/detector.py": "\n".join(
        [f"# line {i}" for i in range(1, 40)]
        + ["class FraudDetector:"]
        + [f"    # line {i}" for i in range(42, 130)]
        + ["    def detect(self, txn):"]
        + [f"        # line {i}" for i in range(132, 250)]
        + ["    def update_model(self, feedback):"]
        + [f"        # line {i}" for i in range(252, 370)]
        + ["    def _load_patterns(self):"]
        + [f"        # line {i}" for i in range(372, 480)]
        + ["    def explain_decision(self, txn_id):"]
        + [f"        # line {i}" for i in range(482, 530)]
    ),

    "src/fraud/rules.py": "\n".join(
        [f"# line {i}" for i in range(1, 20)]
        + ["class RuleEngine:"]
        + [f"    # line {i}" for i in range(22, 70)]
        + ["    def evaluate(self, txn):"]
        + [f"        # line {i}" for i in range(72, 120)]
        + ["    def add_rule(self, rule):"]
        + [f"        # line {i}" for i in range(122, 160)]
    ),

    "src/fraud/scorer.py": "\n".join(
        [f"# line {i}" for i in range(1, 15)]
        + ["class RiskScorer:"]
        + [f"    # line {i}" for i in range(17, 60)]
        + ["    def score(self, features):"]
        + [f"        # line {i}" for i in range(62, 100)]
    ),

    # ── compliance module ───────────────────────────────────────────────────
    "src/compliance/__init__.py": """\
from .reporter import ComplianceReporter
from .audit_log import AuditLogger
""",

    "src/compliance/reporter.py": "\n".join(
        [f"# line {i}" for i in range(1, 60)]
        + ["class ComplianceReporter:"]
        + [f"    # line {i}" for i in range(62, 180)]
        + ["    def generate_report(self, period):"]
        + [f"        # line {i}" for i in range(182, 310)]
        + ["    def submit_to_regulator(self, report):"]
        + [f"        # line {i}" for i in range(312, 430)]
        + ["    def _format_for_swift(self, data):"]
        + [f"        # line {i}" for i in range(432, 510)]
    ),

    "src/compliance/audit_log.py": "\n".join(
        [f"# line {i}" for i in range(1, 25)]
        + ["class AuditLogger:"]
        + [f"    # line {i}" for i in range(27, 80)]
        + ["    def log_event(self, event):"]
        + [f"        # line {i}" for i in range(82, 130)]
        + ["    def query_logs(self, filters):"]
        + [f"        # line {i}" for i in range(132, 170)]
    ),

    # ── gateway module ──────────────────────────────────────────────────────
    "src/gateway/__init__.py": """\
from .api import GatewayAPI
from .auth import AuthManager
from .router import PaymentRouter
""",

    "src/gateway/api.py": "\n".join(
        [f"# line {i}" for i in range(1, 80)]
        + ["class GatewayAPI:"]
        + [f"    # line {i}" for i in range(82, 200)]
        + ["    def handle_request(self, request):"]
        + [f"        # line {i}" for i in range(202, 350)]
        + ["    def authenticate(self, credentials):"]
        + [f"        # line {i}" for i in range(352, 470)]
        + ["    def rate_limit(self, client_id):"]
        + [f"        # line {i}" for i in range(472, 560)]
        + ["    def healthcheck(self):"]
        + [f"        # line {i}" for i in range(562, 590)]
    ),

    "src/gateway/auth.py": "\n".join(
        [f"# line {i}" for i in range(1, 30)]
        + ["class AuthManager:"]
        + [f"    # line {i}" for i in range(32, 100)]
        + ["    def verify_token(self, token):"]
        + [f"        # line {i}" for i in range(102, 160)]
        + ["    def revoke_token(self, token_id):"]
        + [f"        # line {i}" for i in range(162, 200)]
    ),

    "src/gateway/router.py": "\n".join(
        [f"# line {i}" for i in range(1, 20)]
        + ["class PaymentRouter:"]
        + [f"    # line {i}" for i in range(22, 70)]
        + ["    def route(self, txn):"]
        + [f"        # line {i}" for i in range(72, 120)]
    ),

    # ── config & main ───────────────────────────────────────────────────────
    "src/config.py": """\
DATABASE_URL = "postgresql://localhost/paygate"
FRAUD_THRESHOLD = 0.85
MAX_TRANSACTION_AMOUNT = 50000
CURRENCY_WHITELIST = ["USD", "EUR", "GBP"]
LOG_LEVEL = "INFO"
""",

    "src/main.py": """\
from gateway.api import GatewayAPI
from transaction.processor import TransactionProcessor
from fraud.detector import FraudDetector
from compliance.reporter import ComplianceReporter

def main():
    api = GatewayAPI()
    api.start()

if __name__ == "__main__":
    main()
""",

    # ── distractor files ────────────────────────────────────────────────────
    "tests/test_transaction.py": "# unit tests placeholder\n",
    "tests/test_fraud.py": "# fraud tests placeholder\n",
    "tests/test_compliance.py": "# compliance tests placeholder\n",
    "tests/conftest.py": "import pytest\n",
    "scripts/migrate_db.py": "# DB migration script\n",
    "scripts/seed_data.py": "# Seed script\n",
    "docs/api_spec.md": "# API Specification\nSee swagger for details.\n",
    "Makefile": "test:\n\tpytest tests/\n",
    "requirements.txt": "fastapi\npsycopg2\npydantic\n",
    "pyproject.toml": "[tool.poetry]\nname = \"paygate\"\nversion = \"0.1.0\"\n",
}

for rel, content in src_files.items():
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# ─── .agentlens documentation ─────────────────────────────────────────────────

AL = os.path.join(BASE, ".agentlens")

# INDEX.md
os.makedirs(AL, exist_ok=True)
with open(os.path.join(AL, "INDEX.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # PayGate — Project Map

    ## Project Description
    PayGate is a high-throughput payment gateway backend responsible for transaction
    processing, fraud detection, and regulatory compliance reporting.

    ## Modules

    | Slug | Path | Description |
    |------|------|-------------|
    | transaction | src/transaction/ | Core transaction lifecycle: validation, processing, rollback |
    | fraud | src/fraud/ | Real-time fraud detection using ML rules and risk scoring |
    | compliance | src/compliance/ | Regulatory reporting and immutable audit logging |
    | gateway | src/gateway/ | Public API surface: routing, auth, rate limiting |

    ## Entry Points
    - `src/main.py` — Application bootstrap

    ## Hub Files (heavily imported)
    - `src/transaction/models.py` — Imported by fraud, compliance, gateway
    - `src/config.py` — Imported by all modules

    ## High-Priority Warnings
    - ⚠️  SAFETY: `TransactionProcessor.rollback` must never be called without a compensating audit log entry (see fraud/memory.md)
    - ⚠️  WARNING: `ComplianceReporter.submit_to_regulator` is DEPRECATED — use `generate_report` + manual submission
    - ⚠️  FIXME: Race condition in `FraudDetector.update_model` under concurrent load (see fraud/memory.md)
    """))

# AGENT.md
with open(os.path.join(AL, "AGENT.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Agent Instructions
    Always read INDEX.md before exploring any module.
    Follow the hierarchy: INDEX → MODULE → outline/memory → source.
    Do not skip memory.md before suggesting code changes.
    """))

# ── transaction module docs ──────────────────────────────────────────────────
TXN_MOD = os.path.join(AL, "modules", "transaction")
os.makedirs(TXN_MOD, exist_ok=True)

with open(os.path.join(TXN_MOD, "MODULE.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Module: transaction

    ## Purpose
    Manages the full lifecycle of a payment transaction: creation, validation,
    fee application, processing, and rollback.

    ## Files

    | File | Lines | Description |
    |------|-------|-------------|
    | processor.py | 560 | Main orchestrator — large file, see outline.md |
    | validator.py | 190 | Input validation and limit enforcement |
    | models.py | 18 | Core data models: Transaction, TransactionStatus |

    ## Language
    Python 3.11
    """))

with open(os.path.join(TXN_MOD, "outline.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Outline: src/transaction/processor.py (560 lines)

    ## Classes

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | TransactionProcessor | class | 50 | public |

    ## Methods of TransactionProcessor

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | process | method | 111 | public |
    | rollback | method | 201 | public |
    | _validate_amount | method | 281 | private |
    | _apply_fees | method | 341 | private |
    | get_status | method | 421 | public |
    | batch_process | method | 511 | public |
    """))

with open(os.path.join(TXN_MOD, "memory.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Memory: transaction module

    ## TODOs
    - TODO (processor.py:115): Add idempotency key check before processing to prevent duplicate charges
    - TODO (validator.py:88): Extend `check_limits` to support per-merchant velocity limits

    ## WARNINGs
    - WARNING (processor.py:205): `rollback` assumes the downstream ledger is synchronous; async ledgers will cause data inconsistency

    ## SAFETY
    - SAFETY (processor.py:201): Every call to `rollback` MUST be preceded by a call to `AuditLogger.log_event` with event_type='PRE_ROLLBACK'

    ## FIXME
    - FIXME (processor.py:345): Fee calculation double-counts cross-currency conversion when both merchant and customer use non-USD currencies

    ## DEPRECATED
    - DEPRECATED (processor.py:421): `get_status` will be removed in v2; use the event-sourced `StatusProjection` instead
    """))

with open(os.path.join(TXN_MOD, "imports.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Imports: transaction module

    ## processor.py
    - imports: transaction/models.py (Transaction, TransactionStatus)
    - imports: transaction/validator.py (TransactionValidator)
    - imports: src/config.py (MAX_TRANSACTION_AMOUNT, CURRENCY_WHITELIST)
    - imported by: gateway/api.py
    - imported by: compliance/reporter.py

    ## validator.py
    - imports: transaction/models.py (Transaction)
    - imports: src/config.py (MAX_TRANSACTION_AMOUNT)
    - imported by: transaction/processor.py

    ## models.py
    - imports: (stdlib only)
    - imported by: transaction/processor.py, transaction/validator.py, fraud/detector.py, compliance/reporter.py, gateway/api.py
    """))

# ── fraud module docs ────────────────────────────────────────────────────────
FRAUD_MOD = os.path.join(AL, "modules", "fraud")
os.makedirs(FRAUD_MOD, exist_ok=True)

with open(os.path.join(FRAUD_MOD, "MODULE.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Module: fraud

    ## Purpose
    Real-time fraud detection pipeline. Combines ML-based risk scoring with a
    deterministic rule engine. Decisions are explainable via `explain_decision`.

    ## Files

    | File | Lines | Description |
    |------|-------|-------------|
    | detector.py | 530 | Orchestrates detection pipeline — large file, see outline.md |
    | rules.py | 160 | Configurable rule engine |
    | scorer.py | 100 | ML feature scoring |

    ## Language
    Python 3.11
    """))

with open(os.path.join(FRAUD_MOD, "outline.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Outline: src/fraud/detector.py (530 lines)

    ## Classes

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | FraudDetector | class | 41 | public |

    ## Methods of FraudDetector

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | detect | method | 131 | public |
    | update_model | method | 251 | public |
    | _load_patterns | method | 371 | private |
    | explain_decision | method | 481 | public |
    """))

with open(os.path.join(FRAUD_MOD, "memory.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Memory: fraud module

    ## TODOs
    - TODO (detector.py:135): Implement velocity-check feature (number of txns in last 60s per card)
    - TODO (rules.py:75): Add geographic anomaly rule for country-hop detection
    - TODO (scorer.py:65): Replace logistic regression scorer with gradient boosting model

    ## WARNINGs
    - WARNING (detector.py:255): `update_model` is NOT thread-safe; concurrent calls will corrupt the in-memory model weights

    ## FIXME
    - FIXME (detector.py:253): Race condition under concurrent load — model update and inference share the same lock-free data structure

    ## SAFETY
    - SAFETY (detector.py:131): `detect` must NEVER suppress a HIGH risk score solely based on merchant whitelist — whitelist only applies to MEDIUM scores
    - SAFETY (detector.py:481): `explain_decision` must log every call to the audit trail before returning — PCI-DSS requirement

    ## POLICY
    - POLICY (rules.py:122): New rules MUST be reviewed by the compliance team before activation (JIRA: PAY-449)

    ## DEPRECATED
    - DEPRECATED (detector.py:371): `_load_patterns` loads from flat file; will be replaced by streaming config in v2
    """))

with open(os.path.join(FRAUD_MOD, "imports.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Imports: fraud module

    ## detector.py
    - imports: fraud/rules.py (RuleEngine)
    - imports: fraud/scorer.py (RiskScorer)
    - imports: transaction/models.py (Transaction, TransactionStatus)
    - imports: src/config.py (FRAUD_THRESHOLD)
    - imported by: gateway/api.py

    ## rules.py
    - imports: src/config.py (FRAUD_THRESHOLD)
    - imported by: fraud/detector.py

    ## scorer.py
    - imports: (stdlib only)
    - imported by: fraud/detector.py
    """))

# ── compliance module docs ───────────────────────────────────────────────────
COMP_MOD = os.path.join(AL, "modules", "compliance")
os.makedirs(COMP_MOD, exist_ok=True)

with open(os.path.join(COMP_MOD, "MODULE.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Module: compliance

    ## Purpose
    Generates regulatory reports (SWIFT MT940, FinCEN SAR) and maintains an
    immutable append-only audit log for all system events.

    ## Files

    | File | Lines | Description |
    |------|-------|-------------|
    | reporter.py | 510 | Report generation and submission — large file, see outline.md |
    | audit_log.py | 170 | Immutable audit event storage |

    ## Language
    Python 3.11
    """))

with open(os.path.join(COMP_MOD, "outline.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Outline: src/compliance/reporter.py (510 lines)

    ## Classes

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | ComplianceReporter | class | 61 | public |

    ## Methods of ComplianceReporter

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | generate_report | method | 181 | public |
    | submit_to_regulator | method | 311 | public |
    | _format_for_swift | method | 431 | private |
    """))

with open(os.path.join(COMP_MOD, "memory.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Memory: compliance module

    ## TODOs
    - TODO (reporter.py:185): Add support for FinCEN SAR XML format (currently only MT940)
    - TODO (audit_log.py:85): Implement log rotation for entries older than 7 years

    ## WARNINGs
    - WARNING (reporter.py:315): `submit_to_regulator` makes a live HTTP call to the regulator's endpoint — do NOT call in test environments

    ## DEPRECATED
    - DEPRECATED (reporter.py:311): `submit_to_regulator` is deprecated — regulators now require manual portal submission; this method will be removed in v2

    ## SAFETY
    - SAFETY (audit_log.py:82): Audit log entries are IMMUTABLE — never update or delete rows; insert-only pattern enforced at DB level

    ## RULE
    - RULE (reporter.py:181): Reports MUST cover a complete calendar month — partial-month reports will be rejected by regulators
    """))

with open(os.path.join(COMP_MOD, "imports.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Imports: compliance module

    ## reporter.py
    - imports: transaction/models.py (Transaction, TransactionStatus)
    - imports: transaction/processor.py (TransactionProcessor)
    - imports: compliance/audit_log.py (AuditLogger)
    - imports: src/config.py (LOG_LEVEL)
    - imported by: src/main.py

    ## audit_log.py
    - imports: src/config.py (DATABASE_URL, LOG_LEVEL)
    - imported by: compliance/reporter.py
    - imported by: transaction/processor.py
    """))

# ── gateway module docs ──────────────────────────────────────────────────────
GW_MOD = os.path.join(AL, "modules", "gateway")
os.makedirs(GW_MOD, exist_ok=True)

with open(os.path.join(GW_MOD, "MODULE.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Module: gateway

    ## Purpose
    Exposes the public HTTP API. Handles request routing, authentication token
    verification, and client-level rate limiting.

    ## Files

    | File | Lines | Description |
    |------|-------|-------------|
    | api.py | 590 | Main API handler — large file, see outline.md |
    | auth.py | 200 | JWT token verification and revocation |
    | router.py | 120 | Payment routing logic |

    ## Language
    Python 3.11
    """))

with open(os.path.join(GW_MOD, "outline.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Outline: src/gateway/api.py (590 lines)

    ## Classes

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | GatewayAPI | class | 81 | public |

    ## Methods of GatewayAPI

    | Symbol | Kind | Line | Visibility |
    |--------|------|------|------------|
    | handle_request | method | 201 | public |
    | authenticate | method | 351 | public |
    | rate_limit | method | 471 | public |
    | healthcheck | method | 561 | public |
    """))

with open(os.path.join(GW_MOD, "memory.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Memory: gateway module

    ## TODOs
    - TODO (api.py:210): Implement request body size limit (currently unbounded — DoS risk)
    - TODO (auth.py:105): Rotate signing keys automatically on a 90-day schedule

    ## WARNINGs
    - WARNING (api.py:355): `authenticate` falls back to legacy HMAC if JWT fails — legacy path will be removed in v2; do not extend it

    ## FIXME
    - FIXME (api.py:475): Rate limiter uses in-process state; not effective in multi-process deployments

    ## SAFETY
    - SAFETY (api.py:201): `handle_request` MUST call `rate_limit` before `authenticate` — reversing the order creates an auth-bypass vector

    ## DEPRECATED
    - DEPRECATED (auth.py:162): `revoke_token` stores revoked tokens in-memory; tokens survive process restarts — use Redis-backed revocation in v2
    """))

with open(os.path.join(GW_MOD, "imports.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Imports: gateway module

    ## api.py
    - imports: gateway/auth.py (AuthManager)
    - imports: gateway/router.py (PaymentRouter)
    - imports: transaction/processor.py (TransactionProcessor)
    - imports: fraud/detector.py (FraudDetector)
    - imports: src/config.py (LOG_LEVEL)
    - imported by: src/main.py

    ## auth.py
    - imports: src/config.py (LOG_LEVEL)
    - imported by: gateway/api.py

    ## router.py
    - imports: transaction/models.py (Transaction)
    - imports: src/config.py (CURRENCY_WHITELIST)
    - imported by: gateway/api.py
    """))

# ── L2 file docs ─────────────────────────────────────────────────────────────
FILES_DIR = os.path.join(AL, "files")
os.makedirs(FILES_DIR, exist_ok=True)

with open(os.path.join(FILES_DIR, "transaction--processor.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Deep Docs: src/transaction/processor.py

    ## TransactionProcessor

    Central orchestrator for payment transactions. Coordinates validation,
    fee calculation, downstream ledger writes, and rollback compensation.

    ### Critical Design Notes
    - Uses an optimistic locking strategy on the `Transaction` row.
    - The `_apply_fees` method must complete atomically with the ledger write.
    - Rollback is a compensating transaction, NOT a database rollback.

    ### process (line 111)
    Validates → applies fees → writes to ledger → emits event.
    Idempotency key check is PENDING (see memory.md TODO).

    ### rollback (line 201)
    Issues a compensating credit. Caller MUST log PRE_ROLLBACK event first.
    WARNING: synchronous ledger assumption — see memory.md.

    ### _apply_fees (line 341)
    FIXME: double-counts cross-currency fees (see memory.md).
    """))

with open(os.path.join(FILES_DIR, "fraud--detector.md"), "w") as f:
    f.write(textwrap.dedent("""\
    # Deep Docs: src/fraud/detector.py

    ## FraudDetector

    Three-stage pipeline: pattern loading → rule evaluation → ML scoring.

    ### detect (line 131)
    SAFETY: HIGH risk scores are never suppressible by merchant whitelist.
    Returns a FraudDecision with risk_level and explanation_id.

    ### update_model (line 251)
    NOT thread-safe. Wrap calls in an external distributed lock.
    FIXME: race condition with lock-free data structure.

    ### explain_decision (line 481)
    MUST log to audit trail before returning (PCI-DSS).
    """))

print("Workspace generated successfully.")
print(f"Source files: {len(src_files)}")
print("AgentLens docs: .agentlens/INDEX.md, modules/*, files/*")