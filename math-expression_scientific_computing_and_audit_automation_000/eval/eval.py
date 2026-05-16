#!/usr/bin/env python3
"""
Evaluation script for AUDIT-2024-042 math expression batch audit task.
Checks that the agent:
1. Found and read batch_042.json
2. Ran eval_expression.py with --json for all 4 expressions
3. Used correct --precision per expression (50, 50, 120, 80)
4. Correctly handled verified=null cases (expr-002 limit, expr-004 solve)
5. Correctly captured verified=true cases (expr-001 integral, expr-003 Pi)
6. Produced a consolidated audit report JSON file named audit_report_AUDIT-2024-042.json
7. Report contains required fields: audit_id, expressions (list of 4), summary
8. Each expression entry has: id, exact, numeric, verified, precision, version
"""

import sys
import json
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find the audit report file ────────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("audit_report_AUDIT-2024-042.json"))
    
    if not candidates:
        # Also accept slight variations
        candidates = list(Path(workspace).rglob("*AUDIT-2024-042*.json"))
        # Exclude the partial failed file and input batch
        candidates = [c for c in candidates 
                      if "partial_FAILED" not in c.name 
                      and "batch_042.json" != c.name
                      and "batch_042" not in c.name or "report" in c.name.lower() or "audit_report" in c.name.lower()]

    if candidates:
        report_path = candidates[0]
        total_score += add_check(
            "report_file_exists",
            True,
            f"Found audit report at: {report_path}"
        )
    else:
        total_score += add_check(
            "report_file_exists",
            False,
            "No file matching 'audit_report_AUDIT-2024-042.json' found in workspace"
        )
        # Cannot proceed without the file
        return checks, total_score, 9  # 9 remaining checks all fail

    # ── Load the report ───────────────────────────────────────────────────────
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        total_score += add_check(
            "report_valid_json",
            True,
            "Report is valid JSON"
        )
    except Exception as e:
        total_score += add_check(
            "report_valid_json",
            False,
            f"Failed to parse JSON: {e}"
        )
        return checks, total_score, 8

    # ── Check audit_id ────────────────────────────────────────────────────────
    audit_id = report.get("audit_id", "")
    total_score += add_check(
        "report_audit_id",
        audit_id == "AUDIT-2024-042",
        f"audit_id = '{audit_id}' (expected 'AUDIT-2024-042')"
    )

    # ── Check expressions array ───────────────────────────────────────────────
    expressions = report.get("expressions", [])
    total_score += add_check(
        "report_has_4_expressions",
        isinstance(expressions, list) and len(expressions) == 4,
        f"expressions count = {len(expressions)} (expected 4)"
    )

    # ── Check summary field ───────────────────────────────────────────────────
    summary = report.get("summary", None)
    total_score += add_check(
        "report_has_summary",
        summary is not None and isinstance(summary, dict),
        f"summary field present: {summary is not None}"
    )

    # ── Build a lookup by id ──────────────────────────────────────────────────
    expr_map = {}
    if isinstance(expressions, list):
        for e in expressions:
            if isinstance(e, dict) and "id" in e:
                expr_map[e["id"]] = e

    # ── Check expr-001: Integrate[Sin[x]^2, {x, 0, Pi}] ─────────────────────
    # precision=50, verified=True (exact symbolic vs numeric are consistent)
    e001 = expr_map.get("expr-001", {})
    e001_precision = e001.get("precision", None)
    e001_verified = e001.get("verified", "MISSING")
    e001_exact = e001.get("exact", "")
    e001_numeric = e001.get("numeric", "")
    e001_version = e001.get("version", "")

    total_score += add_check(
        "expr001_precision_50",
        e001_precision == 50,
        f"expr-001 precision={e001_precision} (expected 50)"
    )
    total_score += add_check(
        "expr001_verified_true",
        e001_verified is True or e001_verified == "true",
        f"expr-001 verified={e001_verified} (expected true — integral consistency check)"
    )
    total_score += add_check(
        "expr001_exact_correct",
        "Pi/2" in str(e001_exact) or "pi/2" in str(e001_exact).lower(),
        f"expr-001 exact='{e001_exact}' (expected Pi/2)"
    )

    # ── Check expr-002: Limit[(Sin[x]-x)/x^3, x->0] ──────────────────────────
    # precision=50, verified=null (symbolic limit, not directly numerically comparable)
    e002 = expr_map.get("expr-002", {})
    e002_precision = e002.get("precision", None)
    e002_verified = e002.get("verified", "MISSING")
    e002_exact = e002.get("exact", "")

    total_score += add_check(
        "expr002_precision_50",
        e002_precision == 50,
        f"expr-002 precision={e002_precision} (expected 50)"
    )
    total_score += add_check(
        "expr002_verified_null",
        e002_verified is None or e002_verified == "null" or str(e002_verified).lower() == "none",
        f"expr-002 verified={e002_verified!r} (expected null — limit is symbolic, not directly verifiable)"
    )
    total_score += add_check(
        "expr002_exact_correct",
        "-1/6" in str(e002_exact) or "1/6" in str(e002_exact),
        f"expr-002 exact='{e002_exact}' (expected -1/6)"
    )

    # ── Check expr-003: N[Pi, 120] ────────────────────────────────────────────
    # precision=120 (HIGH precision, must be explicitly set), verified=True
    e003 = expr_map.get("expr-003", {})
    e003_precision = e003.get("precision", None)
    e003_verified = e003.get("verified", "MISSING")
    e003_exact = e003.get("exact", "")
    e003_numeric = e003.get("numeric", "")

    total_score += add_check(
        "expr003_precision_120",
        e003_precision == 120,
        f"expr-003 precision={e003_precision} (expected 120 — high precision Pi requires explicit --precision 120)"
    )
    total_score += add_check(
        "expr003_verified_true",
        e003_verified is True or e003_verified == "true",
        f"expr-003 verified={e003_verified} (expected true)"
    )
    total_score += add_check(
        "expr003_numeric_starts_with_pi",
        str(e003_numeric).startswith("3.14159"),
        f"expr-003 numeric starts with '3.14159': '{str(e003_numeric)[:20]}'"
    )

    # ── Check expr-004: Solve[x^5 - x - 1 == 0, x] ───────────────────────────
    # precision=80, verified=null (list of roots, not directly comparable)
    e004 = expr_map.get("expr-004", {})
    e004_precision = e004.get("precision", None)
    e004_verified = e004.get("verified", "MISSING")
    e004_exact = e004.get("exact", "")

    total_score += add_check(
        "expr004_precision_80",
        e004_precision == 80,
        f"expr-004 precision={e004_precision} (expected 80)"
    )
    total_score += add_check(
        "expr004_verified_null",
        e004_verified is None or e004_verified == "null" or str(e004_verified).lower() == "none",
        f"expr-004 verified={e004_verified!r} (expected null — list of roots, not directly verifiable)"
    )

    # ── Check version field (at least one expression must have it) ────────────
    versions_present = [
        e.get("version", "") for e in expressions
        if isinstance(e, dict) and e.get("version")
    ]
    total_score += add_check(
        "version_field_captured",
        len(versions_present) > 0 and any("WolframKernel" in str(v) or "math-expression" in str(v) for v in versions_present),
        f"version field present and contains engine info: {versions_present[:1]}"
    )

    return checks, total_score, 0


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]
        }))
        sys.exit(1)

    workspace = sys.argv[1]

    try:
        checks, score, missing_checks = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": f"Evaluation script crashed: {e}"}]
        }))
        sys.exit(1)

    total_possible = len(checks) + missing_checks
    score_pct = score / max(total_possible, 1)
    passed = score_pct >= 0.75 and any(c["name"] == "report_file_exists" and c["passed"] for c in checks)

    print(json.dumps({
        "passed": passed,
        "score": round(score_pct, 3),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()