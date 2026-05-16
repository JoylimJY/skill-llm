import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def normalize_token(s):
    import re
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def run_eval(workspace):
    checks = []
    score_parts = []

    # ── 1. Find output file ─────────────────────────────────────────────────
    output_file = None
    candidates = list(Path(workspace).rglob("normalized_leads.json"))
    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "No file named normalized_leads.json found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True,
                   "detail": f"Found at {output_file}"})

    # ── 2. Output is valid JSON ─────────────────────────────────────────────
    try:
        data = load_json(output_file)
    except Exception as e:
        checks.append({"name": "output_valid_json", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append({"name": "output_valid_json", "passed": True, "detail": "Parsed OK"})

    # ── 3. Schema validation ────────────────────────────────────────────────
    try:
        import jsonschema
        output_schema = load_json(os.path.join(workspace, "references/location-normalizer-output.schema.json"))
        jsonschema.validate(instance=data, schema=output_schema)
        checks.append({"name": "output_schema_valid", "passed": True, "detail": "Passes output schema"})
        score_parts.append(1.0)
    except Exception as e:
        checks.append({"name": "output_schema_valid", "passed": False, "detail": str(e)})
        score_parts.append(0.0)

    # ── 4. All 13 lead IDs present ──────────────────────────────────────────
    results = data.get("results", [])
    result_map = {r["lead_id"]: r for r in results}
    expected_ids = {"L001","L002","L003","L004","L005","L006","L007",
                    "L008","L009","L010","L011","L012","L013"}
    present_ids = set(result_map.keys())
    missing = expected_ids - present_ids
    if missing:
        checks.append({"name": "all_leads_present", "passed": False,
                        "detail": f"Missing lead IDs: {missing}"})
        score_parts.append(0.0)
    else:
        checks.append({"name": "all_leads_present", "passed": True, "detail": "All 13 leads present"})
        score_parts.append(1.0)

    def check_lead(lead_id, expected_city, expected_locality, expected_micro,
                   expected_unresolved, matched_alias_contains=None, detail_label=""):
        r = result_map.get(lead_id)
        if r is None:
            checks.append({"name": f"lead_{lead_id}_{detail_label}", "passed": False,
                            "detail": "Lead not in output"})
            return 0.0

        city_ok = (r.get("city") == expected_city)
        loc_ok  = (r.get("locality_canonical") == expected_locality)
        mm_ok   = (r.get("micro_market") == expected_micro)
        unr_ok  = (r.get("unresolved_flag") == expected_unresolved)
        conf_ok = isinstance(r.get("confidence"), (int, float))

        alias_ok = True
        if matched_alias_contains:
            ma = str(r.get("matched_alias", "")).lower()
            alias_ok = matched_alias_contains.lower() in ma

        passed = city_ok and loc_ok and mm_ok and unr_ok and conf_ok and alias_ok
        detail = (
            f"city={r.get('city')}(exp={expected_city}) "
            f"locality={r.get('locality_canonical')}(exp={expected_locality}) "
            f"micro={r.get('micro_market')}(exp={expected_micro}) "
            f"unresolved={r.get('unresolved_flag')}(exp={expected_unresolved}) "
            f"confidence={r.get('confidence')} "
            f"matched_alias={r.get('matched_alias')}"
        )
        checks.append({"name": f"lead_{lead_id}_{detail_label}", "passed": passed, "detail": detail})
        return 1.0 if passed else 0.0

    # ── 5. Per-lead checks ──────────────────────────────────────────────────

    # L001: Turner Road → Bandra, Western Suburbs
    score_parts.append(check_lead("L001", "Mumbai", "Bandra", "Western Suburbs",
                                   False, "turner road", "turner_road_to_bandra"))

    # L002: Scruz → Santa Cruz, Western Suburbs
    score_parts.append(check_lead("L002", "Mumbai", "Santa Cruz", "Western Suburbs",
                                   False, "scruz", "scruz_to_santacruz"))

    # L003: "  andheri  w  " (token-normalized) → Andheri, Western Suburbs
    score_parts.append(check_lead("L003", "Mumbai", "Andheri", "Western Suburbs",
                                   False, None, "token_normalized_andheri_w"))

    # L004: P.C.M.C (punctuation stripped → pcmc) → Pimpri-Chinchwad, PCMC
    score_parts.append(check_lead("L004", "Pune", "Pimpri-Chinchwad", "PCMC",
                                   False, None, "pcmc_punctuation_normalized"))

    # L005: Hinjawadi Phase 2 → Hinjewadi, Rajiv Gandhi IT Park
    score_parts.append(check_lead("L005", "Pune", "Hinjewadi", "Rajiv Gandhi IT Park",
                                   False, "hinjawadi phase 2", "hinjawadi_phase2"))

    # L006: Khar W → Khar, Western Suburbs
    score_parts.append(check_lead("L006", "Mumbai", "Khar", "Western Suburbs",
                                   False, "khar w", "khar_w"))

    # L007: Baner Road → Baner, North Pune
    score_parts.append(check_lead("L007", "Pune", "Baner", "North Pune",
                                   False, "baner road", "baner_road"))

    # L008: Koramangala → UNKNOWN → unresolved_flag=True, city/locality null
    r8 = result_map.get("L008", {})
    l8_city_null = r8.get("city") is None
    l8_loc_null  = r8.get("locality_canonical") is None
    l8_unresolved = r8.get("unresolved_flag") is True
    l8_alias_preserved = "koramangala" in str(r8.get("matched_alias", "")).lower()
    l8_passed = l8_city_null and l8_loc_null and l8_unresolved and l8_alias_preserved
    checks.append({"name": "lead_L008_koramangala_unresolved", "passed": l8_passed,
                   "detail": (f"city={r8.get('city')} locality={r8.get('locality_canonical')} "
                               f"unresolved={r8.get('unresolved_flag')} matched_alias={r8.get('matched_alias')}")})
    score_parts.append(1.0 if l8_passed else 0.0)

    # L009: Carter Road → Bandra, Western Suburbs
    score_parts.append(check_lead("L009", "Mumbai", "Bandra", "Western Suburbs",
                                   False, "carter road", "carter_road_to_bandra"))

    # L010: Hiranandani Gardens → Powai, Eastern Suburbs
    score_parts.append(check_lead("L010", "Mumbai", "Powai", "Eastern Suburbs",
                                   False, "hiranandani", "hiranandani_to_powai"))

    # L011: Goregaon-East (token-normalized, hyphen stripped → "goregaon east") → Goregaon, Western Suburbs
    score_parts.append(check_lead("L011", "Mumbai", "Goregaon", "Western Suburbs",
                                   False, None, "goregaon_east_hyphen"))

    # L012: Balewadi High Street → Balewadi, North Pune (unambiguous single match)
    score_parts.append(check_lead("L012", "Pune", "Balewadi", "North Pune",
                                   False, "balewadi", "balewadi_high_street"))

    # L013: XYZ Nagar Phase 99 → completely unknown → unresolved
    r13 = result_map.get("L013", {})
    l13_unresolved = r13.get("unresolved_flag") is True
    l13_city_null  = r13.get("city") is None
    l13_alias_preserved = "xyz nagar" in str(r13.get("matched_alias", "")).lower()
    l13_passed = l13_unresolved and l13_city_null and l13_alias_preserved
    checks.append({"name": "lead_L013_unknown_unresolved", "passed": l13_passed,
                   "detail": (f"city={r13.get('city')} unresolved={r13.get('unresolved_flag')} "
                               f"matched_alias={r13.get('matched_alias')}")})
    score_parts.append(1.0 if l13_passed else 0.0)

    # ── 6. Confidence sanity: resolved leads have confidence > 0.5 ───────────
    resolved_ids = ["L001","L002","L003","L004","L005","L006","L007","L009","L010","L011","L012"]
    conf_failures = []
    for lid in resolved_ids:
        r = result_map.get(lid, {})
        conf = r.get("confidence", 0)
        if not (isinstance(conf, (int, float)) and conf > 0.5):
            conf_failures.append(f"{lid}={conf}")
    conf_ok = len(conf_failures) == 0
    checks.append({"name": "resolved_confidence_above_threshold", "passed": conf_ok,
                   "detail": f"Failing: {conf_failures}" if conf_failures else "All resolved leads have confidence > 0.5"})
    score_parts.append(1.0 if conf_ok else 0.0)

    # ── Final score ─────────────────────────────────────────────────────────
    final_score = sum(score_parts) / len(score_parts) if score_parts else 0.0
    passed = final_score >= 0.85

    return {"passed": passed, "score": round(final_score, 4), "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))