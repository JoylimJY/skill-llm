import os
import random
import subprocess
import json
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── 1. Create a realistic JS payment microservice repo ────────────────────────

repo = WORKSPACE / "payment-service"
repo.mkdir(parents=True, exist_ok=True)

# Initialize git repo
os.chdir(repo)
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "config", "user.email", "dev@fintech.local"], check=True)
subprocess.run(["git", "config", "user.name", "Dev Bot"], check=True)
subprocess.run(["git", "checkout", "-b", "develop"], check=True)

# ─── 2. Create "origin/develop" base commit with existing files ──────────────

base_files = {
    "src/core/ledger.js": textwrap.dedent("""\
        // Ledger core module
        class Ledger {
          constructor(db) { this.db = db; }
          async getBalance(accountId) {
            return this.db.query(`SELECT balance FROM accounts WHERE id = ?`, [accountId]);
          }
        }
        module.exports = Ledger;
    """),
    "src/core/transaction.js": textwrap.dedent("""\
        // Transaction processor
        const crypto = require('crypto');
        class Transaction {
          createHash(data) {
            return crypto.createHash('md5').update(data).digest('hex');
          }
        }
        module.exports = Transaction;
    """),
    "src/utils/logger.js": textwrap.dedent("""\
        const winston = require('winston');
        module.exports = winston.createLogger({
          level: 'info',
          transports: [new winston.transports.Console()]
        });
    """),
    "src/utils/config.js": textwrap.dedent("""\
        module.exports = {
          db: { host: 'localhost', port: 5432 },
          app: { port: 3000 }
        };
    """),
    "src/middleware/auth.js": textwrap.dedent("""\
        function authMiddleware(req, res, next) {
          if (!req.headers['x-api-key']) return res.status(401).send('Unauthorized');
          next();
        }
        module.exports = authMiddleware;
    """),
    "tests/ledger.test.js": textwrap.dedent("""\
        const Ledger = require('../src/core/ledger');
        test('getBalance returns value', async () => {
          const mockDb = { query: jest.fn().mockResolvedValue(100) };
          const ledger = new Ledger(mockDb);
          expect(await ledger.getBalance('acc1')).toBe(100);
        });
    """),
    "tests/transaction.test.js": textwrap.dedent("""\
        const Transaction = require('../src/core/transaction');
        test('createHash returns string', () => {
          const t = new Transaction();
          expect(typeof t.createHash('data')).toBe('string');
        });
    """),
    "package.json": json.dumps({
        "name": "payment-service",
        "version": "1.0.0",
        "scripts": {"test": "jest", "build": "tsc --noEmit"},
        "dependencies": {"winston": "^3.0.0"},
        "devDependencies": {"jest": "^29.0.0", "typescript": "^5.0.0"}
    }, indent=2),
    "tsconfig.json": json.dumps({
        "compilerOptions": {"target": "ES2020", "module": "commonjs", "strict": True}
    }, indent=2),
    "README.md": "# Payment Service\n\nCore payment processing microservice.\n",
    ".gitignore": "node_modules/\ndist/\n",
    "CHANGELOG.md": "## v1.0.0\n- Initial release\n",
}

for path, content in base_files.items():
    full_path = repo / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "chore: initial payment service"], check=True)

# Create a fake remote ref for origin/develop
subprocess.run(["git", "update-ref", "refs/remotes/origin/develop", "HEAD"], check=True)

# ─── 3. Create PR branch with new/modified files (the changes to review) ────

subprocess.run(["git", "checkout", "-b", "feature/payment-v2"], check=True)

# New files added in this PR (these will show in --diff-filter=A)
new_files = {
    "src/payments/processor.js": textwrap.dedent("""\
        // NEW: Payment Processor v2
        const crypto = require('crypto');

        class PaymentProcessor {
          constructor(secret) {
            // BUG: key padded with zeros - insecure key management
            this.key = secret.padEnd(32, '0');
          }

          // P0: Uses MD5 hash instead of HMAC for payment verification
          verifyPayment(payload, signature) {
            const hash = crypto.createHash('md5').update(payload + this.key).digest('hex');
            return hash === signature;
          }

          // P1: No input validation - amount could be negative
          processPayment(amount, fromAccount, toAccount) {
            if (fromAccount === toAccount) return false;
            // Missing: amount > 0 check
            // Missing: null/undefined checks
            return this._transfer(amount, fromAccount, toAccount);
          }

          _transfer(amount, from, to) {
            // P1: No transaction atomicity guarantee
            console.log(`Transferring ${amount} from ${from} to ${to}`);
            return true;
          }
        }

        module.exports = PaymentProcessor;
    """),
    "src/payments/refund.js": textwrap.dedent("""\
        // NEW: Refund Handler
        class RefundHandler {
          // P2: Function exceeds 50 lines and has duplicated logic
          async processRefund(transactionId, amount) {
            // Missing null check for transactionId
            const tx = await this.db.findTransaction(transactionId);
            if (!tx) throw new Error('Transaction not found');
            if (tx.amount < amount) throw new Error('Refund exceeds original');
            // P2: No test coverage for this path
            await this.db.updateTransaction(transactionId, { refunded: true, refundAmount: amount });
            await this.notifyUser(tx.userId, amount);
            return { success: true, refundId: transactionId + '_refund' };
          }

          async notifyUser(userId, amount) {
            // P3: Log message reveals amount (sensitive data)
            console.log(`User ${userId} refunded ${amount}`);
          }
        }
        module.exports = RefundHandler;
    """),
    "src/payments/webhook.js": textwrap.dedent("""\
        // NEW: Webhook Handler
        const express = require('express');
        const router = express.Router();

        // P0: SQL injection vulnerability - direct string interpolation
        router.post('/webhook', async (req, res) => {
          const { event, accountId } = req.body;
          // CRITICAL: unsanitized input in query
          const result = await db.query(`SELECT * FROM accounts WHERE id = '${accountId}'`);
          if (result) {
            res.json({ received: true });
          }
        });

        module.exports = router;
    """),
    "src/payments/rateLimit.js": textwrap.dedent("""\
        // NEW: Rate Limiter
        const limits = {};

        function checkRateLimit(userId) {
          // P1: Race condition - non-atomic read-modify-write
          if (!limits[userId]) limits[userId] = 0;
          limits[userId]++;
          if (limits[userId] > 100) return false;
          // P2: No cleanup - memory leak, limits grow unbounded
          return true;
        }

        module.exports = { checkRateLimit };
    """),
    "src/payments/audit.js": textwrap.dedent("""\
        // NEW: Audit Logger
        class AuditLogger {
          log(action, userId, details) {
            // P3: No timestamp on audit logs
            console.log(JSON.stringify({ action, userId, details }));
          }
        }
        module.exports = AuditLogger;
    """),
    "tests/processor.test.js": textwrap.dedent("""\
        // Incomplete tests for PaymentProcessor
        const PaymentProcessor = require('../src/payments/processor');
        test('processPayment returns true', () => {
          const p = new PaymentProcessor('secret');
          // P2: Test only tests happy path, no negative amount test
          expect(p.processPayment(100, 'acc1', 'acc2')).toBe(true);
        });
    """),
    "src/payments/index.js": textwrap.dedent("""\
        module.exports = {
          PaymentProcessor: require('./processor'),
          RefundHandler: require('./refund'),
        };
    """),
}

# Modified files (already existed)
modified_files = {
    "src/core/transaction.js": textwrap.dedent("""\
        // Transaction processor - updated
        const crypto = require('crypto');
        class Transaction {
          createHash(data) {
            // P2: Still using MD5, should be SHA-256
            return crypto.createHash('md5').update(data).digest('hex');
          }
          // P1: New method without error handling
          parseAmount(str) {
            return parseFloat(str);  // No NaN check
          }
        }
        module.exports = Transaction;
    """),
    "src/middleware/auth.js": textwrap.dedent("""\
        function authMiddleware(req, res, next) {
          const key = req.headers['x-api-key'];
          if (!key) return res.status(401).send('Unauthorized');
          // P1: API key compared in non-constant-time (timing attack possible)
          if (key !== process.env.API_KEY) return res.status(403).send('Forbidden');
          next();
        }
        module.exports = authMiddleware;
    """),
}

for path, content in {**new_files, **modified_files}.items():
    full_path = repo / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "feat: add payment v2 processor, refund handler, webhook, rate limiter"], check=True)

subprocess.run(["git", "add", "-A"], check=True)
# Check if there's anything to commit
result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
if result.stdout.strip():
    subprocess.run(["git", "commit", "-m", "feat: add payment v2 processor, refund handler, webhook, rate limiter"], check=True)

# ─── 4. Create distractor files in workspace (not in the repo) ──────────────

distractor_dir = WORKSPACE / "ops"
distractor_dir.mkdir(exist_ok=True)

distractors = {
    "ops/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "ops/monitoring.yaml": "metrics:\n  - name: latency\n    threshold: 200ms\n",
    "ops/rollback.sh": "#!/bin/bash\necho 'Rolling back...'\n",
    "docs/api-spec.md": "# API Specification\n\n## POST /payment\n",
    "docs/architecture.md": "# Architecture\n\nMicroservices-based payment platform.\n",
    "scripts/db-migrate.sh": "#!/bin/bash\npsql -c 'ALTER TABLE accounts ADD COLUMN v2 BOOLEAN'\n",
    "scripts/seed-data.py": "# Seed script\nprint('Seeding database...')\n",
    "config/staging.env": "DB_HOST=staging-db.internal\nAPI_PORT=3001\n",
    "config/production.env": "DB_HOST=prod-db.internal\nAPI_PORT=3000\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
}

for path, content in distractors.items():
    full_path = WORKSPACE / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ─── 5. Write a task brief file for the agent ────────────────────────────────

brief = WORKSPACE / "task_brief.md"
brief.write_text(textwrap.dedent("""\
    # Code Review Task Brief

    The payment-service team has submitted a PR from branch `feature/payment-v2` targeting `origin/develop`.
    The repository is located at: /workspace/payment-service

    Please complete the following:

    1. Configure the automated code review system with automation preferences.
    2. Run a pre-flight assessment of the PR.
    3. Produce a structured review report.

    See task details in the main prompt.
"""))

print("Workspace setup complete.")
print(f"Repo: {repo}")
print(f"New files in PR: {list(new_files.keys())}")
print(f"Modified files in PR: {list(modified_files.keys())}")