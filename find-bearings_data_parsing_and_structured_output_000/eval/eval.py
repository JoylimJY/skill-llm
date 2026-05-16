import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score_total = 0.0
score_possible = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score_total, score_possible
    score_possible += weight
    if passed:
        score_total += weight

# ── Locate the output file ───────────────────────────────────────────────────
try:
    candidates = list(Path(workspace).rglob("substitution_catalog.json"))
    if not candidates:
        add_check("output_file_exists", False, "substitution_catalog.json not found anywhere in workspace")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)
    output_file = candidates[0]
    with open(output_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    add_check("output_file_exists", True, f"Found at {output_file}")
except Exception as e:
    add_check("output_file_exists", False, f"Error reading output file: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# Helper: find an entry in catalog by standard model or original model field
def find_entry(catalog, model_key):
    """Find a catalog entry where standard_model or original_model matches."""
    for entry in catalog:
        sm = str(entry.get("standard_model", "")).strip()
        om = str(entry.get("original_model", "")).strip()
        if model_key.lower() in sm.lower() or model_key.lower() in om.lower():
            return entry
    return None

# ── CHECK 1: Catalog is a list with 6 entries ─────────────────────────────────
try:
    is_list = isinstance(catalog, list)
    count_ok = len(catalog) == 6 if is_list else False
    add_check("catalog_has_6_entries", is_list and count_ok,
              f"Expected list of 6 entries, got {'list of ' + str(len(catalog)) if is_list else type(catalog).__name__}", weight=1.0)
except Exception as e:
    add_check("catalog_has_6_entries", False, str(e), weight=1.0)

# ── CHECK 2: Inner diameter calculation for 6205 ─────────────────────────────
# 6205: last two digits = 05, so d = 05 × 5 = 25mm
try:
    entry_6205 = find_entry(catalog, "6205")
    if entry_6205 is None:
        add_check("6205_inner_diameter", False, "Entry for 6205 not found", weight=2.0)
    else:
        dims = entry_6205.get("dimensions", {})
        d_val = dims.get("d") if isinstance(dims, dict) else None
        correct = (d_val == 25)
        add_check("6205_inner_diameter", correct,
                  f"6205 inner diameter (d): expected 25mm, got {d_val}", weight=2.0)
except Exception as e:
    add_check("6205_inner_diameter", False, str(e), weight=2.0)

# ── CHECK 3: Inner diameter for 6203 ─────────────────────────────────────────
# 6203: last two digits = 03, special rule → d = 17mm
try:
    entry_6203 = find_entry(catalog, "6203")
    if entry_6203 is None:
        add_check("6203_inner_diameter_special_rule", False, "Entry for 6203 not found", weight=2.0)
    else:
        dims = entry_6203.get("dimensions", {})
        d_val = dims.get("d") if isinstance(dims, dict) else None
        correct = (d_val == 17)
        add_check("6203_inner_diameter_special_rule", correct,
                  f"6203 inner diameter special rule: expected 17mm (03→17), got {d_val}", weight=2.0)
except Exception as e:
    add_check("6203_inner_diameter_special_rule", False, str(e), weight=2.0)

# ── CHECK 4: Inner diameter for 6302 ─────────────────────────────────────────
# 6302: last two digits = 02, special rule → d = 15mm
try:
    entry_6302 = find_entry(catalog, "6302")
    if entry_6302 is None:
        add_check("6302_inner_diameter_special_rule", False, "Entry for 6302 not found", weight=2.0)
    else:
        dims = entry_6302.get("dimensions", {})
        d_val = dims.get("d") if isinstance(dims, dict) else None
        correct = (d_val == 15)
        add_check("6302_inner_diameter_special_rule", correct,
                  f"6302 inner diameter special rule: expected 15mm (02→15), got {d_val}", weight=2.0)
except Exception as e:
    add_check("6302_inner_diameter_special_rule", False, str(e), weight=2.0)

# ── CHECK 5: 6205-2RS cross-references use brand-specific suffixes ────────────
# SKF should be "6205-2RS1" (not "6205-2RS"), NSK should be "6205DDU", FAG "6205.2RSR", NTN "6205LLU"
try:
    entry_6205 = find_entry(catalog, "6205")
    if entry_6205 is None:
        add_check("6205_2RS_brand_suffixes", False, "Entry for 6205 not found", weight=3.0)
    else:
        cr = entry_6205.get("cross_reference", {})
        passed_sub = []
        failed_sub = []
        # SKF: must contain "2RS1"
        skf_val = str(cr.get("SKF", ""))
        if "2RS1" in skf_val:
            passed_sub.append(f"SKF={skf_val}✓")
        else:
            failed_sub.append(f"SKF={skf_val} (expected to contain '2RS1')")
        # NSK: must contain "DDU"
        nsk_val = str(cr.get("NSK", ""))
        if "DDU" in nsk_val:
            passed_sub.append(f"NSK={nsk_val}✓")
        else:
            failed_sub.append(f"NSK={nsk_val} (expected to contain 'DDU')")
        # FAG: must contain "2RSR"
        fag_val = str(cr.get("FAG", ""))
        if "2RSR" in fag_val:
            passed_sub.append(f"FAG={fag_val}✓")
        else:
            failed_sub.append(f"FAG={fag_val} (expected to contain '2RSR')")
        # NTN: must contain "LLU"
        ntn_val = str(cr.get("NTN", ""))
        if "LLU" in ntn_val:
            passed_sub.append(f"NTN={ntn_val}✓")
        else:
            failed_sub.append(f"NTN={ntn_val} (expected to contain 'LLU')")
        
        all_pass = len(failed_sub) == 0
        add_check("6205_2RS_brand_suffixes", all_pass,
                  f"Passed: {passed_sub}; Failed: {failed_sub}", weight=3.0)
except Exception as e:
    add_check("6205_2RS_brand_suffixes", False, str(e), weight=3.0)

# ── CHECK 6: 6203ZZ cross-references use ZZ brand-specific suffix ─────────────
# SKF: "2Z", NSK: "ZZ", FAG: "2ZR", NTN: "ZZ"
try:
    entry_6203 = find_entry(catalog, "6203")
    if entry_6203 is None:
        add_check("6203_ZZ_brand_suffixes", False, "Entry for 6203 not found", weight=3.0)
    else:
        cr = entry_6203.get("cross_reference", {})
        failed_sub = []
        passed_sub = []
        # SKF: ZZ → "2Z"
        skf_val = str(cr.get("SKF", ""))
        if "2Z" in skf_val:
            passed_sub.append(f"SKF={skf_val}✓")
        else:
            failed_sub.append(f"SKF={skf_val} (expected '2Z' for ZZ suffix, not 'ZZ')")
        # FAG: ZZ → "2ZR"
        fag_val = str(cr.get("FAG", ""))
        if "2ZR" in fag_val:
            passed_sub.append(f"FAG={fag_val}✓")
        else:
            failed_sub.append(f"FAG={fag_val} (expected '2ZR' for ZZ suffix)")
        # NSK: ZZ → "ZZ"
        nsk_val = str(cr.get("NSK", ""))
        if "ZZ" in nsk_val:
            passed_sub.append(f"NSK={nsk_val}✓")
        else:
            failed_sub.append(f"NSK={nsk_val} (expected 'ZZ')")

        all_pass = len(failed_sub) == 0
        add_check("6203_ZZ_brand_suffixes", all_pass,
                  f"Passed: {passed_sub}; Failed: {failed_sub}", weight=3.0)
except Exception as e:
    add_check("6203_ZZ_brand_suffixes", False, str(e), weight=3.0)

# ── CHECK 7: NU208 is correctly typed as cylindrical roller bearing ──────────
try:
    entry_nu208 = find_entry(catalog, "NU208")
    if entry_nu208 is None:
        add_check("NU208_type_correct", False, "Entry for NU208 not found", weight=2.0)
    else:
        btype = str(entry_nu208.get("type", "")).lower()
        tname = str(entry_nu208.get("type_name", ""))
        correct = "cylindrical" in btype or "圆柱" in tname
        add_check("NU208_type_correct", correct,
                  f"NU208 type: '{entry_nu208.get('type')}' / '{entry_nu208.get('type_name')}' — expected cylindrical roller", weight=2.0)
except Exception as e:
    add_check("NU208_type_correct", False, str(e), weight=2.0)

# ── CHECK 8: NU208 cross-references use correct brand suffixes ────────────────
# SKF: "NU 208 ECP", NSK: "NU208EW", FAG: "NU208-E-TVP2"
try:
    entry_nu208 = find_entry(catalog, "NU208")
    if entry_nu208 is None:
        add_check("NU208_cross_references", False, "Entry for NU208 not found", weight=3.0)
    else:
        cr = entry_nu208.get("cross_reference", {})
        passed_sub = []
        failed_sub = []
        skf_val = str(cr.get("SKF", ""))
        if "ECP" in skf_val or "208" in skf_val:
            passed_sub.append(f"SKF={skf_val}✓")
        else:
            failed_sub.append(f"SKF={skf_val} (expected NU 208 ECP or similar)")
        fag_val = str(cr.get("FAG", ""))
        if "TVP2" in fag_val or "E-TVP" in fag_val:
            passed_sub.append(f"FAG={fag_val}✓")
        else:
            failed_sub.append(f"FAG={fag_val} (expected NU208-E-TVP2)")
        nsk_val = str(cr.get("NSK", ""))
        if "EW" in nsk_val or "208" in nsk_val:
            passed_sub.append(f"NSK={nsk_val}✓")
        else:
            failed_sub.append(f"NSK={nsk_val} (expected NU208EW)")

        all_pass = len(failed_sub) == 0
        add_check("NU208_cross_references", all_pass,
                  f"Passed: {passed_sub}; Failed: {failed_sub}", weight=3.0)
except Exception as e:
    add_check("NU208_cross_references", False, str(e), weight=3.0)

# ── CHECK 9: All entries have required schema fields ──────────────────────────
required_fields = ["standard_model", "type", "type_name", "dimensions", "seal", "cross_reference"]
try:
    missing_fields_report = []
    for i, entry in enumerate(catalog if isinstance(catalog, list) else []):
        for field in required_fields:
            if field not in entry:
                missing_fields_report.append(f"Entry {i} missing '{field}'")
    passed = len(missing_fields_report) == 0
    add_check("all_entries_have_required_fields", passed,
              f"Missing fields: {missing_fields_report}" if missing_fields_report else "All required fields present", weight=2.0)
except Exception as e:
    add_check("all_entries_have_required_fields", False, str(e), weight=2.0)

# ── CHECK 10: 6206 (open/no seal) is correctly reflected ─────────────────────
try:
    entry_6206 = find_entry(catalog, "6206")
    if entry_6206 is None:
        add_check("6206_open_seal", False, "Entry for 6206 not found", weight=1.0)
    else:
        seal = str(entry_6206.get("seal", "")).lower()
        correct = "open" in seal or seal == "" or seal == "open" or "开" in seal or "无" in seal
        add_check("6206_open_seal", correct,
                  f"6206 seal: '{entry_6206.get('seal')}' — expected open/无密封", weight=1.0)
except Exception as e:
    add_check("6206_open_seal", False, str(e), weight=1.0)

# ── CHECK 11: deep_groove.json updated with new models ───────────────────────
try:
    dg_path = Path(workspace) / "data" / "models" / "deep_groove.json"
    with open(dg_path, "r", encoding="utf-8") as f:
        dg_data = json.load(f)
    models_in_dg = [str(e.get("model", "")) for e in dg_data]
    # At least 6205 or 6204 2RS variants should appear
    has_new = any("6205" in m or "6203" in m or "6302" in m or "6206" in m for m in models_in_dg)
    add_check("deep_groove_json_updated", has_new,
              f"Models in deep_groove.json: {models_in_dg}", weight=1.0)
except Exception as e:
    add_check("deep_groove_json_updated", False, f"Could not verify deep_groove.json: {e}", weight=1.0)

# ── Final scoring ─────────────────────────────────────────────────────────────
final_score = round(score_total / score_possible, 3) if score_possible > 0 else 0.0
overall_passed = final_score >= 0.75

print(json.dumps({
    "passed": overall_passed,
    "score": final_score,
    "checks": checks
}, ensure_ascii=False, indent=2))