import os
import random
import hashlib
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "src/payment",
    "src/auth",
    "src/ledger",
    "internal/middleware",
    "internal/validators",
    "db/migrations",
    "db/seeds",
    "api/schemas",
    "config",
    "docs",
    "output/context-packets",
    ".openclaw",
    "logs",
    "tmp",
    "scripts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Source Go files (severity: important) ────────────────────────────────────
go_files = {
    "src/payment/processor.go": """\
package payment

import "fmt"

// Processor handles transaction routing
type Processor struct {
    ledgerID string
    fee      float64
}

func (p *Processor) Execute(amount float64) error {
    if amount <= 0 {
        return fmt.Errorf("invalid amount: %f", amount)
    }
    return nil
}
""",
    "src/payment/validator.go": """\
package payment

// Validator checks transaction constraints
type Validator struct{}

func (v *Validator) Validate(txID string) bool {
    return len(txID) == 36
}
""",
    "src/auth/jwt.go": """\
package auth

import "time"

type Claims struct {
    UserID    string    `json:"user_id"`
    ExpiresAt time.Time `json:"expires_at"`
}
""",
    "src/ledger/entry.go": """\
package ledger

type Entry struct {
    ID      string  `json:"id"`
    Amount  float64 `json:"amount"`
    Balance float64 `json:"balance"`
}
""",
    "internal/middleware/ratelimit.go": """\
package middleware

import "sync"

type RateLimiter struct {
    mu      sync.Mutex
    counts  map[string]int
}
""",
    "internal/validators/schema.go": """\
package validators

// SchemaValidator validates API payloads
type SchemaValidator struct {
    strict bool
}
""",
}

for path, content in go_files.items():
    (workspace / path).write_text(content)

# ── DB migration SQL files ────────────────────────────────────────────────────
sql_files = {
    "db/migrations/001_create_accounts.sql": """\
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    balance DECIMAL(18,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
""",
    "db/migrations/002_create_transactions.sql": """\
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    amount DECIMAL(18,2) NOT NULL,
    type VARCHAR(20) NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);
""",
    "db/seeds/test_accounts.sql": """\
INSERT INTO accounts (owner_id, balance) VALUES
  ('11111111-1111-1111-1111-111111111111', 1000.00),
  ('22222222-2222-2222-2222-222222222222', 500.00);
""",
}

for path, content in sql_files.items():
    (workspace / path).write_text(content)

# ── API schema JSON ───────────────────────────────────────────────────────────
(workspace / "api/schemas/payment_request.json").write_text(json.dumps({
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["amount", "currency", "recipient"],
    "properties": {
        "amount": {"type": "number", "minimum": 0.01},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "recipient": {"type": "string"}
    }
}, indent=2))

# ── Sensitive .env file (severity: critical) ─────────────────────────────────
(workspace / "config/.env").write_text("""\
DATABASE_URL=postgres://user:REDACTED@localhost:5432/payments
JWT_SECRET=super_secret_key_do_not_share
STRIPE_API_KEY=sk_live_REDACTED
""")

# ── Log files (severity: minor) ───────────────────────────────────────────────
(workspace / "logs/app.log").write_text("""\
2026-03-01 10:00:00 INFO  Server started on :8080
2026-03-01 10:01:22 INFO  Payment processed: txid=abc-001 amount=250.00
2026-03-01 10:02:05 WARN  Rate limit approaching for user=user_42
2026-03-01 10:03:11 ERROR Failed to connect to DB: timeout
""")

(workspace / "tmp/scratch.tmp").write_text("scratch data\n")

# ── Distractor files ──────────────────────────────────────────────────────────
(workspace / "docs/architecture.md").write_text("""\
# Payment Service Architecture

This service handles end-to-end payment processing for the fintech platform.
""")

(workspace / "scripts/deploy.sh").write_text("""\
#!/bin/bash
echo "Deploying payment service..."
go build -o bin/payment-service ./...
""")

(workspace / "config/app.yaml").write_text("""\
server:
  port: 8080
  timeout: 30s
database:
  max_connections: 10
""")

(workspace / "api/schemas/error_response.json").write_text(json.dumps({
    "type": "object",
    "required": ["code", "message"],
    "properties": {
        "code": {"type": "integer"},
        "message": {"type": "string"}
    }
}, indent=2))

# ── OpenClaw config (the skill config) ───────────────────────────────────────
# NOTE: This is deliberately minimal / partially wrong to force the agent
# to follow the SKILL.md defaults (no useful patterns overriding defaults).
(workspace / ".openclaw/context-verifier.yaml").write_text("""\
# context-verifier configuration
version: "1.5.1"
critical_patterns:
  - "*.env"
  - "*credentials*"
  - "*secret*"
  - "AGENTS.md"
  - "pyproject.toml"
  - "Cargo.toml"
output_dir: output/context-packets
""")

# ── Pre-compute and store expected hashes for eval use ────────────────────────
# (stored in a hidden eval-support file, NOT visible to agent)
def sha256_file(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()

eval_data = {}
for rel, content in {**go_files, **sql_files}.items():
    full = workspace / rel
    eval_data[rel] = sha256_file(full)

(workspace / ".eval_hashes.json").write_text(json.dumps(eval_data, indent=2))

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")