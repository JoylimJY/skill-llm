import os
import subprocess
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# --- Project Structure ---
dirs = [
    "finrecon/core",
    "finrecon/reporting",
    "finrecon/ingestion",
    "finrecon/utils",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "scripts",
    "docs",
    "config",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- __init__.py files ---
for pkg in ["finrecon", "finrecon/core", "finrecon/reporting", "finrecon/ingestion", "finrecon/utils", "tests"]:
    (WORKSPACE / pkg / "__init__.py").write_text("")

# ============================================================
# CORE BUG: The real bug lives here.
# accumulate_balances() uses raw float addition, causing
# floating-point precision errors on large transaction sets.
# Two prior "fixes" are documented in comments but only patched
# the reporting layer (symptoms), not this root cause.
# ============================================================
(WORKSPACE / "finrecon/core/ledger.py").write_text(textwrap.dedent("""\
    \"\"\"
    Core ledger arithmetic for the FinRecon reconciliation engine.

    CHANGE LOG (inline, pre-git-migration):
      2024-01-08  rsmith   Fixed display rounding in reporter (patch #1)
      2024-01-15  jdoe     Changed report format to show 2dp always (patch #2)
    \"\"\"

    def accumulate_balances(transactions):
        \"\"\"
        Sum a list of transaction amounts (float) into a running balance.

        Args:
            transactions: list of dicts with keys 'id', 'amount', 'type'
                          type is 'credit' or 'debit'
        Returns:
            float: net balance (credits - debits)
        \"\"\"
        balance = 0.0
        for txn in transactions:
            if txn['type'] == 'credit':
                balance += txn['amount']
            elif txn['type'] == 'debit':
                balance -= txn['amount']
        return balance


    def compute_daily_summary(days):
        \"\"\"
        Compute per-day net balance from a list of day buckets.

        Args:
            days: list of lists of transaction dicts
        Returns:
            list of float: one net balance per day
        \"\"\"
        return [accumulate_balances(day_txns) for day_txns in days]
"""))

# ============================================================
# REPORTING LAYER (symptom patches were applied here — wrong place)
# ============================================================
(WORKSPACE / "finrecon/reporting/reporter.py").write_text(textwrap.dedent("""\
    \"\"\"
    FinRecon daily balance reporter.

    Patch #1 (2024-01-08, rsmith): added round(..., 2) on output — did NOT fix
    discrepancies on multi-day reconciliation.
    Patch #2 (2024-01-15, jdoe): forced ':.2f' format — still seeing wrong totals
    in production on large datasets.
    \"\"\"
    from finrecon.core.ledger import compute_daily_summary


    def generate_report(days, account_id):
        \"\"\"
        Produce a text report of daily balances for an account.
        \"\"\"
        summaries = compute_daily_summary(days)
        lines = [f"Account: {account_id}", "=" * 40]
        for i, bal in enumerate(summaries):
            # Patch #2: always show 2dp
            lines.append(f"  Day {i+1:03d}: {bal:.2f}")
        lines.append("=" * 40)
        # Patch #1: round grand total
        grand_total = round(sum(summaries), 2)
        lines.append(f"  GRAND TOTAL: {grand_total:.2f}")
        return "\\n".join(lines)
"""))

# ============================================================
# INGESTION LAYER
# ============================================================
(WORKSPACE / "finrecon/ingestion/parser.py").write_text(textwrap.dedent("""\
    \"\"\"
    Parses raw CSV-like transaction records into structured dicts.
    \"\"\"
    import csv
    import io


    def parse_transactions(raw_csv):
        \"\"\"
        Parse a CSV string of transactions.
        Columns: id, amount, type
        \"\"\"
        reader = csv.DictReader(io.StringIO(raw_csv))
        results = []
        for row in reader:
            results.append({
                'id': row['id'].strip(),
                'amount': float(row['amount'].strip()),
                'type': row['type'].strip().lower(),
            })
        return results
"""))

# ============================================================
# UTILS
# ============================================================
(WORKSPACE / "finrecon/utils/validation.py").write_text(textwrap.dedent("""\
    def validate_transaction(txn):
        assert 'id' in txn
        assert 'amount' in txn
        assert 'type' in txn
        assert txn['type'] in ('credit', 'debit')
        assert txn['amount'] >= 0
        return True
"""))

(WORKSPACE / "finrecon/utils/formatting.py").write_text(textwrap.dedent("""\
    def format_currency(amount):
        return f\"${amount:,.2f}\"
"""))

# ============================================================
# EXISTING (PASSING) TESTS — distractor tests that pass fine
# ============================================================
(WORKSPACE / "tests/unit/test_parser.py").write_text(textwrap.dedent("""\
    from finrecon.ingestion.parser import parse_transactions

    RAW = \"\"\"id,amount,type
    T001,100.00,credit
    T002,50.00,debit
    T003,25.50,credit
    \"\"\"

    def test_parse_basic():
        txns = parse_transactions(RAW)
        assert len(txns) == 3
        assert txns[0]['type'] == 'credit'
        assert txns[1]['amount'] == 50.0

    def test_parse_types_lowercase():
        raw = \"id,amount,type\\nT001,10.0,CREDIT\\n\"
        txns = parse_transactions(raw)
        assert txns[0]['type'] == 'credit'
"""))

(WORKSPACE / "tests/unit/test_validation.py").write_text(textwrap.dedent("""\
    import pytest
    from finrecon.utils.validation import validate_transaction

    def test_valid_credit():
        assert validate_transaction({'id': 'T1', 'amount': 10.0, 'type': 'credit'})

    def test_valid_debit():
        assert validate_transaction({'id': 'T2', 'amount': 5.0, 'type': 'debit'})

    def test_missing_field():
        with pytest.raises((AssertionError, KeyError)):
            validate_transaction({'id': 'T3', 'amount': 10.0})
"""))

(WORKSPACE / "tests/unit/test_reporter.py").write_text(textwrap.dedent("""\
    from finrecon.reporting.reporter import generate_report

    def test_report_contains_account():
        days = [[{'id': 'T1', 'amount': 100.0, 'type': 'credit'}]]
        report = generate_report(days, 'ACC-001')
        assert 'ACC-001' in report

    def test_report_contains_day():
        days = [[{'id': 'T1', 'amount': 50.0, 'type': 'credit'}]]
        report = generate_report(days, 'ACC-002')
        assert 'Day 001' in report
"""))

# ============================================================
# INTEGRATION TEST that FAILS — demonstrates the precision bug
# This is the known-failing test that prompted the bug report.
# ============================================================
(WORKSPACE / "tests/integration/test_reconciliation.py").write_text(textwrap.dedent("""\
    \"\"\"
    Integration test for multi-day reconciliation accuracy.

    BUG REPORT (2024-01-20):
    On accounts with many small fractional transactions, the grand total
    is off by several cents compared to the authoritative ledger system.
    Two patches have been applied to reporter.py (rounding, formatting)
    but the discrepancy persists.

    Repro: accumulate 10 days of 0.10 credit transactions (100 per day)
    Expected grand total: exactly 100.00 (1000 x 0.10)
    Actual grand total:   varies, e.g. 99.9999999... or 100.00000000001...
    \"\"\"
    from finrecon.core.ledger import accumulate_balances, compute_daily_summary


    def test_single_day_hundred_dimes():
        \"\"\"100 credits of 0.10 must sum to exactly 10.00\"\"\"
        txns = [{'id': f'T{i}', 'amount': 0.10, 'type': 'credit'} for i in range(100)]
        result = accumulate_balances(txns)
        assert result == 10.00, f\"Expected 10.00, got {result!r}\"


    def test_ten_days_grand_total():
        \"\"\"10 days x 100 dimes each must total exactly 100.00\"\"\"
        day = [{'id': f'T{i}', 'amount': 0.10, 'type': 'credit'} for i in range(100)]
        days = [day for _ in range(10)]
        summaries = compute_daily_summary(days)
        grand_total = sum(summaries)
        assert grand_total == 100.00, f\"Expected 100.00, got {grand_total!r}\"


    def test_mixed_credit_debit_precision():
        \"\"\"Mixed small transactions must net to exact zero when equal credits and debits\"\"\"
        txns = (
            [{'id': f'C{i}', 'amount': 0.10, 'type': 'credit'} for i in range(50)] +
            [{'id': f'D{i}', 'amount': 0.10, 'type': 'debit'}  for i in range(50)]
        )
        result = accumulate_balances(txns)
        assert result == 0.00, f\"Expected 0.00, got {result!r}\"
"""))

# ============================================================
# FIXTURE DATA
# ============================================================
(WORKSPACE / "tests/fixtures/sample_transactions.csv").write_text(
    "id,amount,type\n"
    "T001,0.10,credit\n" * 100 +
    "T101,0.10,debit\n" * 50
)

# ============================================================
# SCRIPTS & DOCS (distractors)
# ============================================================
(WORKSPACE / "scripts/run_daily_recon.py").write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Nightly reconciliation runner.\"\"\"
    import sys
    from finrecon.ingestion.parser import parse_transactions
    from finrecon.reporting.reporter import generate_report

    if __name__ == '__main__':
        print('Reconciliation runner — invoke via scheduler')
"""))

(WORKSPACE / "scripts/export_report.sh").write_text(
    "#!/bin/bash\n# Export daily report to /tmp/report.txt\n"
    "python -m finrecon.reporting.reporter \"$@\" > /tmp/report.txt\n"
)

(WORKSPACE / "config/recon_config.yaml").write_text(textwrap.dedent("""\
    account_ids:
      - ACC-001
      - ACC-002
    precision: 2
    currency: USD
    report_dir: /var/reports/finrecon
"""))

(WORKSPACE / "docs/architecture.md").write_text(textwrap.dedent("""\
    # FinRecon Architecture

    ## Components
    - **Ingestion**: Parses raw CSV feeds from upstream banking APIs
    - **Core Ledger**: Accumulates and computes balances
    - **Reporting**: Generates human-readable reconciliation reports

    ## Known Issues
    See JIRA board for open tickets.
"""))

(WORKSPACE / "docs/runbook.md").write_text(textwrap.dedent("""\
    # Operational Runbook

    ## Daily Reconciliation
    1. Ingest files from /data/incoming
    2. Run reconciliation: `python scripts/run_daily_recon.py`
    3. Verify report output
    4. Alert on discrepancies > $0.01
"""))

# ============================================================
# skill_context files
# ============================================================
(WORKSPACE / "skill_context").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "skill_context/SKILL.md").write_text("")
(WORKSPACE / "skill_context/_meta.json").write_text("{}")

# ============================================================
# Git history showing the two prior failed fixes
# ============================================================
os.chdir(WORKSPACE)
subprocess.run(["git", "init"], check=True)
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "Initial commit: FinRecon v1.0 baseline"], check=True)

# Simulate patch #1: rounding in reporter (wrong fix)
# The content is already baked in, so use --allow-empty to record the commit
subprocess.run(["git", "add", "finrecon/reporting/reporter.py"], check=True)
subprocess.run(["git", "commit", "--allow-empty", "-m",
    "fix(reporter): add round(...,2) on grand total output - attempt to fix balance discrepancy (patch #1)"],
    check=True)

# Simulate patch #2: formatting change (wrong fix)
subprocess.run(["git", "add", "finrecon/reporting/reporter.py"], check=True)
subprocess.run(["git", "commit", "--allow-empty", "-m",
    "fix(reporter): force :.2f formatting on all daily balances - discrepancy still reported by QA (patch #2)"],
    check=True)

print("Workspace initialized at /workspace")
print("Run: cd /workspace && pytest tests/ -v  to see the failing integration tests.")