#!/usr/bin/env python3
"""Evaluation script for pest-disease-tracker task."""

import json
import sys
from pathlib import Path

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/root/.openclaw/workspace"
    
    checks = []
    
    # --- Load the pest tracker database ---
    db_path = Path.home() / ".openclaw" / "workspace" / "pest_tracker_db.json"
    
    db = None
    try:
        with open(db_path) as f:
            db = json.load(f)
        checks.append({"name": "pest_tracker_db_exists", "passed": True, "detail": f"Database found at {db_path}"})
    except FileNotFoundError:
        checks.append({"name": "pest_tracker_db_exists", "passed": False, "detail": f"Database not found at {db_path}"})
    except json.JSONDecodeError as e:
        checks.append({"name": "pest_tracker_db_exists", "passed": False, "detail": f"Database is malformed JSON: {e}"})
    
    if db is None:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    issues = db.get("issues", {})
    issues_list = list(issues.values())
    
    # --- Check 1: At least 4 issues tracked (aphids, powdery mildew, early blight, cucumber beetles) ---
    try:
        n_issues = len(issues_list)
        passed = n_issues >= 4
        checks.append({
            "name": "minimum_four_issues_tracked",
            "passed": passed,
            "detail": f"Found {n_issues} issues (need >= 4)"
        })
    except Exception as e:
        checks.append({"name": "minimum_four_issues_tracked", "passed": False, "detail": str(e)})

    # --- Check 2: Aphids present with correct severity (high) and type (pest) ---
    try:
        aphid_issues = [i for i in issues_list if "aphid" in i.get("name", "").lower()]
        found = bool(aphid_issues)
        correct_type = any(i.get("type") == "pest" for i in aphid_issues)
        correct_severity = any(i.get("severity") in ["high", "critical"] for i in aphid_issues)
        passed = found and correct_type and correct_severity
        detail = f"Aphid issues found: {found}, type=pest: {correct_type}, severity high/critical: {correct_severity}"
        checks.append({"name": "aphids_correct_severity_and_type", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "aphids_correct_severity_and_type", "passed": False, "detail": str(e)})

    # --- Check 3: Early blight present with severity=critical and type=disease ---
    try:
        blight_issues = [i for i in issues_list if "early blight" in i.get("name", "").lower() or "blight" in i.get("name","").lower()]
        found = bool(blight_issues)
        correct_type = any(i.get("type") == "disease" for i in blight_issues)
        correct_severity = any(i.get("severity") == "critical" for i in blight_issues)
        passed = found and correct_type and correct_severity
        detail = f"Early blight found: {found}, type=disease: {correct_type}, severity=critical: {correct_severity}"
        checks.append({"name": "early_blight_critical_disease", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "early_blight_critical_disease", "passed": False, "detail": str(e)})

    # --- Check 4: Powdery mildew present with type=disease ---
    try:
        mildew_issues = [i for i in issues_list if "mildew" in i.get("name", "").lower() or "powdery" in i.get("name","").lower()]
        found = bool(mildew_issues)
        correct_type = any(i.get("type") == "disease" for i in mildew_issues)
        passed = found and correct_type
        detail = f"Powdery mildew found: {found}, type=disease: {correct_type}"
        checks.append({"name": "powdery_mildew_as_disease", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "powdery_mildew_as_disease", "passed": False, "detail": str(e)})

    # --- Check 5: Cucumber beetles present as pest ---
    try:
        beetle_issues = [i for i in issues_list if "cucumber" in i.get("name", "").lower() or "beetle" in i.get("name","").lower()]
        found = bool(beetle_issues)
        correct_type = any(i.get("type") == "pest" for i in beetle_issues)
        passed = found and correct_type
        detail = f"Cucumber beetles found: {found}, type=pest: {correct_type}"
        checks.append({"name": "cucumber_beetles_as_pest", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "cucumber_beetles_as_pest", "passed": False, "detail": str(e)})

    # --- Check 6: At least one treatment recorded with status=effective, and that issue is resolved ---
    try:
        has_effective = False
        resolved_after_effective = False
        for issue in issues_list:
            for treatment in issue.get("treatments", []):
                if treatment.get("status") == "effective":
                    has_effective = True
                    if issue.get("status") == "resolved":
                        resolved_after_effective = True
        passed = has_effective and resolved_after_effective
        detail = f"Has effective treatment: {has_effective}, issue marked resolved: {resolved_after_effective}"
        checks.append({"name": "effective_treatment_resolves_issue", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "effective_treatment_resolves_issue", "passed": False, "detail": str(e)})

    # --- Check 7: Each of the 4 main issues has at least one treatment recorded ---
    try:
        issues_with_treatments = [i for i in issues_list if len(i.get("treatments", [])) >= 1]
        passed = len(issues_with_treatments) >= 4
        detail = f"{len(issues_with_treatments)} issues have at least one treatment (need >= 4)"
        checks.append({"name": "all_issues_have_treatments", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "all_issues_have_treatments", "passed": False, "detail": str(e)})

    # --- Check 8: Export file exists at /tmp/ path (testing security constraint) ---
    try:
        # Look for any JSON export file in /tmp
        tmp_exports = list(Path("/tmp").glob("*.json"))
        # Also check workspace
        ws_exports = list(Path(workspace).rglob("audit_export*.json")) + list(Path(workspace).rglob("farm_audit*.json")) + list(Path(workspace).rglob("export*.json"))
        # Also check home dir
        home_exports = list(Path.home().glob("*.json"))
        
        all_exports = tmp_exports + ws_exports + home_exports
        
        valid_export = None
        for exp in all_exports:
            try:
                with open(exp) as f:
                    data = json.load(f)
                if "issues" in data and "export_date" in data:
                    valid_export = exp
                    break
            except Exception:
                continue
        
        passed = valid_export is not None
        detail = f"Valid export found at: {valid_export}" if valid_export else "No valid pest tracker export JSON found in /tmp/, workspace, or home dir"
        checks.append({"name": "export_file_exists_in_safe_path", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "export_file_exists_in_safe_path", "passed": False, "detail": str(e)})

    # --- Check 9: Export contains all tracked issues (completeness) ---
    try:
        if valid_export:
            with open(valid_export) as f:
                export_data = json.load(f)
            export_issue_count = len(export_data.get("issues", []))
            db_issue_count = len(issues_list)
            passed = export_issue_count >= 4 and export_issue_count == db_issue_count
            detail = f"Export has {export_issue_count} issues, DB has {db_issue_count}"
        else:
            passed = False
            detail = "No valid export file to check"
        checks.append({"name": "export_completeness", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "export_completeness", "passed": False, "detail": str(e)})

    # --- Check 10: Severity values are valid (only low/moderate/high/critical used) ---
    try:
        valid_severities = {"low", "moderate", "high", "critical"}
        all_valid = all(i.get("severity") in valid_severities for i in issues_list)
        invalid = [i.get("severity") for i in issues_list if i.get("severity") not in valid_severities]
        passed = all_valid
        detail = f"All severities valid: {all_valid}. Invalid found: {invalid}"
        checks.append({"name": "valid_severity_levels_used", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "valid_severity_levels_used", "passed": False, "detail": str(e)})

    # --- Compute score ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 8  # Need at least 8/10 checks to pass

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()