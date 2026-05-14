#!/usr/bin/env python3
"""
Evaluation script for the lead-storage task.

Usage: python eval_script.py <workspace_dir>
"""
import json
import sys
from pathlib import Path

def find_output_file(workspace: Path):
    """Search for the storage output JSON the agent was asked to create."""
    candidates = list(workspace.rglob("storage_output.json"))
    if candidates:
        return candidates[0]
    return None

def load_json(path: Path):
    with open(path, "r") as f:
        return json.load(f)

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    overall_passed = True

    # ── Locate output file ─────────────────────────────────────────────────────
    output_path = find_output_file(workspace)
    file_found = output_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found at {output_path}" if file_found else "storage_output.json not found anywhere in workspace"
    })
    if not file_found:
        overall_passed = False
        # Short-circuit: can't run further checks
        return overall_passed, 0.0, checks

    # ── Parse output ───────────────────────────────────────────────────────────
    try:
        data = load_json(output_path)
        parse_ok = True
    except Exception as e:
        parse_ok = False
        checks.append({"name": "output_parseable", "passed": False, "detail": str(e)})
        overall_passed = False
        return overall_passed, 0.0, checks

    checks.append({"name": "output_parseable", "passed": True, "detail": "Valid JSON"})

    # ── Validate against output schema ─────────────────────────────────────────
    schema_path = workspace / "references" / "storage-output.schema.json"
    try:
        import jsonschema
        schema = load_json(schema_path)
        jsonschema.validate(instance=data, schema=schema)
        schema_ok = True
        checks.append({"name": "output_matches_schema", "passed": True, "detail": "Passes storage-output.schema.json"})
    except Exception as e:
        schema_ok = False
        checks.append({"name": "output_matches_schema", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── Check top-level status = "success" for approved batch ─────────────────
    status_ok = data.get("status") == "success"
    checks.append({
        "name": "top_level_status_success",
        "passed": status_ok,
        "detail": f"status={data.get('status')}"
    })
    if not status_ok:
        overall_passed = False

    # ── Check stored_count = 4 (5 leads minus 1 duplicate = 4 unique writes) ──
    # Leads: CRE-2024-001, CRE-2024-002, CRE-2024-003, CRE-2024-004
    stored_count = data.get("stored_count", -1)
    stored_count_ok = stored_count == 4
    checks.append({
        "name": "stored_count_equals_4",
        "passed": stored_count_ok,
        "detail": f"stored_count={stored_count} (expected 4)"
    })
    if not stored_count_ok:
        overall_passed = False

    # ── Check duplicate_count = 1 (CRE-2024-001 appears twice) ───────────────
    dup_count = data.get("duplicate_count", -1)
    dup_count_ok = dup_count == 1
    checks.append({
        "name": "duplicate_count_equals_1",
        "passed": dup_count_ok,
        "detail": f"duplicate_count={dup_count} (expected 1)"
    })
    if not dup_count_ok:
        overall_passed = False

    # ── Check records list ────────────────────────────────────────────────────
    records = data.get("records", [])
    expected_ids = {"CRE-2024-001", "CRE-2024-002", "CRE-2024-003", "CRE-2024-004"}

    # Find written records
    written_records = [r for r in records if r.get("write_status") == "written"]
    written_ids = {r["lead_id"] for r in written_records}
    written_ids_ok = written_ids == expected_ids
    checks.append({
        "name": "four_unique_leads_written",
        "passed": written_ids_ok,
        "detail": f"written lead_ids={sorted(written_ids)} (expected {sorted(expected_ids)})"
    })
    if not written_ids_ok:
        overall_passed = False

    # Duplicate record for CRE-2024-001 must appear as "duplicate"
    dup_records = [r for r in records if r.get("write_status") == "duplicate"]
    dup_ids = [r["lead_id"] for r in dup_records]
    dup_lead_ok = "CRE-2024-001" in dup_ids
    checks.append({
        "name": "duplicate_lead_marked_correctly",
        "passed": dup_lead_ok,
        "detail": f"duplicate records: {dup_ids}"
    })
    if not dup_lead_ok:
        overall_passed = False

    # ── Check optional metadata preservation for CRE-2024-001 ────────────────
    lead_001_record = next((r for r in written_records if r.get("lead_id") == "CRE-2024-001"), None)
    if lead_001_record:
        stored = lead_001_record.get("stored_fields", {})
        expected_optional = {
            "deal_type": "lease",
            "asset_class": "office",
            "price_basis": "per_sqft_monthly",
            "area_sqft": 12500,
            "area_basis": "carpet",
            "dataset_mode": "live",
            "record_type": "inbound",
            "city": "Mumbai",
            "city_canonical": "mumbai",
            "locality_canonical": "bandra_kurla_complex",
            "micro_market": "BKC North",
            "location_hint": "Near G-Block metro",
            "urgency": "high",
            "priority_bucket": "tier1"
        }
        missing_or_wrong = []
        for k, v in expected_optional.items():
            if stored.get(k) != v:
                missing_or_wrong.append(f"{k}: expected={v}, got={stored.get(k)}")
        metadata_ok = len(missing_or_wrong) == 0
        checks.append({
            "name": "optional_metadata_preserved_lead_001",
            "passed": metadata_ok,
            "detail": "All optional fields preserved" if metadata_ok else "; ".join(missing_or_wrong)
        })
        if not metadata_ok:
            overall_passed = False
    else:
        checks.append({
            "name": "optional_metadata_preserved_lead_001",
            "passed": False,
            "detail": "CRE-2024-001 not found in written records"
        })
        overall_passed = False

    # ── Check partial metadata for CRE-2024-003 ───────────────────────────────
    lead_003_record = next((r for r in written_records if r.get("lead_id") == "CRE-2024-003"), None)
    if lead_003_record:
        stored_003 = lead_003_record.get("stored_fields", {})
        expected_003 = {
            "city": "Noida",
            "city_canonical": "noida",
            "priority_bucket": "tier2",
            "urgency": "medium",
        }
        missing_003 = [f"{k}: expected={v}, got={stored_003.get(k)}"
                       for k, v in expected_003.items() if stored_003.get(k) != v]
        meta_003_ok = len(missing_003) == 0
        checks.append({
            "name": "optional_metadata_preserved_lead_003",
            "passed": meta_003_ok,
            "detail": "OK" if meta_003_ok else "; ".join(missing_003)
        })
        if not meta_003_ok:
            overall_passed = False
    else:
        checks.append({
            "name": "optional_metadata_preserved_lead_003",
            "passed": False,
            "detail": "CRE-2024-003 not found in written records"
        })
        overall_passed = False

    # ── Check unconfirmed batch produces failure output ────────────────────────
    # Agent must also process broker_inbox/unconfirmed_batch.json and produce
    # a failure output — look for a separate failure output file.
    failure_candidates = list(workspace.rglob("storage_failure_output.json"))
    failure_file_found = len(failure_candidates) > 0
    checks.append({
        "name": "failure_output_file_exists",
        "passed": failure_file_found,
        "detail": f"Found at {failure_candidates[0]}" if failure_file_found else
                  "storage_failure_output.json not found — missing rejection of unconfirmed batch"
    })
    if not failure_file_found:
        overall_passed = False
    else:
        try:
            fail_data = load_json(failure_candidates[0])
            fail_status_ok = fail_data.get("status") == "failure"
            fail_msg_ok = bool(fail_data.get("error_message", "").strip())
            fail_combined = fail_status_ok and fail_msg_ok
            checks.append({
                "name": "failure_output_correct_status_and_message",
                "passed": fail_combined,
                "detail": f"status={fail_data.get('status')}, error_message_present={fail_msg_ok}"
            })
            if not fail_combined:
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "failure_output_correct_status_and_message",
                "passed": False,
                "detail": str(e)
            })
            overall_passed = False

    # ── Compute score ──────────────────────────────────────────────────────────
    total = len(checks)
    passed_n = sum(1 for c in checks if c["passed"])
    score = round(passed_n / total, 4) if total > 0 else 0.0

    return overall_passed, score, checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace dir provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    try:
        overall_passed, score, checks = run_checks(workspace_dir)
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "eval_internal_error",
                                      "passed": False, "detail": str(e)}]}))
        sys.exit(1)

    print(json.dumps({"passed": overall_passed, "score": score, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()