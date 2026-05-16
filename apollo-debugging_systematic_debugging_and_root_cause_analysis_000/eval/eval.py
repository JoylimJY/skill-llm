import subprocess
import sys
import json
import ast
import re
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Evaluator error: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ----------------------------------------------------------------
    # CHECK 1: The integration tests now pass
    # (i.e., the root-cause fix was applied)
    # ----------------------------------------------------------------
    def check_integration_tests_pass():
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/integration/test_reconciliation.py", "-v", "--tb=short"],
            capture_output=True, text=True, cwd=str(workspace)
        )
        passed = result.returncode == 0
        output_tail = (result.stdout + result.stderr)[-2000:]
        return passed, f"pytest exit={result.returncode}\n{output_tail}"

    checks.append(run_check("integration_tests_pass", check_integration_tests_pass))

    # ----------------------------------------------------------------
    # CHECK 2: The fix is in ledger.py (root cause), NOT only in reporter.py
    # A symptom-only fix (changing reporter.py rounding) must NOT be the sole change.
    # ----------------------------------------------------------------
    def check_fix_in_ledger():
        ledger_path = workspace / "finrecon/core/ledger.py"
        if not ledger_path.exists():
            return False, "ledger.py not found"
        content = ledger_path.read_text()
        # Must use Decimal or integer/cents arithmetic — any of these patterns
        uses_decimal = "Decimal" in content
        uses_int_cents = re.search(r'int\s*\(.*\*\s*100', content) is not None
        uses_round_internal = re.search(r'round\(.*txn\[.amount.\]', content) is not None
        # Also check: importing Decimal or using integer math
        has_from_decimal = "from decimal import" in content
        has_import_decimal = "import decimal" in content.lower()
        fixed = uses_decimal or has_from_decimal or has_import_decimal or uses_int_cents
        if fixed:
            return True, "ledger.py contains root-cause arithmetic fix (Decimal or integer-cents approach)"
        return False, "ledger.py does not appear to contain a precision-safe arithmetic fix"

    checks.append(run_check("fix_targets_root_cause_in_ledger", check_fix_in_ledger))

    # ----------------------------------------------------------------
    # CHECK 3: A new failing-test file was created BEFORE the fix
    # (per Phase 4 Step 1: create failing test case first)
    # We detect this by checking that a new test file exists that
    # explicitly tests accumulate_balances arithmetic precision,
    # beyond the pre-existing integration test.
    # ----------------------------------------------------------------
    def check_new_test_file_exists():
        test_files = list((workspace / "tests").rglob("*.py"))
        # Original integration test already exists — look for an ADDITIONAL test file
        # that the agent created (not one of the 4 pre-existing ones)
        existing = {
            "tests/__init__.py",
            "tests/unit/test_parser.py",
            "tests/unit/test_validation.py",
            "tests/unit/test_reporter.py",
            "tests/integration/test_reconciliation.py",
        }
        new_test_files = []
        for tf in test_files:
            rel = str(tf.relative_to(workspace))
            if rel not in existing and tf.name != "__init__.py":
                content = tf.read_text()
                # Must reference ledger or accumulate_balances
                if "accumulate_balances" in content or "ledger" in content.lower():
                    new_test_files.append(rel)

        if new_test_files:
            return True, f"New test file(s) targeting ledger arithmetic found: {new_test_files}"
        return False, "No new test file found that targets the root-cause (accumulate_balances in ledger.py)"

    checks.append(run_check("new_failing_test_created", check_new_test_file_exists))

    # ----------------------------------------------------------------
    # CHECK 4: All pre-existing passing tests still pass (no regression)
    # ----------------------------------------------------------------
    def check_no_regression():
        result = subprocess.run(
            ["python", "-m", "pytest",
             "tests/unit/test_parser.py",
             "tests/unit/test_validation.py",
             "tests/unit/test_reporter.py",
             "-v", "--tb=short"],
            capture_output=True, text=True, cwd=str(workspace)
        )
        passed = result.returncode == 0
        output_tail = (result.stdout + result.stderr)[-1500:]
        return passed, f"pytest exit={result.returncode}\n{output_tail}"

    checks.append(run_check("no_regression_in_existing_tests", check_no_regression))

    # ----------------------------------------------------------------
    # CHECK 5: Fix is minimal — ledger.py should not be a complete rewrite
    # (accumulate_balances function must still exist, not replaced wholesale)
    # ----------------------------------------------------------------
    def check_fix_is_minimal():
        ledger_path = workspace / "finrecon/core/ledger.py"
        if not ledger_path.exists():
            return False, "ledger.py not found"
        content = ledger_path.read_text()
        has_fn = "def accumulate_balances" in content
        has_compute = "def compute_daily_summary" in content
        if has_fn and has_compute:
            return True, "accumulate_balances and compute_daily_summary both still present (minimal fix)"
        return False, f"Functions missing — possible wholesale rewrite. accumulate_balances={has_fn}, compute_daily_summary={has_compute}"

    checks.append(run_check("fix_is_minimal_not_rewrite", check_fix_is_minimal))

    # ----------------------------------------------------------------
    # CHECK 6: reporter.py fix is NOT the sole fix (symptom not mistaken for root cause)
    # Verify the arithmetic test passes when calling ledger directly (not via reporter)
    # ----------------------------------------------------------------
    def check_arithmetic_correct_at_source():
        test_code = textwrap.dedent("""\
            import sys
            sys.path.insert(0, '/workspace')
            from finrecon.core.ledger import accumulate_balances
            txns = [{'id': f'T{i}', 'amount': 0.10, 'type': 'credit'} for i in range(100)]
            result = accumulate_balances(txns)
            assert result == 10.00, f"Got {result!r}"
            print("PASS")
        """)
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            tmpname = f.name
        try:
            result = subprocess.run(
                ["python", tmpname],
                capture_output=True, text=True, cwd=str(workspace)
            )
            passed = result.returncode == 0 and "PASS" in result.stdout
            return passed, f"Direct arithmetic check: exit={result.returncode} stdout={result.stdout!r} stderr={result.stderr[-500:]!r}"
        finally:
            os.unlink(tmpname)

    import textwrap
    checks.append(run_check("arithmetic_correct_at_source_not_just_display", check_arithmetic_correct_at_source))

    # ----------------------------------------------------------------
    # Score and output
    # ----------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count >= 5  # Must pass at least 5 of 6

    output = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()