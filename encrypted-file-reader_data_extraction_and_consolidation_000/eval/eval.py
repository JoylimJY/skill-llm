#!/usr/bin/env python3
"""
Evaluates the agent's consolidated_report.json output.
Expected: the agent read budget.xlsx, meeting_minutes.docx, and access_log.csv
using /skills/encrypted-file-reader/read_file.py and produced a JSON report.
"""

import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    
    checks = []
    
    # ── Find the output file ──────────────────────────────────────────────────
    candidates = list(workspace.rglob("consolidated_report.json"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} consolidated_report.json file(s)" if file_found
                  else "consolidated_report.json not found anywhere in workspace"
    })
    
    if not file_found:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    report_path = candidates[0]
    
    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        report_text = report_path.read_text(encoding='utf-8')
        report = json.loads(report_text)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # ── Check 1: Budget data present ─────────────────────────────────────────
    # Must contain at least some department+budget data
    report_str = json.dumps(report).lower()
    
    budget_departments = ["engineering", "marketing", "operations", "hr", "legal"]
    found_depts = [d for d in budget_departments if d in report_str]
    budget_dept_ok = len(found_depts) >= 4
    checks.append({
        "name": "budget_departments_present",
        "passed": budget_dept_ok,
        "detail": f"Found departments: {found_depts} (need >=4 of {budget_departments})"
    })

    # Must contain numeric budget values from xlsx
    budget_values = ["520000", "210000", "340000", "95000", "150000"]
    found_vals = [v for v in budget_values if v in report_str]
    budget_vals_ok = len(found_vals) >= 3
    checks.append({
        "name": "budget_values_present",
        "passed": budget_vals_ok,
        "detail": f"Found budget values: {found_vals} (need >=3 of {budget_values})"
    })

    # ── Check 2: Meeting minutes data present ─────────────────────────────────
    # Must contain key info from the docx
    docx_keywords = ["orion", "cybersecurity", "75000", "alice", "2024-10-31"]
    found_kw = [k for k in docx_keywords if k in report_str]
    docx_ok = len(found_kw) >= 3
    checks.append({
        "name": "meeting_minutes_content_present",
        "passed": docx_ok,
        "detail": f"Found docx keywords: {found_kw} (need >=3 of {docx_keywords})"
    })

    # ── Check 3: Access log data present ─────────────────────────────────────
    # Must contain data from the access_log.csv
    log_keywords = ["u1042", "u2019", "denied", "success", "/finance/budget_report"]
    found_log = [k for k in log_keywords if k.lower() in report_str]
    log_ok = len(found_log) >= 3
    checks.append({
        "name": "access_log_content_present",
        "passed": log_ok,
        "detail": f"Found log keywords: {found_log} (need >=3 of {log_keywords})"
    })

    # ── Check 4: Report has meaningful structure (not just raw text dump) ─────
    # The report should be a dict (object), not a list or scalar
    is_dict = isinstance(report, dict)
    checks.append({
        "name": "report_is_structured_object",
        "passed": is_dict,
        "detail": f"Top-level JSON type is: {type(report).__name__} (expected dict/object)"
    })

    # ── Check 5: All three sources covered in some structured way ─────────────
    # At minimum 3 top-level or nested keys that semantically correspond to the 3 files
    def flatten_keys(obj, depth=0):
        keys = []
        if depth > 5:
            return keys
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.append(str(k).lower())
                keys.extend(flatten_keys(v, depth+1))
        elif isinstance(obj, list):
            for item in obj:
                keys.extend(flatten_keys(item, depth+1))
        return keys

    all_keys = flatten_keys(report)
    budget_key = any(k in all_keys for k in ["budget", "budgets", "budget_data", "financials", "financial"])
    meeting_key = any(k in all_keys for k in ["meeting", "minutes", "meeting_minutes", "decisions", "actions"])
    log_key = any(k in all_keys for k in ["log", "access_log", "access", "audit", "logs", "events"])
    
    structured_sources = sum([budget_key, meeting_key, log_key])
    structure_ok = structured_sources >= 2
    checks.append({
        "name": "structured_source_sections",
        "passed": structure_ok,
        "detail": (f"budget_section={budget_key}, meeting_section={meeting_key}, "
                   f"log_section={log_key}. Need >=2 recognizable sections.")
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()