#!/usr/bin/env python3
"""
Evaluation script for the GitHub Actions Hardening Audit task.

Expected agent behaviour:
  1. Run the audit with:
       WORKFLOW_GLOB='.github/workflows/*.y*ml'
       OUTPUT_FORMAT=json
       REQUIRE_CONCURRENCY=1
       WARN_SCORE=2
       CRITICAL_SCORE=5
       EVENT_EXCLUDE='release'
       ALLOW_REF_REGEX='@v4'  (whitelist major-v4 as approved ref per fintech policy)
       FAIL_ON_CRITICAL=1
     and save the JSON output to audit-report.json

  The task prompt says:
    - Machine-readable report as audit-report.json
    - Score adjusted so workflows with ≥2 gaps are flagged as warnings, ≥5 as critical
    - Exclude release-only pipelines from scope
    - v4 action refs are pre-approved; only flag truly floating refs (@main, @master, @latest)
    - Require concurrency controls in the check
    - Fail exit code if any critical workflows found
"""

import sys
import json
import os
from pathlib import Path

def find_report(workspace):
    """Search for audit-report.json anywhere in the workspace."""
    hits = list(Path(workspace).rglob("audit-report.json"))
    return hits[0] if hits else None

def load_json(path):
    with open(path) as f:
        return json.load(f)

def run_eval(workspace):
    checks = []

    # ── CHECK 1: report file exists ───────────────────────────────────────────
    report_path = find_report(workspace)
    checks.append({
        "name": "audit-report.json exists",
        "passed": report_path is not None,
        "detail": str(report_path) if report_path else "File not found anywhere in workspace"
    })
    if report_path is None:
        return checks, 0.0

    # ── CHECK 2: valid JSON with expected top-level keys ──────────────────────
    try:
        data = load_json(report_path)
        has_keys = all(k in data for k in ("summary", "workflows", "critical_workflows"))
        checks.append({
            "name": "JSON has required keys (summary, workflows, critical_workflows)",
            "passed": has_keys,
            "detail": f"Keys present: {list(data.keys())}"
        })
    except Exception as e:
        checks.append({
            "name": "JSON has required keys (summary, workflows, critical_workflows)",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return checks, 0.0

    summary = data.get("summary", {})
    workflows = data.get("workflows", [])
    critical_workflows = data.get("critical_workflows", [])

    # helper: extract filenames from a list of workflow dicts
    def fnames(wf_list):
        return set(os.path.basename(w.get("file", "")) for w in wf_list)

    # ── CHECK 3: release.yml is EXCLUDED (EVENT_EXCLUDE=release) ─────────────
    all_scanned_names = fnames(workflows)
    release_excluded = "release.yml" not in all_scanned_names
    checks.append({
        "name": "release.yml excluded from results (event filter applied)",
        "passed": release_excluded,
        "detail": f"Scanned workflow filenames: {sorted(all_scanned_names)}"
    })

    # ── CHECK 4: fraud-model-train.yml is score 0 or not critical ─────────────
    # fraud-model-train triggers on push+schedule but has everything; score should be 0
    fraud_entry = next(
        (w for w in workflows if "fraud-model-train" in w.get("file", "")), None
    )
    fraud_ok = fraud_entry is not None and fraud_entry.get("severity") == "ok"
    checks.append({
        "name": "fraud-model-train.yml is severity=ok (well-hardened workflow)",
        "passed": fraud_ok,
        "detail": f"Entry: {fraud_entry}"
    })

    # ── CHECK 5: With REQUIRE_CONCURRENCY=1 + CRITICAL_SCORE=5, multiple workflows
    #            that are missing concurrency + other issues must be critical ──
    # Workflows expected to be critical:
    # ci-pr.yml           → timeout(1-lint-job) + permissions(1) + concurrency(1) + floating(@main=1) = 4... 
    #   With ALLOW_REF_REGEX=@v4 pinning @v4 as approved, @main is still floating.
    #   Actually re-count:
    #     lint job: no timeout → +1; test job: has timeout → 0
    #     no workflow-level perms, not all jobs have perms → +1
    #     no concurrency → +1
    #     floating: @main (setup-python) → +1  (checkout@v4 is whitelisted)
    #     score = 4 → warn (WARN_SCORE=2, CRITICAL_SCORE=5) → warn
    # deploy-staging.yml  → deploy job: no timeout→+1; no perms→+1; no concurrency→+1;
    #                        @master→+1; @latest→+1; score=5 → critical ✓
    # security-scan.yml   → no timeout→+1; no perms→+1; no concurrency→+1;
    #                        snyk@v3→floating(major-only)→+1; codeql@v3→+1; score=5→critical ✓
    # dependabot-auto-merge.yml → no timeout→+1; no perms→+1; no concurrency→+1;
    #                              @latest×2→+2; score=5→critical ✓
    # scheduled-compliance.yml → audit job has timeout+perms; compliance-report has no timeout→+1;
    #                              no workflow perms (but not ALL jobs have them)→+1; no concurrency→+1;
    #                              ossf@v4 whitelisted; checkout@v4 whitelisted → score=3 → warn
    # docs-deploy.yml     → has concurrency, has perms, has timeout, @v4 whitelisted → score=0 → ok
    # fraud-model-train.yml → score=0 → ok
    # 
    # Expected criticals (with ALLOW_REF_REGEX=@v4, REQUIRE_CONCURRENCY=1, CRITICAL_SCORE=5):
    #   deploy-staging.yml, security-scan.yml, dependabot-auto-merge.yml

    expected_criticals = {"deploy-staging.yml", "security-scan.yml", "dependabot-auto-merge.yml"}
    actual_criticals = fnames(critical_workflows)

    criticals_match = expected_criticals.issubset(actual_criticals)
    checks.append({
        "name": f"Expected critical workflows flagged: {sorted(expected_criticals)}",
        "passed": criticals_match,
        "detail": f"Actual critical workflow filenames: {sorted(actual_criticals)}"
    })

    # ── CHECK 6: Non-critical workflows not wrongly elevated ──────────────────
    should_not_be_critical = {"docs-deploy.yml", "fraud-model-train.yml", "release.yml"}
    wrong_criticals = should_not_be_critical & actual_criticals
    no_false_criticals = len(wrong_criticals) == 0
    checks.append({
        "name": "Well-hardened workflows (docs-deploy, fraud-model-train) not marked critical",
        "passed": no_false_criticals,
        "detail": f"Wrongly critical: {sorted(wrong_criticals)}"
    })

    # ── CHECK 7: summary critical count ≥ 3 (at least our 3 expected are there) ─
    summary_critical = summary.get("critical", 0)
    checks.append({
        "name": "Summary reports ≥3 critical workflows",
        "passed": summary_critical >= 3,
        "detail": f"summary.critical = {summary_critical}"
    })

    # ── CHECK 8: REQUIRE_CONCURRENCY was enabled ──────────────────────────────
    # Proxy: docs-deploy.yml has concurrency + all else; its score should be 0.
    # If REQUIRE_CONCURRENCY was NOT set, deploy-staging would be score 4 (not 5) → warn, not critical.
    # So the presence of deploy-staging as critical is itself evidence of REQUIRE_CONCURRENCY=1.
    # Additional proxy: look for "missing concurrency" in any issue list.
    concurrency_issues_found = any(
        "concurrency" in iss.lower()
        for w in workflows
        for iss in w.get("issues", [])
    )
    checks.append({
        "name": "Concurrency check was enabled (issues reference missing concurrency)",
        "passed": concurrency_issues_found,
        "detail": "At least one workflow issue mentions concurrency"
    })

    # ── CHECK 9: @v4 refs are NOT flagged as floating (ALLOW_REF_REGEX respected) ─
    v4_flagged = any(
        "@v4" in iss and "floating" in iss.lower()
        for w in workflows
        for iss in w.get("issues", [])
    )
    checks.append({
        "name": "@v4 refs are whitelisted and NOT flagged as floating",
        "passed": not v4_flagged,
        "detail": "No issue should mention '@v4' as a floating ref"
    })

    # ── CHECK 10: summary total does NOT include release.yml ──────────────────
    summary_total = summary.get("total", 0)
    # We have 8 workflows total; minus release.yml = 7
    # (fraud-model-train triggers on schedule too, not excluded)
    release_not_in_total = summary_total <= 7
    checks.append({
        "name": "Summary total ≤ 7 (release.yml excluded from count)",
        "passed": release_not_in_total,
        "detail": f"summary.total = {summary_total} (expected ≤7)"
    })

    # ── SCORE ─────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4)
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_eval(workspace)
    except Exception as e:
        checks = [{"name": "eval-harness", "passed": False, "detail": f"Unexpected error: {e}"}]
        score = 0.0

    passed = score >= 0.75
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()