#!/usr/bin/env python3
"""
Evaluation script for the GitHub Actions Duplicate Run Audit task.

Grading criteria:
1. Output file ci_waste_report.json exists somewhere in workspace.
2. It is valid JSON with the expected top-level structure (summary + top_groups or critical_groups).
3. The run is filtered correctly:
   - hotfix branches are excluded.
   - schedule events are excluded.
   - workflow_match restricts to payment-ci, deploy-staging, infra-validate (or similar scoped set).
4. Group A (payment-ci/main/push/SHA_PAYMENT) appears with severity=critical.
5. Group G (deploy-staging/main/push/SHA_G) appears with severity=critical.
6. Group C (hotfix branch) is NOT present (branch_exclude worked).
7. Group D (schedule event) is NOT present (event_exclude worked).
8. summary.critical_groups >= 2.
9. The report was produced via OUTPUT_FORMAT=json (machine-readable).
10. FAIL_ON_CRITICAL=1 flag was used — evidenced by a saved exit-code file OR we just verify the
    JSON was produced (since FAIL_ON_CRITICAL=1 exits 1 when critical groups exist, the agent
    must capture output before the exit-code kills the pipeline).

We check items 1-9 deterministically.
"""

import json
import sys
from pathlib import Path

def find_report(workspace: Path):
    """Search for ci_waste_report.json anywhere in the workspace."""
    candidates = list(workspace.rglob("ci_waste_report.json"))
    return candidates[0] if candidates else None

def main():
    workspace = Path(sys.argv[1])
    checks = []
    passed_all = True

    # -----------------------------------------------------------------------
    # CHECK 1: File exists
    # -----------------------------------------------------------------------
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "ci_waste_report.json exists",
        "passed": file_exists,
        "detail": str(report_path) if file_exists else "File not found anywhere in workspace",
    })
    if not file_exists:
        passed_all = False
        # Cannot continue
        score = 0.0
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return

    # -----------------------------------------------------------------------
    # CHECK 2: Valid JSON
    # -----------------------------------------------------------------------
    try:
        with open(report_path) as f:
            report = json.load(f)
        valid_json = True
        checks.append({"name": "Valid JSON", "passed": True, "detail": f"Parsed successfully from {report_path}"})
    except Exception as e:
        valid_json = False
        checks.append({"name": "Valid JSON", "passed": False, "detail": str(e)})
        passed_all = False
        score = 0.1
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return

    # -----------------------------------------------------------------------
    # CHECK 3: Top-level structure has 'summary' and at least one group key
    # -----------------------------------------------------------------------
    has_summary = isinstance(report.get("summary"), dict)
    has_groups = "top_groups" in report or "critical_groups" in report
    struct_ok = has_summary and has_groups
    checks.append({
        "name": "JSON structure has summary + groups",
        "passed": struct_ok,
        "detail": f"summary={has_summary}, groups_key={has_groups}",
    })
    if not struct_ok:
        passed_all = False

    # -----------------------------------------------------------------------
    # Collect all groups for analysis
    # -----------------------------------------------------------------------
    all_groups = []
    for key in ("top_groups", "critical_groups"):
        if isinstance(report.get(key), list):
            all_groups.extend(report[key])
    # Deduplicate by (workflow, branch, event, head_sha)
    seen = set()
    unique_groups = []
    for g in all_groups:
        k = (g.get("workflow",""), g.get("branch",""), g.get("event",""), g.get("head_sha",""))
        if k not in seen:
            seen.add(k)
            unique_groups.append(g)

    # -----------------------------------------------------------------------
    # CHECK 4: Group A is present and critical
    # SHA_PAYMENT = "abc123def456abc123def456abc123def456abc1"
    # -----------------------------------------------------------------------
    SHA_PAYMENT = "abc123def456abc123def456abc123def456abc1"
    group_a = [g for g in unique_groups
               if g.get("workflow") == "payment-ci"
               and g.get("branch") == "main"
               and g.get("event") == "push"
               and g.get("head_sha") == SHA_PAYMENT]
    group_a_present = len(group_a) > 0
    group_a_critical = group_a_present and group_a[0].get("severity") == "critical"
    checks.append({
        "name": "payment-ci/main/push burst is present",
        "passed": group_a_present,
        "detail": f"Found {len(group_a)} matching group(s). Workflows in report: {list(set(g.get('workflow') for g in unique_groups))}",
    })
    checks.append({
        "name": "payment-ci/main/push burst is severity=critical",
        "passed": group_a_critical,
        "detail": f"severity={group_a[0].get('severity') if group_a_present else 'N/A'}, run_count={group_a[0].get('run_count') if group_a_present else 'N/A'}",
    })
    if not group_a_present or not group_a_critical:
        passed_all = False

    # -----------------------------------------------------------------------
    # CHECK 5: Group G is present and critical
    # deploy-staging on main push, SHA_G = "bbbb1111bbbb2222bbbb3333bbbb4444bbbb5555"
    # -----------------------------------------------------------------------
    SHA_G = "bbbb1111bbbb2222bbbb3333bbbb4444bbbb5555"
    group_g = [g for g in unique_groups
               if g.get("workflow") == "deploy-staging"
               and g.get("branch") == "main"
               and g.get("event") == "push"
               and g.get("head_sha") == SHA_G]
    group_g_present = len(group_g) > 0
    group_g_critical = group_g_present and group_g[0].get("severity") == "critical"
    checks.append({
        "name": "deploy-staging/main/push burst is present",
        "passed": group_g_present,
        "detail": f"Found {len(group_g)} matching group(s)",
    })
    checks.append({
        "name": "deploy-staging/main/push burst is severity=critical",
        "passed": group_g_critical,
        "detail": f"severity={group_g[0].get('severity') if group_g_present else 'N/A'}, run_count={group_g[0].get('run_count') if group_g_present else 'N/A'}",
    })
    if not group_g_present or not group_g_critical:
        passed_all = False

    # -----------------------------------------------------------------------
    # CHECK 6: Hotfix branch excluded
    # Group C: hotfix/pci-patch branch — must NOT appear
    # -----------------------------------------------------------------------
    SHA_HOTFIX = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    group_c = [g for g in unique_groups if "hotfix" in g.get("branch", "").lower()]
    hotfix_excluded = len(group_c) == 0
    checks.append({
        "name": "hotfix branch runs are excluded (branch_exclude filter)",
        "passed": hotfix_excluded,
        "detail": f"Found {len(group_c)} hotfix groups; expected 0. Groups: {[g.get('branch') for g in group_c]}",
    })
    if not hotfix_excluded:
        passed_all = False

    # -----------------------------------------------------------------------
    # CHECK 7: Schedule event excluded
    # Group D: canary-test on schedule — must NOT appear
    # -----------------------------------------------------------------------
    group_d = [g for g in unique_groups if g.get("event") == "schedule"]
    schedule_excluded = len(group_d) == 0
    checks.append({
        "name": "schedule events are excluded (event_exclude filter)",
        "passed": schedule_excluded,
        "detail": f"Found {len(group_d)} schedule-event groups; expected 0.",
    })
    if not schedule_excluded:
        passed_all = False

    # -----------------------------------------------------------------------
    # CHECK 8: summary.critical_groups >= 2
    # -----------------------------------------------------------------------
    try:
        critical_count = report["summary"].get("critical_groups", 0)
        crit_ok = critical_count >= 2
    except Exception:
        critical_count = -1
        crit_ok = False
    checks.append({
        "name": "summary.critical_groups >= 2",
        "passed": crit_ok,
        "detail": f"critical_groups={critical_count}",
    })
    if not crit_ok:
        passed_all = False

    # -----------------------------------------------------------------------
    # CHECK 9: summary.total_wasted_minutes > 0
    # -----------------------------------------------------------------------
    try:
        wasted = report["summary"].get("total_wasted_minutes", 0)
        wasted_ok = float(wasted) > 0
    except Exception:
        wasted = 0
        wasted_ok = False
    checks.append({
        "name": "summary.total_wasted_minutes > 0",
        "passed": wasted_ok,
        "detail": f"total_wasted_minutes={wasted}",
    })
    if not wasted_ok:
        passed_all = False

    # -----------------------------------------------------------------------
    # CHECK 10: Wasted minutes are non-trivially large (>= 50 min total)
    # This validates the custom window and duration math.
    # Group A alone: 7 wasted * ~8 min each = ~56 min
    # Group G alone: 6 wasted * ~11.67 min each = ~70 min
    # -----------------------------------------------------------------------
    try:
        wasted_val = float(report["summary"].get("total_wasted_minutes", 0))
        large_wasted = wasted_val >= 50.0
    except Exception:
        large_wasted = False
        wasted_val = 0
    checks.append({
        "name": "total_wasted_minutes >= 50 (validates time-window math)",
        "passed": large_wasted,
        "detail": f"total_wasted_minutes={wasted_val}",
    })
    if not large_wasted:
        passed_all = False

    # -----------------------------------------------------------------------
    # Score
    # -----------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks,
    }, indent=2))

if __name__ == "__main__":
    main()