import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic directory structure with distractors ---
dirs = [
    "src/payments",
    "src/auth",
    "src/notifications",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "docs/architecture",
    "infra/terraform",
    "infra/docker",
    "scripts/db",
    "memory",  # memory dir already exists but may be empty/partial
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files (realistic fintech project) ---
distractor_files = {
    "src/payments/transaction.py": """\
class Transaction:
    def __init__(self, tx_id, amount, currency):
        self.tx_id = tx_id
        self.amount = amount
        self.currency = currency

    def validate(self):
        return self.amount > 0 and self.currency in ['USD', 'EUR', 'GBP']
""",
    "src/payments/processor.py": """\
import logging

logger = logging.getLogger(__name__)

def process_payment(transaction):
    if not transaction.validate():
        raise ValueError("Invalid transaction")
    logger.info(f"Processing {transaction.tx_id}")
    return {"status": "pending", "tx_id": transaction.tx_id}
""",
    "src/auth/jwt_handler.py": """\
import hashlib

def generate_token(user_id: str, secret: str) -> str:
    return hashlib.sha256(f"{user_id}:{secret}".encode()).hexdigest()

def verify_token(token: str, user_id: str, secret: str) -> bool:
    expected = generate_token(user_id, secret)
    return token == expected
""",
    "src/notifications/email_sender.py": """\
def send_notification(email: str, subject: str, body: str):
    print(f"[MOCK] Sending email to {email}: {subject}")
    return True
""",
    "tests/unit/test_transaction.py": """\
import pytest
# from src.payments.transaction import Transaction

def test_valid_transaction():
    # tx = Transaction('tx001', 100.0, 'USD')
    # assert tx.validate() == True
    pass

def test_invalid_amount():
    # tx = Transaction('tx002', -5.0, 'USD')
    # assert tx.validate() == False
    pass
""",
    "tests/integration/test_processor.py": """\
# Integration tests for payment processor
# Requires running MongoDB instance
def test_processor_integration():
    pass
""",
    "docs/api/openapi.yaml": """\
openapi: 3.0.0
info:
  title: FinPay API
  version: 2.1.0
paths:
  /payments:
    post:
      summary: Create payment
      requestBody:
        required: true
""",
    "docs/architecture/system_overview.md": """\
# System Architecture

## Overview
FinPay processes transactions using a microservices approach.

## Components
- Payment Service
- Auth Service  
- Notification Service
""",
    "infra/terraform/main.tf": """\
terraform {
  required_version = ">= 1.0"
}

resource "aws_instance" "app_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
}
""",
    "infra/docker/docker-compose.yml": """\
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
""",
    "scripts/db/migrate_postgres_to_mongo.py": """\
#!/usr/bin/env python3
\"\"\"
Migration script: PostgreSQL -> MongoDB
Completed: 2026-07-14
Engineer: Sarah Chen
\"\"\"

import json

def migrate_transactions():
    print("Migration completed successfully")
    print("Records migrated: 2,847,391")
    print("Validation: PASSED")
    return True

if __name__ == "__main__":
    migrate_transactions()
""",
    "scripts/db/rollback.py": """\
#!/usr/bin/env python3
\"\"\"Rollback script - NOT EXECUTED - kept for safety\"\"\"

def rollback():
    print("Rollback procedure available but not needed")
""",
    ".env.example": """\
DATABASE_URL=mongodb://localhost:27017/finpay
JWT_SECRET=your-secret-here
NOTIFICATION_SERVICE_URL=http://notifications:8081
""",
    "README.md": """\
# FinPay Transaction Service

A high-throughput payment processing microservice.

## Stack
- Python 3.11
- MongoDB 6.0 (migrated from PostgreSQL 14 on 2026-07-14)
- FastAPI

## Setup
See docs/ for full setup instructions.
""",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- CREATE THE PROBLEM: Messy/partial existing memory files ---
# MEMORY.md exists but is outdated and messy - agent must update it
today = date.today()
yesterday = today - timedelta(days=1)
two_days_ago = today - timedelta(days=2)

memory_md_content = f"""\
# MEMORY.md - AI Assistant Shared Memory

## 🎯 Active Projects
| Project | Status | Links | Last Updated |
|---------|--------|-------|--------------|
| FinPay DB Migration | 🟡 In Progress | [Migration Script](/scripts/db/migrate_postgres_to_mongo.py) | {two_days_ago.strftime('%Y-%m-%d')} |
| FinPay Auth Refactor | 🔴 Blocked | [JWT Handler](/src/auth/jwt_handler.py) | {two_days_ago.strftime('%Y-%m-%d')} |
| FinPay Notification Service | ⚪ Planned | | {two_days_ago.strftime('%Y-%m-%d')} |

## 👤 User Preferences
| Aspect | Preference |
|--------|------------|
| Communication | Direct, concise |
| Code Style | PEP8, type hints preferred |
| Documentation | Update memory files after every session |

## 📚 Important Decisions
### {two_days_ago.strftime('%Y-%m-%d')}
- **Decision:** Use MongoDB 6.0 as the target database for migration
- **Reason:** Better horizontal scaling for transaction volume

### {(two_days_ago - timedelta(days=5)).strftime('%Y-%m-%d')}
- **Decision:** Adopt FastAPI over Flask for new endpoints
- **Reason:** Native async support and automatic OpenAPI generation
"""

(workspace / "MEMORY.md").write_text(memory_md_content)

# MEMORY_INDEX.md exists but is also outdated
memory_index_content = f"""\
# MEMORY_INDEX.md - Quick Reference

## 📊 Project Status Overview
| Project | Status | Owner | Priority |
|---------|--------|-------|----------|
| FinPay DB Migration | 🟡 In Progress | Sarah Chen | HIGH |
| FinPay Auth Refactor | 🔴 Blocked | TBD | MEDIUM |
| FinPay Notification Service | ⚪ Planned | TBD | LOW |

## 🔗 Key Links
- [Migration Script](/scripts/db/migrate_postgres_to_mongo.py)
- [API Docs](/docs/api/openapi.yaml)
- [System Overview](/docs/architecture/system_overview.md)

## 📅 Last Updated
{two_days_ago.strftime('%Y-%m-%d')} by Claude
"""

(workspace / "MEMORY_INDEX.md").write_text(memory_index_content)

# Yesterday's session log exists (partial context)
yesterday_log_path = workspace / "memory" / f"{yesterday.strftime('%Y-%m-%d')}.md"
yesterday_log_content = f"""\
# {yesterday.strftime('%Y-%m-%d')}

## Completed
- Reviewed migration script logic with Sarah
- Validated data integrity checks in migrate_postgres_to_mongo.py
- Confirmed rollback script is in place as safety net

## In Progress
- Final dry-run of migration on staging environment
- Awaiting sign-off from DevOps team

## Notes
- Migration ready to execute pending final approval
- All 2,847,391 historical transaction records need to be migrated
- MongoDB connection string confirmed working in staging
- DevOps sign-off expected tomorrow morning
"""
yesterday_log_path.write_text(yesterday_log_content)

# Older log for additional context
older_log_path = workspace / "memory" / f"{two_days_ago.strftime('%Y-%m-%d')}.md"
older_log_content = f"""\
# {two_days_ago.strftime('%Y-%m-%d')}

## Completed
- Set up MongoDB 6.0 instance in staging
- Wrote initial migration script skeleton
- Defined data schema mapping (PostgreSQL tables -> MongoDB collections)

## In Progress
- Migration script implementation

## Notes
- PostgreSQL had 3 main tables: transactions, users, audit_log
- MongoDB will use collections: transactions, users, audit_events
"""
older_log_path.write_text(older_log_content)

# NOTE: No today's log exists yet — agent must create it
today_log_path = workspace / "memory" / f"{today.strftime('%Y-%m-%d')}.md"
assert not today_log_path.exists(), "Today's log should NOT exist yet"

print(f"Workspace generated successfully.")
print(f"Today's date: {today.strftime('%Y-%m-%d')}")
print(f"Today's log path (should NOT exist): {today_log_path}")
print(f"Files created: {len(distractor_files)} distractor files")