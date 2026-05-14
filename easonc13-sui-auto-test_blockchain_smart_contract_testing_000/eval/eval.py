#!/usr/bin/env python3
"""
Evaluation script for the sui-coverage task.
Checks that the agent:
1. Generated a coverage.md report using analyze_source.py
2. Added tests for uncovered functions (emergency_pause, emergency_resume, destroy_empty_vault, compute_net_flow)
3. Added #[expected_failure] tests with correct error codes (EVaultFrozen, ENotOwner, EDepositTooSmall, EInsufficientBalance)
4. Added branch coverage tests for classify_risk (all 4 branches)
5. The coverage report shows full coverage after fixes
"""

import sys
import json
import re
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    pkg_dir = ws / "defi_vault"
    tests_dir = pkg_dir / "tests"
    sources_dir = pkg_dir / "sources"
    
    checks = []
    
    # ============================================================
    # Check 1: coverage.md was generated
    # ============================================================
    coverage_md_files = list(pkg_dir.rglob("coverage.md"))
    if not coverage_md_files:
        # Also check workspace root
        coverage_md_files = list(ws.rglob("coverage.md"))
    
    coverage_md_exists = len(coverage_md_files) > 0
    coverage_md_content = ""
    if coverage_md_exists:
        coverage_md_content = coverage_md_files[0].read_text()
    
    checks.append({
        "name": "coverage_md_generated",
        "passed": coverage_md_exists,
        "detail": f"coverage.md found at: {coverage_md_files[0] if coverage_md_exists else 'NOT FOUND'}"
    })
    
    # ============================================================
    # Check 2: coverage.md mentions the module 'vault'
    # ============================================================
    mentions_vault = "vault" in coverage_md_content.lower()
    checks.append({
        "name": "coverage_md_mentions_vault_module",
        "passed": mentions_vault,
        "detail": f"coverage.md content mentions 'vault': {mentions_vault}"
    })
    
    # ============================================================
    # Collect all test file content
    # ============================================================
    all_test_content = ""
    test_files = list(tests_dir.glob("*.move")) + list(sources_dir.glob("*.move"))
    for tf in test_files:
        try:
            all_test_content += tf.read_text() + "\n"
        except Exception as e:
            pass
    
    # ============================================================
    # Check 3: emergency_pause is now called in tests
    # ============================================================
    emergency_pause_tested = bool(re.search(r'vault::emergency_pause\s*\(', all_test_content))
    checks.append({
        "name": "emergency_pause_tested",
        "passed": emergency_pause_tested,
        "detail": f"vault::emergency_pause() called in at least one test: {emergency_pause_tested}"
    })
    
    # ============================================================
    # Check 4: emergency_resume is now called in tests
    # ============================================================
    emergency_resume_tested = bool(re.search(r'vault::emergency_resume\s*\(', all_test_content))
    checks.append({
        "name": "emergency_resume_tested",
        "passed": emergency_resume_tested,
        "detail": f"vault::emergency_resume() called in at least one test: {emergency_resume_tested}"
    })
    
    # ============================================================
    # Check 5: destroy_empty_vault is called in tests
    # ============================================================
    destroy_empty_tested = bool(re.search(r'vault::destroy_empty_vault\s*\(', all_test_content))
    checks.append({
        "name": "destroy_empty_vault_tested",
        "passed": destroy_empty_tested,
        "detail": f"vault::destroy_empty_vault() called in at least one test: {destroy_empty_tested}"
    })
    
    # ============================================================
    # Check 6: compute_net_flow is called in tests
    # ============================================================
    net_flow_tested = bool(re.search(r'vault::compute_net_flow\s*\(', all_test_content))
    checks.append({
        "name": "compute_net_flow_tested",
        "passed": net_flow_tested,
        "detail": f"vault::compute_net_flow() called in at least one test: {net_flow_tested}"
    })
    
    # ============================================================
    # Check 7: EVaultFrozen expected_failure test exists
    # ============================================================
    vault_frozen_ef = bool(re.search(
        r'#\[expected_failure\s*\(\s*abort_code\s*=\s*(?:vault::)?EVaultFrozen\s*\)\]',
        all_test_content
    ))
    checks.append({
        "name": "EVaultFrozen_expected_failure_test",
        "passed": vault_frozen_ef,
        "detail": f"#[expected_failure(abort_code = EVaultFrozen)] test found: {vault_frozen_ef}"
    })
    
    # ============================================================
    # Check 8: ENotOwner expected_failure test exists
    # ============================================================
    not_owner_ef = bool(re.search(
        r'#\[expected_failure\s*\(\s*abort_code\s*=\s*(?:vault::)?ENotOwner\s*\)\]',
        all_test_content
    ))
    checks.append({
        "name": "ENotOwner_expected_failure_test",
        "passed": not_owner_ef,
        "detail": f"#[expected_failure(abort_code = ENotOwner)] test found: {not_owner_ef}"
    })
    
    # ============================================================
    # Check 9: EDepositTooSmall expected_failure test exists
    # ============================================================
    deposit_too_small_ef = bool(re.search(
        r'#\[expected_failure\s*\(\s*abort_code\s*=\s*(?:vault::)?EDepositTooSmall\s*\)\]',
        all_test_content
    ))
    checks.append({
        "name": "EDepositTooSmall_expected_failure_test",
        "passed": deposit_too_small_ef,
        "detail": f"#[expected_failure(abort_code = EDepositTooSmall)] test found: {deposit_too_small_ef}"
    })
    
    # ============================================================
    # Check 10: EInsufficientBalance expected_failure test exists
    # (for either withdraw or deposit overflow path)
    # ============================================================
    insuf_balance_ef = bool(re.search(
        r'#\[expected_failure\s*\(\s*abort_code\s*=\s*(?:vault::)?EInsufficientBalance\s*\)\]',
        all_test_content
    ))
    checks.append({
        "name": "EInsufficientBalance_expected_failure_test",
        "passed": insuf_balance_ef,
        "detail": f"#[expected_failure(abort_code = EInsufficientBalance)] test found: {insuf_balance_ef}"
    })
    
    # ============================================================
    # Check 11: classify_risk has at least 3 different test variants
    # (need to cover 0, <10000, <100000, >=100000)
    # ============================================================
    classify_calls = re.findall(r'vault::classify_risk\s*\(([^)]+)\)', all_test_content)
    # Count unique values/branches tested
    unique_classify_values = set()
    for call in classify_calls:
        val = call.strip()
        try:
            numeric_val = int(val.replace('_', ''))
            if numeric_val == 0:
                unique_classify_values.add("zero")
            elif numeric_val < 10000:
                unique_classify_values.add("low")
            elif numeric_val < 100000:
                unique_classify_values.add("medium")
            else:
                unique_classify_values.add("high")
        except ValueError:
            # Variable, count as a branch
            unique_classify_values.add(val[:10])
    
    classify_branches_covered = len(unique_classify_values) >= 3 or len(classify_calls) >= 3
    checks.append({
        "name": "classify_risk_branch_coverage",
        "passed": classify_branches_covered,
        "detail": f"classify_risk called with {len(classify_calls)} different args covering {len(unique_classify_values)} branches (need >=3): {list(unique_classify_values)}"
    })
    
    # ============================================================
    # Check 12: Tests use proper #[test] annotation (not just naive calls)
    # ============================================================
    proper_test_annotations = len(re.findall(r'#\[test\]', all_test_content))
    # Agent should have added at least 5 new tests beyond the original 3
    has_sufficient_new_tests = proper_test_annotations >= 8
    checks.append({
        "name": "sufficient_test_count",
        "passed": has_sufficient_new_tests,
        "detail": f"Found {proper_test_annotations} #[test] annotations (need >= 8 to cover all gaps)"
    })
    
    # ============================================================
    # Check 13: Run analyze_source.py and verify it reports improved/full coverage
    # ============================================================
    final_analysis_passed = False
    final_analysis_detail = "Could not run analyze_source.py"
    try:
        result = subprocess.run(
            ["python3", "/root/clawd/skills/sui-coverage/analyze_source.py",
             "-m", "vault", "-p", str(pkg_dir)],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        
        # Check if full coverage achieved OR significantly fewer gaps
        if "FULL COVERAGE ACHIEVED" in output or "0 coverage gaps" in output.lower():
            final_analysis_passed = True
            final_analysis_detail = "analyze_source.py reports full coverage achieved"
        else:
            # Count remaining gaps
            remaining_gaps = re.search(r'(\d+) coverage gaps found', output)
            if remaining_gaps:
                gap_count = int(remaining_gaps.group(1))
                # Originally had ~5+ gaps; if reduced to <= 1 it's close
                final_analysis_passed = gap_count <= 1
                final_analysis_detail = f"analyze_source.py reports {gap_count} remaining gaps"
            else:
                final_analysis_detail = f"analyze_source.py output: {output[:300]}"
    except Exception as e:
        final_analysis_detail = f"Exception running analyze_source.py: {e}"
    
    checks.append({
        "name": "final_coverage_analysis_improved",
        "passed": final_analysis_passed,
        "detail": final_analysis_detail
    })
    
    # ============================================================
    # Check 14: AdminCap is properly used via test_only helper
    # (not constructed directly, which would be invalid Move)
    # ============================================================
    # Agent should use vault::create_admin_cap, not AdminCap { id: ... }
    direct_admin_cap_construct = bool(re.search(r'AdminCap\s*\{', all_test_content))
    uses_create_admin_cap = bool(re.search(r'vault::create_admin_cap\s*\(', all_test_content))
    
    # If emergency_pause is tested, agent should use the proper helper
    if emergency_pause_tested:
        admin_cap_usage_correct = uses_create_admin_cap and not direct_admin_cap_construct
        checks.append({
            "name": "admin_cap_via_test_helper",
            "passed": admin_cap_usage_correct,
            "detail": f"Uses vault::create_admin_cap(): {uses_create_admin_cap}, Direct construction: {direct_admin_cap_construct}"
        })
    else:
        checks.append({
            "name": "admin_cap_via_test_helper",
            "passed": False,
            "detail": "emergency_pause not tested so AdminCap helper usage cannot be verified"
        })
    
    # ============================================================
    # Compute final score
    # ============================================================
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    overall_passed = score >= 0.80  # Require 80%+ to pass
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    try:
        result = run_checks(sys.argv[1])
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": f"Evaluation crashed: {e}"}]
        }))