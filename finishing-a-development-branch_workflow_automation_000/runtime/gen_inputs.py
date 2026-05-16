#!/usr/bin/env python3
"""
Generate the sandbox workspace: a fintech data pipeline repo with a git worktree
set up for a feature branch. The agent must integrate the feature branch back
into main via local merge and clean up the worktree.
"""

import os
import subprocess
import random
import textwrap
import shlex
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
REPO_DIR = WORKSPACE / "fintech-pipeline"
WORKTREE_DIR = WORKSPACE / "worktrees" / "currency-converter"

# ── 1. Create main repo ───────────────────────────────────────────────────────
REPO_DIR.mkdir(parents=True, exist_ok=True)

def git(cmd, cwd=None):
    cwd = cwd or REPO_DIR
    result = subprocess.run(
        ["git"] + shlex.split(cmd),
        cwd=str(cwd),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Some commands are expected to sometimes fail; print for debug
        print(f"[git {cmd}] stderr: {result.stderr.strip()}")
    return result

git("init", cwd=REPO_DIR)
git("checkout -b main", cwd=REPO_DIR)

# ── 2. Scaffold realistic fintech project structure ───────────────────────────
# Source tree
(REPO_DIR / "src").mkdir()
(REPO_DIR / "src" / "pipeline").mkdir()
(REPO_DIR / "src" / "pipeline" / "__init__.py").write_text("")
(REPO_DIR / "src" / "pipeline" / "ingestion.py").write_text(textwrap.dedent("""\
    \"\"\"Data ingestion layer for market feed processing.\"\"\"
    import json
    from pathlib import Path

    class MarketFeedIngester:
        def __init__(self, feed_path: str):
            self.feed_path = Path(feed_path)

        def load(self):
            with open(self.feed_path) as f:
                return json.load(f)

        def validate(self, record: dict) -> bool:
            required = {"symbol", "price", "timestamp", "currency"}
            return required.issubset(record.keys())
"""))

(REPO_DIR / "src" / "pipeline" / "normalizer.py").write_text(textwrap.dedent("""\
    \"\"\"Price normalization utilities.\"\"\"

    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY"}

    def normalize_price(price: float, currency: str) -> float:
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        return round(price, 6)
"""))

(REPO_DIR / "src" / "pipeline" / "storage.py").write_text(textwrap.dedent("""\
    \"\"\"Time-series storage backend abstraction.\"\"\"
    import sqlite3
    from typing import List, Dict

    class TimeSeriesStore:
        def __init__(self, db_path: str = ":memory:"):
            self.conn = sqlite3.connect(db_path)
            self._init_schema()

        def _init_schema(self):
            self.conn.execute(
                \"\"\"CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT NOT NULL,
                    ts INTEGER NOT NULL
                )\"\"\"
            )
            self.conn.commit()

        def insert(self, records: List[Dict]):
            self.conn.executemany(
                "INSERT INTO prices (symbol, price, currency, ts) VALUES (?,?,?,?)",
                [(r["symbol"], r["price"], r["currency"], r["timestamp"]) for r in records]
            )
            self.conn.commit()

        def count(self) -> int:
            return self.conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
"""))

# Config files (distractors)
(REPO_DIR / "config").mkdir()
(REPO_DIR / "config" / "feeds.yaml").write_text(textwrap.dedent("""\
    feeds:
      - name: nasdaq_level2
        endpoint: "internal://nasdaq/l2"
        interval_ms: 100
      - name: fx_spot
        endpoint: "internal://fx/spot"
        interval_ms: 500
"""))

(REPO_DIR / "config" / "logging.yaml").write_text(textwrap.dedent("""\
    version: 1
    handlers:
      console:
        class: logging.StreamHandler
        level: INFO
    root:
      level: INFO
      handlers: [console]
"""))

(REPO_DIR / "config" / "db.yaml").write_text(textwrap.dedent("""\
    database:
      path: /var/lib/pipeline/prices.db
      wal_mode: true
      cache_size_mb: 256
"""))

# Docs (distractors)
(REPO_DIR / "docs").mkdir()
(REPO_DIR / "docs" / "architecture.md").write_text(textwrap.dedent("""\
    # Architecture

    ## Components
    - **Ingester**: Reads raw feed data
    - **Normalizer**: Standardises prices to 6dp
    - **Store**: Writes to SQLite time-series DB

    ## Data Flow
    Feed → Ingester → Normalizer → Store
"""))
(REPO_DIR / "docs" / "runbook.md").write_text(textwrap.dedent("""\
    # Operations Runbook

    ## Restart procedure
    1. Stop the ingester service: `systemctl stop pipeline-ingester`
    2. Verify DB integrity: `sqlite3 /var/lib/pipeline/prices.db "PRAGMA integrity_check;"`
    3. Restart: `systemctl start pipeline-ingester`
"""))
(REPO_DIR / "docs" / "onboarding.md").write_text(textwrap.dedent("""\
    # Developer Onboarding

    Clone the repo and run `pip install -e .[dev]`.
    All tests live under `tests/`.
"""))

# Scripts (distractors)
(REPO_DIR / "scripts").mkdir()
(REPO_DIR / "scripts" / "backfill.py").write_text(textwrap.dedent("""\
    \"\"\"One-off backfill script for historical price data.\"\"\"
    import argparse, sys

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("--from-date", required=True)
        parser.add_argument("--to-date", required=True)
        args = parser.parse_args()
        print(f"Backfilling from {args.from_date} to {args.to_date}")

    if __name__ == "__main__":
        main()
"""))
(REPO_DIR / "scripts" / "health_check.sh").write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Checking pipeline health..."
    curl -sf http://localhost:8080/health || { echo "UNHEALTHY"; exit 1; }
    echo "OK"
"""))

# CI config (distractor)
(REPO_DIR / ".github").mkdir()
(REPO_DIR / ".github" / "workflows").mkdir()
(REPO_DIR / ".github" / "workflows" / "ci.yml").write_text(textwrap.dedent("""\
    name: CI
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: actions/setup-python@v4
            with:
              python-version: '3.11'
          - run: pip install pytest
          - run: pytest
"""))

# Setup.py (distractor)
(REPO_DIR / "setup.py").write_text(textwrap.dedent("""\
    from setuptools import setup, find_packages
    setup(
        name="fintech-pipeline",
        version="0.4.1",
        packages=find_packages("src"),
        package_dir={"": "src"},
    )
"""))

# ── 3. Tests on main (passing) ────────────────────────────────────────────────
(REPO_DIR / "tests").mkdir()
(REPO_DIR / "tests" / "__init__.py").write_text("")
(REPO_DIR / "tests" / "test_ingestion.py").write_text(textwrap.dedent("""\
    import pytest, json, tempfile, os
    from pipeline.ingestion import MarketFeedIngester

    def test_validate_valid_record():
        ingester = MarketFeedIngester("/dev/null")
        record = {"symbol": "AAPL", "price": 182.5, "timestamp": 1700000000, "currency": "USD"}
        assert ingester.validate(record) is True

    def test_validate_missing_field():
        ingester = MarketFeedIngester("/dev/null")
        record = {"symbol": "AAPL", "price": 182.5, "timestamp": 1700000000}
        assert ingester.validate(record) is False
"""))

(REPO_DIR / "tests" / "test_normalizer.py").write_text(textwrap.dedent("""\
    import pytest
    from pipeline.normalizer import normalize_price

    def test_normalize_usd():
        assert normalize_price(100.123456789, "USD") == 100.123457

    def test_normalize_unsupported():
        with pytest.raises(ValueError, match="Unsupported currency"):
            normalize_price(1.0, "CHF")
"""))

(REPO_DIR / "tests" / "test_storage.py").write_text(textwrap.dedent("""\
    import pytest
    from pipeline.storage import TimeSeriesStore

    def test_insert_and_count():
        store = TimeSeriesStore(":memory:")
        records = [
            {"symbol": "AAPL", "price": 182.5, "currency": "USD", "timestamp": 1700000001},
            {"symbol": "MSFT", "price": 375.2, "currency": "USD", "timestamp": 1700000002},
        ]
        store.insert(records)
        assert store.count() == 2
"""))

# conftest for sys.path
(REPO_DIR / "conftest.py").write_text(textwrap.dedent("""\
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
"""))

# ── 4. Initial commit on main ─────────────────────────────────────────────────
git("add .", cwd=REPO_DIR)
git("commit -m 'Initial commit: pipeline skeleton'", cwd=REPO_DIR)

# ── 5. Create feature branch and add currency converter ───────────────────────
git("checkout -b feature/currency-converter", cwd=REPO_DIR)

(REPO_DIR / "src" / "pipeline" / "currency.py").write_text(textwrap.dedent("""\
    \"\"\"Currency conversion module for multi-currency price normalisation.\"\"\"
    from typing import Optional

    # Rates relative to USD (illustrative, static for testing)
    _RATES_TO_USD = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.27,
        "JPY": 0.0067,
        "CHF": 1.12,
        "CAD": 0.74,
        "AUD": 0.65,
    }

    class CurrencyConverter:
        def __init__(self, rates: Optional[dict] = None):
            self._rates = rates or _RATES_TO_USD

        def to_usd(self, amount: float, source_currency: str) -> float:
            if source_currency not in self._rates:
                raise ValueError(f"Unknown currency: {source_currency}")
            return round(amount * self._rates[source_currency], 6)

        def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
            usd = self.to_usd(amount, from_currency)
            if to_currency not in self._rates:
                raise ValueError(f"Unknown currency: {to_currency}")
            return round(usd / self._rates[to_currency], 6)

        def supported_currencies(self) -> list:
            return sorted(self._rates.keys())
"""))

(REPO_DIR / "tests" / "test_currency.py").write_text(textwrap.dedent("""\
    import pytest
    from pipeline.currency import CurrencyConverter

    def test_usd_to_usd():
        c = CurrencyConverter()
        assert c.to_usd(100.0, "USD") == 100.0

    def test_eur_to_usd():
        c = CurrencyConverter()
        result = c.to_usd(100.0, "EUR")
        assert abs(result - 108.0) < 0.01

    def test_convert_eur_to_gbp():
        c = CurrencyConverter()
        result = c.convert(100.0, "EUR", "GBP")
        expected = round(108.0 / 1.27, 6)
        assert abs(result - expected) < 0.001

    def test_unknown_currency_raises():
        c = CurrencyConverter()
        with pytest.raises(ValueError, match="Unknown currency"):
            c.to_usd(50.0, "XYZ")

    def test_supported_currencies_sorted():
        c = CurrencyConverter()
        supported = c.supported_currencies()
        assert supported == sorted(supported)
        assert "USD" in supported
        assert "EUR" in supported
"""))

git("add .", cwd=REPO_DIR)
git("commit -m 'feat: add multi-currency conversion module'", cwd=REPO_DIR)

# Second commit on feature branch (more realistic)
(REPO_DIR / "src" / "pipeline" / "normalizer.py").write_text(textwrap.dedent("""\
    \"\"\"Price normalization utilities with multi-currency support.\"\"\"
    from pipeline.currency import CurrencyConverter

    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"}

    _converter = CurrencyConverter()

    def normalize_price(price: float, currency: str) -> float:
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        return round(price, 6)

    def normalize_to_usd(price: float, currency: str) -> float:
        \"\"\"Convert any supported currency to USD.\"\"\"
        return _converter.to_usd(price, currency)
"""))

# Update the normalizer test to reflect that CHF is now supported on the feature branch
(REPO_DIR / "tests" / "test_normalizer.py").write_text(textwrap.dedent("""\
    import pytest
    from pipeline.normalizer import normalize_price

    def test_normalize_usd():
        assert normalize_price(100.123456789, "USD") == 100.123457

    def test_normalize_chf():
        assert normalize_price(100.0, "CHF") == 100.0

    def test_normalize_unsupported():
        with pytest.raises(ValueError, match="Unsupported currency"):
            normalize_price(1.0, "SGD")
"""))

git("add .", cwd=REPO_DIR)
git("commit -m 'feat: extend normalizer with USD conversion'", cwd=REPO_DIR)

# Go back to main to set up worktree
git("checkout main", cwd=REPO_DIR)

# ── 6. Add the worktree ───────────────────────────────────────────────────────
WORKTREE_DIR.parent.mkdir(parents=True, exist_ok=True)

result = subprocess.run(
    ["git", "worktree", "add", str(WORKTREE_DIR), "feature/currency-converter"],
    cwd=str(REPO_DIR),
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"ERROR: git worktree add failed: {result.stderr.strip()}")
    raise RuntimeError("Failed to create worktree")
print(f"Worktree add: {result.stdout.strip()} {result.stderr.strip()}")

# ── 7. Verify the setup ───────────────────────────────────────────────────────
wt_list = subprocess.run(
    ["git", "worktree", "list"],
    cwd=str(REPO_DIR),
    capture_output=True, text=True
)
print("Worktrees:\n", wt_list.stdout)

branch_list = subprocess.run(
    ["git", "branch"],
    cwd=str(REPO_DIR),
    capture_output=True, text=True
)
print("Branches:\n", branch_list.stdout)

# ── 8. Write a context note for the agent (not a hint file — operational) ─────
# This simulates the ticket/context the agent might receive alongside the prompt.
# We write it to a neutral location as "project metadata" not a README.
(REPO_DIR / "TICKET.txt").write_text(textwrap.dedent("""\
    JIRA: FIN-2847
    Title: Multi-currency price normalisation
    Author: sarah.chen@fintech.example
    Status: Implementation complete — awaiting integration

    Branch: feature/currency-converter
    Worktree: /workspace/worktrees/currency-converter

    Notes:
    - All unit tests pass locally
    - Reviewed by: marco.rossi@fintech.example
    - No migration needed (additive change)
"""))

print("Workspace generation complete.")
print(f"  Main repo: {REPO_DIR}")
print(f"  Worktree:  {WORKTREE_DIR}")