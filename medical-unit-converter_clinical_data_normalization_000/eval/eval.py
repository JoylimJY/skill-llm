import json
import sys
import math
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── locate the output file ─────────────────────────────────────────────────
    candidates = list(workspace_path.rglob("conversion_results.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found at {candidates[0]}" if file_found else "conversion_results.json not found anywhere in workspace",
    })

    if not file_found:
        return finalize(checks)

    result_path = candidates[0]

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": str(e)})
        return finalize(checks)

    checks.append({"name": "json_parseable", "passed": True, "detail": "File parsed as valid JSON"})

    # ── structure: must be a list or a dict with a results list ─────────────────
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        # Accept {"results": [...]} or {"conversions": [...]} wrapper
        entries = data.get("results") or data.get("conversions") or data.get("entries") or []
    else:
        checks.append({"name": "structure_valid", "passed": False, "detail": f"Top-level must be list or object with results list, got {type(data)}"})
        return finalize(checks)

    checks.append({
        "name": "structure_valid",
        "passed": len(entries) >= 9,
        "detail": f"Found {len(entries)} entries (expected at least 9 including fallback)",
    })

    # ── helper to find entry by analyte + from_unit + to_unit ──────────────────
    def find_entry(analyte_kw, from_kw, to_kw):
        """Find a successful conversion entry (not a fallback) for given keys."""
        for e in entries:
            if not isinstance(e, dict):
                continue
            a = str(e.get("analyte", "")).lower()
            f = str(e.get("from_unit", "")).lower().replace("/", "_").replace(" ", "_")
            t = str(e.get("to_unit", "")).lower().replace("/", "_").replace(" ", "_")
            if analyte_kw in a and from_kw in f and to_kw in t:
                return e
        return None

    # ── check 1: glucose mg_dl → mmol_l (PT-001, value=126) ───────────────────
    g1 = find_entry("glucose", "mg", "mmol")
    if g1:
        cv = g1.get("converted_value")
        expected_cv = round(126 * 0.0555, 4)  # 6.993
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        formula_ok = "0.0555" in str(g1.get("formula", "")) and "126" in str(g1.get("formula", ""))
        ref_ok = "3.9" in str(g1.get("reference_range", "")) and "5.6" in str(g1.get("reference_range", ""))
        checks.append({
            "name": "glucose_mg_dl_to_mmol_l_value",
            "passed": cv_ok,
            "detail": f"converted_value={cv}, expected≈{expected_cv}",
        })
        checks.append({
            "name": "glucose_mg_dl_to_mmol_l_formula",
            "passed": formula_ok,
            "detail": f"formula='{g1.get('formula')}', must contain '126' and '0.0555'",
        })
        checks.append({
            "name": "glucose_mg_dl_to_mmol_l_reference_range",
            "passed": ref_ok,
            "detail": f"reference_range='{g1.get('reference_range')}', must contain 3.9 and 5.6",
        })
    else:
        for nm in ["glucose_mg_dl_to_mmol_l_value", "glucose_mg_dl_to_mmol_l_formula", "glucose_mg_dl_to_mmol_l_reference_range"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 2: glucose mmol_l → mg_dl (PT-002, value=7.2) ──────────────────
    g2 = find_entry("glucose", "mmol", "mg")
    if g2:
        cv = g2.get("converted_value")
        expected_cv = round(7.2 * 18.018, 4)  # 129.7296
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "18.018" in str(g2.get("formula", ""))
        ref_ok = "70" in str(g2.get("reference_range", "")) and "100" in str(g2.get("reference_range", ""))
        checks.append({"name": "glucose_mmol_l_to_mg_dl_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected≈{expected_cv}"})
        checks.append({"name": "glucose_mmol_l_to_mg_dl_factor", "passed": factor_ok, "detail": f"formula must contain '18.018'"})
        checks.append({"name": "glucose_mmol_l_to_mg_dl_ref", "passed": ref_ok, "detail": f"reference_range must contain 70 and 100"})
    else:
        for nm in ["glucose_mmol_l_to_mg_dl_value", "glucose_mmol_l_to_mg_dl_factor", "glucose_mmol_l_to_mg_dl_ref"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 3: cholesterol mg_dl → mmol_l (PT-003, value=215) ──────────────
    c1 = find_entry("cholesterol", "mg", "mmol")
    if c1:
        cv = c1.get("converted_value")
        expected_cv = round(215 * 0.02586, 4)  # 5.5599
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "0.02586" in str(c1.get("formula", ""))
        checks.append({"name": "cholesterol_mg_dl_to_mmol_l_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected≈{expected_cv}"})
        checks.append({"name": "cholesterol_mg_dl_to_mmol_l_factor", "passed": factor_ok, "detail": "formula must contain '0.02586'"})
    else:
        for nm in ["cholesterol_mg_dl_to_mmol_l_value", "cholesterol_mg_dl_to_mmol_l_factor"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 4: cholesterol mmol_l → mg_dl (PT-004, value=5.8) ──────────────
    c2 = find_entry("cholesterol", "mmol", "mg")
    if c2:
        cv = c2.get("converted_value")
        expected_cv = round(5.8 * 38.67, 4)  # 224.286
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "38.67" in str(c2.get("formula", ""))
        checks.append({"name": "cholesterol_mmol_l_to_mg_dl_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected≈{expected_cv}"})
        checks.append({"name": "cholesterol_mmol_l_to_mg_dl_factor", "passed": factor_ok, "detail": "formula must contain '38.67'"})
    else:
        for nm in ["cholesterol_mmol_l_to_mg_dl_value", "cholesterol_mmol_l_to_mg_dl_factor"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 5: creatinine mg_dl → umol_l (PT-005, value=1.1, factor=88.4) ──
    cr1 = find_entry("creatinine", "mg", "umol")
    if cr1 is None:
        cr1 = find_entry("creatinine", "mg", "mol")  # μmol/L might match
    if cr1:
        cv = cr1.get("converted_value")
        expected_cv = round(1.1 * 88.4, 4)  # 97.24
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "88.4" in str(cr1.get("formula", ""))
        ref_ok = "62" in str(cr1.get("reference_range", "")) and "115" in str(cr1.get("reference_range", ""))
        checks.append({"name": "creatinine_mg_dl_to_umol_l_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected≈{expected_cv}"})
        checks.append({"name": "creatinine_mg_dl_to_umol_l_factor_88_4", "passed": factor_ok, "detail": "formula must contain '88.4' (not 88.0 or other approximation)"})
        checks.append({"name": "creatinine_mg_dl_to_umol_l_ref", "passed": ref_ok, "detail": "reference_range must contain 62 and 115"})
    else:
        for nm in ["creatinine_mg_dl_to_umol_l_value", "creatinine_mg_dl_to_umol_l_factor_88_4", "creatinine_mg_dl_to_umol_l_ref"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 6: creatinine umol_l → mg_dl (PT-006, value=97.5) ─────────────
    cr2 = find_entry("creatinine", "umol", "mg")
    if cr2 is None:
        cr2 = find_entry("creatinine", "mol", "mg")
    if cr2:
        cv = cr2.get("converted_value")
        expected_cv = round(97.5 * 0.01131, 4)  # 1.1027
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "0.01131" in str(cr2.get("formula", ""))
        checks.append({"name": "creatinine_umol_l_to_mg_dl_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected≈{expected_cv}"})
        checks.append({"name": "creatinine_umol_l_to_mg_dl_factor_0_01131", "passed": factor_ok, "detail": "formula must contain '0.01131'"})
    else:
        for nm in ["creatinine_umol_l_to_mg_dl_value", "creatinine_umol_l_to_mg_dl_factor_0_01131"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 7: hemoglobin g_dl → g_l (PT-007, value=14.5, factor=10) ───────
    hb1 = find_entry("hemoglobin", "g_dl", "g_l")
    if hb1 is None:
        # broad search
        for e in entries:
            if not isinstance(e, dict):
                continue
            a = str(e.get("analyte", "")).lower()
            f = str(e.get("from_unit", "")).lower()
            t = str(e.get("to_unit", "")).lower()
            if "hemo" in a and "dl" in f and "g_l" in t or ("hemo" in a and "dl" in f and t == "g_l"):
                hb1 = e
                break
    if hb1 is None:
        # Even broader
        for e in entries:
            if not isinstance(e, dict):
                continue
            a = str(e.get("analyte", "")).lower()
            cv_val = e.get("converted_value")
            if "hemo" in a and cv_val is not None:
                if math.isclose(float(cv_val), 145.0, rel_tol=0.01):
                    hb1 = e
                    break
    if hb1:
        cv = hb1.get("converted_value")
        expected_cv = round(14.5 * 10, 4)  # 145.0
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "10" in str(hb1.get("formula", ""))
        ref_ok = "130" in str(hb1.get("reference_range", "")) and "175" in str(hb1.get("reference_range", ""))
        checks.append({"name": "hemoglobin_g_dl_to_g_l_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected=145.0"})
        checks.append({"name": "hemoglobin_g_dl_to_g_l_factor_10", "passed": factor_ok, "detail": "formula must contain factor '10'"})
        checks.append({"name": "hemoglobin_g_dl_to_g_l_ref", "passed": ref_ok, "detail": "reference_range must contain 130 and 175"})
    else:
        for nm in ["hemoglobin_g_dl_to_g_l_value", "hemoglobin_g_dl_to_g_l_factor_10", "hemoglobin_g_dl_to_g_l_ref"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 8: hemoglobin g_l → g_dl (PT-008, value=155, factor=0.1) ───────
    hb2 = None
    for e in entries:
        if not isinstance(e, dict):
            continue
        a = str(e.get("analyte", "")).lower()
        cv_val = e.get("converted_value")
        if "hemo" in a and cv_val is not None:
            if math.isclose(float(cv_val), 15.5, rel_tol=0.01):
                hb2 = e
                break
    if hb2:
        cv = hb2.get("converted_value")
        expected_cv = round(155 * 0.1, 4)  # 15.5
        cv_ok = cv is not None and math.isclose(float(cv), expected_cv, rel_tol=1e-3)
        factor_ok = "0.1" in str(hb2.get("formula", ""))
        ref_ok = "13" in str(hb2.get("reference_range", "")) and "17.5" in str(hb2.get("reference_range", ""))
        checks.append({"name": "hemoglobin_g_l_to_g_dl_value", "passed": cv_ok, "detail": f"converted_value={cv}, expected=15.5"})
        checks.append({"name": "hemoglobin_g_l_to_g_dl_factor_0_1", "passed": factor_ok, "detail": "formula must contain '0.1'"})
        checks.append({"name": "hemoglobin_g_l_to_g_dl_ref", "passed": ref_ok, "detail": "reference_range must mention 13 and 17.5"})
    else:
        for nm in ["hemoglobin_g_l_to_g_dl_value", "hemoglobin_g_l_to_g_dl_factor_0_1", "hemoglobin_g_l_to_g_dl_ref"]:
            checks.append({"name": nm, "passed": False, "detail": "Entry not found"})

    # ── check 9: fallback entry for TSH (PT-009) ─────────────────────────────
    REQUIRED_PARTIAL = "Manual formula not available for this unit pair"
    fallback_entry = None
    for e in entries:
        if not isinstance(e, dict):
            continue
        # look for TSH or miu or pmol or a fallback marker
        raw = json.dumps(e).lower()
        if "tsh" in raw or "miu" in raw or "pmol" in raw or "fallback" in raw or "partial" in raw or "unsupported" in raw.lower():
            fallback_entry = e
            break
    if fallback_entry is None:
        # Also scan for the exact required phrase anywhere in file text
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            if REQUIRED_PARTIAL in raw_text:
                fallback_entry = {"_raw_text_match": True}
        except Exception:
            pass

    fallback_found = fallback_entry is not None
    checks.append({
        "name": "fallback_entry_for_unsupported_tsh",
        "passed": fallback_found,
        "detail": f"Fallback entry for TSH/unsupported pair found: {fallback_found}",
    })

    # Check that the exact mandated phrase is present
    if fallback_entry and not fallback_entry.get("_raw_text_match"):
        raw_entry = json.dumps(fallback_entry)
        exact_phrase_ok = REQUIRED_PARTIAL in raw_entry
        # Also check the raw file text
        if not exact_phrase_ok:
            try:
                with open(result_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                exact_phrase_ok = REQUIRED_PARTIAL in raw_text
            except Exception:
                pass
        checks.append({
            "name": "fallback_exact_partial_result_phrase",
            "passed": exact_phrase_ok,
            "detail": f"Must contain exact string: '{REQUIRED_PARTIAL}'",
        })
    elif fallback_entry and fallback_entry.get("_raw_text_match"):
        checks.append({
            "name": "fallback_exact_partial_result_phrase",
            "passed": True,
            "detail": f"Exact phrase found in file text: '{REQUIRED_PARTIAL}'",
        })
    else:
        checks.append({
            "name": "fallback_exact_partial_result_phrase",
            "passed": False,
            "detail": f"No fallback entry to check phrase in",
        })

    # ── check 10: all 8 successful entries have all required fields ───────────
    required_fields = {"converted_value", "formula", "from_unit", "to_unit", "analyte", "reference_range"}
    successful_entries = [
        e for e in entries
        if isinstance(e, dict)
        and "converted_value" in e
        and e.get("converted_value") is not None
    ]
    fields_ok_count = sum(
        1 for e in successful_entries
        if required_fields.issubset(set(e.keys()))
    )
    checks.append({
        "name": "all_successful_entries_have_required_fields",
        "passed": fields_ok_count >= 8,
        "detail": f"{fields_ok_count}/8 successful entries have all required fields: {required_fields}",
    })

    return finalize(checks)


def finalize(checks):
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall = score >= 0.85
    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))