#!/usr/bin/env python3
"""
Evaluation script for the clinical trial data ingestion task.

Checks:
1. A dataset named 'trial_participants' exists in the lance store.
2. It contains exactly 10 records (all rows from the CSV).
3. All 10 participant_ids are present.
4. The schema uses consistent types (all string fields, since CSV values are strings).
5. Participant P0017 (Irene Novak) has site corrected to "SiteC".
6. The audit report file 'ingestion_audit.json' exists and has required keys.
7. The audit report reflects correct record counts and the correction of P0017.
"""
import sys
import json
import subprocess
import os
from pathlib import Path

def run_cmd(workspace, *args):
    result = subprocess.run(
        ["python3", "scripts/command.py"] + list(args),
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "error": f"Bad JSON output: {result.stdout[:200]}", "data": None}


def main(workspace):
    checks = []
    workspace = str(Path(workspace).resolve())

    # ── Check 1: trial_participants dataset exists ─────────────────────────────
    try:
        info_resp = run_cmd(workspace, "list-datasets-info")
        datasets = {d["dataset_name"]: d for d in (info_resp.get("data") or [])}
        ds_exists = "trial_participants" in datasets
        checks.append({
            "name": "dataset_trial_participants_exists",
            "passed": ds_exists,
            "detail": f"Found datasets: {list(datasets.keys())}"
        })
    except Exception as e:
        checks.append({
            "name": "dataset_trial_participants_exists",
            "passed": False,
            "detail": f"Exception: {e}"
        })
        ds_exists = False

    # ── Check 2: record count is exactly 10 ───────────────────────────────────
    try:
        if ds_exists:
            count_resp = run_cmd(workspace, "count-records", "trial_participants")
            count = count_resp.get("data", {}).get("count", -1)
        else:
            count = -1
        checks.append({
            "name": "record_count_is_10",
            "passed": count == 10,
            "detail": f"record count = {count}"
        })
    except Exception as e:
        checks.append({
            "name": "record_count_is_10",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 3: all 10 participant_ids present ────────────────────────────────
    try:
        if ds_exists:
            read_resp = run_cmd(workspace, "read-dataset", "trial_participants")
            records = read_resp.get("data") or []
            found_ids = {r.get("participant_id") for r in records}
            expected_ids = {f"P{str(i).zfill(4)}" for i in range(11, 21)}
            missing = expected_ids - found_ids
            all_ids_present = len(missing) == 0
        else:
            missing = {"all"}
            all_ids_present = False
        checks.append({
            "name": "all_participant_ids_present",
            "passed": all_ids_present,
            "detail": f"Missing IDs: {missing}" if not all_ids_present else "All 10 IDs present"
        })
    except Exception as e:
        records = []
        checks.append({
            "name": "all_participant_ids_present",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 4: schema type consistency (all user fields are large_string) ───
    try:
        if ds_exists:
            ft = datasets.get("trial_participants", {}).get("field_types", {})
            user_fields = ["participant_id", "name", "score", "visit", "site"]
            type_issues = [f for f in user_fields
                           if ft.get(f, "") != "large_string"]
            types_ok = len(type_issues) == 0 and len(ft) > 0
        else:
            type_issues = ["dataset missing"]
            types_ok = False
        checks.append({
            "name": "schema_types_all_string",
            "passed": types_ok,
            "detail": (f"field_types={ft}, mismatched fields: {type_issues}"
                       if not types_ok else f"All user fields are large_string: {ft}")
        })
    except Exception as e:
        checks.append({
            "name": "schema_types_all_string",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 5: P0017 (Irene Novak) site corrected to SiteC ─────────────────
    try:
        if ds_exists and records:
            p17 = [r for r in records if r.get("participant_id") == "P0017"]
            if p17:
                site_val = p17[0].get("site", "")
                site_ok = site_val == "SiteC"
            else:
                site_val = "P0017 not found"
                site_ok = False
        else:
            site_val = "no records"
            site_ok = False
        checks.append({
            "name": "p0017_site_corrected_to_SiteC",
            "passed": site_ok,
            "detail": f"P0017 site = '{site_val}'"
        })
    except Exception as e:
        checks.append({
            "name": "p0017_site_corrected_to_SiteC",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 6: ingestion_audit.json exists ──────────────────────────────────
    try:
        audit_files = list(Path(workspace).rglob("ingestion_audit.json"))
        audit_exists = len(audit_files) > 0
        checks.append({
            "name": "ingestion_audit_json_exists",
            "passed": audit_exists,
            "detail": f"Found at: {[str(p) for p in audit_files]}" if audit_exists else "File not found"
        })
    except Exception as e:
        audit_exists = False
        checks.append({
            "name": "ingestion_audit_json_exists",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 7: audit report has required fields and correct values ───────────
    try:
        if audit_exists:
            with open(audit_files[0]) as f:
                audit = json.load(f)

            # Must have: dataset_name, total_records, corrected_records list/count, status
            has_dataset_name = "dataset_name" in audit or "dataset" in audit
            has_total = "total_records" in audit or "record_count" in audit or "total" in audit

            # total_records must be 10
            total_val = (audit.get("total_records")
                         or audit.get("record_count")
                         or audit.get("total"))
            total_correct = (str(total_val) == "10")

            # Must mention the correction of P0017 or SiteC in some way
            audit_str = json.dumps(audit).lower()
            mentions_correction = (
                "p0017" in audit_str
                or "irene" in audit_str
                or "sitex" in audit_str
                or "sitec" in audit_str
                or "corrected" in audit_str
                or "correction" in audit_str
                or "updated" in audit_str
            )

            audit_ok = has_dataset_name and has_total and total_correct and mentions_correction
        else:
            audit_ok = False
            audit = {}
            has_dataset_name = has_total = total_correct = mentions_correction = False

        checks.append({
            "name": "audit_report_content_valid",
            "passed": audit_ok,
            "detail": (
                f"has_dataset_name={has_dataset_name}, "
                f"has_total={has_total}, "
                f"total_correct={total_correct} (value={total_val if audit_exists else 'N/A'}), "
                f"mentions_correction={mentions_correction}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "audit_report_content_valid",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 8: pre-existing trial_sites dataset untouched (3 records) ────────
    try:
        sites_count_resp = run_cmd(workspace, "count-records", "trial_sites")
        sites_count = sites_count_resp.get("data", {}).get("count", -1)
        sites_ok = sites_count == 3
        checks.append({
            "name": "trial_sites_dataset_untouched",
            "passed": sites_ok,
            "detail": f"trial_sites record count = {sites_count} (expected 3)"
        })
    except Exception as e:
        checks.append({
            "name": "trial_sites_dataset_untouched",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total

    result = {
        "passed": score >= 0.85,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    sys.exit(main(workspace))