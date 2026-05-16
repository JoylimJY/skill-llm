import sys
import json
from pathlib import Path

def run_eval(workspace_dir):
    checks = []
    total_score = 0.0
    max_checks = 12

    # Find the output file
    output_files = list(Path(workspace_dir).rglob("shaft_design_report.json"))
    
    if not output_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "shaft_design_report.json not found anywhere in workspace"}]
        }))
        return

    # Use the most recently modified one if multiple found
    report_path = sorted(output_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_parseable", "passed": False, "detail": f"Could not parse JSON: {e}"}]
        }))
        return

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {report_path}"})
    total_score += 1

    def find_value(d, *keys):
        """Recursively search for any of the given keys in a nested dict, return first match."""
        if isinstance(d, dict):
            for k, v in d.items():
                k_lower = k.lower().replace("-", "_")
                for key in keys:
                    if key.lower() in k_lower:
                        return v
            for v in d.values():
                result = find_value(v, *keys)
                if result is not None:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = find_value(item, *keys)
                if result is not None:
                    return result
        return None

    def numeric_in_range(val, lo, hi):
        try:
            v = float(str(val).replace("~", "").replace("≤", "").strip())
            return lo <= v <= hi
        except:
            return False

    def str_contains_any(val, options):
        if val is None:
            return False
        s = str(val).lower().replace(" ", "")
        return any(opt.lower().replace(" ", "") in s for opt in options)

    # ── CHECK 1: Key dimensions b=10, h=8 (shaft dia 38mm falls in >30~38 range → b=10, h=8)
    # GB/T 1095: >38~44 → b=12, h=8; but shaft is 38 which is exactly at boundary.
    # The table says >30~38 → b=10, h=8. Shaft diameter IS 38mm: ">30~38" includes 38 (upper bound inclusive).
    # So correct answer: b=10, h=8.
    key_b = find_value(report, "key_width", "key_b", "b_mm", "键宽")
    b_correct = str_contains_any(key_b, ["10"])
    checks.append({
        "name": "key_width_b_correct",
        "passed": b_correct,
        "detail": f"Expected key width b=10mm (shaft 38mm → >30~38 range per GB/T 1095). Got: {key_b}"
    })
    if b_correct:
        total_score += 1

    key_h = find_value(report, "key_height", "key_h", "h_mm", "键高")
    h_correct = str_contains_any(key_h, ["8"])
    checks.append({
        "name": "key_height_h_correct",
        "passed": h_correct,
        "detail": f"Expected key height h=8mm (shaft 38mm → >30~38 range per GB/T 1095). Got: {key_h}"
    })
    if h_correct:
        total_score += 1

    # ── CHECK 2: Working length for A-type key: l = L - b = 70 - 10 = 60mm
    key_l = find_value(report, "key_working_length", "working_length", "l_mm", "工作长度")
    l_correct = str_contains_any(key_l, ["60"])
    checks.append({
        "name": "key_working_length_correct",
        "passed": l_correct,
        "detail": f"Expected l=L-b=70-10=60mm for A-type key. Got: {key_l}"
    })
    if l_correct:
        total_score += 1

    # ── CHECK 3: Key stress σ = 2T/(b·h·l) = 2×350000/(10×8×60) = 700000/4800 ≈ 145.8 MPa
    # Acceptable range: 144~148 MPa (rounding tolerance)
    key_stress = find_value(report, "key_stress", "stress_mpa", "挤压应力", "σ")
    stress_correct = False
    stress_val = None
    try:
        stress_val = float(str(key_stress).strip())
        stress_correct = 143.0 <= stress_val <= 148.0
    except:
        pass
    checks.append({
        "name": "key_stress_calculated_correctly",
        "passed": stress_correct,
        "detail": f"Expected σ=2×350000/(10×8×60)≈145.8 MPa (range 143~148). Got: {key_stress}"
    })
    if stress_correct:
        total_score += 1

    # ── CHECK 4: Key strength adequacy — [σ]=120~150 MPa for static steel.
    # 145.8 is within 120~150, so key strength IS adequate (borderline but within range).
    key_adequate = find_value(report, "key_strength_adequate", "strength_adequate", "adequate", "是否满足", "强度")
    # Accept "adequate", "yes", "满足", "true", "ok", "pass" etc.
    adequate_correct = str_contains_any(key_adequate, ["adequate", "yes", "满足", "true", "ok", "pass", "sufficient", "合格"])
    checks.append({
        "name": "key_strength_adequacy_correct",
        "passed": adequate_correct,
        "detail": f"σ≈145.8 MPa ≤ [σ]=150 MPa (upper bound for static steel connection), so strength IS adequate. Got: {key_adequate}"
    })
    if adequate_correct:
        total_score += 1

    # ── CHECK 5: Bearing seat shaft tolerance = k5 or k6 (NOT h6 which was the wrong intern value)
    bearing_shaft_tol = find_value(report, "bearing_seat_tolerance_shaft", "bearing_shaft_tolerance", "轴承档公差", "shaft_tolerance_bearing")
    bearing_shaft_correct = str_contains_any(bearing_shaft_tol, ["k5", "k6"])
    checks.append({
        "name": "bearing_seat_shaft_tolerance_correct",
        "passed": bearing_shaft_correct,
        "detail": f"Expected k5 or k6 for bearing seat on shaft (not h6). Got: {bearing_shaft_tol}"
    })
    if bearing_shaft_correct:
        total_score += 1

    # ── CHECK 6: Bearing seat bore tolerance = H6 or H7
    bearing_bore_tol = find_value(report, "bearing_seat_tolerance_bore", "bearing_bore_tolerance", "轴承室公差", "bore_tolerance")
    bearing_bore_correct = str_contains_any(bearing_bore_tol, ["H6", "H7"])
    checks.append({
        "name": "bearing_seat_bore_tolerance_correct",
        "passed": bearing_bore_correct,
        "detail": f"Expected H6 or H7 for bearing seat bore. Got: {bearing_bore_tol}"
    })
    if bearing_bore_correct:
        total_score += 1

    # ── CHECK 7: Keyway slot tolerance shaft = H9 (NOT H7 which was the wrong intern value)
    keyway_shaft_tol = find_value(report, "keyway_slot_tolerance_shaft", "keyway_shaft_tolerance", "键槽公差轴", "轴槽公差")
    keyway_shaft_correct = str_contains_any(keyway_shaft_tol, ["H9"])
    checks.append({
        "name": "keyway_shaft_tolerance_correct",
        "passed": keyway_shaft_correct,
        "detail": f"Expected H9 for shaft keyway slot (not H7). Got: {keyway_shaft_tol}"
    })
    if keyway_shaft_correct:
        total_score += 1

    # ── CHECK 8: Keyway hub tolerance = D10
    keyway_hub_tol = find_value(report, "keyway_slot_tolerance_hub", "keyway_hub_tolerance", "毂槽公差", "hub_tolerance")
    keyway_hub_correct = str_contains_any(keyway_hub_tol, ["D10"])
    checks.append({
        "name": "keyway_hub_tolerance_correct",
        "passed": keyway_hub_correct,
        "detail": f"Expected D10 for hub keyway slot. Got: {keyway_hub_tol}"
    })
    if keyway_hub_correct:
        total_score += 1

    # ── CHECK 9: Ra bearing seat = 0.2~0.4 μm (NOT 1.6 which was the wrong intern value)
    ra_bearing = find_value(report, "ra_bearing_seat", "bearing_seat_ra", "轴承档粗糙度", "轴承档ra")
    # Accept any value/string that contains 0.2 or 0.4 or "0.2~0.4"
    ra_bearing_correct = str_contains_any(ra_bearing, ["0.2", "0.4", "0.2~0.4"])
    checks.append({
        "name": "ra_bearing_seat_correct",
        "passed": ra_bearing_correct,
        "detail": f"Expected Ra 0.2~0.4 μm for bearing seat (not 1.6). Got: {ra_bearing}"
    })
    if ra_bearing_correct:
        total_score += 1

    # ── CHECK 10: Ra oil seal = 0.4~0.8 μm
    ra_oil_seal = find_value(report, "ra_oil_seal", "oil_seal_ra", "油封档粗糙度", "油封ra")
    ra_oil_correct = str_contains_any(ra_oil_seal, ["0.4", "0.8", "0.4~0.8"])
    checks.append({
        "name": "ra_oil_seal_correct",
        "passed": ra_oil_correct,
        "detail": f"Expected Ra 0.4~0.8 μm for oil seal. Got: {ra_oil_seal}"
    })
    if ra_oil_correct:
        total_score += 1

    # ── CHECK 11: Ra keyway flank = 1.6~3.2 μm
    ra_keyway = find_value(report, "ra_keyway_flank", "keyway_ra", "键槽粗糙度", "键槽侧面ra")
    ra_keyway_correct = str_contains_any(ra_keyway, ["1.6", "3.2", "1.6~3.2"])
    checks.append({
        "name": "ra_keyway_flank_correct",
        "passed": ra_keyway_correct,
        "detail": f"Expected Ra 1.6~3.2 μm for keyway flank. Got: {ra_keyway}"
    })
    if ra_keyway_correct:
        total_score += 1

    # ── CHECK 12: Bearing recommended as deep groove ball bearing (径向载荷, general motor application)
    bearing_type = find_value(report, "bearing_recommended_type", "bearing_type", "推荐轴承", "轴承类型")
    bearing_type_correct = str_contains_any(bearing_type, ["deep groove", "深沟球", "6000", "6200", "6300", "ball bearing", "球轴承"])
    checks.append({
        "name": "bearing_type_recommended_correct",
        "passed": bearing_type_correct,
        "detail": f"Expected deep groove ball bearing recommendation. Got: {bearing_type}"
    })
    if bearing_type_correct:
        total_score += 1

    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    final_score = total_score / max_checks
    overall_passed = final_score >= 0.75  # Must pass at least 9/12 checks

    print(json.dumps({
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)