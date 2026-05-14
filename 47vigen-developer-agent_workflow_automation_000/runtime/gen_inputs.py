#!/usr/bin/env python3
"""
Generate the sandbox workspace: a realistic FinTech Node.js payment API project
with multiple distractor files and a pending feature requirement document.
"""

import os
import random
import subprocess
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# ── 1. Initialize git repo with `staging` branch ──────────────────────────────
subprocess.run(["git", "init", str(WORKSPACE)], check=True)
subprocess.run(["git", "-C", str(WORKSPACE), "config", "user.email", "agent@devteam.local"], check=True)
subprocess.run(["git", "-C", str(WORKSPACE), "config", "user.name", "Developer Agent"], check=True)

# ── 2. Project structure ───────────────────────────────────────────────────────
dirs = [
    "src/api/routes",
    "src/api/middleware",
    "src/services",
    "src/models",
    "src/utils",
    "src/config",
    "src/validators",
    "tests/unit",
    "tests/integration",
    "docs",
    "scripts",
    "references",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 3. package.json (pnpm-compatible) ─────────────────────────────────────────
package_json = """{
  "name": "payment-api",
  "version": "1.4.2",
  "description": "FinTech Payment Processing API",
  "main": "src/index.js",
  "scripts": {
    "build": "node scripts/build.js",
    "test": "jest",
    "start": "node src/index.js",
    "lint": "eslint src/"
  },
  "dependencies": {
    "express": "^4.18.2",
    "uuid": "^9.0.0",
    "decimal.js": "^10.4.3"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=8.0.0"
  }
}
"""
(WORKSPACE / "package.json").write_text(package_json)

# ── 4. Build script (must succeed for pnpm build to pass) ─────────────────────
build_script = """#!/usr/bin/env node
// Simplified build script: validates source files exist and writes build manifest
const fs = require('fs');
const path = require('path');

console.log('Starting build process...');

const requiredFiles = [
  'src/index.js',
  'src/services/paymentService.js',
  'src/models/transaction.js',
];

let allFound = true;
for (const f of requiredFiles) {
  if (!fs.existsSync(path.join(__dirname, '..', f))) {
    console.error(`MISSING: ${f}`);
    allFound = false;
  }
}

if (!allFound) {
  console.error('Build failed: required source files missing.');
  process.exit(1);
}

// Write build manifest
const manifest = {
  buildTime: new Date().toISOString(),
  version: require('../package.json').version,
  files: requiredFiles,
};
fs.mkdirSync(path.join(__dirname, '../dist'), { recursive: true });
fs.writeFileSync(
  path.join(__dirname, '../dist/build-manifest.json'),
  JSON.stringify(manifest, null, 2)
);

console.log('Build completed successfully in 2.3s');
console.log('Output written to dist/build-manifest.json');
"""
(WORKSPACE / "scripts" / "build.js").write_text(build_script)

# ── 5. Core source files ───────────────────────────────────────────────────────
index_js = """const express = require('express');
const app = express();
app.use(express.json());

const paymentRoutes = require('./api/routes/payments');
const transactionRoutes = require('./api/routes/transactions');

app.use('/api/payments', paymentRoutes);
app.use('/api/transactions', transactionRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Payment API running on port ${PORT}`));

module.exports = app;
"""
(WORKSPACE / "src" / "index.js").write_text(index_js)

payment_service = """/**
 * Payment Service
 * Handles core payment processing logic
 */
class PaymentService {
  constructor() {
    this.supportedCurrencies = ['USD', 'EUR', 'GBP', 'JPY'];
  }

  async processPayment(amount, currency, merchantId) {
    if (!this.supportedCurrencies.includes(currency)) {
      throw new Error(`Unsupported currency: ${currency}`);
    }
    // TODO: Add fee calculation before processing
    return {
      transactionId: require('uuid').v4(),
      amount,
      currency,
      merchantId,
      status: 'processed',
      timestamp: new Date().toISOString(),
    };
  }

  async refundPayment(transactionId, amount) {
    return { transactionId, refundAmount: amount, status: 'refunded' };
  }
}

module.exports = new PaymentService();
"""
(WORKSPACE / "src" / "services" / "paymentService.js").write_text(payment_service)

transaction_model = """/**
 * Transaction Model
 * Represents a payment transaction record
 */
class Transaction {
  constructor({ id, amount, currency, merchantId, status, fee = 0 }) {
    this.id = id;
    this.amount = amount;
    this.currency = currency;
    this.merchantId = merchantId;
    this.status = status;
    this.fee = fee;
    this.createdAt = new Date().toISOString();
  }

  toJSON() {
    return {
      id: this.id,
      amount: this.amount,
      currency: this.currency,
      merchantId: this.merchantId,
      status: this.status,
      fee: this.fee,
      createdAt: this.createdAt,
    };
  }
}

module.exports = Transaction;
"""
(WORKSPACE / "src" / "models" / "transaction.js").write_text(transaction_model)

# ── 6. API Routes ──────────────────────────────────────────────────────────────
payments_route = """const express = require('express');
const router = express.Router();
const paymentService = require('../../services/paymentService');

router.post('/process', async (req, res) => {
  try {
    const { amount, currency, merchantId } = req.body;
    const result = await paymentService.processPayment(amount, currency, merchantId);
    res.json({ success: true, data: result });
  } catch (err) {
    res.status(400).json({ success: false, error: err.message });
  }
});

module.exports = router;
"""
(WORKSPACE / "src" / "api" / "routes" / "payments.js").write_text(payments_route)

transactions_route = """const express = require('express');
const router = express.Router();

router.get('/:id', async (req, res) => {
  res.json({ transactionId: req.params.id, status: 'mock' });
});

module.exports = router;
"""
(WORKSPACE / "src" / "api" / "routes" / "transactions.js").write_text(transactions_route)

# ── 7. Middleware & Utilities (distractor files) ───────────────────────────────
(WORKSPACE / "src" / "api" / "middleware" / "auth.js").write_text("""module.exports = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey) return res.status(401).json({ error: 'Missing API key' });
  next();
};
""")

(WORKSPACE / "src" / "api" / "middleware" / "rateLimiter.js").write_text("""const requests = new Map();
module.exports = (req, res, next) => {
  const ip = req.ip;
  const count = (requests.get(ip) || 0) + 1;
  requests.set(ip, count);
  if (count > 100) return res.status(429).json({ error: 'Too many requests' });
  next();
};
""")

(WORKSPACE / "src" / "utils" / "logger.js").write_text("""const log = (level, msg) => console.log(`[${level.toUpperCase()}] ${new Date().toISOString()} - ${msg}`);
module.exports = { info: m => log('info', m), error: m => log('error', m), warn: m => log('warn', m) };
""")

(WORKSPACE / "src" / "utils" / "currency.js").write_text("""const EXCHANGE_RATES = { USD: 1, EUR: 0.92, GBP: 0.79, JPY: 149.5 };
module.exports = {
  convert: (amount, from, to) => amount * (EXCHANGE_RATES[to] / EXCHANGE_RATES[from]),
  getRates: () => ({ ...EXCHANGE_RATES }),
};
""")

(WORKSPACE / "src" / "config" / "database.js").write_text("""module.exports = {
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  name: process.env.DB_NAME || 'payments_db',
  pool: { min: 2, max: 10 },
};
""")

(WORKSPACE / "src" / "config" / "app.js").write_text("""module.exports = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3000'),
  apiVersion: 'v1',
  maxPaymentAmount: 1000000,
};
""")

(WORKSPACE / "src" / "validators" / "paymentValidator.js").write_text("""module.exports = {
  validateAmount: (amount) => typeof amount === 'number' && amount > 0 && amount <= 1000000,
  validateCurrency: (cur) => ['USD', 'EUR', 'GBP', 'JPY'].includes(cur),
  validateMerchant: (id) => typeof id === 'string' && id.length > 0,
};
""")

# ── 8. Test files (distractor) ─────────────────────────────────────────────────
(WORKSPACE / "tests" / "unit" / "paymentService.test.js").write_text("""describe('PaymentService', () => {
  it('should process valid payments', () => {
    expect(true).toBe(true);
  });
});
""")

(WORKSPACE / "tests" / "integration" / "payments.test.js").write_text("""describe('Payment API', () => {
  it('POST /api/payments/process returns 200', () => {
    expect(true).toBe(true);
  });
});
""")

# ── 9. Docs & references (distractor) ─────────────────────────────────────────
(WORKSPACE / "docs" / "api-spec.md").write_text("""# Payment API Specification v1.4
## Endpoints
- POST /api/payments/process
- GET /api/transactions/:id
""")

(WORKSPACE / "docs" / "architecture.md").write_text("""# System Architecture
Three-tier: API layer → Service layer → Data layer
""")

(WORKSPACE / "references" / "fee-schedule.md").write_text("""# Merchant Fee Schedule
| Tier      | Monthly Volume    | Rate   |
|-----------|-------------------|--------|
| Standard  | < $10,000         | 2.9%   |
| Growth    | $10,001–$100,000  | 2.4%   |
| Enterprise| > $100,000        | 1.9%   |

International transactions: +1.5% surcharge
""")

# ── 10. Feature requirement document ──────────────────────────────────────────
requirement_doc = """# Feature Requirement: Transaction Fee Calculator

**Ticket ID:** PAY-2847
**Priority:** High
**Requestor:** Product Team
**Date:** 2024-01-15

## Business Context

Our merchants need to see the exact fees deducted from each transaction in real time.
Currently the system processes payments without surfacing fee details, causing reconciliation
issues and merchant complaints.

## Required Changes

1. **New fee calculation service** (`src/services/feeCalculator.js`):
   - Calculate fees based on the merchant fee schedule (see references/fee-schedule.md)
   - Support Standard, Growth, and Enterprise tiers
   - Add +1.5% for international (non-USD) transactions

2. **Update PaymentService** (`src/services/paymentService.js`):
   - Integrate fee calculation into `processPayment()`
   - Return fee breakdown in the payment result

3. **Update Transaction Model** (`src/models/transaction.js`):
   - Add `feeAmount`, `feeRate`, and `netAmount` fields

## Acceptance Criteria

- Fee is calculated correctly before transaction is processed
- Payment response includes: gross amount, fee amount, fee rate, net amount
- Existing tests continue to pass
- No breaking changes to the payment API contract

## Notes

This touches 3 files and introduces a new service module. The fee logic is moderately
complex due to tiered rates and currency surcharges.
"""
(WORKSPACE / "docs" / "PAY-2847-fee-calculator.md").write_text(requirement_doc)

# ── 11. Initial git commit on staging ─────────────────────────────────────────
subprocess.run(["git", "-C", str(WORKSPACE), "checkout", "-b", "staging"], check=True)
subprocess.run(["git", "-C", str(WORKSPACE), "add", "."], check=True)
subprocess.run(
    ["git", "-C", str(WORKSPACE), "commit", "-m", "chore: initial project scaffold"],
    check=True
)

print("✅ Workspace generated successfully.")
print(f"   Repo path: {WORKSPACE}")
print(f"   Current branch: staging")
print(f"   Files created: {len(list(WORKSPACE.rglob('*')))}")