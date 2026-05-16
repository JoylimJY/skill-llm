#!/usr/bin/env python3
"""
Evaluation script for the Apple device inventory task.
Checks that inventory_report.json was correctly produced.
"""
import sys
import json
import re
from pathlib import Path

def main(workspace):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Locate the output file ───────────────────────────────────────────
    candidates = list(workspace.rglob("inventory_report.json"))
    
    if not candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "inventory_report.json not found anywhere in workspace"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = candidates[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })

    # ── Parse JSON ───────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({
            "name": "output_file_valid_json",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({
        "name": "output_file_valid_json",
        "passed": True,
        "detail": "File parses as valid JSON"
    })

    # ── Normalize: accept both list and dict-keyed structures ────────────
    # The report can be a list of dicts, or a dict with serial/asset_tag keys.
    def find_entry(report, serial):
        serial_upper = serial.upper()
        if isinstance(report, list):
            for item in report:
                if isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str) and v.upper() == serial_upper:
                            return item
        elif isinstance(report, dict):
            # Could be keyed by serial or asset_tag
            for k, v in report.items():
                if k.upper() == serial_upper:
                    return v
                if isinstance(v, dict):
                    for vv in v.values():
                        if isinstance(vv, str) and vv.upper() == serial_upper:
                            return v
        return None

    def get_val(entry, *keys):
        """Case-insensitive key lookup."""
        if not isinstance(entry, dict):
            return None
        for k in keys:
            for ek, ev in entry.items():
                if ek.lower() == k.lower():
                    return ev
        return None

    def str_contains_ci(haystack, needle):
        if haystack is None:
            return False
        return needle.lower() in str(haystack).lower()

    # ════════════════════════════════════════════════════════════════════
    # ASSET-001: C02JH7GJDKQ1
    # Expected: C02 = Quanta/Tech Com China, J = 2012 H2,
    #           H = week 14 in half → actual week = 14+26 = 40
    #           model DKQ → MacBookPro10,1
    # ════════════════════════════════════════════════════════════════════
    SERIAL1 = "C02JH7GJDKQ1"
    entry1 = find_entry(report, SERIAL1)

    if entry1 is None:
        checks.append({
            "name": "asset001_entry_present",
            "passed": False,
            "detail": f"No entry found for serial {SERIAL1}"
        })
    else:
        checks.append({
            "name": "asset001_entry_present",
            "passed": True,
            "detail": f"Entry found for {SERIAL1}"
        })

        # Location: should mention Quanta or China (from C02)
        loc_val = (get_val(entry1, "location", "manufacturing_location",
                           "manufacture_location", "factory") or "")
        loc_ok = (
            str_contains_ci(loc_val, "quanta") or
            str_contains_ci(loc_val, "china") or
            str_contains_ci(loc_val, "C02")
        )
        # Also check nested location fields
        if not loc_ok:
            raw_json = json.dumps(entry1).lower()
            loc_ok = "quanta" in raw_json or ("c02" in raw_json and "china" in raw_json)
        checks.append({
            "name": "asset001_location_correct",
            "passed": loc_ok,
            "detail": f"Location value: '{loc_val}'. Expected Quanta/China (C02 prefix)."
        })

        # Year: 2012
        year_val = get_val(entry1, "year", "manufacture_year")
        year_ok = str_contains_ci(year_val, "2012")
        if not year_ok:
            year_ok = "2012" in json.dumps(entry1)
        checks.append({
            "name": "asset001_year_correct",
            "passed": year_ok,
            "detail": f"Year value: '{year_val}'. Expected 2012."
        })

        # Half: H2
        half_val = get_val(entry1, "half", "half_year", "period")
        half_ok = str_contains_ci(half_val, "H2") or str_contains_ci(half_val, "second")
        if not half_ok:
            half_ok = "h2" in json.dumps(entry1).lower()
        checks.append({
            "name": "asset001_half_correct",
            "passed": half_ok,
            "detail": f"Half value: '{half_val}'. Expected H2."
        })

        # Actual week: 40 (14 + 26 because H2)
        # This is the proprietary trap: H2 offset of +26
        entry1_str = json.dumps(entry1)
        week_ok = "40" in entry1_str
        # Must be clearly about actual week, not just any 40
        # Check it's not just the asset tag or year appearing as 40
        checks.append({
            "name": "asset001_actual_week_40_h2_offset",
            "passed": week_ok,
            "detail": (
                f"Looking for actual week=40 (week-in-half=14, +26 for H2). "
                f"Entry JSON: {entry1_str[:300]}"
            )
        })

        # Model identifier: MacBookPro10,1
        model_ok = (
            str_contains_ci(get_val(entry1, "model_identifier", "model_id",
                                    "device_identifier"), "MacBookPro10,1") or
            "macbookpro10,1" in entry1_str.lower()
        )
        checks.append({
            "name": "asset001_model_identifier_macbookpro10_1",
            "passed": model_ok,
            "detail": f"Expected MacBookPro10,1. Entry: {entry1_str[:300]}"
        })

        # Device description: should mention MacBook Pro, 15", Retina, 2012
        device_ok = (
            "macbook pro" in entry1_str.lower() and
            ("retina" in entry1_str.lower() or "15" in entry1_str)
        )
        checks.append({
            "name": "asset001_device_description",
            "passed": device_ok,
            "detail": f"Expected MacBook Pro 15 Retina. Entry: {entry1_str[:300]}"
        })

    # ════════════════════════════════════════════════════════════════════
    # ASSET-002: C02RTHGUHG7H
    # Expected: C02 = Quanta China, R = 2016 H1,
    #           T = week 23 (H1, actual week = 23 no offset)
    #           HG7H → iPhone9,1 (iPhone 7 GSM)
    # ════════════════════════════════════════════════════════════════════
    SERIAL2 = "C02RTHGUHG7H"
    entry2 = find_entry(report, SERIAL2)

    if entry2 is None:
        checks.append({
            "name": "asset002_entry_present",
            "passed": False,
            "detail": f"No entry found for serial {SERIAL2}"
        })
    else:
        checks.append({
            "name": "asset002_entry_present",
            "passed": True,
            "detail": f"Entry found for {SERIAL2}"
        })

        entry2_str = json.dumps(entry2)

        # Year: 2016
        year_ok2 = "2016" in entry2_str
        checks.append({
            "name": "asset002_year_2016",
            "passed": year_ok2,
            "detail": f"Expected year 2016. Entry: {entry2_str[:300]}"
        })

        # Half: H1
        half_ok2 = "h1" in entry2_str.lower() or "first" in entry2_str.lower()
        checks.append({
            "name": "asset002_half_h1",
            "passed": half_ok2,
            "detail": f"Expected H1. Entry: {entry2_str[:300]}"
        })

        # Actual week: 23 (T = week 23, H1 no offset)
        week_ok2 = "23" in entry2_str
        checks.append({
            "name": "asset002_actual_week_23",
            "passed": week_ok2,
            "detail": f"Expected week 23 (T code, H1 no offset). Entry: {entry2_str[:300]}"
        })

        # Model: iPhone9,1 and iPhone 7
        model_ok2 = (
            "iphone9,1" in entry2_str.lower() or
            "iphone 7" in entry2_str.lower()
        )
        checks.append({
            "name": "asset002_model_iphone7",
            "passed": model_ok2,
            "detail": f"Expected iPhone9,1 / iPhone 7. Entry: {entry2_str[:300]}"
        })

    # ════════════════════════════════════════════════════════════════════
    # ASSET-003: K4PMWCGJT4  (10-char new format, post-2021)
    # Expected: flagged as new randomized format, requires web lookup,
    #           references checkcoverage.apple.com
    # ════════════════════════════════════════════════════════════════════
    SERIAL3 = "K4PMWCGJT4"
    entry3 = find_entry(report, SERIAL3)

    if entry3 is None:
        checks.append({
            "name": "asset003_entry_present",
            "passed": False,
            "detail": f"No entry found for serial {SERIAL3}"
        })
    else:
        checks.append({
            "name": "asset003_entry_present",
            "passed": True,
            "detail": f"Entry found for {SERIAL3}"
        })

        entry3_str = json.dumps(entry3)

        # Must flag as new format / undecipherable
        new_format_ok = (
            "randomize" in entry3_str.lower() or
            "new format" in entry3_str.lower() or
            "2021" in entry3_str or
            "cannot" in entry3_str.lower() or
            "web lookup" in entry3_str.lower() or
            "requires_web_lookup" in entry3_str.lower()
        )
        # Check requires_web_lookup is true-ish
        rwl = get_val(entry3, "requires_web_lookup", "web_lookup_required",
                      "needs_web_lookup")
        if rwl is True or str(rwl).lower() in ("true", "yes", "1"):
            new_format_ok = True
        checks.append({
            "name": "asset003_flagged_new_format",
            "passed": new_format_ok,
            "detail": f"Expected new-format flag / requires_web_lookup=true. Entry: {entry3_str[:300]}"
        })

        # Must reference checkcoverage.apple.com
        coverage_ok = "checkcoverage.apple.com" in entry3_str.lower()
        checks.append({
            "name": "asset003_checkcoverage_url_present",
            "passed": coverage_ok,
            "detail": (
                f"Expected reference to checkcoverage.apple.com. "
                f"Entry: {entry3_str[:300]}"
            )
        })

        # Must NOT claim to have decoded year/location from this serial
        false_decode = (
            get_val(entry3, "year") not in (None, "", "unknown", "Unknown", "N/A") and
            str(get_val(entry3, "year")).isdigit()
        )
        # Allow if there's a clear 'unknown' marker
        no_false_decode = not false_decode
        # Be lenient — if model_info is null/none/empty that's fine
        checks.append({
            "name": "asset003_no_false_decode",
            "passed": no_false_decode,
            "detail": (
                "New-format serial must NOT produce false decoded year. "
                f"year field: {get_val(entry3, 'year')}"
            )
        })

    # ── Scoring ──────────────────────────────────────────────────────────
    check_weights = {
        "output_file_exists":                         1.0,
        "output_file_valid_json":                     1.0,
        "asset001_entry_present":                     1.0,
        "asset001_location_correct":                  1.5,
        "asset001_year_correct":                      1.0,
        "asset001_half_correct":                      1.0,
        "asset001_actual_week_40_h2_offset":          2.5,  # KEY TRAP
        "asset001_model_identifier_macbookpro10_1":   2.0,
        "asset001_device_description":                1.0,
        "asset002_entry_present":                     1.0,
        "asset002_year_2016":                         1.0,
        "asset002_half_h1":                           1.0,
        "asset002_actual_week_23":                    1.5,
        "asset002_model_iphone7":                     2.0,
        "asset003_entry_present":                     1.0,
        "asset003_flagged_new_format":                2.0,
        "asset003_checkcoverage_url_present":         2.5,  # KEY TRAP
        "asset003_no_false_decode":                   1.5,
    }

    total_weight = sum(check_weights.values())
    earned = 0.0
    checks_by_name = {c["name"]: c for c in checks}

    for name, weight in check_weights.items():
        if name in checks_by_name and checks_by_name[name]["passed"]:
            earned += weight

    score = round(earned / total_weight, 4)
    passed = score >= 0.75  # 75% threshold

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)
    main(sys.argv[1])