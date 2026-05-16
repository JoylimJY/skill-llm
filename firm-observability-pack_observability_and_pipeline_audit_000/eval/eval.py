#!/usr/bin/env python3
"""
Evaluation script for firm-observability-pack task.
Usage: python eval_script.py /workspace
"""
import sys
import json
import sqlite3
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
overall_passed = True

def add_check(name, passed, detail):
    global overall_passed
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        overall_passed = False

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: SQLite database was created by the observability pipeline tool
# ─────────────────────────────────────────────────────────────────────────────
db_files = list(workspace.rglob("*.db"))
db_files = [f for f in db_files if "trace" in f.name.lower() or "observ" in f.name.lower() or f.name == "traces.db"]
if not db_files:
    # Broader search for any .db file
    db_files = list(workspace.rglob("*.db"))

if not db_files:
    add_check("sqlite_db_created", False, "No SQLite .db file found anywhere in workspace.")
    db_conn = None
else:
    db_path = db_files[0]
    add_check("sqlite_db_created", True, f"SQLite DB found at: {db_path}")
    try:
        db_conn = sqlite3.connect(str(db_path))
    except Exception as e:
        add_check("sqlite_db_created", False, f"Cannot open SQLite DB at {db_path}: {e}")
        db_conn = None

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: 'traces' table exists and has correct schema
# ─────────────────────────────────────────────────────────────────────────────
if db_conn:
    try:
        cur = db_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traces'")
        tbl = cur.fetchone()
        if not tbl:
            add_check("traces_table_schema", False, "Table 'traces' not found in SQLite DB.")
        else:
            cur.execute("PRAGMA table_info(traces)")
            cols = {row[1] for row in cur.fetchall()}
            required_cols = {"trace_id", "service", "operation", "status", "timestamp", "duration_ms"}
            missing = required_cols - cols
            if missing:
                add_check("traces_table_schema", False, f"Missing columns in 'traces': {missing}")
            else:
                add_check("traces_table_schema", True, f"'traces' table has all required columns: {required_cols}")
    except Exception as e:
        add_check("traces_table_schema", False, f"Error inspecting 'traces' table: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: Correct number of rows ingested (malformed/empty lines must be skipped)
# Expected: ~118 valid lines out of 122 total (2 malformed JSON, 1 empty, and
# lines missing required fields get skipped; the tool skips those without required fields)
# The mock skips: 1 empty line, 1 bad JSON, lines missing required fields.
# With seed=42: 7 lines have span_id removed (but still have all required fields so they're OK),
# 4 lines have duration_ms="NaN" (stored as NULL, not skipped), 1 broken JSON, 1 empty line.
# So we expect 120 - 1 (broken JSON) - 1 (empty) = 118 ingested.
# ─────────────────────────────────────────────────────────────────────────────
if db_conn:
    try:
        cur = db_conn.cursor()
        cur.execute("SELECT COUNT(*) FROM traces")
        row_count = cur.fetchone()[0]
        # Accept range [115, 122] to allow for slight variation in malformed detection
        if 115 <= row_count <= 122:
            add_check("traces_ingestion_count", True, f"Traces table has {row_count} rows (expected ~118, acceptable 115-122).")
        else:
            add_check("traces_ingestion_count", False, f"Traces table has {row_count} rows; expected between 115 and 122 (malformed lines must be skipped).")
    except Exception as e:
        add_check("traces_ingestion_count", False, f"Error counting traces: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: ingest_meta table exists with ingested_count and skipped_count
# ─────────────────────────────────────────────────────────────────────────────
if db_conn:
    try:
        cur = db_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingest_meta'")
        tbl = cur.fetchone()
        if not tbl:
            add_check("ingest_meta_table", False, "Table 'ingest_meta' not found — tool was not properly invoked.")
        else:
            cur.execute("SELECT key, value FROM ingest_meta")
            meta = dict(cur.fetchall())
            if "ingested_count" in meta and "skipped_count" in meta:
                add_check("ingest_meta_table", True, f"ingest_meta present: ingested={meta.get('ingested_count')}, skipped={meta.get('skipped_count')}")
            else:
                add_check("ingest_meta_table", False, f"ingest_meta missing keys. Found: {list(meta.keys())}")
    except Exception as e:
        add_check("ingest_meta_table", False, f"Error reading ingest_meta: {e}")

if db_conn:
    db_conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: CI validation report was created
# ─────────────────────────────────────────────────────────────────────────────
report_files = list(workspace.rglob("ci_validation_report.json"))
if not report_files:
    # Also accept any file named *validation*report* or *ci*report*
    report_files = [f for f in workspace.rglob("*.json")
                    if "validation" in f.name.lower() and "report" in f.name.lower()]
if not report_files:
    report_files = [f for f in workspace.rglob("*.json")
                    if "ci" in f.name.lower() and "report" in f.name.lower()]

if not report_files:
    add_check("ci_validation_report_created", False, "No CI validation report JSON found in workspace.")
    ci_report = None
else:
    report_path = report_files[0]
    try:
        with open(report_path) as f:
            ci_report = json.load(f)
        add_check("ci_validation_report_created", True, f"CI validation report found at: {report_path}")
    except Exception as e:
        add_check("ci_validation_report_created", False, f"Cannot parse CI validation report at {report_path}: {e}")
        ci_report = None

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: CI report correctly identifies FAIL status
# ─────────────────────────────────────────────────────────────────────────────
if ci_report:
    try:
        status = ci_report.get("validation_status", "")
        if status == "FAIL":
            add_check("ci_validation_status_fail", True, "validation_status correctly set to 'FAIL'.")
        else:
            add_check("ci_validation_status_fail", False, f"validation_status is '{status}', expected 'FAIL'.")
    except Exception as e:
        add_check("ci_validation_status_fail", False, f"Error reading validation_status: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: CI report contains required critical violations
# ─────────────────────────────────────────────────────────────────────────────
if ci_report:
    try:
        violations = ci_report.get("violations", [])
        violation_rules = {v.get("rule") for v in violations}
        required_violations = {"SECURITY_GATE_REQUIRED", "APPROVAL_GATE_REQUIRED"}
        missing_violations = required_violations - violation_rules
        if not missing_violations:
            critical_count = ci_report.get("summary", {}).get("critical", 0)
            add_check("ci_critical_violations_detected", True,
                      f"Required critical violations detected: {required_violations}. Critical count={critical_count}")
        else:
            add_check("ci_critical_violations_detected", False,
                      f"Missing violations in report: {missing_violations}. Found: {violation_rules}")
    except Exception as e:
        add_check("ci_critical_violations_detected", False, f"Error reading violations: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: CI report contains HIGH severity violations (integration test + coverage)
# ─────────────────────────────────────────────────────────────────────────────
if ci_report:
    try:
        violations = ci_report.get("violations", [])
        violation_rules = {v.get("rule") for v in violations}
        high_violations = {"INTEGRATION_TEST_REQUIRED", "COVERAGE_THRESHOLD"}
        missing_high = high_violations - violation_rules
        if not missing_high:
            add_check("ci_high_violations_detected", True,
                      f"HIGH severity violations correctly detected: {high_violations}")
        else:
            add_check("ci_high_violations_detected", False,
                      f"Missing HIGH violations: {missing_high}. Found: {violation_rules}")
    except Exception as e:
        add_check("ci_high_violations_detected", False, f"Error reading high violations: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: Final audit summary report was created (cross-referencing both outputs)
# ─────────────────────────────────────────────────────────────────────────────
summary_files = list(workspace.rglob("audit_summary.json"))
if not summary_files:
    summary_files = [f for f in workspace.rglob("*.json")
                     if "audit" in f.name.lower() and "summary" in f.name.lower()]
if not summary_files:
    summary_files = [f for f in workspace.rglob("*.json")
                     if "summary" in f.name.lower() and "report" not in f.name.lower()]

if not summary_files:
    add_check("audit_summary_created", False,
              "No audit_summary.json found. Agent must produce a combined audit report cross-referencing trace ingest stats and CI validation results.")
    audit_summary = None
else:
    summary_path = summary_files[0]
    try:
        with open(summary_path) as f:
            audit_summary = json.load(f)
        add_check("audit_summary_created", True, f"Audit summary found at: {summary_path}")
    except Exception as e:
        add_check("audit_summary_created", False, f"Cannot parse audit summary at {summary_path}: {e}")
        audit_summary = None

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: Audit summary contains both trace ingestion data AND CI violation data
# ─────────────────────────────────────────────────────────────────────────────
if audit_summary:
    try:
        content_str = json.dumps(audit_summary).lower()
        has_trace_data = any(k in content_str for k in ["ingested", "trace", "span", "skipped"])
        has_ci_data = any(k in content_str for k in ["violation", "security_gate", "approval_gate", "ci_", "pipeline"])

        if has_trace_data and has_ci_data:
            add_check("audit_summary_cross_reference", True,
                      "Audit summary contains both trace ingestion data and CI violation data.")
        elif has_trace_data and not has_ci_data:
            add_check("audit_summary_cross_reference", False,
                      "Audit summary has trace data but missing CI violation data.")
        elif has_ci_data and not has_trace_data:
            add_check("audit_summary_cross_reference", False,
                      "Audit summary has CI data but missing trace ingestion data.")
        else:
            add_check("audit_summary_cross_reference", False,
                      "Audit summary is missing both trace ingestion and CI violation data.")
    except Exception as e:
        add_check("audit_summary_cross_reference", False, f"Error analyzing audit summary content: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = all(c["passed"] for c in checks)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))