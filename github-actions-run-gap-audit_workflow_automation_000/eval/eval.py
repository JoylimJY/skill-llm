#!/usr/bin/env python3
"""
Evaluate the agent's audit_report.json output for the GitHub Actions Run Gap Audit task.
"""
import json
import sys
import os
from pathlib import Path

def load_json_file(path: Path):
    with open(path) as f:
        return json.load(f)

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── 1. Find the output file ───────────────────────────────────────────────
    candidates = list(ws.rglob("audit_report.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "audit_report.json exists",
        "passed": file_found,
        "detail": f"Found at {candidates[0]}" if file_found else "File not found anywhere in workspace",
    })
    if not file_found:
        return checks, 0.0

    report_path = candidates[0]

    # ── 2. Valid JSON ─────────────────────────────────────────────────────────
    try:
        data = load_json_file(report_path)
        checks.append({"name": "Valid JSON", "passed": True, "detail": "Parsed successfully"})
    except Exception as e:
        checks.append({"name": "Valid JSON", "passed": False, "detail": str(e)})
        return checks, 0.1

    # ── 3. JSON structure has 'groups' key ────────────────────────────────────
    has_groups = isinstance(data, dict) and "groups" in data
    checks.append({
        "name": "JSON has 'groups' key",
        "passed": has_groups,
        "detail": f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else type(data)}",
    })
    if not has_groups:
        return checks, 0.15

    groups = data["groups"]

    # ── Helper: find group by key attributes ──────────────────────────────────
    def find_group(repo_fragment, workflow, branch, event):
        for g in groups:
            r = g.get("repo", g.get("repository", ""))
            w = g.get("workflow", g.get("workflowName", ""))
            b = g.get("branch", g.get("headBranch", ""))
            ev = g.get("event", "")
            if (repo_fragment in r and workflow in w
                    and branch == b and event == ev):
                return g
        return None

    # ── 4. GROUP A (compliance-check/main/schedule) is CRITICAL ──────────────
    # gap~90h, median~24h, 90>24*2.5=60 ✓ AND 90>24 ✓ → critical
    g_a = find_group("compliance-engine", "compliance-check", "main", "schedule")
    a_present = g_a is not None
    checks.append({
        "name": "GROUP A present (compliance-check/main/schedule)",
        "passed": a_present,
        "detail": f"Group data: {g_a}" if a_present else "Not found in output groups",
    })
    if a_present:
        severity_a = g_a.get("severity", g_a.get("status", "")).lower()
        a_critical = severity_a == "critical"
        checks.append({
            "name": "GROUP A severity is 'critical'",
            "passed": a_critical,
            "detail": f"Got severity='{severity_a}', expected 'critical' (gap~90h > median~24h * 2.5 = 60h AND > 24h)",
        })

    # ── 5. GROUP B (deploy-prod/release/push) is WARN ────────────────────────
    # gap~20h, median~6h, 20>6*1.5=9 ✓ AND 20>12 ✓ → warn
    # 20>6*2.5=15 ✓ BUT 20<24 (MIN_CRITICAL_GAP_HOURS) → NOT critical
    g_b = find_group("payment-service", "deploy-prod", "release", "push")
    b_present = g_b is not None
    checks.append({
        "name": "GROUP B present (deploy-prod/release/push)",
        "passed": b_present,
        "detail": f"Group data: {g_b}" if b_present else "Not found in output groups",
    })
    if b_present:
        severity_b = g_b.get("severity", g_b.get("status", "")).lower()
        b_warn = severity_b == "warn"
        checks.append({
            "name": "GROUP B severity is 'warn'",
            "passed": b_warn,
            "detail": f"Got severity='{severity_b}', expected 'warn' (gap~20h > median~6h * 1.5=9h AND > 12h BUT gap 20h < MIN_CRITICAL_GAP_HOURS=24h)",
        })

    # ── 6. GROUP C (security-scan) is EXCLUDED (WORKFLOW_EXCLUDE=security) ───
    g_c = find_group("api-gateway", "security-scan", "main", "push")
    c_excluded = g_c is None
    checks.append({
        "name": "GROUP C excluded (security-scan filtered by WORKFLOW_EXCLUDE)",
        "passed": c_excluded,
        "detail": "security-scan group correctly absent" if c_excluded else f"security-scan group should be excluded but found: {g_c}",
    })

    # ── 7. GROUP D (feature-xyz branch) is EXCLUDED (BRANCH_EXCLUDE=feature) ─
    g_d = find_group("compliance-engine", "unit-tests", "feature-xyz", "push")
    d_excluded = g_d is None
    checks.append({
        "name": "GROUP D excluded (feature-xyz branch filtered by BRANCH_EXCLUDE)",
        "passed": d_excluded,
        "detail": "feature-xyz group correctly absent" if d_excluded else f"feature-xyz group should be excluded but found: {g_d}",
    })

    # ── 8. GROUP E (workflow_dispatch event) is EXCLUDED ─────────────────────
    g_e = find_group("payment-service", "integration-tests", "main", "workflow_dispatch")
    e_excluded = g_e is None
    checks.append({
        "name": "GROUP E excluded (workflow_dispatch filtered by EVENT_EXCLUDE)",
        "passed": e_excluded,
        "detail": "workflow_dispatch group correctly absent" if e_excluded else f"workflow_dispatch group should be excluded but found: {g_e}",
    })

    # ── 9. GROUP F (lint, only 3 runs) is EXCLUDED (below MIN_RUNS=4) ─────────
    g_f = find_group("api-gateway", "lint", "main", "push")
    f_excluded = g_f is None
    checks.append({
        "name": "GROUP F excluded (lint has < MIN_RUNS=4 runs)",
        "passed": f_excluded,
        "detail": "lint group (3 runs) correctly absent" if f_excluded else f"lint group should be excluded (MIN_RUNS=4) but found: {g_f}",
    })

    # ── 10. GROUP G (audit-report/main/schedule) is OK ───────────────────────
    # gap~50h, median~48h, 50>48*1.5=72? NO → ok
    g_g = find_group("compliance-engine", "audit-report", "main", "schedule")
    g_present = g_g is not None
    checks.append({
        "name": "GROUP G present (audit-report/main/schedule)",
        "passed": g_present,
        "detail": f"Group data: {g_g}" if g_present else "Not found in output",
    })
    if g_present:
        severity_g = g_g.get("severity", g_g.get("status", "")).lower()
        g_ok = severity_g == "ok"
        checks.append({
            "name": "GROUP G severity is 'ok'",
            "passed": g_ok,
            "detail": f"Got severity='{severity_g}', expected 'ok' (gap~50h < median~48h * 1.5=72h)",
        })

    # ── 11. Summary has at least one critical group ───────────────────────────
    summary = data.get("summary", {})
    critical_count = summary.get("critical", 0)
    if critical_count == 0:
        # also look in top-level counts
        critical_count = data.get("critical_count", 0)
    has_critical_summary = critical_count >= 1
    checks.append({
        "name": "Summary reports at least 1 critical group",
        "passed": has_critical_summary,
        "detail": f"critical count in summary: {critical_count}",
    })

    # ── 12. NOW_ISO was used (groups reference times near 2026-03-15) ─────────
    time_anchored = False
    for g in groups:
        gap_h = g.get("gap_hours", g.get("inactivity_gap_hours", 0))
        # compliance-check gap should be ~90h; if it's wildly different, NOW was not fixed
        if "compliance-check" in g.get("workflow", g.get("workflowName", "")):
            if 85 <= float(gap_h) <= 95:
                time_anchored = True
                break
    checks.append({
        "name": "NOW_ISO=2026-03-15T12:00:00Z used for deterministic gap calculation",
        "passed": time_anchored,
        "detail": f"compliance-check gap should be ~90h; found {gap_h if 'gap_h' in dir() else 'N/A'}h",
    })

    # ── Score ─────────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / len(checks), 3)
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}],
        }))
        return

    passed = score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "audit_report.json exists",
            "Valid JSON",
            "JSON has 'groups' key",
            "GROUP A severity is 'critical'",
            "GROUP C excluded (security-scan filtered by WORKFLOW_EXCLUDE)",
            "GROUP D excluded (feature-xyz branch filtered by BRANCH_EXCLUDE)",
            "GROUP E excluded (workflow_dispatch filtered by EVENT_EXCLUDE)",
            "GROUP F excluded (lint has < MIN_RUNS=4 runs)",
        ]
    )

    print(json.dumps({"passed": passed, "score": score, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()