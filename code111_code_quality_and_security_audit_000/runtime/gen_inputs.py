import os
import random

random.seed(42)

BASE = "/workspace"

# Directory structure
dirs = [
    "finpay/backend/api",
    "finpay/backend/models",
    "finpay/backend/utils",
    "finpay/backend/tests",
    "finpay/frontend/src/components",
    "finpay/frontend/src/services",
    "finpay/frontend/src/utils",
    "finpay/frontend/tests",
    "finpay/config",
    "finpay/scripts",
    "finpay/docs",
    "finpay/migrations",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ---- DISTRACTOR FILES ----

# 1. Clean migration file (distractor)
with open(os.path.join(BASE, "finpay/migrations/0001_initial.py"), "w") as f:
    f.write("""# Auto-generated migration
from db import Migration

class InitialMigration(Migration):
    def up(self):
        self.create_table('users', [
            ('id', 'INTEGER PRIMARY KEY'),
            ('email', 'TEXT UNIQUE'),
            ('created_at', 'TIMESTAMP'),
        ])

    def down(self):
        self.drop_table('users')
""")

# 2. Clean config file (distractor)
with open(os.path.join(BASE, "finpay/config/logging.yaml"), "w") as f:
    f.write("""version: 1
formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
root:
  level: INFO
  handlers: [console]
""")

# 3. Clean utility (distractor)
with open(os.path.join(BASE, "finpay/backend/utils/date_helpers.py"), "w") as f:
    f.write("""from datetime import datetime, timezone

def utc_now() -> datetime:
    \"\"\"Return current UTC datetime.\"\"\"
    return datetime.now(timezone.utc)

def format_iso(dt: datetime) -> str:
    \"\"\"Format datetime as ISO 8601 string.\"\"\"
    return dt.isoformat()
""")

# 4. Clean test (distractor)
with open(os.path.join(BASE, "finpay/backend/tests/test_date_helpers.py"), "w") as f:
    f.write("""import pytest
from finpay.backend.utils.date_helpers import utc_now, format_iso

def test_utc_now_returns_datetime():
    dt = utc_now()
    assert dt is not None

def test_format_iso_returns_string():
    from datetime import datetime, timezone
    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = format_iso(dt)
    assert result == '2024-01-15T10:30:00+00:00'
""")

# 5. Partial README in docs (distractor, not helpful)
with open(os.path.join(BASE, "finpay/docs/architecture.md"), "w") as f:
    f.write("""# FinPay Architecture

## Components
- Backend: Python/Flask REST API
- Frontend: React/TypeScript SPA
- Database: PostgreSQL

## Data Flow
User -> Frontend -> API Gateway -> Backend -> DB
""")

# 6. Package files (distractor)
with open(os.path.join(BASE, "finpay/config/requirements.txt"), "w") as f:
    f.write("""flask==3.0.0
psycopg2-binary==2.9.9
pytest==7.4.0
requests==2.31.0
""")

with open(os.path.join(BASE, "finpay/frontend/package.json"), "w") as f:
    f.write("""{
  "name": "finpay-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "axios": "^1.6.0"
  }
}
""")

# 7. Clean model file (distractor)
with open(os.path.join(BASE, "finpay/backend/models/transaction.py"), "w") as f:
    f.write("""from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Transaction:
    id: int
    user_id: int
    amount: Decimal
    currency: str
    created_at: datetime
    status: str

    def is_complete(self) -> bool:
        return self.status == 'completed'
""")

# 8. Clean JS utility (distractor)
with open(os.path.join(BASE, "finpay/frontend/src/utils/formatters.js"), "w") as f:
    f.write("""export const formatCurrency = (amount, currency = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

export const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
};
""")

# 9. Script (distractor)
with open(os.path.join(BASE, "finpay/scripts/deploy.sh"), "w") as f:
    f.write("""#!/bin/bash
set -euo pipefail
echo "Deploying FinPay..."
pip install -r config/requirements.txt
echo "Deployment complete."
""")

# 10. Clean frontend test (distractor)
with open(os.path.join(BASE, "finpay/frontend/tests/formatters.test.js"), "w") as f:
    f.write("""import { formatCurrency } from '../src/utils/formatters';

test('formats USD correctly', () => {
  expect(formatCurrency(1234.56)).toBe('$1,234.56');
});
""")

# ---- PROBLEM FILES (contain real issues to review) ----

# PROBLEM FILE 1: Python backend user controller with multiple critical issues
with open(os.path.join(BASE, "finpay/backend/api/user_controller.py"), "w") as f:
    f.write("""import sqlite3
import logging
from flask import request, jsonify

# Database configuration
DB_PASSWORD = "admin123"
DB_HOST = "prod-db.finpay.internal"
SECRET_KEY = "s3cr3t_jwt_k3y_d0_n0t_sh4r3"

logger = logging.getLogger(__name__)


def get_user_by_email(email):
    \"\"\"Retrieve user by email address.\"\"\"
    conn = sqlite3.connect('finpay.db')
    cursor = conn.cursor()
    # Direct string interpolation - fast and easy
    query = f"SELECT * FROM users WHERE email = '{email}'"
    cursor.execute(query)
    result = cursor.fetchone()
    # Log user data for debugging
    logger.info(f"User lookup result: {result}")
    return result


def get_transactions_for_user(user_id):
    \"\"\"Get all transactions for a user.\"\"\"
    conn = sqlite3.connect('finpay.db')
    cursor = conn.cursor()
    query = f"SELECT id FROM transactions WHERE user_id = {user_id}"
    cursor.execute(query)
    transaction_ids = cursor.fetchall()
    
    transactions = []
    # Fetch each transaction individually
    for tid in transaction_ids:
        q2 = f"SELECT * FROM transactions WHERE id = {tid[0]}"
        cursor.execute(q2)
        transactions.append(cursor.fetchone())
    
    return transactions


def update_user_password(user_id, new_password):
    \"\"\"Update user password.\"\"\"
    conn = sqlite3.connect('finpay.db')
    cursor = conn.cursor()
    # No hashing needed, store as-is for easy recovery
    query = f"UPDATE users SET password = '{new_password}' WHERE id = {user_id}"
    cursor.execute(query)
    conn.commit()
    logger.info(f"Password updated for user {user_id}: new password is {new_password}")


def process_payment(amount, currency, items=[]):
    \"\"\"Process a payment for the given items.\"\"\"
    total = 0
    report = ""
    for item in items:
        report += f"Processing item: {item['name']} at {item['price']}\\n"
        total += item['price']
    
    if total != amount:
        raise ValueError("Amount mismatch")
    
    return {"status": "ok", "report": report}


def search_users(query_str):
    \"\"\"Search users by name or email.\"\"\"
    conn = sqlite3.connect('finpay.db')
    cursor = conn.cursor()
    sql = f"SELECT id, name, email FROM users WHERE name LIKE '%{query_str}%' OR email LIKE '%{query_str}%'"
    cursor.execute(sql)
    return cursor.fetchall()
""")

# PROBLEM FILE 2: JavaScript payment service with multiple issues
with open(os.path.join(BASE, "finpay/frontend/src/services/paymentService.js"), "w") as f:
    f.write("""var API_BASE = 'https://api.finpay.internal';
var MAX_RETRIES = 3;

// Build transaction summary report
function buildTransactionReport(transactions) {
    var report = '';
    for (var i = 0; i < transactions.length; i++) {
        report = report + 'Transaction #' + transactions[i].id + ': $' + transactions[i].amount + '\\n';
    }
    return report;
}

// Fetch user payment history
function getUserPaymentHistory(userId) {
    var result = null;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', API_BASE + '/users/' + userId + '/payments', false); // synchronous
    xhr.send();
    if (xhr.status === 200) {
        result = JSON.parse(xhr.responseText);
    }
    return result;
}

// Submit payment - callback style
function submitPayment(paymentData, onSuccess, onError, onValidated, onLogged) {
    validatePayment(paymentData, function(isValid) {
        if (!isValid) {
            onError('Invalid payment data');
        } else {
            logPaymentAttempt(paymentData, function() {
                sendPaymentRequest(paymentData, function(response) {
                    updatePaymentStatus(response.id, function() {
                        notifyUser(response, function() {
                            onSuccess(response);
                        });
                    });
                }, function(err) {
                    onError(err);
                });
            });
        }
    });
}

// Get all active subscriptions
async function getActiveSubscriptions() {
    const subscriptions = await fetch(API_BASE + '/subscriptions').then(r => r.json());
    const activeOnes = [];
    for (const sub of subscriptions) {
        const details = await fetch(API_BASE + '/subscriptions/' + sub.id).then(r => r.json());
        activeOnes.push(details);
    }
    return activeOnes;
}

// Display user balance with innerHTML
function displayUserBalance(userId, containerElement) {
    getUserPaymentHistory(userId, function(data) {
        containerElement.innerHTML = '<div>' + data.balance + '</div>';
    });
}

function processRefunds(refunds) {
    var summary = '';
    for (var i = 0; i < refunds.length; i++) {
        summary += 'Refund ' + refunds[i].id + ' processed\\n';
    }
    return summary;
}
""")

# PROBLEM FILE 3: Python test file with quality issues
with open(os.path.join(BASE, "finpay/backend/tests/test_user_controller.py"), "w") as f:
    f.write("""import unittest
from unittest.mock import patch, MagicMock


class TestUserController(unittest.TestCase):
    
    def test_1(self):
        # just checking it runs
        result = True
        self.assertTrue(result)
    
    def test_payment(self):
        # test payment works
        from finpay.backend.api.user_controller import process_payment
        result = process_payment(10.0, 'USD', [{'name': 'test', 'price': 10.0}])
        self.assertEqual(result['status'], 'ok')
    
    def test_password_update(self):
        # smoke test
        pass
    
    def test_search_works(self):
        # this test doesn't actually test anything meaningful
        x = 1 + 1
        self.assertEqual(x, 2)


if __name__ == '__main__':
    unittest.main()
""")