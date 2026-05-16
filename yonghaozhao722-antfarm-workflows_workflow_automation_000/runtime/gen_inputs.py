import os
import json
import random
import pathlib

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "services/payments/src/handlers",
    "services/payments/src/middleware",
    "services/payments/tests/unit",
    "services/payments/tests/integration",
    "services/auth/src",
    "services/auth/tests",
    "infra/terraform/modules/rds",
    "infra/terraform/modules/ecs",
    "infra/k8s/overlays/prod",
    "infra/k8s/overlays/staging",
    "docs/architecture",
    "docs/runbooks",
    "scripts/migration",
    "scripts/seed",
    ".github/workflows",
]
for d in dirs:
    pathlib.Path(os.path.join(workspace, d)).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "services/payments/src/handlers/charge.js": """\
const stripe = require('stripe')(process.env.STRIPE_KEY);

async function charge(req, res) {
  // BUG: token validation skipped under concurrent load
  const { amount, currency, token } = req.body;
  const charge = await stripe.charges.create({ amount, currency, source: token });
  res.json({ success: true, id: charge.id });
}
module.exports = { charge };
""",
    "services/payments/src/handlers/refund.js": """\
async function refund(req, res) {
  const { chargeId } = req.body;
  // TODO: add idempotency key
  res.json({ refunded: chargeId });
}
module.exports = { refund };
""",
    "services/payments/src/middleware/auth.js": """\
function authMiddleware(req, res, next) {
  const token = req.headers['x-auth-token'];
  if (!token) return res.status(401).json({ error: 'Missing token' });
  // BUG: JWT expiry not verified
  next();
}
module.exports = authMiddleware;
""",
    "services/payments/tests/unit/charge.test.js": """\
const { charge } = require('../../src/handlers/charge');
describe('charge handler', () => {
  it('should fail without token', async () => {
    // placeholder
  });
});
""",
    "services/payments/tests/integration/flow.test.js": """\
describe('payment flow', () => {
  it('completes end-to-end charge and refund', async () => {
    // placeholder
  });
});
""",
    "services/auth/src/jwt.js": """\
const jwt = require('jsonwebtoken');
const SECRET = process.env.JWT_SECRET || 'insecure-default';
function sign(payload) { return jwt.sign(payload, SECRET, { expiresIn: '1h' }); }
function verify(token) { return jwt.verify(token, SECRET); }
module.exports = { sign, verify };
""",
    "infra/terraform/modules/rds/main.tf": """\
resource "aws_db_instance" "payments" {
  allocated_storage = 20
  engine            = "postgres"
  instance_class    = "db.t3.micro"
  name              = "payments"
}
""",
    "infra/k8s/overlays/prod/kustomization.yaml": """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
""",
    "docs/runbooks/payment-outage.md": """\
# Payment Outage Runbook
1. Check Stripe dashboard
2. Verify DB connectivity
3. Rollback last deploy if needed
""",
    "docs/architecture/payments-service.md": """\
# Payments Service Architecture
- Node.js Express service
- PostgreSQL backend
- Stripe integration for charges
""",
    ".github/workflows/ci.yml": """\
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm test
""",
    "scripts/migration/001_initial.sql": """\
CREATE TABLE transactions (
  id SERIAL PRIMARY KEY,
  amount INTEGER NOT NULL,
  currency VARCHAR(3) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending'
);
""",
    "scripts/seed/dev_data.sql": """\
INSERT INTO transactions (amount, currency, status) VALUES (1000, 'USD', 'completed');
INSERT INTO transactions (amount, currency, status) VALUES (500, 'EUR', 'pending');
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    pathlib.Path(full_path).parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── Bug report context file (raw, messy — agent must extract info from it) ──
bug_report = {
    "ticket_id": "PAY-4417",
    "title": "Authentication bypass under concurrent load in payments service",
    "severity": "critical",
    "reported_by": "monitoring-bot",
    "repro_steps": [
        "Send 50 concurrent POST /charge requests with invalid/expired JWT tokens",
        "Observe that ~30% of requests succeed despite invalid auth",
        "Root cause suspected: race condition in authMiddleware token check"
    ],
    "affected_files": [
        "services/payments/src/middleware/auth.js",
        "services/payments/src/handlers/charge.js"
    ],
    "environment": "production",
    "logs_snippet": "WARN: JWT verification skipped, token=null, req_id=abc123"
}

with open(os.path.join(workspace, "bug_report.json"), "w") as f:
    json.dump(bug_report, f, indent=2)

# ── Intentionally absent: no bug_run_report.json, no antfarm config ──
print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")