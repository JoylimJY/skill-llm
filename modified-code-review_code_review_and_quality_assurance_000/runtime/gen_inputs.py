import os
import subprocess
import textwrap

WORKSPACE = "/workspace"

# --- Directory structure ---
dirs = [
    "payment-service/src/api",
    "payment-service/src/models",
    "payment-service/src/utils",
    "payment-service/src/middleware",
    "payment-service/tests/unit",
    "payment-service/tests/integration",
    "payment-service/config",
    "payment-service/docs",
    "payment-service/scripts",
    "payment-service/.github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files (realistic, unrelated to the diff) ---
distractors = {
    "payment-service/config/settings.py": textwrap.dedent("""\
        import os

        DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/payments")
        REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-do-not-use-in-prod")
        DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
        MAX_RETRY_ATTEMPTS = 3
        PAYMENT_TIMEOUT_SECONDS = 30
    """),
    "payment-service/config/logging.yaml": textwrap.dedent("""\
        version: 1
        handlers:
          console:
            class: logging.StreamHandler
            level: INFO
        root:
          level: INFO
          handlers: [console]
    """),
    "payment-service/src/models/transaction.py": textwrap.dedent("""\
        from dataclasses import dataclass
        from decimal import Decimal
        from datetime import datetime
        from enum import Enum

        class TransactionStatus(Enum):
            PENDING = "pending"
            COMPLETED = "completed"
            FAILED = "failed"
            REFUNDED = "refunded"

        @dataclass
        class Transaction:
            id: str
            amount: Decimal
            currency: str
            status: TransactionStatus
            created_at: datetime
            merchant_id: str
            customer_id: str
    """),
    "payment-service/src/models/merchant.py": textwrap.dedent("""\
        from dataclasses import dataclass

        @dataclass
        class Merchant:
            id: str
            name: str
            api_key: str
            fee_rate: float
            is_active: bool
    """),
    "payment-service/src/middleware/auth.py": textwrap.dedent("""\
        from functools import wraps
        from flask import request, jsonify
        import hmac
        import hashlib

        def require_api_key(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                api_key = request.headers.get('X-API-Key')
                if not api_key:
                    return jsonify({'error': 'Missing API key'}), 401
                # TODO: validate against database
                return f(*args, **kwargs)
            return decorated
    """),
    "payment-service/src/utils/currency.py": textwrap.dedent("""\
        SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CNY']

        def normalize_amount(amount, currency):
            if currency == 'JPY':
                return int(amount)
            return round(float(amount), 2)
    """),
    "payment-service/docs/api_spec.md": textwrap.dedent("""\
        # Payment Service API

        ## POST /api/v1/charge
        Initiates a payment charge.

        ### Request Body
        - `amount` (number, required): Amount in smallest currency unit
        - `currency` (string, required): ISO 4217 currency code
        - `merchant_id` (string, required): Merchant identifier
        - `customer_id` (string, required): Customer identifier

        ### Response
        - `transaction_id`: Unique transaction identifier
        - `status`: Transaction status
    """),
    "payment-service/.github/workflows/ci.yml": textwrap.dedent("""\
        name: CI
        on: [push, pull_request]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v3
              - name: Run tests
                run: pytest tests/
    """),
    "payment-service/scripts/migrate.py": textwrap.dedent("""\
        #!/usr/bin/env python3
        \"\"\"Database migration runner.\"\"\"
        import sys
        print("Running migrations...")
    """),
    "payment-service/src/middleware/rate_limit.py": textwrap.dedent("""\
        from flask import request, jsonify
        from functools import wraps
        import time

        _request_counts = {}

        def rate_limit(max_per_minute=60):
            def decorator(f):
                @wraps(f)
                def wrapper(*args, **kwargs):
                    key = request.remote_addr
                    now = time.time()
                    window = _request_counts.get(key, [])
                    window = [t for t in window if now - t < 60]
                    if len(window) >= max_per_minute:
                        return jsonify({'error': 'Rate limit exceeded'}), 429
                    window.append(now)
                    _request_counts[key] = window
                    return f(*args, **kwargs)
                return wrapper
            return decorator
    """),
}

for path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Core files that will be part of the diff ---
# Original versions (will be committed as base)

original_charge_api = textwrap.dedent("""\
    from flask import Flask, request, jsonify
    from decimal import Decimal
    import uuid
    import logging

    app = Flask(__name__)
    logger = logging.getLogger(__name__)

    def calculate_fee(amount):
        \"\"\"Calculate transaction fee.\"\"\"
        return float(amount) * 0.029 + 0.30

    @app.route('/api/v1/charge', methods=['POST'])
    def charge():
        data = request.json
        amount = data['amount']
        currency = data['currency']
        merchant_id = data['merchant_id']
        customer_id = data['customer_id']

        fee = calculate_fee(amount)
        transaction_id = str(uuid.uuid4())

        logger.info(f"Charge created: {transaction_id}")
        return jsonify({
            'transaction_id': transaction_id,
            'amount': amount,
            'fee': fee,
            'currency': currency,
            'status': 'pending'
        }), 201

    if __name__ == '__main__':
        app.run(debug=True)
""")

original_test_charge = textwrap.dedent("""\
    import pytest
    from payment-service.src.api.charge import app, calculate_fee

    @pytest.fixture
    def client():
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_calculate_fee_standard():
        fee = calculate_fee(100)
        assert abs(fee - 3.20) < 0.001

    def test_calculate_fee_small_amount():
        fee = calculate_fee(1)
        assert abs(fee - 0.329) < 0.001

    def test_charge_endpoint_success(client):
        response = client.post('/api/v1/charge', json={
            'amount': 100,
            'currency': 'USD',
            'merchant_id': 'merch_123',
            'customer_id': 'cust_456'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'transaction_id' in data
        assert data['status'] == 'pending'

    def test_charge_missing_fields(client):
        response = client.post('/api/v1/charge', json={'amount': 50})
        assert response.status_code == 400
""")

original_fee_calculator = textwrap.dedent("""\
    from decimal import Decimal

    STANDARD_RATE = Decimal('0.029')
    FIXED_FEE = Decimal('0.30')

    def calculate_transaction_fee(amount: Decimal) -> Decimal:
        \"\"\"Calculate the standard transaction fee.\"\"\"
        return amount * STANDARD_RATE + FIXED_FEE
""")

# --- Initialize git repo ---
repo_path = os.path.join(WORKSPACE, "payment-service")
subprocess.run(["git", "init"], cwd=repo_path, check=True)
subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=repo_path, check=True)
subprocess.run(["git", "config", "user.name", "Dev"], cwd=repo_path, check=True)

# Write original files
with open(os.path.join(repo_path, "src/api/charge.py"), "w") as f:
    f.write(original_charge_api)

with open(os.path.join(repo_path, "src/utils/fee_calculator.py"), "w") as f:
    f.write(original_fee_calculator)

with open(os.path.join(repo_path, "tests/unit/test_charge.py"), "w") as f:
    f.write(original_test_charge)

# Commit the base
subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
subprocess.run(["git", "commit", "-m", "Initial commit: payment charge endpoint"], cwd=repo_path, check=True)

# --- Now make the messy, problematic changes ---

# MODIFIED charge.py: has SQL injection risk, removes input validation, adds eval(), uses raw string concat
modified_charge_api = textwrap.dedent("""\
    from flask import Flask, request, jsonify
    import uuid
    import logging
    import sqlite3

    app = Flask(__name__)
    logger = logging.getLogger(__name__)

    def calculate_fee(amount, fee_type="standard"):
        # Dynamic fee calculation
        fee_rules = {
            "standard": "amount * 0.029 + 0.30",
            "premium": "amount * 0.019 + 0.15",
            "micropay": "amount * 0.049 + 0.05",
        }
        rule = fee_rules.get(fee_type, fee_rules["standard"])
        return eval(rule)  # evaluate the fee rule

    def log_transaction_to_db(transaction_id, merchant_id, amount):
        conn = sqlite3.connect("transactions.db")
        cursor = conn.cursor()
        # Log transaction for audit
        query = "INSERT INTO audit_log VALUES ('" + transaction_id + "', '" + merchant_id + "', " + str(amount) + ")"
        cursor.execute(query)
        conn.commit()
        conn.close()

    @app.route('/api/v1/charge', methods=['POST'])
    def charge():
        data = request.json
        amount = data.get('amount')
        currency = data.get('currency')
        merchant_id = data.get('merchant_id')
        customer_id = data.get('customer_id')
        fee_type = data.get('fee_type', 'standard')

        fee = calculate_fee(amount, fee_type)
        transaction_id = str(uuid.uuid4())

        log_transaction_to_db(transaction_id, merchant_id, amount)

        logger.info("Charge created: " + transaction_id + " for merchant: " + merchant_id)
        return jsonify({
            'transaction_id': transaction_id,
            'amount': amount,
            'fee': fee,
            'currency': currency,
            'status': 'pending'
        }), 201

    @app.route('/api/v1/charge/<transaction_id>', methods=['GET'])
    def get_charge(transaction_id):
        conn = sqlite3.connect("transactions.db")
        cursor = conn.cursor()
        query = "SELECT * FROM audit_log WHERE id = '" + transaction_id + "'"
        result = cursor.execute(query).fetchone()
        conn.close()
        return jsonify({'transaction': result}), 200

    if __name__ == '__main__':
        app.run(debug=True)
""")

# MODIFIED fee_calculator.py: added new merchant-tier system but with a bug
modified_fee_calculator = textwrap.dedent("""\
    from decimal import Decimal
    from typing import Optional

    STANDARD_RATE = Decimal('0.029')
    FIXED_FEE = Decimal('0.30')

    MERCHANT_TIERS = {
        "bronze": {"rate": Decimal('0.029'), "fixed": Decimal('0.30')},
        "silver": {"rate": Decimal('0.025'), "fixed": Decimal('0.25')},
        "gold":   {"rate": Decimal('0.019'), "fixed": Decimal('0.15')},
    }

    def calculate_transaction_fee(amount: Decimal, merchant_tier: Optional[str] = None) -> Decimal:
        \"\"\"Calculate transaction fee based on merchant tier.\"\"\"
        if merchant_tier and merchant_tier in MERCHANT_TIERS:
            tier = MERCHANT_TIERS[merchant_tier]
            return amount * tier["rate"] + tier["fixed"]
        # Bug: uses float arithmetic instead of Decimal for default case
        return float(amount) * 0.029 + 0.30

    def get_tier_info(tier_name: str) -> dict:
        # No input validation - will KeyError on unknown tier
        return MERCHANT_TIERS[tier_name]

    def batch_calculate_fees(amounts: list, merchant_tier: str = "bronze") -> list:
        results = []
        for i in range(len(amounts)):
            fee = calculate_transaction_fee(amounts[i], merchant_tier)
            results.append(fee)
        # Missing: no handling for empty list, no type checking
        return results
""")

# DELETED test file (simulated by staging a deletion)
# Write new integration test (incomplete, poorly written)
new_integration_test = textwrap.dedent("""\
    # Integration tests for charge endpoint
    import requests

    BASE_URL = "http://localhost:5000"

    def test_charge_live():
        # This test requires a live server - not suitable for CI
        r = requests.post(BASE_URL + "/api/v1/charge", json={
            "amount": 100,
            "currency": "USD",
            "merchant_id": "merch_test",
            "customer_id": "cust_test"
        })
        print(r.json())
        assert r.status_code == 201

    def test_premium_fee():
        r = requests.post(BASE_URL + "/api/v1/charge", json={
            "amount": 500,
            "currency": "USD",
            "merchant_id": "merch_gold",
            "customer_id": "cust_vip",
            "fee_type": "premium"
        })
        print(r.json())
""")

# Apply changes
with open(os.path.join(repo_path, "src/api/charge.py"), "w") as f:
    f.write(modified_charge_api)

with open(os.path.join(repo_path, "src/utils/fee_calculator.py"), "w") as f:
    f.write(modified_fee_calculator)

# Delete the unit test
os.remove(os.path.join(repo_path, "tests/unit/test_charge.py"))

# Add the new (bad) integration test
with open(os.path.join(repo_path, "tests/integration/test_charge_integration.py"), "w") as f:
    f.write(new_integration_test)

# Stage all changes
subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True)

print("Workspace setup complete. Git repo initialized with staged changes ready for review.")
print("Run `git diff --cached` in /workspace/payment-service to see the diff.")