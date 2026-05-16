import os
import json
import random
import datetime

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create realistic fintech directory structure with distractor files ---

dirs = [
    "src/gateway",
    "src/auth",
    "src/ledger",
    "tests/unit",
    "tests/integration",
    "deploy/k8s",
    "deploy/scripts",
    "docs/api",
    "logs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "src/gateway/handler.py": """\
# Payment gateway handler
import json

def handle_request(req):
    # Route incoming payment requests
    if req.get('type') == 'charge':
        return process_charge(req)
    return {'status': 'unknown_type'}

def process_charge(req):
    amount = req.get('amount', 0)
    if amount <= 0:
        raise ValueError('Invalid amount')
    return {'status': 'ok', 'amount': amount}
""",
    "src/gateway/router.py": """\
# Request router for payment gateway
ROUTES = {
    '/pay': 'handler.handle_request',
    '/refund': 'refund.handle_refund',
    '/status': 'status.get_status',
}
""",
    "src/auth/token.py": """\
import hashlib, time

def generate_token(user_id: str) -> str:
    ts = str(int(time.time()))
    return hashlib.sha256((user_id + ts).encode()).hexdigest()
""",
    "src/ledger/transactions.py": """\
transactions = []

def record(txn_id, amount, status):
    transactions.append({'id': txn_id, 'amount': amount, 'status': status})

def get_all():
    return transactions
""",
    "tests/unit/test_handler.py": """\
from src.gateway.handler import process_charge

def test_valid_charge():
    result = process_charge({'amount': 100})
    assert result['status'] == 'ok'

def test_invalid_amount():
    try:
        process_charge({'amount': -5})
        assert False
    except ValueError:
        pass
""",
    "tests/integration/test_gateway_flow.py": """\
# Integration test for full payment flow
# Requires running gateway server
def test_ping():
    # placeholder
    pass
""",
    "deploy/k8s/deployment.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-gateway
  template:
    metadata:
      labels:
        app: payment-gateway
    spec:
      containers:
      - name: gateway
        image: fintech/payment-gateway:latest
        ports:
        - containerPort: 8443
""",
    "deploy/scripts/deploy.sh": """\
#!/bin/bash
echo "Deploying payment gateway..."
kubectl apply -f deploy/k8s/deployment.yaml
echo "Done."
""",
    "docs/api/payment_api.md": """\
# Payment API

## POST /pay
Initiates a payment transaction.

### Request Body
```json
{
  "amount": 100,
  "currency": "USD",
  "merchant_id": "m_123"
}
```

### Response
```json
{
  "status": "ok",
  "transaction_id": "txn_abc"
}
```
""",
    "logs/gateway.log": """\
2026-03-10 09:01:22 INFO  Gateway started on port 8443
2026-03-10 09:01:23 INFO  SSL context loaded
2026-03-10 09:05:11 INFO  Request received: POST /pay amount=250
2026-03-10 09:05:11 INFO  Transaction processed: txn_00123
2026-03-10 09:12:44 WARN  High latency detected: 340ms
2026-03-10 09:30:00 INFO  Health check: OK
""",
    "tmp/scratch.json": json.dumps({"note": "temporary workspace, ignore", "ts": 1710000000}),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE KEY FILE: config.json (payment gateway config — the important file to modify) ---
config = {
    "service_name": "payment-gateway",
    "gateway_port": 8443,
    "admin_port": 8080,
    "database": {
        "host": "db.internal.fintech.io",
        "port": 5432,
        "name": "payments_db",
        "pool_size": 10
    },
    "auth": {
        "token_expiry_seconds": 3600,
        "max_failed_attempts": 5
    },
    "rate_limiting": {
        "enabled": True,
        "requests_per_minute": 1000
    },
    "logging": {
        "level": "INFO",
        "file": "logs/gateway.log"
    }
}

config_path = os.path.join(workspace, "config.json")
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print("Workspace generated successfully.")
print(f"config.json created at: {config_path}")
print(f"gateway_port currently set to: {config['gateway_port']}")