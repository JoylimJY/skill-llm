import sys
import json
import csv
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    csv_path = Path(workspace) / "papers" / "extraction_table.csv"

    REQUIRED_COLS = [
        "rob_selection", "rob_measurement", "rob_confounding",
        "rob_reporting", "rob_overall", "rob_notes",
    ]
    VALID_VALUES = {"low", "unclear", "high"}

    # ── CHECK 1: file exists ──────────────────────────────────────────────────
    if not csv_path.exists():
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "papers/extraction_table.csv not found."})
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append({"name": "file_exists", "passed": True,
                    "detail": "papers/extraction_table.csv present."})

    # ── load CSV ──────────────────────────────────────────────────────────────
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames or []
    except Exception as e:
        checks.append({"name": "csv_parseable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 2: canonical column names present (old bad names gone) ──────────
    bad_cols = {"Risk_Selection", "rob_Measurement", "RoB_overall"}
    has_bad = any(c in fieldnames for c in bad_cols)
    has_required = all(c in fieldnames for c in REQUIRED_COLS)
    col_check_passed = has_required and not has_bad
    checks.append({
        "name": "canonical_columns_normalized",
        "passed": col_check_passed,
        "detail": (
            f"Required cols present: {has_required}. "
            f"Bad legacy cols still present: {has_bad}. "
            f"Fieldnames: {fieldnames}"
        ),
    })

    if not has_required:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 3: all rows have valid (lowercase) values in every RoB domain ──
    domain_cols = ["rob_selection", "rob_measurement", "rob_confounding", "rob_reporting"]
    all_valid = True
    invalid_details = []
    for row in rows:
        sid = row.get("study_id", "?")
        for col in domain_cols:
            val = row.get(col, "").strip().lower()
            if val not in VALID_VALUES:
                all_valid = False
                invalid_details.append(f"{sid}/{col}='{row.get(col,'')}'")
    checks.append({
        "name": "all_domain_values_valid_lowercase",
        "passed": all_valid,
        "detail": "Invalid cells: " + (", ".join(invalid_details) if invalid_details else "none"),
    })

    # ── CHECK 4: rob_overall valid and lowercase ──────────────────────────────
    overall_valid = True
    overall_details = []
    for row in rows:
        sid = row.get("study_id", "?")
        val = row.get("rob_overall", "").strip().lower()
        if val not in VALID_VALUES:
            overall_valid = False
            overall_details.append(f"{sid}/rob_overall='{row.get('rob_overall','')}'")
    checks.append({
        "name": "rob_overall_valid_lowercase",
        "passed": overall_valid,
        "detail": "Invalid overall cells: " + (", ".join(overall_details) if overall_details else "none"),
    })

    # ── CHECK 5: conservative rob_overall rule ────────────────────────────────
    conservative_ok = True
    conservative_details = []
    for row in rows:
        sid = row.get("study_id", "?")
        domain_vals = [row.get(c, "").strip().lower() for c in domain_cols]
        overall = row.get("rob_overall", "").strip().lower()
        if "high" in domain_vals:
            expected = "high"
        elif "unclear" in domain_vals:
            expected = "unclear"
        else:
            expected = "low"
        if overall != expected:
            conservative_ok = False
            conservative_details.append(
                f"{sid}: domains={domain_vals} → expected={expected}, got={overall}"
            )
    checks.append({
        "name": "rob_overall_conservative_rule",
        "passed": conservative_ok,
        "detail": "Violations: " + ("; ".join(conservative_details) if conservative_details else "none"),
    })

    # ── CHECK 6: rob_notes non-empty and short (<=3 sentences / ~300 chars) ──
    notes_ok = True
    notes_details = []
    for row in rows:
        sid = row.get("study_id", "?")
        notes = row.get("rob_notes", "").strip()
        if not notes:
            notes_ok = False
            notes_details.append(f"{sid}: notes empty")
        elif len(notes) > 400:
            notes_ok = False
            notes_details.append(f"{sid}: notes too long ({len(notes)} chars)")
    checks.append({
        "name": "rob_notes_present_and_concise",
        "passed": notes_ok,
        "detail": "Issues: " + ("; ".join(notes_details) if notes_details else "none"),
    })

    # ── CHECK 7: no legacy badly-cased values anywhere in the file ───────────
    casing_ok = True
    casing_details = []
    for row in rows:
        sid = row.get("study_id", "?")
        for col in REQUIRED_COLS[:-1]:  # skip rob_notes
            raw = row.get(col, "")
            if raw.strip() and raw.strip() != raw.strip().lower():
                casing_ok = False
                casing_details.append(f"{sid}/{col}='{raw}'")
    checks.append({
        "name": "no_mixed_case_rob_values",
        "passed": casing_ok,
        "detail": "Mixed-case cells: " + (", ".join(casing_details) if casing_details else "none"),
    })

    # ── CHECK 8: study count unchanged (8 studies) ───────────────────────────
    row_count_ok = len(rows) == 8
    checks.append({
        "name": "row_count_unchanged",
        "passed": row_count_ok,
        "detail": f"Expected 8 rows, found {len(rows)}.",
    })

    # ── overall score ─────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 3)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))