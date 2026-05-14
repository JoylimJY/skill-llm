import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# --- Directory Structure ---
dirs = [
    "legacy/payment_core",
    "legacy/payment_core/tests",
    "legacy/payment_core/utils",
    "legacy/payment_core/adapters",
    "legacy/audit_logs",
    "legacy/audit_logs/2022",
    "legacy/audit_logs/2023",
    "legacy/audit_logs/2024",
    "docs/meeting_notes",
    "docs/specs",
    "docs/diagrams_stubs",
    "infra/ci",
    "infra/monitoring",
    "infra/monitoring/alerts",
    "scripts/migration",
    "scripts/rollback",
    "team/onboarding",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- DISTRACTOR FILES (realistic but irrelevant) ---
distractors = {
    "legacy/payment_core/charge.py": """\
# charge.py - core charging logic
# Last touched: 2021-03-14 by @dave
import stripe
from .utils import retry, log_transaction

STRIPE_MAX_RETRIES = 3

def charge_card(amount, currency, token):
    for attempt in range(STRIPE_MAX_RETRIES):
        try:
            result = stripe.Charge.create(amount=amount, currency=currency, source=token)
            log_transaction(result)
            return result
        except stripe.error.RateLimitError:
            retry(attempt)
    raise RuntimeError("Charge failed after retries")
""",
    "legacy/payment_core/refund.py": """\
# refund.py - BROKEN: uses deprecated stripe v2 API
# TODO: migrate to PaymentIntent-based refunds
def process_refund(charge_id, amount=None):
    import stripe
    # BUG: partial refunds silently drop cents due to int truncation
    amt = int(amount) if amount else None
    return stripe.Refund.create(charge=charge_id, amount=amt)
""",
    "legacy/payment_core/utils/retry.py": """\
import time, random
def retry(attempt, base=1.5):
    time.sleep(base ** attempt + random.uniform(0, 0.5))
""",
    "legacy/payment_core/utils/log_transaction.py": """\
import json, datetime
LOG_FILE = "/var/log/payments/transactions.log"
def log_transaction(result):
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps({'ts': str(datetime.datetime.utcnow()), 'id': result.get('id')}) + '\\n')
""",
    "legacy/payment_core/adapters/stripe_adapter.py": """\
# Adapter wrapping raw stripe SDK - partially migrated
# Status: 60% complete, blocked on PCI DSS review (ticket PAY-2241)
class StripeAdapter:
    def __init__(self, api_key):
        import stripe
        stripe.api_key = api_key

    def create_intent(self, amount, currency):
        import stripe
        return stripe.PaymentIntent.create(amount=amount, currency=currency)
""",
    "legacy/payment_core/adapters/braintree_adapter.py": """\
# Braintree adapter - ABANDONED 2023
# Do not use; kept for rollback reference only
class BraintreeAdapter:
    pass  # never implemented
""",
    "legacy/payment_core/tests/test_charge.py": """\
# WARNING: 0% coverage on refund.py, 12% on charge.py
import pytest
def test_charge_happy_path():
    pass  # stub - not implemented

def test_refund_partial():
    pass  # BUG: int truncation not tested
""",
    "legacy/audit_logs/2022/pci_scan_2022_q4.txt": """\
PCI DSS Scan - Q4 2022
FAIL: TLS 1.0 still enabled on payment endpoint
FAIL: Refund endpoint lacks idempotency key support
PASS: Tokenization layer compliant
NOTE: Re-scan required within 90 days
""",
    "legacy/audit_logs/2023/pci_scan_2023_q2.txt": """\
PCI DSS Scan - Q2 2023
FAIL: Refund endpoint idempotency still not fixed (carry-over from Q4 2022)
FAIL: Logging PII in transaction logs (charge.py line 9)
PASS: TLS 1.0 disabled
WARN: stripe SDK pinned to v2.x; EOL announced for Dec 2024
""",
    "legacy/audit_logs/2024/pci_scan_2024_q1.txt": """\
PCI DSS Scan - Q1 2024
FAIL: stripe SDK v2 EOL in 45 days - CRITICAL
FAIL: Refund int-truncation bug causes <$0.01 discrepancies in 0.3% of txns
FAIL: No rollback procedure documented for payment module
PASS: Idempotency keys added to charge.py (fixed Q2 2023)
WARN: test coverage payment_core < 15%
""",
    "docs/meeting_notes/arch_review_kickoff_2024-09-02.txt": """\
Attendees: @sarah (Eng Lead), @mike (Backend), @priya (Compliance), @tom (QA)

Discussion:
- stripe SDK must be upgraded before Dec 2024 or we lose payment processing capability
- refund int-truncation: finance found $2,300 in discrepancies over 18 months
- rollback plan: none exists, @mike says "we'd have to redeploy manually"
- test coverage: tom says 15% is not acceptable, needs 60% before release
- @priya: PCI audit scheduled Nov 15, 2024 - hard deadline
- @sarah: proposed 3-phase plan but not documented yet

Action Items (unresolved):
- someone needs to own the stripe upgrade
- write rollback runbook
- get coverage to 60%
- priya needs compliance sign-off checklist
""",
    "docs/meeting_notes/eng_standup_2024-09-10.txt": """\
Quick notes:
- mike started stripe SDK v3 spike, says 2 days to assess breaking changes
- tom: still no test plan
- sarah: remind everyone friday deadline is the arch review presentation
- open question: do we split the refund fix from the SDK upgrade or bundle?
""",
    "docs/specs/payment_module_original_spec_2021.txt": """\
[ORIGINAL SPEC - 2021 - LARGELY STALE]
Payment Module v1
- Supports: Stripe, Braintree (future)
- Refunds: full only (partial added ad-hoc in 2022 without spec update)
- No SLA defined
- No rollback procedure
- Owner: @dave (left company 2023)
""",
    "docs/specs/stripe_v3_migration_notes_draft.txt": """\
DRAFT - DO NOT DISTRIBUTE
stripe v2 -> v3 breaking changes (partial list from mike's spike):
1. stripe.Charge.create() removed -> use PaymentIntent
2. stripe.Refund.create() params changed: charge_id -> payment_intent
3. Currency handling: v3 uses decimal not integer cents (breaking for refund.py)
4. Webhook signature verification now mandatory
5. Test mode key format changed (sk_test_ prefix still valid but new endpoints)

Risk: refund.py int-truncation bug interacts badly with v3 decimal handling
Estimated effort: 5-8 days for core migration + 3 days testing
""",
    "docs/diagrams_stubs/payment_flow.txt": """\
[TEXT STUB - diagram tool unavailable]
charge_card() -> StripeAdapter.create_intent() [PARTIAL]
                OR stripe.Charge.create() [LEGACY, EOL]
log_transaction() -> /var/log/payments/transactions.log [CONTAINS PII - BUG]
process_refund() -> stripe.Refund.create() [DEPRECATED API]
""",
    "infra/ci/pipeline.yml": """\
stages:
  - test
  - lint
  - deploy

test:
  script:
    - pytest legacy/payment_core/tests/ --cov=legacy/payment_core --cov-fail-under=15
  # TODO: raise coverage threshold once tests are written

deploy:
  script:
    - ./scripts/deploy.sh
  only:
    - main
""",
    "infra/monitoring/alerts/payment_errors.yml": """\
alerts:
  - name: RefundFailureSpike
    condition: refund_error_rate > 0.5%
    severity: P1
    owner: unassigned  # @dave left, nobody picked this up

  - name: StripeSDKDeprecationWarning
    condition: stripe_sdk_version == 'v2'
    severity: P0
    owner: unassigned
    note: "Will become hard failure after Dec 2024"
""",
    "scripts/migration/stripe_v3_migrate.sh": """\
#!/bin/bash
# STUB - not implemented
# Intended to run automated migration of stripe API calls
echo "TODO: implement migration script"
exit 1
""",
    "scripts/rollback/rollback_payment.sh": """\
#!/bin/bash
# STUB - no rollback procedure defined
echo "ERROR: No rollback procedure documented. Contact @dave (no longer at company)."
exit 1
""",
    "team/onboarding/payment_module_onboarding.txt": """\
Welcome to the payments team.
The payment module lives in legacy/payment_core/.
Primary contact was @dave, who left in 2023.
There is no current documented owner.
Key risk: stripe SDK upgrade is overdue.
Good luck.
""",
    "infra/monitoring/dashboard_stub.txt": """\
Grafana dashboard URL: [INTERNAL - not accessible externally]
Key metrics: charge_success_rate, refund_error_rate, sdk_version_gauge
Last updated: 2023-11-01 (stale)
""",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- PRIMARY INPUT: Messy engineer notes that the agent must process ---
messy_notes = """\
=== PAYMENT MODULE REFACTOR - RAW NOTES (Sarah, Eng Lead) ===
date: september 2024, pulling this together before friday

ok so here's the mess:
stripe sdk v2 is dying in december. mike says 2 days to scope the work, 5-8 days to do it.
we have a refund bug that's been bleeding money for 18 months - finance is mad
the int truncation thing in refund.py interacts BADLY with the v3 decimal change mike found
test coverage is a joke (15%), priya wants 60% before the nov audit
nobody owns the alert rules since dave left
there's literally no rollback plan. if we deploy and break payments, we are just... stuck
PCI audit is nov 15. that's the hard wall.
the braintree adapter is dead weight, probably safe to delete but need to confirm with @priya
log_transaction writes PII to disk - another PCI fail, needs a fix
we could do this in phases:
  phase 1: fix the refund bug + PII logging (low risk, self-contained)
  phase 2: stripe sdk v3 upgrade (medium risk, needs rollback plan)  
  phase 3: test coverage push to 60% (low risk but time consuming)
or we could bundle phases 1+2 together to reduce deployment count but that increases blast radius
risks i'm worried about:
  - breaking live payments during migration (catastrophic)
  - missing the nov 15 audit date
  - no rollback if phase 2 goes wrong
  - mike might be the only one who understands the stripe internals now
things i need in the output:
  - what to do TODAY vs this week
  - who owns each thing (need to assign: sarah=eng lead, mike=backend, tom=qa, priya=compliance)
  - what's the rollback if stripe migration breaks prod?
  - acceptance criteria so we know when we're done
  - what are we assuming that might be wrong?

i don't have time to clean this up properly, just need a real plan document by friday.
"""

with open(os.path.join(BASE, "docs/refactor_raw_notes.txt"), "w") as f:
    f.write(messy_notes)

print("Workspace generated successfully.")
print("Files created:")
for rel_path in list(distractors.keys()) + ["docs/refactor_raw_notes.txt"]:
    print(f"  {os.path.join(BASE, rel_path)}")