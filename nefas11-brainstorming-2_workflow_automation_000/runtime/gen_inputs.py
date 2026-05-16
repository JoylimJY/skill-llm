import os
import random
from pathlib import Path
from datetime import date

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "src/fraud_engine/detectors",
    "src/fraud_engine/models",
    "src/fraud_engine/utils",
    "src/api/routes",
    "src/api/middleware",
    "tests/unit",
    "tests/integration",
    "config/environments",
    "scripts/migrations",
    "docs/adr",
    "docs/runbooks",
    "docs/design",  # exists but empty - agent must place file here
    ".github/workflows",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor source files ---
distractor_files = {
    "src/fraud_engine/detectors/velocity_check.py": """\
# Velocity check detector
# Checks transaction rate per user

class VelocityDetector:
    def __init__(self, window_seconds=60, max_tx=10):
        self.window = window_seconds
        self.max_tx = max_tx

    def check(self, user_id, transactions):
        recent = [t for t in transactions if t['age'] < self.window]
        return len(recent) > self.max_tx
""",
    "src/fraud_engine/detectors/geo_check.py": """\
# Geo anomaly detector
# Flags impossible travel scenarios

class GeoDetector:
    EARTH_RADIUS_KM = 6371

    def check(self, tx1, tx2):
        pass  # TODO: implement haversine
""",
    "src/fraud_engine/models/transaction.py": """\
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    id: str
    user_id: str
    amount: float
    currency: str
    merchant_id: str
    timestamp: datetime
    country_code: str
""",
    "src/fraud_engine/models/alert.py": """\
# Alert model - placeholder
# Not yet implemented
class Alert:
    pass
""",
    "src/fraud_engine/utils/scoring.py": """\
def compute_risk_score(signals: list[float]) -> float:
    if not signals:
        return 0.0
    return sum(signals) / len(signals)
""",
    "src/api/routes/transactions.py": """\
from flask import Blueprint, request, jsonify

bp = Blueprint('transactions', __name__)

@bp.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    # TODO: run fraud checks
    return jsonify({'status': 'pending'}), 202
""",
    "src/api/middleware/auth.py": """\
# JWT auth middleware
# Not fully implemented
def require_auth(f):
    return f
""",
    "tests/unit/test_velocity.py": """\
import pytest
from src.fraud_engine.detectors.velocity_check import VelocityDetector

def test_velocity_over_limit():
    det = VelocityDetector(window_seconds=60, max_tx=3)
    txs = [{'age': i * 5} for i in range(5)]
    assert det.check('user1', txs) is True
""",
    "tests/integration/test_api.py": """\
# Integration tests for fraud API
# Requires running server

def test_placeholder():
    pass
""",
    "config/environments/production.yaml": """\
database:
  host: prod-db.internal
  port: 5432
  name: fraud_db
redis:
  host: prod-redis.internal
  port: 6379
kafka:
  brokers:
    - kafka-1.internal:9092
    - kafka-2.internal:9092
""",
    "config/environments/staging.yaml": """\
database:
  host: staging-db.internal
  port: 5432
  name: fraud_db_staging
redis:
  host: staging-redis.internal
  port: 6379
""",
    "scripts/migrations/001_create_transactions.sql": """\
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    amount DECIMAL(20,4) NOT NULL,
    currency CHAR(3) NOT NULL,
    merchant_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
""",
    "docs/adr/001-use-kafka-for-events.md": """\
# ADR 001: Use Kafka for Event Streaming

## Status
Accepted

## Context
We need reliable event streaming between fraud engine and downstream services.

## Decision
Use Apache Kafka.

## Consequences
- Requires Kafka cluster management
- Enables high-throughput event processing
""",
    "docs/runbooks/incident-response.md": """\
# Incident Response Runbook

## Alert Triage
1. Check Grafana dashboard
2. Review recent deployments
3. Escalate if P1

## Contacts
- On-call: pagerduty
""",
    ".github/workflows/ci.yml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest tests/
""",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- THE CORE INPUT: Messy stakeholder interview notes ---
# This is the raw, unstructured data the agent must synthesize
today = date.today().isoformat()

interview_notes = f"""\
STAKEHOLDER INTERVIEW NOTES - Transaction Anomaly Alerting Feature
Collected: {today}
Interviewer: Product Lead (Maya Chen)
Attendees: Backend Lead (Raj Patel), Compliance Officer (Sandra Wu), CTO (James Okafor)

=== RAW NOTES (unedited) ===

Maya: So we've been getting complaints from the ops team that fraud events are just going into a log somewhere and nobody's notified in real time. What's the actual problem we're solving here?

Raj: Right so right now when the fraud engine flags a transaction it writes to the fraud_events table and... that's it. Nobody gets pinged. The ops team has to manually query the DB every morning. We've missed two high-value fraud cases last month because of this.

Sandra: From compliance perspective we need alerts within 5 minutes of detection for anything above $10,000. That's a regulatory requirement now per our new licensing agreement.

James: The bigger picture - we want customers notified too, not just ops. Eventually. But first things first.

Maya: What counts as success here?

Raj: Ops team gets a Slack/email ping within 5 min of a high-risk flag. We can query alert history. Nothing falls through the cracks.

Sandra: Audit log of all alerts sent. Regulators will ask.

James: Don't break existing fraud detection pipeline. It's stable. Build around it.

=== APPROACH DISCUSSION ===

Three options came up in the meeting:

OPTION A - Simple webhook: Add a webhook call directly inside the existing VelocityDetector and GeoDetector classes. Whenever they return True (fraud flagged), hit a Slack webhook URL. Fast to build, maybe 1-2 days. Problem: hard to add new notification channels later, detectors become coupled to alerting logic, no retry mechanism.

OPTION B - Event-driven alerting service: Write fraud flags to Kafka (already in infra). New AlertService consumes fraud_events topic, handles deduplication, retries, and fan-out to multiple channels (Slack, email, SMS later). Solid pattern, 1-2 weeks. Complexity: need to manage consumer group, offset tracking, service deployment.

OPTION C - Polling alert worker + notification abstraction layer: Scheduled worker polls fraud_events table every 30 seconds, NotificationRouter dispatches to registered handlers. Simpler than Kafka consumer, still decoupled, 3-5 days. Tradeoff: 30-second polling lag might violate Sandra's 5-min SLA only if queue backs up badly.

James picked Option B. "We already have Kafka. Use it. Do it right."

=== COMPONENTS DISCUSSION ===

Raj listed what changes:
- fraud_engine/detectors: no changes needed (they already write to fraud_events table)
- New AlertService: new microservice, consumes Kafka fraud_events topic
- NotificationRouter (inside AlertService): dispatches to Slack, email handlers
- Database: new alert_log table for audit trail
- API: new GET /alerts endpoint for ops dashboard query

Sandra wants edge cases covered:
- Duplicate alerts if Kafka message replayed (idempotency key needed)
- What if Slack is down? Need retry with backoff.
- Alert for same transaction shouldn't fire twice even if two detectors flag it.
- Very high volume scenarios - don't alert-storm ops team (rate limit per user maybe?)

Testing discussion:
- Unit: AlertService message parsing, NotificationRouter dispatch logic, deduplication logic
- Integration: Full flow from fraud_events Kafka message to Slack notification delivery (use test Kafka + mock Slack)

Success criteria agreed:
- Ops team receives Slack notification within 5 minutes of fraud flag
- All alerts persisted in alert_log table with timestamp and transaction ID
- No duplicate alerts for same transaction ID
- System handles Slack downtime gracefully (retry + dead-letter)
- GET /alerts endpoint returns paginated alert history

=== END OF NOTES ===
"""

(workspace / "docs" / "stakeholder-interview-notes.txt").write_text(interview_notes)

# A deliberately misleading partial draft that's wrong/incomplete
partial_draft = """\
# Feature: Real-time Alerts

This feature adds alerting capabilities.

We will use Kafka.

TODO: fill in details
TODO: figure out components
TODO: ask Sandra about compliance stuff
"""

(workspace / "docs" / "design" / "DRAFT-do-not-use.md").write_text(partial_draft)

print("Workspace generated successfully.")
print(f"Today's date: {today}")