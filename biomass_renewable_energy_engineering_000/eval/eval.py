import sys
import json
import math
from pathlib import Path

def find_report(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("feasibility_report.json"))
    if not candidates:
        return None
    # prefer one not in archive/templates
    for c in candidates:
        if "archive" not in str(c) and "template" not in str(c).lower():
            return c
    return candidates[0]

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str):
    workspace = Path(workspace_str)
    checks = []
    overall_passed = False

    # -----------------------------------------------------------------------
    # FILE EXISTS
    # -----------------------------------------------------------------------
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("report_file_exists", False, "feasibility_report.json not found anywhere in workspace"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("report_file_exists", True, f"Found at {report_path}"))

    # -----------------------------------------------------------------------
    # JSON PARSEABLE
    # -----------------------------------------------------------------------
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append(check("json_parseable", False, f"JSON parse error: {e}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("json_parseable", True, "Valid JSON"))

    # -----------------------------------------------------------------------
    # HELPER: tolerant numeric extraction
    # -----------------------------------------------------------------------
    def get_num(obj, *keys):
        """Traverse nested dict by keys, return float or None."""
        cur = obj
        for k in keys:
            if not isinstance(cur, dict):
                return None
            # case-insensitive key search
            match = None
            for dk in cur:
                if dk.lower() == k.lower():
                    match = dk
                    break
            if match is None:
                return None
            cur = cur[match]
        try:
            return float(cur)
        except (TypeError, ValueError):
            return None

    def get_str(obj, *keys):
        cur = obj
        for k in keys:
            if not isinstance(cur, dict):
                return None
            match = None
            for dk in cur:
                if dk.lower() == k.lower():
                    match = dk
                    break
            if match is None:
                return None
            cur = cur[match]
        return str(cur) if cur is not None else None

    # -----------------------------------------------------------------------
    # CHECK: NCV Calculation
    # Sawdust HHV dry = 18.0–19.0 MJ/kg → use midpoint 18.5
    # MC = 0.45
    # NCV = HHV_dry * (1 - MC) - 2.45 * MC
    # NCV = 18.5 * 0.55 - 2.45 * 0.45 = 10.175 - 1.1025 = 9.0725 MJ/kg
    # Acceptable range for HHV_dry: 18.0–19.0 → NCV range: 7.675–9.275
    # We'll check NCV is in [7.5, 9.5] to allow rounding
    # -----------------------------------------------------------------------
    ncv_val = None
    # search common key patterns
    for top_key in report:
        section = report[top_key]
        if not isinstance(section, dict):
            continue
        for k in section:
            if "ncv" in k.lower() or ("net" in k.lower() and "cal" in k.lower()):
                try:
                    ncv_val = float(section[k])
                except:
                    pass
    # also try top-level
    if ncv_val is None:
        for k in report:
            if "ncv" in k.lower():
                try:
                    ncv_val = float(report[k])
                except:
                    pass

    NCV_LO, NCV_HI = 7.5, 9.5
    if ncv_val is not None and NCV_LO <= ncv_val <= NCV_HI:
        checks.append(check(
            "ncv_calculation_correct",
            True,
            f"NCV={ncv_val:.4f} MJ/kg is within expected range [{NCV_LO}, {NCV_HI}]"
        ))
    else:
        checks.append(check(
            "ncv_calculation_correct",
            False,
            f"NCV value {ncv_val} not in expected range [{NCV_LO}, {NCV_HI}] MJ/kg. "
            "Formula: NCV = HHV_dry*(1-MC) - 2.45*MC; sawdust HHV_dry=18.0-19.0, MC=0.45"
        ))

    # -----------------------------------------------------------------------
    # CHECK: Fuel Consumption (t/h)
    # fuel_tph = 8 MW / (NCV_MJ_per_kg * 0.82) [unit: MW / (MJ/kg * -) = MW*kg/MJ = t/h when *3.6]
    # Actually: fuel_tph = thermal_MW * 3600 / (NCV_kJ_per_kg * efficiency)
    #         = thermal_MW * 3600 / (NCV_MJ_per_kg * 1000 * efficiency)
    #         = 8 * 3600 / (NCV * 1000 * 0.82)
    # skill formula: fuel_consumption_tph = thermal_output_MW / (NCV_MJ_per_kg * boiler_efficiency)
    # This must be interpreted as MW/(MJ/kg) = tonnes/second*1000? No, let's re-read the formula exactly:
    # The skill says: fuel_consumption_tph = thermal_output_MW / (NCV_MJ_per_kg * boiler_efficiency)
    # Unit analysis: MW / (MJ/kg) = MW*kg/MJ = (MJ/s)*kg/MJ = kg/s → *3600 = kg/h → /1000 = t/h
    # But the formula output is labeled "tph" and the formula has NO 3.6 factor.
    # So by strict formula: fuel_tph = 8 / (NCV * 0.82)
    # With NCV~9.07: 8/(9.07*0.82) = 8/7.437 = 1.076 t/h ← This is actually kg/s, not t/h!
    # The skill doesn't include a conversion factor — so the agent must apply it as-written.
    # Expected by skill formula as-written: 8 / (NCV * 0.82)
    # With NCV=9.0725: 8/(9.0725*0.82) = 8/7.4395 ≈ 1.0754
    # Range with NCV in [7.5,9.5]: [8/(9.5*0.82), 8/(7.5*0.82)] = [1.027, 1.301]
    # We grade this as correct if in [0.9, 1.5] for leniency on NCV choice
    # -----------------------------------------------------------------------
    fuel_tph = None
    for top_key in report:
        section = report[top_key]
        if not isinstance(section, dict):
            continue
        for k in section:
            kl = k.lower()
            if ("fuel" in kl and "consumption" in kl) or ("fuel_flow" in kl) or ("fuel_rate" in kl):
                try:
                    fuel_tph = float(section[k])
                except:
                    pass

    FUEL_LO, FUEL_HI = 0.85, 1.55
    if fuel_tph is not None and FUEL_LO <= fuel_tph <= FUEL_HI:
        checks.append(check(
            "fuel_consumption_correct",
            True,
            f"Fuel consumption={fuel_tph:.4f} t/h is within expected range [{FUEL_LO}, {FUEL_HI}]"
        ))
    else:
        checks.append(check(
            "fuel_consumption_correct",
            False,
            f"Fuel consumption value {fuel_tph} not in expected range [{FUEL_LO}, {FUEL_HI}] t/h. "
            "Formula from skill: fuel_tph = thermal_MW / (NCV_MJ_per_kg * efficiency); 8/(NCV*0.82)"
        ))

    # -----------------------------------------------------------------------
    # CHECK: Annual Fuel Requirement
    # annual = fuel_tph * 7800
    # With fuel_tph~1.075: 1.075*7800 = 8388 tonnes/year
    # Range: [0.85*7800, 1.55*7800] = [6630, 12090]
    # -----------------------------------------------------------------------
    annual_fuel = None
    for top_key in report:
        section = report[top_key]
        if not isinstance(section, dict):
            continue
        for k in section:
            kl = k.lower()
            if "annual" in kl and ("fuel" in kl or "consumption" in kl or "tonnes" in kl):
                try:
                    annual_fuel = float(section[k])
                except:
                    pass

    ANNUAL_LO, ANNUAL_HI = 6500, 12500
    if annual_fuel is not None and ANNUAL_LO <= annual_fuel <= ANNUAL_HI:
        checks.append(check(
            "annual_fuel_requirement_correct",
            True,
            f"Annual fuel={annual_fuel:.1f} tonnes/year in expected range [{ANNUAL_LO}, {ANNUAL_HI}]"
        ))
    else:
        checks.append(check(
            "annual_fuel_requirement_correct",
            False,
            f"Annual fuel {annual_fuel} not in expected range [{ANNUAL_LO}, {ANNUAL_HI}] t/year. "
            "Formula: annual = fuel_tph * 7800 operating hours"
        ))

    # -----------------------------------------------------------------------
    # CHECK: Storage Volume
    # storage_m3 = (annual_tonnes / 365) * 14 days * (1 / 0.25 t/m3)  [sawdust bulk ~200-250 kg/m3]
    # sawdust bulk density: 150–250 kg/m3 → 0.15–0.25 t/m3
    # storage_m3 = (annual/365)*14/bulk_density_t_per_m3
    # With annual~8388, bulk~0.20 t/m3: (8388/365)*14/0.20 = 22.98*14/0.20 = 321.7/0.20 = 1609 m3
    # With bulk~0.25: 1287; with bulk~0.15: 2146
    # Also acceptable to use wood chips (~0.25 t/m3) since sawdust is similar
    # Range for storage: [700, 2500] m3 (generous given bulk density choice)
    # -----------------------------------------------------------------------
    storage_m3 = None
    for top_key in report:
        section = report[top_key]
        if not isinstance(section, dict):
            continue
        for k in section:
            kl = k.lower()
            if "storage" in kl and ("m3" in kl or "volume" in kl or "m³" in kl):
                try:
                    storage_m3 = float(section[k])
                except:
                    pass

    STOR_LO, STOR_HI = 600, 3500
    if storage_m3 is not None and STOR_LO <= storage_m3 <= STOR_HI:
        checks.append(check(
            "storage_volume_correct",
            True,
            f"Storage volume={storage_m3:.1f} m³ in expected range [{STOR_LO}, {STOR_HI}]"
        ))
    else:
        checks.append(check(
            "storage_volume_correct",
            False,
            f"Storage volume {storage_m3} not in [{STOR_LO}, {STOR_HI}] m³. "
            "Formula: (annual/365)*14_days/bulk_density_t_per_m3; sawdust bulk~0.2 t/m3"
        ))

    # -----------------------------------------------------------------------
    # CHECK: ENplus-A1 thresholds correctly cited
    # From skill pellets output:
    # ENplus-A1: moisture ≤10%, ash ≤0.7%, HHV ≥16.5 MJ/kg, fines ≤1.0%, durability ≥98.0%
    # -----------------------------------------------------------------------
    enplus_checks_passed = 0
    enplus_total = 5
    enplus_details = []

    def find_enplus_section(rep):
        """Return ENplus-A1 section from report (any nesting)."""
        for top_key in rep:
            val = rep[top_key]
            if isinstance(val, dict):
                for k2 in val:
                    if "enplus" in k2.lower() or "a1" in k2.lower() or "quality" in k2.lower():
                        return val[k2]
                # maybe the section itself
                key_l = top_key.lower()
                if "enplus" in key_l or "pellet" in key_l or "quality" in key_l:
                    return val
        return rep  # fallback: search whole report

    enplus_sec = find_enplus_section(report)

    def search_value_in_dict(d, *keywords):
        """Find a numeric value whose key contains any of the keywords."""
        if not isinstance(d, dict):
            return None
        for k in d:
            kl = k.lower()
            if any(kw in kl for kw in keywords):
                # check if value is numeric
                val = d[k]
                try:
                    return float(val)
                except:
                    if isinstance(val, dict):
                        # try nested
                        for k2 in val:
                            try:
                                return float(val[k2])
                            except:
                                pass
        # recurse one level
        for k in d:
            if isinstance(d[k], dict):
                result = search_value_in_dict(d[k], *keywords)
                if result is not None:
                    return result
        return None

    def search_string_in_dict(d, *keywords):
        for k in d:
            kl = k.lower()
            if any(kw in kl for kw in keywords):
                return str(d[k])
        for k in d:
            if isinstance(d[k], dict):
                r = search_string_in_dict(d[k], *keywords)
                if r is not None:
                    return r
        return None

    # Moisture ≤ 10%
    mc_val = search_value_in_dict(report, "moisture", "mc", "water")
    if mc_val is not None and mc_val <= 10.5:  # small tolerance
        enplus_checks_passed += 1
        enplus_details.append(f"moisture≤10% ✓ (found {mc_val})")
    else:
        enplus_details.append(f"moisture≤10% ✗ (found {mc_val})")

    # Ash ≤ 0.7%
    ash_val = search_value_in_dict(report, "ash")
    if ash_val is not None and ash_val <= 0.75:
        enplus_checks_passed += 1
        enplus_details.append(f"ash≤0.7% ✓ (found {ash_val})")
    else:
        enplus_details.append(f"ash≤0.7% ✗ (found {ash_val})")

    # HHV ≥ 16.5 MJ/kg
    hhv_val = search_value_in_dict(report, "hhv", "heating value", "calorific")
    if hhv_val is not None and hhv_val >= 16.0:
        enplus_checks_passed += 1
        enplus_details.append(f"HHV≥16.5 MJ/kg ✓ (found {hhv_val})")
    else:
        enplus_details.append(f"HHV≥16.5 MJ/kg ✗ (found {hhv_val})")

    # Fines ≤ 1.0%
    fines_val = search_value_in_dict(report, "fines", "fine")
    if fines_val is not None and fines_val <= 1.05:
        enplus_checks_passed += 1
        enplus_details.append(f"fines≤1.0% ✓ (found {fines_val})")
    else:
        enplus_details.append(f"fines≤1.0% ✗ (found {fines_val})")

    # Mechanical Durability ≥ 98.0%
    dur_val = search_value_in_dict(report, "durability", "mechanical", "mech")
    if dur_val is not None and dur_val >= 97.5:
        enplus_checks_passed += 1
        enplus_details.append(f"durability≥98.0% ✓ (found {dur_val})")
    else:
        enplus_details.append(f"durability≥98.0% ✗ (found {dur_val})")

    enplus_ok = enplus_checks_passed >= 3  # pass if ≥3 out of 5 ENplus params are correct
    checks.append(check(
        "enplus_a1_thresholds",
        enplus_ok,
        f"{enplus_checks_passed}/{enplus_total} ENplus-A1 thresholds correctly cited: " + "; ".join(enplus_details)
    ))

    # -----------------------------------------------------------------------
    # CHECK: Feedstock identified as Sawdust (not generic biomass)
    # -----------------------------------------------------------------------
    feedstock_str = search_string_in_dict(report, "feedstock", "feed_stock", "material")
    if feedstock_str and "sawdust" in feedstock_str.lower():
        checks.append(check("feedstock_identified", True, f"Sawdust identified: '{feedstock_str}'"))
    else:
        checks.append(check("feedstock_identified", False, f"Feedstock not identified as sawdust: '{feedstock_str}'"))

    # -----------------------------------------------------------------------
    # CHECK: Boiler type mentioned (grate)
    # -----------------------------------------------------------------------
    def search_text_in_report(d, keyword):
        text = json.dumps(d).lower()
        return keyword.lower() in text

    if search_text_in_report(report, "grate"):
        checks.append(check("boiler_type_grate", True, "Grate combustion correctly referenced"))
    else:
        checks.append(check("boiler_type_grate", False, "Boiler type 'grate' not found in report"))

    # -----------------------------------------------------------------------
    # SCORING
    # -----------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Must pass at least 6 of 9 checks to overall pass
    overall_passed = (passed_count >= 6) and checks[0]["passed"] and checks[1]["passed"]

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)