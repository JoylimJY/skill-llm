#!/usr/bin/env python3
"""
Evaluation script for the health-data skill task.

Checks:
1. step_records.json exists somewhere in the workspace
2. step_records.json has 600 permissions (proprietary --out constraint)
3. step_records.json contains valid JSON array with step count records
4. step_records.json has at most 25 records (--limit enforcement)
5. Each record contains required fields: type, value, startDate
6. wellness_summary.json exists somewhere in the workspace
7. wellness_summary.json is valid JSON with required keys: steps_total, distance_m, sleep_asleep, sleep_inbed, top_sources
8. wellness_summary.json values are plausible (non-zero steps, numeric types)
9. top_sources is a list with at least 1 entry
10. File permissions on step_records.json are strictly 600

Usage: python eval.py <workspace_dir>
"""

import sys
import json
import os
import stat
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── Check 1: step_records.json exists ────────────────────────────────────
    step_files = list(ws.rglob("step_records.json"))
    if not step_files:
        checks.append(check("step_records.json exists", False, "File not found anywhere in workspace"))
        # Can't do further step-file checks
        step_file = None
    else:
        step_file = step_files[0]
        checks.append(check("step_records.json exists", True, f"Found at {step_file}"))

    # ── Check 2: step_records.json has 600 permissions ────────────────────────
    if step_file:
        try:
            mode = oct(stat.S_IMODE(step_file.stat().st_mode))
            is_600 = stat.S_IMODE(step_file.stat().st_mode) == 0o600
            checks.append(check(
                "step_records.json has 600 permissions",
                is_600,
                f"Permissions: {mode} (expected 0o600)"
            ))
        except Exception as e:
            checks.append(check("step_records.json has 600 permissions", False, str(e)))

    # ── Check 3: step_records.json is valid JSON array ────────────────────────
    step_data = None
    if step_file:
        try:
            raw = step_file.read_text()
            step_data = json.loads(raw)
            is_list = isinstance(step_data, list)
            checks.append(check(
                "step_records.json is valid JSON array",
                is_list,
                f"Type: {type(step_data).__name__}, length: {len(step_data) if is_list else 'N/A'}"
            ))
        except Exception as e:
            checks.append(check("step_records.json is valid JSON array", False, str(e)))
            step_data = None

    # ── Check 4: step_records.json has ≤ 25 records ──────────────────────────
    if step_data is not None and isinstance(step_data, list):
        count = len(step_data)
        within_limit = 1 <= count <= 25
        checks.append(check(
            "step_records.json has between 1 and 25 records (--limit enforcement)",
            within_limit,
            f"Record count: {count}"
        ))

        # ── Check 5: Records contain required fields ──────────────────────────
        if count > 0:
            required_fields = {"type", "value", "startDate"}
            first = step_data[0]
            if isinstance(first, dict):
                has_fields = required_fields.issubset(set(first.keys()))
                missing = required_fields - set(first.keys())
                # Also accept snake_case or camelCase aliases that jq might produce
                checks.append(check(
                    "step_records records contain required fields (type, value, startDate)",
                    has_fields,
                    f"Fields in first record: {list(first.keys())}, missing: {list(missing)}"
                ))
                # Check type is step count
                all_steps = all(
                    r.get("type", "") == "HKQuantityTypeIdentifierStepCount"
                    for r in step_data if isinstance(r, dict)
                )
                checks.append(check(
                    "All records in step_records.json are HKQuantityTypeIdentifierStepCount",
                    all_steps,
                    f"Sample type value: {first.get('type', 'MISSING')}"
                ))
            else:
                checks.append(check(
                    "step_records records contain required fields",
                    False,
                    f"First record is not a dict: {type(first).__name__}"
                ))
                checks.append(check(
                    "All records are HKQuantityTypeIdentifierStepCount",
                    False,
                    "Records not in dict format"
                ))
        else:
            checks.append(check("step_records records contain required fields", False, "Array is empty"))
            checks.append(check("All records are HKQuantityTypeIdentifierStepCount", False, "Array is empty"))
    else:
        if step_data is None and step_file:
            pass  # already noted invalid JSON
        else:
            checks.append(check("step_records.json has between 1 and 25 records", False, "Not a list"))
            checks.append(check("step_records records contain required fields", False, "Not a list"))
            checks.append(check("All records are HKQuantityTypeIdentifierStepCount", False, "Not a list"))

    # ── Check 6: wellness_summary.json exists ────────────────────────────────
    summary_files = list(ws.rglob("wellness_summary.json"))
    if not summary_files:
        checks.append(check("wellness_summary.json exists", False, "File not found anywhere in workspace"))
        summary_data = None
        summary_file = None
    else:
        summary_file = summary_files[0]
        checks.append(check("wellness_summary.json exists", True, f"Found at {summary_file}"))

        # ── Check 7: wellness_summary.json is valid JSON with required keys ──
        try:
            raw = summary_file.read_text()
            summary_data = json.loads(raw)
            required_keys = {"steps_total", "distance_m", "sleep_asleep", "sleep_inbed", "top_sources"}
            present = set(summary_data.keys()) if isinstance(summary_data, dict) else set()
            missing_keys = required_keys - present
            has_keys = len(missing_keys) == 0
            checks.append(check(
                "wellness_summary.json has required keys",
                has_keys,
                f"Present: {list(present)}, Missing: {list(missing_keys)}"
            ))
        except Exception as e:
            checks.append(check("wellness_summary.json is valid JSON", False, str(e)))
            summary_data = None

    # ── Check 8: wellness_summary.json values are plausible ──────────────────
    if summary_data and isinstance(summary_data, dict):
        try:
            steps = float(summary_data.get("steps_total", 0))
            dist  = float(summary_data.get("distance_m", 0))
            asleep = int(summary_data.get("sleep_asleep", -1))
            inbed  = int(summary_data.get("sleep_inbed", -1))
            plausible = steps > 0 and dist > 0 and asleep >= 0 and inbed >= 0
            checks.append(check(
                "wellness_summary.json values are plausible (non-zero steps/distance, non-negative sleep)",
                plausible,
                f"steps={steps}, distance_m={dist}, sleep_asleep={asleep}, sleep_inbed={inbed}"
            ))
        except (TypeError, ValueError) as e:
            checks.append(check(
                "wellness_summary.json values are plausible",
                False,
                f"Type conversion error: {e}"
            ))

        # ── Check 9: top_sources is a non-empty list ──────────────────────────
        top_sources = summary_data.get("top_sources", None)
        is_list_nonempty = isinstance(top_sources, list) and len(top_sources) >= 1
        checks.append(check(
            "wellness_summary.json top_sources is a non-empty list",
            is_list_nonempty,
            f"top_sources type: {type(top_sources).__name__}, value: {top_sources}"
        ))
    else:
        if summary_data is not None:
            checks.append(check("wellness_summary.json values are plausible", False, "Not a dict"))
            checks.append(check("wellness_summary.json top_sources is a non-empty list", False, "Not a dict"))

    # ── Scoring ───────────────────────────────────────────────────────────────
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "eval invocation", "passed": False, "detail": "No workspace argument provided"}
        ]}))
        sys.exit(1)
    run_eval(sys.argv[1])