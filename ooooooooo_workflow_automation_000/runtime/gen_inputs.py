import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "docs/architecture",
    "docs/api",
    "infra/ci",
    "infra/docker",
    "scripts/utils",
    "legacy/v1",
    "legacy/v2/core",
    "reports/2023",
    "reports/2024/q1",
    "config/env",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "docs/architecture/overview.txt": "System architecture overview - DRAFT\nNot yet reviewed.\n",
    "docs/api/endpoints.txt": "GET /validate  POST /submit  DELETE /cancel\n",
    "infra/ci/pipeline.yaml": "stages:\n  - test\n  - build\n  - deploy\n",
    "infra/docker/Dockerfile.prod": "FROM python:3.11-alpine\nCOPY . /app\n",
    "scripts/utils/clean.sh": "#!/bin/bash\nrm -rf __pycache__\n",
    "legacy/v1/validator.py": "# DEPRECATED - do not use\ndef validate(x): return True\n",
    "legacy/v2/core/engine.py": "# OLD ENGINE\nclass OldEngine: pass\n",
    "reports/2023/q4_summary.txt": "Q4 2023 summary - transactions processed: 1.2M\n",
    "reports/2024/q1/metrics.csv": "date,volume,errors\n2024-01-01,50000,12\n2024-01-02,51200,8\n",
    "config/env/dev.env": "ENV=development\nDEBUG=true\nDB_URL=sqlite:///dev.db\n",
    "config/env/prod.env": "ENV=production\nDEBUG=false\nDB_URL=postgresql://prod-db:5432/txdb\n",
    "scripts/utils/seed_data.py": "# Seed script\nTRANSACTIONS = [{'id': i, 'amount': i*10} for i in range(100)]\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── The actual implementation plan ─────────────────────────────────────────
plan_content = """\
# Implementation Plan: Transaction Validator Library v2

## Objective
Build a robust Python transaction validation library that checks transaction data for
correctness, fraud indicators, and business-rule compliance.

## Tasks

### Task 1: Setup project structure
- Create `src/` directory with `__init__.py`
- Create `tests/` directory with `__init__.py`
- Create `src/validator/__init__.py` and `src/validator/models.py`
- Deliverable: directory structure exists and is importable

### Task 2: Implement Transaction data model
- In `src/validator/models.py`, define a `Transaction` dataclass with fields:
  - `transaction_id: str`
  - `amount: float`
  - `currency: str`
  - `sender: str`
  - `receiver: str`
  - `timestamp: str`
- TDD: Write `tests/test_models.py` FIRST, then implement

### Task 3: Implement amount validation rule
- Create `src/validator/rules.py`
- Implement `validate_amount(tx: Transaction) -> bool`:
  - Returns True if amount > 0 and amount <= 1_000_000
  - Returns False otherwise
- TDD: Write `tests/test_rules.py` with at least 3 test cases FIRST, then implement

### Task 4: Implement currency validation rule
- In `src/validator/rules.py`, add `validate_currency(tx: Transaction) -> bool`:
  - Accepts only: USD, EUR, GBP, JPY, CNY
  - Returns True if currency is in allowed list, False otherwise
- TDD: Add tests to `tests/test_rules.py` FIRST, then implement

### Task 5: Implement fraud detection heuristic
- Create `src/validator/fraud.py`
- Implement `is_suspicious(tx: Transaction) -> bool`:
  - Returns True if amount > 500_000
  - Returns True if sender == receiver
  - Returns False otherwise
- TDD: Write `tests/test_fraud.py` FIRST, then implement

### Task 6: Implement main Validator class
- Create `src/validator/engine.py`
- Implement `Validator` class with method `validate(tx: Transaction) -> dict`:
  - Runs all rules (amount, currency, fraud)
  - Returns dict: `{"valid": bool, "errors": list[str], "suspicious": bool}`
- TDD: Write `tests/test_engine.py` FIRST, then implement

### Task 7: Integration test and final verification
- Create `tests/test_integration.py`
- Write an end-to-end test using `Validator` with at least 2 valid and 2 invalid transactions
- Run full test suite and confirm all tests pass

## Validation Steps
- After each task: run `pytest tests/ -v` to confirm no regressions
- After task 3: at least 3 test cases for amount validation must exist
- After task 7: full test suite must pass (0 failures)

## Dependencies
- Task 2 must complete before Tasks 3, 4, 5, 6
- Task 3 and Task 4 must complete before Task 6
- Task 5 must complete before Task 6
- Task 6 must complete before Task 7
"""

(workspace / "PLAN.md").write_text(plan_content)

# ── git init so commits are possible ──────────────────────────────────────
os.system("cd /workspace && git init && git config user.email 'agent@test.local' && git config user.name 'Agent'")

print("Workspace initialized successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")