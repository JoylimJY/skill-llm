#!/usr/bin/env python3
"""
Evaluation script for the GitHub Actions Runtime Regression Audit task.
Expected agent behaviour:
  1. Run the audit script with:
       BASELINE_GLOB pointing at artifacts/github-actions/baseline/*.json
       CURRENT_GLOB  pointing at artifacts/github-actions/current/*.json
       WARN_DELTA_SECONDS=60   CRITICAL_DELTA_SECONDS=150
       WARN_DELTA_PERCENT=20   CRITICAL_DELTA_PERCENT=40
       OUTPUT_FORMAT=json
       FAIL_ON_CRITICAL=1
       JOB_EXCLUDE=e2e        (exclude the brand-new e2e-tests job from regression ranking)
       TOP_N=10
  2. Capture output to a file named  regression-report.json  (anywhere in workspace)
  3. The report must correctly classify:
       - fintech/payments / CI Pipeline / build-docker  → CRITICAL
       - fintech/ledger   / CI Pipeline / integration   → CRITICAL
       - fintech/payments / CI Pipeline / run-unit-tests → WARN
       - fintech/ledger   / CI Pipeline / lint           → WARN
       - fintech/auth     / Security Audit / security-scan → OK
  4. e2e-tests must appear in new_jobs (not filtered, since JOB_EXCLUDE=e2e excludes it
     from baseline matching scope but the script actually excludes it entirely — 
     CORRECT: with JOB_EXCLUDE=e2e, e2e-tests is excluded from ALL processing)
     → so e2e-tests should NOT appear in new_jobs either (it's excluded entirely)
  5. summary.critical == 2, summary.warn == 2, summary.ok == 1
"""

import sys
import json
import math
from pathlib import Path

def main(workspace: str):
    ws = Path(workspace)
    checks = []
    passed_all = True

    def add_check(name: str, passed: bool, detail: str):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── Find regression-report.json ─────────────────────────────────────────
    report_files = list(ws.rglob("regression-report.json"))
    if not report_files:
        add_check("report_file_exists", False, "regression-report.json not found anywhere in workspace")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = report_files[0]
    add_check("report_file_exists", True, f"Found at {report_path.relative_to(ws)}")

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        add_check("report_valid_json", False, f"JSON parse error: {e}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    add_check("report_valid_json", True, "Valid JSON")

    # ── Check top-level keys ─────────────────────────────────────────────────
    has_summary     = "summary"     in report
    has_regressions = "regressions" in report
    has_new_jobs    = "new_jobs"    in report
    add_check("report_has_required_keys",
              has_summary and has_regressions and has_new_jobs,
              f"summary={has_summary}, regressions={has_regressions}, new_jobs={has_new_jobs}")

    if not (has_summary and has_regressions):
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    summary     = report["summary"]
    regressions = report["regressions"]

    # ── Summary counts ───────────────────────────────────────────────────────
    # With JOB_EXCLUDE=e2e: e2e-tests is excluded entirely, so:
    #   compared jobs: build-docker(CRIT), run-unit-tests(WARN), lint(WARN), integration(CRIT), security-scan(OK) = 5
    #   critical=2, warn=2, ok=1, new_jobs=0
    expected_critical = 2
    expected_warn     = 2
    expected_ok       = 1
    expected_new      = 0  # e2e excluded by JOB_EXCLUDE

    got_critical = summary.get("critical", -1)
    got_warn     = summary.get("warn", -1)
    got_ok       = summary.get("ok", -1)
    got_new      = summary.get("new_jobs", -1)

    add_check("summary_critical_count",
              got_critical == expected_critical,
              f"Expected critical={expected_critical}, got {got_critical}")
    add_check("summary_warn_count",
              got_warn == expected_warn,
              f"Expected warn={expected_warn}, got {got_warn}")
    add_check("summary_ok_count",
              got_ok == expected_ok,
              f"Expected ok={expected_ok}, got {got_ok}")
    add_check("summary_new_jobs_count",
              got_new == expected_new,
              f"Expected new_jobs={expected_new} (e2e excluded), got {got_new}")

    # ── Per-job severity ─────────────────────────────────────────────────────
    # Build a lookup: (repo, workflow, job) -> severity
    reg_index = {}
    for r in regressions:
        key = (r.get("repo", ""), r.get("workflow", ""), r.get("job", ""))
        reg_index[key] = r.get("severity", "")

    expected_severities = {
        ("fintech/payments", "CI Pipeline", "build-docker"):    "critical",
        ("fintech/ledger",   "CI Pipeline", "integration"):     "critical",
        ("fintech/payments", "CI Pipeline", "run-unit-tests"):  "warn",
        ("fintech/ledger",   "CI Pipeline", "lint"):            "warn",
        ("fintech/auth",     "Security Audit", "security-scan"): "ok",
    }

    for (repo, wf, job), expected_sev in expected_severities.items():
        key = (repo, wf, job)
        got_sev = reg_index.get(key, "MISSING")
        add_check(f"severity_{job.replace('-','_')}",
                  got_sev == expected_sev,
                  f"{repo}/{wf}/{job}: expected={expected_sev}, got={got_sev}")

    # ── e2e-tests NOT in new_jobs (excluded by JOB_EXCLUDE) ─────────────────
    new_jobs_list = report.get("new_jobs", [])
    e2e_in_new = any(nj.get("job", "") == "e2e-tests" for nj in new_jobs_list)
    add_check("e2e_excluded_from_new_jobs",
              not e2e_in_new,
              f"e2e-tests should be excluded by JOB_EXCLUDE filter; found_in_new_jobs={e2e_in_new}")

    # ── build-docker delta sanity (avg delta ~170s) ──────────────────────────
    bd_key = ("fintech/payments", "CI Pipeline", "build-docker")
    if bd_key in reg_index:
        bd_entry = next((r for r in regressions
                         if r.get("repo") == bd_key[0]
                         and r.get("workflow") == bd_key[1]
                         and r.get("job") == bd_key[2]), None)
        if bd_entry:
            delta = bd_entry.get("delta_avg", 0)
            plausible = 150 <= delta <= 200
            add_check("build_docker_delta_avg_plausible",
                      plausible,
                      f"build-docker delta_avg expected ~170s, got {delta}")
        else:
            add_check("build_docker_delta_avg_plausible", False, "build-docker entry missing from regressions list")
    else:
        add_check("build_docker_delta_avg_plausible", False, "build-docker not in regressions index")

    # ── p95 present in output ────────────────────────────────────────────────
    has_p95 = any("cur_p95" in r for r in regressions)
    add_check("p95_metrics_present", has_p95,
              "At least one regression entry must include p95 metrics (cur_p95)")

    # ── Score ────────────────────────────────────────────────────────────────
    n = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / n, 4) if n > 0 else 0.0

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks,
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    main(sys.argv[1])