import sys
import json
import subprocess
import os
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    workspace = Path(workspace)

    # --- Locate the audit_report.json ---
    candidates = list(workspace.rglob("audit_report.json"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "audit_report.json exists", "passed": False, "detail": "No audit_report.json found anywhere in the workspace."}]
        }

    report_path = candidates[0]

    # CHECK 1: File exists
    checks.append({"name": "audit_report.json exists", "passed": True, "detail": f"Found at {report_path}"})

    # Load the report
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "audit_report.json is valid JSON", "passed": False, "detail": str(e)}]
        }
    checks.append({"name": "audit_report.json is valid JSON", "passed": True, "detail": "Parsed successfully."})

    # --- Run the ground truth ourselves to know what the tool produces ---
    v1 = str(workspace / "contracts/software_licenses/license_policy_v1.txt")
    v2 = str(workspace / "contracts/software_licenses/license_policy_v2.txt")

    # Ground truth: with --ignore-space --stats --format json
    try:
        result_ignore = subprocess.run(
            ["python3", str(workspace / "scripts/diff.py"), "file", v1, v2,
             "--format", "json", "--stats", "--ignore-space"],
            capture_output=True, text=True, cwd=str(workspace)
        )
        ground_truth_ignore = json.loads(result_ignore.stdout)
    except Exception as e:
        checks.append({"name": "Ground truth (ignore-space) computable", "passed": False, "detail": str(e)})
        passed_all = False
        ground_truth_ignore = None

    # Ground truth: WITHOUT --ignore-space --stats --format json  
    try:
        result_nospace = subprocess.run(
            ["python3", str(workspace / "scripts/diff.py"), "file", v1, v2,
             "--format", "json", "--stats"],
            capture_output=True, text=True, cwd=str(workspace)
        )
        ground_truth_nospace = json.loads(result_nospace.stdout)
    except Exception as e:
        checks.append({"name": "Ground truth (no ignore-space) computable", "passed": False, "detail": str(e)})
        passed_all = False
        ground_truth_nospace = None

    # CHECK 3: Report contains a 'stats' or equivalent summary block
    has_stats = False
    stats_obj = None
    if "stats" in report:
        has_stats = True
        stats_obj = report["stats"]
    elif "summary" in report:
        has_stats = True
        stats_obj = report["summary"]
    elif "changes" in report and isinstance(report["changes"], dict):
        has_stats = True
        stats_obj = report["changes"]

    checks.append({
        "name": "Report contains stats/summary block",
        "passed": has_stats,
        "detail": f"Found stats block: {json.dumps(stats_obj)}" if has_stats else "Missing 'stats', 'summary', or 'changes' key with statistics."
    })
    if not has_stats:
        passed_all = False

    # CHECK 4: The stats counts match --ignore-space ground truth (not the nospace version)
    # This verifies the agent used --ignore-space
    if ground_truth_ignore and ground_truth_nospace and stats_obj:
        gt_added = ground_truth_ignore["stats"]["added"]
        gt_deleted = ground_truth_ignore["stats"]["deleted"]
        gt_modified = ground_truth_ignore["stats"]["modified"]
        gt_total = ground_truth_ignore["stats"]["total_changes"]

        # Extract counts from report stats — flexible key names
        def extract_count(obj, *keys):
            for k in keys:
                if k in obj:
                    return obj[k]
            return None

        rep_added = extract_count(stats_obj, "added", "additions", "inserted", "new_lines")
        rep_deleted = extract_count(stats_obj, "deleted", "deletions", "removed", "removed_lines")
        rep_modified = extract_count(stats_obj, "modified", "changes", "updated", "changed_lines")
        rep_total = extract_count(stats_obj, "total_changes", "total", "total_diff", "change_count")

        # Check that the counts match the ignore-space ground truth (NOT the raw diff)
        gt_nospace_added = ground_truth_nospace["stats"]["added"]
        gt_nospace_total = ground_truth_nospace["stats"]["total_changes"]

        # If agent used --ignore-space, their total should match gt_total (ignore-space version)
        # If they did NOT use --ignore-space, total would match gt_nospace_total (larger due to whitespace diffs)
        used_ignore_space = False
        if rep_total is not None:
            if rep_total == gt_total:
                used_ignore_space = True
            elif rep_total == gt_nospace_total and gt_total != gt_nospace_total:
                used_ignore_space = False

        checks.append({
            "name": "Stats match --ignore-space diff (not raw diff with whitespace noise)",
            "passed": used_ignore_space,
            "detail": (
                f"Report total_changes={rep_total}, "
                f"ignore-space ground truth total={gt_total}, "
                f"raw diff total={gt_nospace_total}. "
                f"{'PASS: agent correctly used --ignore-space.' if used_ignore_space else 'FAIL: counts suggest agent did NOT use --ignore-space or used custom diff logic.'}"
            )
        })
        if not used_ignore_space:
            passed_all = False

        # CHECK 5: Correct added count
        added_ok = (rep_added == gt_added) if rep_added is not None else False
        checks.append({
            "name": f"Added lines count = {gt_added}",
            "passed": added_ok,
            "detail": f"Report says added={rep_added}, expected {gt_added} (ignore-space)."
        })
        if not added_ok:
            passed_all = False

        # CHECK 6: Correct deleted count
        deleted_ok = (rep_deleted == gt_deleted) if rep_deleted is not None else False
        checks.append({
            "name": f"Deleted lines count = {gt_deleted}",
            "passed": deleted_ok,
            "detail": f"Report says deleted={rep_deleted}, expected {gt_deleted} (ignore-space)."
        })
        if not deleted_ok:
            passed_all = False

        # CHECK 7: Correct modified count
        modified_ok = (rep_modified == gt_modified) if rep_modified is not None else False
        checks.append({
            "name": f"Modified lines count = {gt_modified}",
            "passed": modified_ok,
            "detail": f"Report says modified={rep_modified}, expected {gt_modified} (ignore-space)."
        })
        if not modified_ok:
            passed_all = False
    else:
        checks.append({"name": "Stats count verification", "passed": False, "detail": "Could not verify stats due to earlier failures."})
        passed_all = False

    # CHECK 8: Report includes a list of actual differences (not just stats)
    has_diffs = False
    diffs_list = None
    if "differences" in report and isinstance(report["differences"], list):
        has_diffs = True
        diffs_list = report["differences"]
    elif "diff" in report and isinstance(report["diff"], list):
        has_diffs = True
        diffs_list = report["diff"]
    elif "changes_detail" in report and isinstance(report["changes_detail"], list):
        has_diffs = True
        diffs_list = report["changes_detail"]

    checks.append({
        "name": "Report contains a list of individual differences",
        "passed": has_diffs,
        "detail": f"Found {len(diffs_list)} entries in differences list." if has_diffs else "No 'differences', 'diff', or 'changes_detail' list found."
    })
    if not has_diffs:
        passed_all = False

    # CHECK 9: The differences contain entries with expected types (added/deleted/modified)
    if has_diffs and ground_truth_ignore:
        gt_diffs = ground_truth_ignore["differences"]
        # Check that at least one entry has a 'type' field with a recognized value
        valid_types = {"added", "deleted", "modified"}
        type_ok = False
        for entry in diffs_list:
            if isinstance(entry, dict) and entry.get("type") in valid_types:
                type_ok = True
                break
        checks.append({
            "name": "Differences entries have valid 'type' field (added/deleted/modified)",
            "passed": type_ok,
            "detail": f"Sample entry types found: {list(set(e.get('type','?') for e in diffs_list[:5] if isinstance(e,dict)))}"
        })
        if not type_ok:
            passed_all = False

        # CHECK 10: Correct total number of diff entries (should match ignore-space count)
        expected_diff_count = len(gt_diffs)
        actual_diff_count = len(diffs_list)
        diff_count_ok = (actual_diff_count == expected_diff_count)
        checks.append({
            "name": f"Number of diff entries = {expected_diff_count}",
            "passed": diff_count_ok,
            "detail": f"Report has {actual_diff_count} diff entries, expected {expected_diff_count} (from --ignore-space tool output)."
        })
        if not diff_count_ok:
            passed_all = False

    # CHECK 11: Report includes document identification (file names or version references)
    has_doc_refs = False
    report_str = json.dumps(report).lower()
    for keyword in ["v1", "v2", "license_policy", "version", "1.0", "2.0", "file_a", "file_b", "source", "target"]:
        if keyword in report_str:
            has_doc_refs = True
            break
    checks.append({
        "name": "Report references document identity (version/filename)",
        "passed": has_doc_refs,
        "detail": "Report contains references to document versions or filenames." if has_doc_refs else "Report does not identify which documents were compared."
    })
    if not has_doc_refs:
        passed_all = False

    # Final score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))