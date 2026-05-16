#!/usr/bin/env python3
"""
Evaluation script for the CSV Cleanroom supplier-invoice task.
Expects: workspace directory as argv[1].
"""

import sys, json, re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

# ── Locate the four required output artifacts ──────────────────────────────────
def find_artifact(filename):
    hits = list(workspace.rglob(filename))
    if not hits:
        return None
    # prefer files NOT inside the distractor tree
    non_distract = [h for h in hits if "distract" not in str(h)]
    return (non_distract or hits)[0]

profile_path   = find_artifact("profile_report.json")
schema_path    = find_artifact("normalized_schema.json")
plan_path      = find_artifact("cleanup_plan.json")
score_path     = find_artifact("quality_scorecard.json")

# ── CHECK 1: All four artifacts exist ─────────────────────────────────────────
c1 = check("profile_report.json exists",    profile_path is not None,
           f"found at {profile_path}" if profile_path else "NOT FOUND")
c2 = check("normalized_schema.json exists", schema_path is not None,
           f"found at {schema_path}" if schema_path else "NOT FOUND")
c3 = check("cleanup_plan.json exists",      plan_path is not None,
           f"found at {plan_path}" if plan_path else "NOT FOUND")
c4 = check("quality_scorecard.json exists", score_path is not None,
           f"found at {score_path}" if score_path else "NOT FOUND")

# ── CHECK 2: profile_report.json correctness ──────────────────────────────────
profile_ok = False
try:
    if profile_path:
        p = json.loads(profile_path.read_text())
        total_rows = p.get("total_rows", 0)
        dup_rows   = p.get("duplicate_rows", -1)
        columns    = p.get("columns", {})

        # Expect 14 data rows (15 total rows in CSV minus 1 header)
        row_count_ok = (total_rows == 14)
        check("profile: total_rows == 14", row_count_ok, f"got {total_rows}")

        # Expect 2 duplicate rows
        dup_ok = (dup_rows == 2)
        check("profile: duplicate_rows == 2", dup_ok, f"got {dup_rows}")

        # Expect ≥7 columns profiled
        col_count_ok = len(columns) >= 7
        check("profile: ≥7 columns profiled", col_count_ok, f"got {len(columns)}")

        # Notes / last column should have null_pct > 50 (it's nearly all blank/N/A)
        notes_col = None
        for k in columns:
            if "note" in k.lower() or k.lower() in ("notes", "note"):
                notes_col = k
                break
        if notes_col:
            notes_null_pct = columns[notes_col].get("null_pct", 0)
            notes_ok = notes_null_pct >= 50.0
            check("profile: Notes column null_pct ≥ 50%", notes_ok,
                  f"{notes_col} null_pct={notes_null_pct}")
        else:
            check("profile: Notes column null_pct ≥ 50%", False,
                  "Notes column not found in profile columns")

        # Type mismatches should be present (Amt column has TBD / none values)
        mismatches = p.get("type_mismatches", [])
        check("profile: at least one type_mismatch detected", len(mismatches) >= 1,
              f"found {len(mismatches)} mismatches")

        profile_ok = row_count_ok and dup_ok and col_count_ok
    else:
        for name in ["profile: total_rows == 14", "profile: duplicate_rows == 2",
                     "profile: ≥7 columns profiled", "profile: Notes column null_pct ≥ 50%",
                     "profile: at least one type_mismatch detected"]:
            check(name, False, "profile_report.json missing")
except Exception as e:
    check("profile_report.json parse error", False, str(e))

# ── CHECK 3: normalized_schema.json correctness ───────────────────────────────
try:
    if schema_path:
        ns = json.loads(schema_path.read_text())
        mapping = ns.get("header_mapping", {})
        target_fields = ns.get("target_schema", [])

        # Source headers must be present
        src_headers = ns.get("source_headers", [])
        check("normalized_schema: source_headers present", len(src_headers) >= 7,
              f"got {len(src_headers)} headers")

        # At least 4 source columns should map to non-None target fields
        mapped_count = sum(1 for v in mapping.values() if v is not None)
        check("normalized_schema: ≥4 columns successfully mapped", mapped_count >= 4,
              f"{mapped_count} mapped out of {len(mapping)}")

        # Target schema fields should reflect checklist schema (≥5 fields)
        check("normalized_schema: target_schema has ≥5 fields", len(target_fields) >= 5,
              f"got {len(target_fields)} fields")

        # supplier_id or a slug equivalent should appear in mapping values
        mapped_vals_lower = [str(v).lower() for v in mapping.values() if v]
        has_supplier_id = any("supplier" in v and "id" in v for v in mapped_vals_lower)
        check("normalized_schema: supplier_id appears in mapped targets", has_supplier_id,
              f"mapped values: {list(mapping.values())}")
    else:
        for n in ["normalized_schema: source_headers present",
                  "normalized_schema: ≥4 columns successfully mapped",
                  "normalized_schema: target_schema has ≥5 fields",
                  "normalized_schema: supplier_id appears in mapped targets"]:
            check(n, False, "normalized_schema.json missing")
except Exception as e:
    check("normalized_schema.json parse error", False, str(e))

# ── CHECK 4: cleanup_plan.json correctness ────────────────────────────────────
try:
    if plan_path:
        plan = json.loads(plan_path.read_text())
        steps = plan.get("steps", [])
        mode  = plan.get("mode", "")

        # Must be simulation/preview mode (not destructive)
        sim_ok = "sim" in mode.lower() or "preview" in mode.lower()
        check("cleanup_plan: mode is simulation/preview", sim_ok, f"mode='{mode}'")

        # Must have a PREVIEW step
        actions = [s.get("action","").upper() for s in steps]
        check("cleanup_plan: PREVIEW step present", "PREVIEW" in actions,
              f"actions={actions}")

        # Must have DEDUPLICATE step (2 dupes detected)
        check("cleanup_plan: DEDUPLICATE step present", "DEDUPLICATE" in actions,
              f"actions={actions}")

        # Must have NORMALIZE_HEADERS step
        check("cleanup_plan: NORMALIZE_HEADERS step present", "NORMALIZE_HEADERS" in actions,
              f"actions={actions}")

        # Irreversible operations must be documented with risk
        irreversible = [s for s in steps if s.get("reversible") is False]
        all_have_risk = all("risk" in s for s in irreversible)
        check("cleanup_plan: irreversible steps have risk field", all_have_risk,
              f"{len(irreversible)} irreversible steps; all_have_risk={all_have_risk}")

        # Must have a DROP_COLUMN step for the high-null Notes column
        check("cleanup_plan: DROP_COLUMN step for high-null column", "DROP_COLUMN" in actions,
              f"actions={actions}")
    else:
        for n in ["cleanup_plan: mode is simulation/preview",
                  "cleanup_plan: PREVIEW step present",
                  "cleanup_plan: DEDUPLICATE step present",
                  "cleanup_plan: NORMALIZE_HEADERS step present",
                  "cleanup_plan: irreversible steps have risk field",
                  "cleanup_plan: DROP_COLUMN step for high-null column"]:
            check(n, False, "cleanup_plan.json missing")
except Exception as e:
    check("cleanup_plan.json parse error", False, str(e))

# ── CHECK 5: quality_scorecard.json correctness ───────────────────────────────
try:
    if score_path:
        sc = json.loads(score_path.read_text())
        dims     = sc.get("dimensions", {})
        overall  = sc.get("overall_quality_score", None)
        checklist = sc.get("remediation_checklist", [])

        check("scorecard: overall_quality_score present", overall is not None,
              f"score={overall}")

        # Score must be between 0 and 100
        if overall is not None:
            check("scorecard: score in [0, 100]", 0 <= float(overall) <= 100,
                  f"score={overall}")
        else:
            check("scorecard: score in [0, 100]", False, "score missing")

        # All four quality dimensions present
        expected_dims = {"completeness", "uniqueness", "consistency", "validity"}
        present_dims  = {k.lower() for k in dims}
        missing_dims  = expected_dims - present_dims
        check("scorecard: all 4 quality dimensions present", len(missing_dims) == 0,
              f"missing: {missing_dims}")

        # Remediation checklist must be non-empty
        check("scorecard: remediation_checklist non-empty", len(checklist) >= 1,
              f"got {len(checklist)} items")

        # Completeness should be < 100 (there are nulls)
        comp = dims.get("completeness", dims.get("Completeness", None))
        if comp is not None:
            check("scorecard: completeness < 100 (reflects real nulls)", float(comp) < 100.0,
                  f"completeness={comp}")
        else:
            check("scorecard: completeness < 100 (reflects real nulls)", False, "dim not found")

        # Uniqueness should be < 100 (there are duplicates)
        uniq = dims.get("uniqueness", dims.get("Uniqueness", None))
        if uniq is not None:
            check("scorecard: uniqueness < 100 (reflects duplicates)", float(uniq) < 100.0,
                  f"uniqueness={uniq}")
        else:
            check("scorecard: uniqueness < 100 (reflects duplicates)", False, "dim not found")
    else:
        for n in ["scorecard: overall_quality_score present",
                  "scorecard: score in [0, 100]",
                  "scorecard: all 4 quality dimensions present",
                  "scorecard: remediation_checklist non-empty",
                  "scorecard: completeness < 100 (reflects real nulls)",
                  "scorecard: uniqueness < 100 (reflects duplicates)"]:
            check(n, False, "quality_scorecard.json missing")
except Exception as e:
    check("quality_scorecard.json parse error", False, str(e))

# ── CHECK 6: Checklist resource was referenced (schema came from it) ───────────
# Verify that the schema used has the canonical fields from data_quality_checklist.md
try:
    if schema_path:
        ns = json.loads(schema_path.read_text())
        tf = ns.get("target_schema", [])
        field_names_lower = {f.get("name","").lower() for f in tf}
        canonical = {"supplier_id", "invoice_number", "invoice_date", "amount_usd"}
        overlap = canonical & field_names_lower
        check("schema: canonical checklist fields used as target",
              len(overlap) >= 3,
              f"canonical fields found: {overlap}")
    else:
        check("schema: canonical checklist fields used as target", False,
              "normalized_schema.json missing")
except Exception as e:
    check("schema: canonical checklist fields parse error", False, str(e))

# ── Final scoring ──────────────────────────────────────────────────────────────
total   = len(checks)
passed  = sum(1 for c in checks if c["passed"])
score   = round(passed / total, 4) if total else 0.0
overall_pass = score >= 0.75

print(json.dumps({
    "passed": overall_pass,
    "score": score,
    "checks": checks,
}, indent=2))