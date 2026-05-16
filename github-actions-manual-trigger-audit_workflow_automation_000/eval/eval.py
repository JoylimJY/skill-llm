#!/usr/bin/env python3
"""
Evaluation script for the GitHub Actions Manual Trigger Audit task.

Usage: python3 eval_script.py <workspace_dir>

Checks:
1. Output file exists at the specified path and is valid JSON.
2. JSON structure matches output contract (summary + groups + critical_groups).
3. GROUP_BY=workflow-branch grouping is correct (keys include branch).
4. fintech-org/infra-bot / "Infra Provisioner" workflow is excluded (WORKFLOW_EXCLUDE).
5. external-vendor/third-party-lib is excluded (REPO_MATCH=fintech-org).
6. Groups with <MIN_RUNS runs are excluded (Smoke Test has only 3 runs).
7. "Release Deploy" / main in payments-api is CRITICAL (ratio ~0.714, streak=5).
8. "Nightly Risk Calc" / main in risk-engine is CRITICAL (ratio ~0.875, streak=5).
9. At least one group is WARN severity.
10. Script exited with code 1 (FAIL_ON_CRITICAL=1) OR output JSON contains critical groups
    (we infer this from the JSON content since we can't observe exit code post-hoc).
11. Output file is named 'audit_report.json'.
"""
import json
import sys
import re
from pathlib import Path

def load_json_file(path: Path):
    with open(path) as f:
        return json.load(f)

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    passed_all = True

    def check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── Find the output file ──────────────────────────────────────────────────
    # Agent is asked to save output as 'audit_report.json'
    candidates = list(ws.rglob("audit_report.json"))
    # Filter out distractor files in archive dirs
    candidates = [c for c in candidates if "archive" not in str(c)]

    if not candidates:
        check("output_file_exists", False, "audit_report.json not found anywhere in workspace")
        return checks, False

    report_path = candidates[0]
    check("output_file_exists", True, f"Found at {report_path.relative_to(ws)}")

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        data = load_json_file(report_path)
    except Exception as e:
        check("output_valid_json", False, f"JSON parse error: {e}")
        return checks, False

    check("output_valid_json", True, "Valid JSON")

    # ── Top-level structure ───────────────────────────────────────────────────
    has_summary = "summary" in data
    has_groups = "groups" in data
    check("json_has_summary_and_groups",
          has_summary and has_groups,
          f"summary={'summary' in data}, groups={'groups' in data}")

    if not has_groups:
        return checks, False

    groups = data.get("groups", [])

    # ── workflow-branch grouping: group keys must encode branch ───────────────
    # In workflow-branch mode, the group key or group object must distinguish by branch.
    # We look for evidence that the same workflow name appears with different branches,
    # OR that group objects carry a 'branch' / 'headBranch' field.
    group_keys = []
    for g in groups:
        if isinstance(g, dict):
            # Could be keyed by "group", "workflow", "key", etc.
            key_field = g.get("group") or g.get("workflow") or g.get("key") or g.get("name") or ""
            group_keys.append(key_field)

    # Check: "Release Deploy" appears twice (main and release/2024-q2) OR groups carry branch info
    release_deploy_entries = [g for g in groups if isinstance(g, dict) and
                               ("Release Deploy" in str(g.get("group","")) or
                                "Release Deploy" in str(g.get("workflow","")) or
                                "Release Deploy" in str(g.get("key","")) or
                                "Release Deploy" in str(g.get("name","")))]

    branch_in_keys = any("main" in k or "release" in k or "/" in k for k in group_keys)
    groups_have_branch_field = any(
        isinstance(g, dict) and ("branch" in g or "headBranch" in g or "head_branch" in g)
        for g in groups
    )
    workflow_branch_grouping = (len(release_deploy_entries) >= 2) or branch_in_keys or groups_have_branch_field

    check("workflow_branch_grouping",
          workflow_branch_grouping,
          f"Release Deploy entries: {len(release_deploy_entries)}, "
          f"branch in keys: {branch_in_keys}, "
          f"branch field in groups: {groups_have_branch_field}")

    # ── Infra Provisioner excluded ────────────────────────────────────────────
    infra_present = any(
        isinstance(g, dict) and "Infra Provisioner" in json.dumps(g)
        for g in groups
    )
    check("infra_provisioner_excluded",
          not infra_present,
          "Infra Provisioner should be excluded by WORKFLOW_EXCLUDE" if infra_present
          else "Infra Provisioner correctly absent")

    # ── External vendor repo excluded ─────────────────────────────────────────
    ext_present = any(
        isinstance(g, dict) and "external-vendor" in json.dumps(g)
        for g in groups
    )
    check("external_vendor_excluded",
          not ext_present,
          "external-vendor/third-party-lib should be excluded by REPO_MATCH" if ext_present
          else "external-vendor repo correctly absent")

    # ── Smoke Test excluded (below MIN_RUNS=5, has only 3 runs) ──────────────
    smoke_present = any(
        isinstance(g, dict) and "Smoke Test" in json.dumps(g)
        for g in groups
    )
    check("smoke_test_excluded_min_runs",
          not smoke_present,
          "Smoke Test (3 runs < MIN_RUNS=5) should be excluded" if smoke_present
          else "Smoke Test correctly excluded")

    # ── Release Deploy/main is CRITICAL ──────────────────────────────────────
    def get_severity(g):
        return (g.get("severity") or g.get("status") or g.get("level") or "").lower()

    def matches_workflow_branch(g, workflow_substr, branch_substr):
        g_str = json.dumps(g)
        return workflow_substr in g_str and branch_substr in g_str

    release_main_groups = [g for g in groups if isinstance(g, dict) and
                           matches_workflow_branch(g, "Release Deploy", "main") and
                           "release/2024-q2" not in json.dumps(g)]
    release_main_critical = any(get_severity(g) == "critical" for g in release_main_groups)
    check("release_deploy_main_critical",
          release_main_critical,
          f"Found {len(release_main_groups)} Release Deploy/main groups, "
          f"severities: {[get_severity(g) for g in release_main_groups]}")

    # ── Nightly Risk Calc is CRITICAL ─────────────────────────────────────────
    nightly_groups = [g for g in groups if isinstance(g, dict) and
                      "Nightly Risk Calc" in json.dumps(g)]
    nightly_critical = any(get_severity(g) == "critical" for g in nightly_groups)
    check("nightly_risk_calc_critical",
          nightly_critical,
          f"Found {len(nightly_groups)} Nightly Risk Calc groups, "
          f"severities: {[get_severity(g) for g in nightly_groups]}")

    # ── At least one WARN group ───────────────────────────────────────────────
    warn_groups = [g for g in groups if isinstance(g, dict) and get_severity(g) == "warn"]
    check("at_least_one_warn_group",
          len(warn_groups) >= 1,
          f"Found {len(warn_groups)} warn-severity groups")

    # ── critical_groups field present in JSON output ──────────────────────────
    has_critical_groups_field = "critical_groups" in data
    check("json_has_critical_groups_field",
          has_critical_groups_field,
          "JSON output contract requires 'critical_groups' field in JSON mode")

    if has_critical_groups_field:
        critical_list = data.get("critical_groups", [])
        check("critical_groups_nonempty",
              len(critical_list) >= 1,
              f"critical_groups has {len(critical_list)} entries")

    # ── summary field sanity ──────────────────────────────────────────────────
    if has_summary and isinstance(data["summary"], dict):
        summary = data["summary"]
        total_groups = summary.get("total_groups") or summary.get("groups") or summary.get("group_count")
        check("summary_reports_multiple_groups",
              total_groups is None or (isinstance(total_groups, int) and total_groups >= 2),
              f"summary total_groups={total_groups}")

    # Final score: weighted
    scored = [
        ("output_file_exists", 0.10),
        ("output_valid_json", 0.05),
        ("json_has_summary_and_groups", 0.05),
        ("workflow_branch_grouping", 0.15),
        ("infra_provisioner_excluded", 0.10),
        ("external_vendor_excluded", 0.10),
        ("smoke_test_excluded_min_runs", 0.10),
        ("release_deploy_main_critical", 0.10),
        ("nightly_risk_calc_critical", 0.10),
        ("at_least_one_warn_group", 0.05),
        ("json_has_critical_groups_field", 0.05),
        ("critical_groups_nonempty", 0.05),
    ]
    check_map = {c["name"]: c["passed"] for c in checks}
    score = sum(w for name, w in scored if check_map.get(name, False))

    return checks, score

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": "No workspace path provided"}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": f"Unexpected evaluator error: {e}"}))
        sys.exit(1)

    passed = score >= 0.70
    print(json.dumps({
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()