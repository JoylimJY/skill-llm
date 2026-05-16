import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # ─── CHECK 1: Preferences file at correct proprietary path ──────────────
    pref_path = Path.home() / ".openclaw" / "workspace" / ".iterative-code-review" / "preferences.json"
    
    pref_data = None
    try:
        pref_data = load_json_file(pref_path)
        checks.append({
            "name": "preferences.json at correct path",
            "passed": True,
            "detail": f"Found preferences.json at {pref_path}"
        })
    except FileNotFoundError:
        checks.append({
            "name": "preferences.json at correct path",
            "passed": False,
            "detail": f"File not found at proprietary path: {pref_path}. Agent may have placed it elsewhere."
        })
    except json.JSONDecodeError as e:
        checks.append({
            "name": "preferences.json at correct path",
            "passed": False,
            "detail": f"File found but invalid JSON: {e}"
        })

    # ─── CHECK 2: preferences.json has all required fields with correct types ──
    if pref_data is not None:
        required_fields = {
            "autoFix": bool,
            "autoContinue": bool,
            "maxRounds": int,
            "severityThreshold": str
        }
        valid_severities = {"P0", "P1", "P2", "P3"}
        field_issues = []
        
        for field, expected_type in required_fields.items():
            if field not in pref_data:
                field_issues.append(f"Missing field: {field}")
            elif not isinstance(pref_data[field], expected_type):
                field_issues.append(f"Field {field} has wrong type: expected {expected_type.__name__}, got {type(pref_data[field]).__name__}")
        
        if "severityThreshold" in pref_data and pref_data["severityThreshold"] not in valid_severities:
            field_issues.append(f"severityThreshold must be P0/P1/P2/P3, got: {pref_data.get('severityThreshold')}")
        
        if "maxRounds" in pref_data and isinstance(pref_data["maxRounds"], int):
            if pref_data["maxRounds"] > 10:
                field_issues.append(f"maxRounds exceeds MAX_ROUNDS=10 limit: {pref_data['maxRounds']}")
        
        checks.append({
            "name": "preferences.json fields valid",
            "passed": len(field_issues) == 0,
            "detail": "All required fields present and typed correctly" if not field_issues else "; ".join(field_issues)
        })
    else:
        checks.append({
            "name": "preferences.json fields valid",
            "passed": False,
            "detail": "Cannot validate fields - file not loaded"
        })

    # ─── CHECK 3: Pre-flight assessment file exists ───────────────────────────
    # Accept any JSON file with "preflight" in name or exact names
    preflight_candidates = list(workspace.rglob("preflight*.json")) + \
                           list(workspace.rglob("pre_flight*.json")) + \
                           list(workspace.rglob("pre-flight*.json")) + \
                           list(workspace.rglob("preflight_assessment*")) + \
                           list(workspace.rglob("*preflight*assessment*"))
    
    preflight_data = None
    preflight_path = None
    for p in preflight_candidates:
        try:
            preflight_data = load_json_file(p)
            preflight_path = p
            break
        except Exception:
            continue
    
    checks.append({
        "name": "preflight_assessment.json exists",
        "passed": preflight_data is not None,
        "detail": f"Found at {preflight_path}" if preflight_data else f"No preflight JSON found in {workspace}. Searched for: preflight*.json, pre_flight*.json"
    })

    # ─── CHECK 4: Preflight correctly identifies file counts and size tier ─────
    if preflight_data is not None:
        # The PR adds 7 new files + modifies 2 = 9 total changed files → "small" tier (<10)
        # New files: processor.js, refund.js, webhook.js, rateLimit.js, audit.js, index.js, processor.test.js = 7
        
        size_tier_correct = False
        size_tier_detail = ""
        
        # Check for size tier
        tier_value = None
        for key in ["sizeTier", "size_tier", "tier", "changeScale", "change_scale", "scale"]:
            if key in preflight_data:
                tier_value = str(preflight_data[key]).lower()
                break
        
        if tier_value:
            size_tier_correct = tier_value in ["small", "small (<10)", "small (< 10)"]
            size_tier_detail = f"Size tier reported as '{tier_value}'. Expected 'small' (total changed files <10: 7 new + 2 modified = 9)"
        else:
            size_tier_detail = "No size tier field found in preflight data"
        
        checks.append({
            "name": "preflight identifies correct size tier (small)",
            "passed": size_tier_correct,
            "detail": size_tier_detail
        })

        # Check new files count (7 new files were added)
        new_files_correct = False
        new_files_detail = ""
        
        new_files_value = None
        for key in ["newFiles", "new_files", "addedFiles", "added_files", "newFilesCount", "new_files_count"]:
            if key in preflight_data:
                new_files_value = preflight_data[key]
                break
        
        if new_files_value is not None:
            if isinstance(new_files_value, list):
                new_files_correct = len(new_files_value) == 7
                new_files_detail = f"New files list has {len(new_files_value)} entries, expected 7"
            elif isinstance(new_files_value, int):
                new_files_correct = new_files_value == 7
                new_files_detail = f"New files count is {new_files_value}, expected 7"
            else:
                new_files_detail = f"newFiles field has unexpected type: {type(new_files_value)}"
        else:
            new_files_detail = "No new files field found in preflight data"
        
        checks.append({
            "name": "preflight identifies 7 new files",
            "passed": new_files_correct,
            "detail": new_files_detail
        })

        # Check timeout values for small tier
        # Small: Reviewer=4min, Fixer=6min, Final=8min
        timeout_correct = False
        timeout_detail = ""
        
        timeout_value = None
        for key in ["reviewerTimeout", "reviewer_timeout", "timeouts", "timeout"]:
            if key in preflight_data:
                timeout_value = preflight_data[key]
                break
        
        if timeout_value is not None:
            if isinstance(timeout_value, dict):
                # Check reviewer timeout
                rv = timeout_value.get("reviewer") or timeout_value.get("Reviewer")
                if rv in [4, "4", "4min", "4 min", "4 minutes", "240s"]:
                    timeout_correct = True
                    timeout_detail = f"Reviewer timeout correctly set to 4 minutes for small tier"
                else:
                    timeout_detail = f"Reviewer timeout is '{rv}', expected 4 (minutes) for small tier"
            elif isinstance(timeout_value, (int, str)):
                # Accept if they specify 4 min for reviewer
                timeout_detail = f"Timeout structure: {timeout_value}"
                timeout_correct = str(timeout_value) in ["4", "4min", "4 min"]
        else:
            timeout_detail = "No timeout field found in preflight data"
        
        checks.append({
            "name": "preflight timeout tier matches small (reviewer=4min)",
            "passed": timeout_correct,
            "detail": timeout_detail
        })
    else:
        checks.extend([
            {"name": "preflight identifies correct size tier (small)", "passed": False, "detail": "No preflight file"},
            {"name": "preflight identifies 7 new files", "passed": False, "detail": "No preflight file"},
            {"name": "preflight timeout tier matches small (reviewer=4min)", "passed": False, "detail": "No preflight file"},
        ])

    # ─── CHECK 5: Review report file exists ───────────────────────────────────
    report_candidates = list(workspace.rglob("review_report*.json")) + \
                        list(workspace.rglob("review-report*.json")) + \
                        list(workspace.rglob("*review*report*.json")) + \
                        list(workspace.rglob("code_review*.json")) + \
                        list(workspace.rglob("*issues*.json"))
    
    report_data = None
    report_path = None
    for p in report_candidates:
        try:
            report_data = load_json_file(p)
            report_path = p
            break
        except Exception:
            continue
    
    checks.append({
        "name": "review_report.json exists",
        "passed": report_data is not None,
        "detail": f"Found at {report_path}" if report_data else f"No review report JSON found. Expected file like review_report.json or code_review_report.json"
    })

    # ─── CHECK 6: Report has correct severity structure (P0, P1, P2, P3) ──────
    if report_data is not None:
        severity_structure_ok = False
        severity_detail = ""
        
        issues = []
        # Accept various structures
        if isinstance(report_data, list):
            issues = report_data
        elif "issues" in report_data:
            issues = report_data["issues"]
        elif "findings" in report_data:
            issues = report_data["findings"]
        elif "problems" in report_data:
            issues = report_data["problems"]
        
        if issues:
            # Check that severities use the P0/P1/P2/P3 classification
            valid_severities = {"P0", "P1", "P2", "P3"}
            severity_values = set()
            for issue in issues:
                if isinstance(issue, dict):
                    for sev_key in ["severity", "level", "priority"]:
                        if sev_key in issue:
                            severity_values.add(str(issue[sev_key]).upper())
                            break
            
            invalid_severities = severity_values - valid_severities
            if invalid_severities:
                severity_detail = f"Found invalid severity values: {invalid_severities}. Must use P0/P1/P2/P3 only"
            elif not severity_values:
                severity_detail = "No severity values found in issues"
            else:
                severity_structure_ok = True
                severity_detail = f"All severities valid: {severity_values}"
        else:
            severity_detail = "No issues/findings array found in report"
        
        checks.append({
            "name": "report uses P0/P1/P2/P3 severity classification",
            "passed": severity_structure_ok,
            "detail": severity_detail
        })

        # ─── CHECK 7: Report correctly identifies P0 issues ───────────────────
        # Expected P0 issues: SQL injection in webhook.js, MD5+key in processor.js verifyPayment
        p0_issues_found = 0
        p0_detail = ""
        
        for issue in issues:
            if isinstance(issue, dict):
                sev = str(issue.get("severity", issue.get("level", issue.get("priority", "")))).upper()
                if sev == "P0":
                    p0_issues_found += 1
        
        # Should have at least 2 P0 issues (SQL injection + crypto misuse)
        p0_correct = p0_issues_found >= 2
        p0_detail = f"Found {p0_issues_found} P0 issues. Expected at least 2 (SQL injection in webhook.js, insecure crypto in processor.js)"
        
        checks.append({
            "name": "report identifies at least 2 P0 critical issues",
            "passed": p0_correct,
            "detail": p0_detail
        })

        # ─── CHECK 8: Report identifies P1 issues ─────────────────────────────
        p1_issues_found = 0
        for issue in issues:
            if isinstance(issue, dict):
                sev = str(issue.get("severity", issue.get("level", issue.get("priority", "")))).upper()
                if sev == "P1":
                    p1_issues_found += 1
        
        # Should have at least 2 P1 issues (no input validation, race condition, timing attack)
        p1_correct = p1_issues_found >= 2
        checks.append({
            "name": "report identifies at least 2 P1 high issues",
            "passed": p1_correct,
            "detail": f"Found {p1_issues_found} P1 issues. Expected at least 2 (missing input validation, race condition/timing attack)"
        })

        # ─── CHECK 9: Report has round structure and 3 reviewers ──────────────
        round_structure_ok = False
        round_detail = ""
        
        # Look for round data or reviewer data
        has_rounds = "rounds" in report_data or "round" in report_data
        has_reviewers = False
        
        if isinstance(report_data, dict):
            report_str = json.dumps(report_data).lower()
            has_reviewers = ("reviewer-1" in report_str or "reviewer1" in report_str or 
                           "reviewer_1" in report_str or 
                           ("reviewer" in report_str and 
                            sum(1 for kw in ["functionality", "security", "quality", 
                                           "correctness", "功能", "安全", "质量",
                                           "reviewer-2", "reviewer-3", "reviewer2", "reviewer3"] 
                                if kw in report_str) >= 2))
        
        round_structure_ok = has_rounds or has_reviewers
        round_detail = f"Round structure present: {has_rounds}, Multiple reviewer evidence: {has_reviewers}"
        
        checks.append({
            "name": "report shows parallel reviewer structure (3 reviewers)",
            "passed": round_structure_ok,
            "detail": round_detail
        })

        # ─── CHECK 10: Exit criteria determination ────────────────────────────
        exit_criteria_ok = False
        exit_detail = ""
        
        report_str = json.dumps(report_data).lower()
        
        # Look for exit criteria logic: two consecutive clean rounds OR maxRounds
        exit_keywords = ["exit", "consecutive", "clean round", "两轮", "maxrounds", "max_rounds", 
                        "exit criteria", "termination", "stop condition", "no issues",
                        "continues", "continue", "next round", "final round"]
        
        exit_keywords_found = [kw for kw in exit_keywords if kw in report_str]
        exit_criteria_ok = len(exit_keywords_found) >= 1
        
        exit_detail = f"Exit criteria keywords found: {exit_keywords_found}" if exit_keywords_found else "No exit criteria logic found in report"
        
        checks.append({
            "name": "report includes exit criteria assessment",
            "passed": exit_criteria_ok,
            "detail": exit_detail
        })

        # ─── CHECK 11: Final round must be Full Review (not Delta) ────────────
        final_round_ok = False
        final_detail = ""
        
        if "full review" in report_str or "full_review" in report_str or "fullreview" in report_str:
            final_round_ok = True
            final_detail = "Report mentions Full Review requirement for final round"
        elif "final" in report_str and "delta" not in report_str:
            # They mention final without delta - could be OK
            final_round_ok = True
            final_detail = "Report references final round without incorrect Delta Review usage"
        elif "delta review" in report_str and "final" in report_str:
            # They mention delta in context of final - need to check if it's correctly excluded
            final_round_ok = False
            final_detail = "Report may incorrectly use Delta Review for final round"
        else:
            final_round_ok = True  # Give benefit of doubt if not contradicted
            final_detail = "Final round review mode not explicitly stated"
        
        checks.append({
            "name": "final round uses Full Review (not Delta)",
            "passed": final_round_ok,
            "detail": final_detail
        })
    else:
        checks.extend([
            {"name": "report uses P0/P1/P2/P3 severity classification", "passed": False, "detail": "No report file"},
            {"name": "report identifies at least 2 P0 critical issues", "passed": False, "detail": "No report file"},
            {"name": "report identifies at least 2 P1 high issues", "passed": False, "detail": "No report file"},
            {"name": "report shows parallel reviewer structure (3 reviewers)", "passed": False, "detail": "No report file"},
            {"name": "report includes exit criteria assessment", "passed": False, "detail": "No report file"},
            {"name": "final round uses Full Review (not Delta)", "passed": False, "detail": "No report file"},
        ])

    # ─── CHECK 12: severityThreshold compliance in report ─────────────────────
    if report_data is not None and pref_data is not None:
        threshold = pref_data.get("severityThreshold", "P0")
        report_str = json.dumps(report_data).lower()
        
        threshold_ok = threshold.lower() in report_str or "severitythreshold" in report_str or "severity_threshold" in report_str
        checks.append({
            "name": "report references severityThreshold from preferences",
            "passed": threshold_ok,
            "detail": f"Preferences severityThreshold is {threshold}. Found in report: {threshold_ok}"
        })
    else:
        checks.append({
            "name": "report references severityThreshold from preferences",
            "passed": False,
            "detail": "Cannot check - missing preferences or report file"
        })

    # ─── Compute score ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= (total * 0.75)  # 75% threshold to pass
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace argument provided"}]}))
        sys.exit(1)
    
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))