#!/usr/bin/env python3
"""
Evaluation script for the sui-coverage task.
Checks that the agent has:
  1. Generated coverage.md via analyze_source.py
  2. Added Move tests covering the three gaps:
     A) emergency_pause() function called in a test
     B) EInsufficientFunds assertion failure path tested with #[expected_failure]
     C) classify_deposit with large amount (>=1000) branch tested
  3. Used correct #[expected_failure(abort_code = ...)] syntax
  4. Tests are syntactically valid Move (basic checks)
"""
import sys
import json
import re
from pathlib import Path

def find_file(workspace: Path, filename: str):
    """Search for a file recursively in the workspace."""
    results = list(workspace.rglob(filename))
    return results[0] if results else None

def run_checks(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight

    # ── CHECK 1: coverage.md exists ────────────────────────────────────────
    try:
        coverage_md = find_file(workspace, "coverage.md")
        if coverage_md is None:
            add_check(
                "coverage_md_exists",
                False,
                "coverage.md not found anywhere in workspace",
                weight=1.0
            )
            cov_content = ""
        else:
            cov_content = coverage_md.read_text()
            add_check(
                "coverage_md_exists",
                True,
                f"Found coverage.md at {coverage_md}",
                weight=1.0
            )
    except Exception as e:
        cov_content = ""
        add_check("coverage_md_exists", False, f"Exception reading coverage.md: {e}", weight=1.0)

    # ── CHECK 2: coverage.md contains gap identification ───────────────────
    try:
        has_emergency_pause_mention = "emergency_pause" in cov_content
        has_insufficient_mention = "EInsufficientFunds" in cov_content or "insufficient" in cov_content.lower() or "Insufficient" in cov_content
        has_branch_mention = "classify_deposit" in cov_content or "branch" in cov_content.lower() or "1000" in cov_content

        gap_count = sum([has_emergency_pause_mention, has_insufficient_mention, has_branch_mention])
        add_check(
            "coverage_md_identifies_gaps",
            gap_count >= 2,
            f"coverage.md identifies {gap_count}/3 gaps (emergency_pause={has_emergency_pause_mention}, "
            f"EInsufficientFunds={has_insufficient_mention}, branch={has_branch_mention})",
            weight=1.5
        )
    except Exception as e:
        add_check("coverage_md_identifies_gaps", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 3: Test file has new tests (more than original 4) ───────────
    try:
        # Look for the test file (could be the existing one or a new one)
        test_files = list(workspace.rglob("*.move"))
        test_files = [f for f in test_files if "test" in f.name.lower() or "tests" in str(f.parent).lower()]
        
        # Also check all .move files for test content
        all_move = list(workspace.rglob("*.move"))
        
        all_test_content = ""
        for mf in all_move:
            try:
                content = mf.read_text()
                if "#[test]" in content or "#[test_only]" in content:
                    all_test_content += content + "\n"
            except Exception:
                pass

        # Count test functions
        test_fun_matches = re.findall(r'#\[test\]', all_test_content)
        num_tests = len(test_fun_matches)
        
        add_check(
            "new_tests_added",
            num_tests >= 6,  # Started with 4, need at least 3 new ones (one per gap)
            f"Found {num_tests} test functions across all .move files (need >= 6 for 3 new gap tests)",
            weight=1.5
        )
    except Exception as e:
        add_check("new_tests_added", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 4: emergency_pause() is called in a test ────────────────────
    try:
        all_move_content = ""
        for mf in workspace.rglob("*.move"):
            try:
                c = mf.read_text()
                all_move_content += c + "\n"
            except Exception:
                pass

        # Look for emergency_pause called inside a test function
        # Strategy: find test functions that contain emergency_pause
        test_blocks = re.findall(
            r'#\[test\][^\]]*\]?\s*(?:#\[expected_failure[^\]]*\]\s*)?fun\s+\w+[^{]*\{[^}]*emergency_pause[^}]*\}',
            all_move_content,
            re.DOTALL
        )
        # Also simpler check: emergency_pause appears in the test section
        emergency_in_tests = (
            "emergency_pause" in all_move_content and
            bool(re.search(r'#\[test\].*?emergency_pause', all_move_content, re.DOTALL))
        )
        
        add_check(
            "gap_a_emergency_pause_tested",
            emergency_in_tests,
            f"emergency_pause() called inside a test function: {emergency_in_tests}",
            weight=2.0
        )
    except Exception as e:
        add_check("gap_a_emergency_pause_tested", False, f"Exception: {e}", weight=2.0)

    # ── CHECK 5: EInsufficientFunds failure path tested with expected_failure
    try:
        all_move_content = ""
        for mf in workspace.rglob("*.move"):
            try:
                c = mf.read_text()
                all_move_content += c + "\n"
            except Exception:
                pass

        # Must have #[expected_failure(abort_code = EInsufficientFunds)] or abort_code = 1
        pattern_name = r'#\s*\[\s*expected_failure\s*\(\s*abort_code\s*=\s*EInsufficientFunds'
        pattern_num  = r'#\s*\[\s*expected_failure\s*\(\s*abort_code\s*=\s*1\s*[,\)]'
        # Also accept module-qualified: vault::EInsufficientFunds
        pattern_qual = r'#\s*\[\s*expected_failure\s*\(\s*abort_code\s*=\s*vault::EInsufficientFunds'

        has_expected_failure_correct = bool(
            re.search(pattern_name, all_move_content) or
            re.search(pattern_num, all_move_content) or
            re.search(pattern_qual, all_move_content)
        )

        add_check(
            "gap_b_expected_failure_insufficient_funds",
            has_expected_failure_correct,
            f"Found correct #[expected_failure(abort_code = EInsufficientFunds)] or equivalent: {has_expected_failure_correct}",
            weight=2.5
        )
    except Exception as e:
        add_check("gap_b_expected_failure_insufficient_funds", False, f"Exception: {e}", weight=2.5)

    # ── CHECK 6: expected_failure test actually calls withdraw ─────────────
    try:
        all_move_content = ""
        for mf in workspace.rglob("*.move"):
            try:
                c = mf.read_text()
                all_move_content += c + "\n"
            except Exception:
                pass

        # Find expected_failure blocks that mention withdraw
        ef_blocks = re.findall(
            r'#\s*\[\s*expected_failure[^\]]*\]\s*fun\s+\w+[^{]*\{[^}]*\}',
            all_move_content,
            re.DOTALL
        )
        ef_calls_withdraw = any("withdraw" in b for b in ef_blocks)

        add_check(
            "gap_b_expected_failure_calls_withdraw",
            ef_calls_withdraw,
            f"At least one expected_failure test calls withdraw(): {ef_calls_withdraw}",
            weight=1.5
        )
    except Exception as e:
        add_check("gap_b_expected_failure_calls_withdraw", False, f"Exception: {e}", weight=1.5)

    # ── CHECK 7: classify_deposit large-amount branch tested ──────────────
    try:
        all_move_content = ""
        for mf in workspace.rglob("*.move"):
            try:
                c = mf.read_text()
                all_move_content += c + "\n"
            except Exception:
                pass

        # Test should call classify_deposit with value >= 1000 and assert result == 2
        has_large_branch = (
            "classify_deposit" in all_move_content and
            bool(re.search(r'classify_deposit\s*\(\s*1\d{3,}', all_move_content)) or
            bool(re.search(r'classify_deposit\s*\(\s*[2-9]\d{3}', all_move_content))
        )
        # Also accept: classify_deposit(1000) or classify_deposit(5000) etc
        has_1000_plus = bool(re.search(r'classify_deposit\s*\(\s*(\d{4,})\s*\)', all_move_content))
        if has_1000_plus:
            # Verify the number is >= 1000
            matches = re.findall(r'classify_deposit\s*\(\s*(\d+)\s*\)', all_move_content)
            has_large_branch = any(int(m) >= 1000 for m in matches)
        
        add_check(
            "gap_c_large_branch_tested",
            has_large_branch,
            f"classify_deposit called with value >= 1000 in a test: {has_large_branch}",
            weight=2.0
        )
    except Exception as e:
        add_check("gap_c_large_branch_tested", False, f"Exception: {e}", weight=2.0)

    # ── CHECK 8: No syntax issues in new tests (basic Move structure) ──────
    try:
        all_move_content = ""
        for mf in workspace.rglob("*.move"):
            try:
                c = mf.read_text()
                all_move_content += c + "\n"
            except Exception:
                pass

        # Braces must be balanced in the entire content
        open_braces = all_move_content.count("{")
        close_braces = all_move_content.count("}")
        braces_balanced = abs(open_braces - close_braces) <= 2  # small tolerance

        # Every fun must have a body
        fun_without_body = bool(re.search(r'\bfun\s+\w+[^{;]*;', all_move_content))

        syntax_ok = braces_balanced and not fun_without_body
        add_check(
            "basic_move_syntax_valid",
            syntax_ok,
            f"Braces balanced ({open_braces}/{close_braces}), no stub functions: {syntax_ok}",
            weight=1.0
        )
    except Exception as e:
        add_check("basic_move_syntax_valid", False, f"Exception: {e}", weight=1.0)

    # ── CHECK 9: sui move test --coverage --trace was run ─────────────────
    try:
        # The mock sui writes .coverage_trace.json when --coverage --trace is used
        trace_file = find_file(workspace, ".coverage_trace.json")
        trace_exists = trace_file is not None and trace_file.stat().st_size > 10
        add_check(
            "coverage_trace_generated",
            trace_exists,
            f".coverage_trace.json exists (evidence of `sui move test --coverage --trace`): {trace_exists}",
            weight=1.0
        )
    except Exception as e:
        add_check("coverage_trace_generated", False, f"Exception: {e}", weight=1.0)

    # ── Final score ────────────────────────────────────────────────────────
    max_score = 14.0  # sum of all weights
    normalized = round(total_score / max_score, 3)
    passed = normalized >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "coverage_md_exists",
            "gap_b_expected_failure_insufficient_funds",
            "gap_a_emergency_pause_tested",
            "gap_c_large_branch_tested",
        ]
    )

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "arg_error", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))