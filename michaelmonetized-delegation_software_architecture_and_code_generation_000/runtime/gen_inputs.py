import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "src/core",
    "src/services/payments",
    "src/services/notifications",
    "src/services/auth",
    "src/api/routes",
    "src/api/middleware",
    "src/models",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "docs",
    "config",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Architecture document (the single source of truth) ──────────────────────
arch_doc = textwrap.dedent("""\
# FinShield Platform — Architecture Document
Version: 2.4.1  |  Classification: INTERNAL

## System Overview
FinShield is a real-time financial compliance platform that ingests payment
events, enriches them with risk metadata, and routes them through a multi-stage
validation pipeline before settlement.

## Layered Architecture

### Layer 1 — API Gateway  (src/api/)
Responsibility: HTTP ingestion, authentication, rate-limiting.
Files: src/api/routes/*.py, src/api/middleware/*.py
Naming: kebab-case filenames, PascalCase handler classes, camelCase methods.

### Layer 2 — Service Layer  (src/services/)
Responsibility: Business logic.  Each service is a single-responsibility module.
Files: src/services/<domain>/<service-name>.py
Naming: kebab-case filenames, PascalCase class names, camelCase method names.
Rule: Services MUST NOT import from other services directly; use shared models.

### Layer 3 — Core Engine  (src/core/)
Responsibility: Orchestration, pipeline management, shared infrastructure.
Files: src/core/*.py
Naming: kebab-case filenames, PascalCase classes.

### Layer 4 — Models  (src/models/)
Responsibility: Typed data contracts (Pydantic).  No business logic allowed here.
Files: src/models/<entity>.py  (kebab-case)
Naming: PascalCase model classes.

### Layer 5 — Utilities  (src/utils/)
Responsibility: Pure, stateless helper functions with NO side-effects.
Files: src/utils/<concern>.py  (kebab-case)
Naming: camelCase function names.

## Existing Services Inventory
| Service File                              | Class               | Purpose                         |
|-------------------------------------------|---------------------|---------------------------------|
| src/services/payments/payment-processor.py | PaymentProcessor   | Charge initiation & settlement  |
| src/services/notifications/notifier.py    | Notifier            | Email/SMS dispatch              |
| src/services/auth/token-validator.py      | TokenValidator      | JWT verification                |

## Data Flow
HTTP Request → API Gateway → Core Orchestrator → Service Layer → Models → DB

## Changelog Policy
All structural changes MUST be recorded in CHANGELOG.md at the repo root.

## Pending Feature Request — TXN-099
### Feature: Transaction Risk Validator
Add a new service that:
1. Accepts a transaction payload (amount, currency, merchant_id, user_id).
2. Validates that `amount` is a positive float ≤ 50,000.
3. Validates that `currency` is an ISO 4217 three-letter code.
4. Validates that `merchant_id` and `user_id` are non-empty UUIDs.
5. Returns a typed `ValidationResult` model containing `is_valid` (bool),
   `errors` (list[str]), and `risk_score` (float 0.0–1.0, where amounts
   near the limit score higher).
6. The service must raise `ValueError` for completely malformed payloads.
7. The `ValidationResult` model must live in `src/models/`.
8. The service class must be named according to layer-2 naming rules.
9. Tests must be placed in the matching test directory.
""")

with open(os.path.join(WORKSPACE, "ARCHITECTURE.md"), "w") as f:
    f.write(arch_doc)

# ── Existing source files (distractors & context) ────────────────────────────
files = {
    "src/services/payments/payment-processor.py": textwrap.dedent("""\
        from src.models.payment import Payment
        from typing import Optional

        class PaymentProcessor:
            def initiateCharge(self, payment: Payment) -> bool:
                if payment.amount <= 0:
                    raise ValueError("Amount must be positive")
                return True

            def settle(self, payment_id: str) -> Optional[str]:
                return f"settled:{payment_id}"
        """),

    "src/services/notifications/notifier.py": textwrap.dedent("""\
        class Notifier:
            def sendEmail(self, recipient: str, subject: str, body: str) -> None:
                pass

            def sendSMS(self, phone: str, message: str) -> None:
                pass
        """),

    "src/services/auth/token-validator.py": textwrap.dedent("""\
        class TokenValidator:
            def validateToken(self, token: str) -> bool:
                return len(token) > 0
        """),

    "src/models/payment.py": textwrap.dedent("""\
        from pydantic import BaseModel

        class Payment(BaseModel):
            payment_id: str
            amount: float
            currency: str
            merchant_id: str
            user_id: str
        """),

    "src/core/orchestrator.py": textwrap.dedent("""\
        class Orchestrator:
            def dispatch(self, event: dict) -> None:
                pass
        """),

    "src/api/routes/transactions.py": textwrap.dedent("""\
        class TransactionRoute:
            def handleIncoming(self, payload: dict) -> dict:
                return {}
        """),

    "src/api/middleware/auth-middleware.py": textwrap.dedent("""\
        class AuthMiddleware:
            def applyAuth(self, request: dict) -> dict:
                return request
        """),

    "src/utils/currency-helpers.py": textwrap.dedent("""\
        def normalizeCurrency(code: str) -> str:
            return code.upper().strip()
        """),

    "src/utils/uuid-helpers.py": textwrap.dedent("""\
        import uuid

        def isValidUuid(value: str) -> bool:
            try:
                uuid.UUID(str(value))
                return True
            except ValueError:
                return False
        """),

    "config/settings.yaml": textwrap.dedent("""\
        environment: production
        max_transaction_amount: 50000
        supported_currencies_url: https://internal.finshield.io/currencies
        """),

    "scripts/run-migrations.sh": "#!/bin/bash\necho 'Running DB migrations...'\n",

    "tests/unit/test_payment_processor.py": textwrap.dedent("""\
        from src.services.payments.payment_processor import PaymentProcessor

        def test_initiate_charge_positive():
            pp = PaymentProcessor()
            assert pp.initiateCharge({'amount': 100}) is True
        """),

    "tests/integration/test_pipeline.py": textwrap.dedent("""\
        def test_pipeline_smoke():
            assert True
        """),

    "docs/api-reference.md": "# API Reference\nTBD\n",
}

for rel_path, content in files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── Intentionally missing: CHANGELOG.md, validation-result model, validator service ──
# The agent must create these from scratch after reading the architecture doc.

print("Workspace generated successfully.")
print(f"Files created: {len(files) + 1} (including ARCHITECTURE.md)")