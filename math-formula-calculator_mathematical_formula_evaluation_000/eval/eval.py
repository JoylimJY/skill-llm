import sys
import json
import math
from pathlib import Path

def find_report(workspace):
    """Find price_score_report.json anywhere in workspace."""
    hits = list(Path(workspace).rglob("price_score_report.json"))
    if not hits:
        return None
    return hits[0]

def approx_equal(a, b, tol=0.02):
    """Tolerance-based float comparison."""
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False

def evaluate(workspace):
    checks = []
    total_score = 0.0

    # ── Locate report ────────────────────────────────────────────────────────
    report_path = find_report(workspace)
    check_found = {
        "name": "report_file_exists",
        "passed": report_path is not None,
        "detail": f"Found at {report_path}" if report_path else "price_score_report.json not found anywhere in workspace"
    }
    checks.append(check_found)
    if not check_found["passed"]:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        checks.append({"name": "json_parseable", "passed": True, "detail": "File is valid JSON"})
        total_score += 0.05
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 1: Benchmark Price Calculation ─────────────────────────────────
    # Valid bids: V001=498.50, V002=521.00, V003=476.20
    # After removing highest (534.80) and lowest (389.00):
    # Benchmark = (498.50 + 521.00 + 476.20) / 3 = 1495.70 / 3 = 498.5667
    EXPECTED_BENCHMARK = (498.50 + 521.00 + 476.20) / 3  # ≈ 498.5667

    bp_val = None
    try:
        bp_raw = report.get("benchmark_price")
        if isinstance(bp_raw, dict):
            # might be nested as {"value": ...}
            bp_val = float(bp_raw.get("value", bp_raw.get("benchmark_price", 0)))
        else:
            bp_val = float(bp_raw)
        bp_ok = approx_equal(bp_val, EXPECTED_BENCHMARK, tol=0.05)
        checks.append({
            "name": "benchmark_price_correct",
            "passed": bp_ok,
            "detail": f"Got {bp_val:.4f}, expected ~{EXPECTED_BENCHMARK:.4f} (498.50+521.00+476.20)/3"
        })
        if bp_ok:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "benchmark_price_correct", "passed": False, "detail": f"Could not extract benchmark_price: {e}"})

    # ── CHECK 2: Formula Analysis Structure ──────────────────────────────────
    try:
        fa = report.get("formula_analysis", {})
        fa_str = json.dumps(fa).lower()

        has_outer = any(k in fa_str for k in ["iferror", "outer", "外层"])
        has_round = "round" in fa_str
        has_if = "if" in fa_str
        has_max = "max" in fa_str
        has_abs = "abs" in fa_str
        has_coeff = any(k in fa_str for k in ["0.6", "0.9"])

        fa_ok = all([has_outer or has_round, has_if, has_max, has_abs, has_coeff])
        checks.append({
            "name": "formula_analysis_structure",
            "passed": fa_ok,
            "detail": f"iferror/outer={has_outer}, round={has_round}, if={has_if}, max={has_max}, abs={has_abs}, coefficients={has_coeff}"
        })
        if fa_ok:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "formula_analysis_structure", "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 3: All 5 vendors present ───────────────────────────────────────
    try:
        vendors = report.get("vendor_scores", [])
        vendor_ids_found = set()
        for v in vendors:
            vid = str(v.get("vendor_id", v.get("id", v.get("name", "")))).upper()
            for code in ["V001", "V002", "V003", "V004", "V005"]:
                if code in vid or any(name_frag in str(v).upper() for name_frag in [
                    "HUABEI", "DONGNAN", "XIBEI", "ZHONGNAN", "BEIBU"
                ]):
                    pass
            vendor_ids_found.add(vid[:4] if len(vid) >= 4 else vid)

        # More robust: check count
        count_ok = len(vendors) == 5
        checks.append({
            "name": "all_5_vendors_present",
            "passed": count_ok,
            "detail": f"Found {len(vendors)} vendor entries, expected 5"
        })
        if count_ok:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "all_5_vendors_present", "passed": False, "detail": f"Error: {e}"})
        vendors = []

    # ── CHECK 4: Correct price scores per vendor ─────────────────────────────
    # Using benchmark = (498.50+521.00+476.20)/3 ≈ 498.5667
    # F2 = 30 (benchmark score)
    E2 = EXPECTED_BENCHMARK
    F2 = 30.0

    def calc_score(bid):
        bid = float(bid)
        if bid < E2:
            raw = F2 - abs(bid - E2) / E2 * 100 * 0.6
        elif bid == E2:
            raw = F2
        else:
            raw = F2 - abs(bid - E2) / E2 * 100 * 0.9
        result = max(0.0, raw)
        return round(result, 2)

    expected_scores = {
        "V001": calc_score(498.50),   # 498.50 < 498.5667 → coeff 0.6
        "V002": calc_score(521.00),   # 521.00 > 498.5667 → coeff 0.9
        "V003": calc_score(476.20),   # 476.20 < 498.5667 → coeff 0.6
        "V004": calc_score(389.00),   # 389.00 < 498.5667 → coeff 0.6
        "V005": calc_score(534.80),   # 534.80 > 498.5667 → coeff 0.9
    }
    # V001: 498.50 < 498.5667 → diff=0.0667, /E2=0.0001338, *100=0.01338, *0.6=0.00803, 30-0.00803≈29.99
    # V002: 521.00 > 498.5667 → diff=22.4333, /E2=0.04500, *100=4.500, *0.9=4.050, 30-4.050=25.95
    # V003: 476.20 < 498.5667 → diff=22.3667, /E2=0.04487, *100=4.487, *0.6=2.692, 30-2.692=27.31
    # V004: 389.00 < 498.5667 → diff=109.5667, /E2=0.21976, *100=21.976, *0.6=13.185, 30-13.185=16.81
    # V005: 534.80 > 498.5667 → diff=36.2333, /E2=0.07268, *100=7.268, *0.9=6.541, 30-6.541=23.46

    score_checks_passed = 0
    for v_entry in vendors:
        v_str = json.dumps(v_entry)

        # Determine which vendor this is
        matched_id = None
        bid_price_val = None
        for code, bid_val in [("V001", 498.50), ("V002", 521.00), ("V003", 476.20), ("V004", 389.00), ("V005", 534.80)]:
            bid_str_variants = [str(bid_val), str(int(bid_val)) if bid_val == int(bid_val) else ""]
            name_map = {
                "V001": "HUABEI", "V002": "DONGNAN", "V003": "XIBEI",
                "V004": "ZHONGNAN", "V005": "BEIBU"
            }
            if code in v_str.upper() or name_map[code] in v_str.upper():
                matched_id = code
                bid_price_val = bid_val
                break
            # Try matching by bid price value
            for bsv in bid_str_variants:
                if bsv and bsv in v_str:
                    matched_id = code
                    bid_price_val = bid_val
                    break
            if matched_id:
                break

        if not matched_id:
            continue

        expected = expected_scores[matched_id]

        # Extract price_score from various possible keys
        actual_score = None
        for key in ["price_score", "score", "final_score", "result", "价格分"]:
            if key in v_entry:
                try:
                    actual_score = float(v_entry[key])
                    break
                except (ValueError, TypeError):
                    pass

        if actual_score is None:
            # Try to find a float in the entry that matches
            import re
            nums = re.findall(r'\b\d+\.\d+\b', v_str)
            for n in nums:
                if approx_equal(float(n), expected, tol=0.05):
                    actual_score = float(n)
                    break

        if actual_score is not None and approx_equal(actual_score, expected, tol=0.05):
            score_checks_passed += 1

    score_check_ok = score_checks_passed >= 4  # at least 4 of 5 correct
    checks.append({
        "name": "vendor_price_scores_correct",
        "passed": score_check_ok,
        "detail": (
            f"{score_checks_passed}/5 vendor scores correct. "
            f"Expected: V001≈{expected_scores['V001']}, V002≈{expected_scores['V002']}, "
            f"V003≈{expected_scores['V003']}, V004≈{expected_scores['V004']}, V005≈{expected_scores['V005']}"
        )
    })
    if score_check_ok:
        total_score += 0.30

    # ── CHECK 5: Correct coefficient direction (KEY TRAP) ───────────────────
    # The trap: low bid (< benchmark) uses 0.6, high bid (> benchmark) uses 0.9
    # V003=476.20 < E2 → coeff 0.6 → score ≈ 27.31
    # V002=521.00 > E2 → coeff 0.9 → score ≈ 25.95
    # If agent swaps 0.6/0.9: V003 would get ~25.56, V002 would get ~27.30
    # We verify V002 < V003 (higher bid gets lower score when both off-benchmark)
    try:
        v002_score = None
        v003_score = None
        for v_entry in vendors:
            v_str = json.dumps(v_entry)
            for key in ["price_score", "score", "final_score", "result"]:
                if key in v_entry:
                    try:
                        val = float(v_entry[key])
                        if "V002" in v_str.upper() or "DONGNAN" in v_str.upper():
                            v002_score = val
                        if "V003" in v_str.upper() or "XIBEI" in v_str.upper():
                            v003_score = val
                    except (ValueError, TypeError):
                        pass

        if v002_score is not None and v003_score is not None:
            # V002 (over benchmark, 0.9 coeff) should score LESS than V003 (under benchmark, 0.6 coeff)
            coeff_ok = v002_score < v003_score
            checks.append({
                "name": "coefficient_direction_correct",
                "passed": coeff_ok,
                "detail": (
                    f"V002(521.00, over benchmark)={v002_score}, V003(476.20, under benchmark)={v003_score}. "
                    f"Over-benchmark bids penalized more (coeff 0.9 > coeff 0.6 for under-benchmark). "
                    f"{'CORRECT: V002 < V003 ✓' if coeff_ok else 'WRONG: coefficients likely swapped!'}"
                )
            })
            if coeff_ok:
                total_score += 0.15
        else:
            checks.append({
                "name": "coefficient_direction_correct",
                "passed": False,
                "detail": f"Could not extract V002 or V003 scores to verify coefficient direction. v002={v002_score}, v003={v003_score}"
            })
    except Exception as e:
        checks.append({"name": "coefficient_direction_correct", "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 6: Denominator is benchmark price (not bid price) ─────────────
    # V004=389.00, E2≈498.57
    # Correct: |389-498.57|/498.57 = 109.57/498.57 = 0.2198 → *100*0.6=13.186 → 30-13.186=16.81
    # Wrong (÷bid): |389-498.57|/389 = 109.57/389 = 0.2817 → *100*0.6=16.90 → 30-16.90=13.10
    try:
        v004_score = None
        for v_entry in vendors:
            v_str = json.dumps(v_entry)
            if "V004" in v_str.upper() or "ZHONGNAN" in v_str.upper():
                for key in ["price_score", "score", "final_score", "result"]:
                    if key in v_entry:
                        try:
                            v004_score = float(v_entry[key])
                            break
                        except (ValueError, TypeError):
                            pass

        if v004_score is not None:
            correct_v004 = expected_scores["V004"]  # ≈16.81
            wrong_v004_with_bid_denom = round(max(0, 30 - abs(389.00 - E2) / 389.00 * 100 * 0.6), 2)
            denom_ok = approx_equal(v004_score, correct_v004, tol=0.1) and not approx_equal(v004_score, wrong_v004_with_bid_denom, tol=0.1)
            checks.append({
                "name": "denominator_is_benchmark_not_bid",
                "passed": denom_ok,
                "detail": (
                    f"V004 score: got {v004_score}, correct(÷benchmark)≈{correct_v004}, "
                    f"wrong(÷bid_price)≈{wrong_v004_with_bid_denom}"
                )
            })
            if denom_ok:
                total_score += 0.10
        else:
            checks.append({
                "name": "denominator_is_benchmark_not_bid",
                "passed": False,
                "detail": "Could not extract V004 score to verify denominator"
            })
    except Exception as e:
        checks.append({"name": "denominator_is_benchmark_not_bid", "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 7: Boundary Analysis Present ──────────────────────────────────
    try:
        ba = report.get("boundary_analysis", {})
        ba_str = json.dumps(ba).lower()
        has_zero_div = any(k in ba_str for k in ["zero", "除零", "分母", "iferror", "denominator"])
        has_negative = any(k in ba_str for k in ["negative", "负", "max(0", "max(0,", "clamp", "floor"])
        has_iferror = "iferror" in ba_str

        ba_ok = (has_zero_div or has_iferror) and has_negative
        checks.append({
            "name": "boundary_analysis_present",
            "passed": ba_ok,
            "detail": f"zero_div/iferror_check={has_zero_div or has_iferror}, negative_score_check={has_negative}"
        })
        if ba_ok:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "boundary_analysis_present", "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 8: Calculation steps recorded (intermediate results) ───────────
    try:
        steps_present = 0
        for v_entry in vendors:
            steps_keys = ["steps", "calculation_steps", "intermediate", "计算步骤", "process"]
            for sk in steps_keys:
                if sk in v_entry and v_entry[sk]:
                    steps_present += 1
                    break
            # Also check if nested detail
            v_str = json.dumps(v_entry)
            if any(k in v_str.lower() for k in ["step", "abs(", "round(", "中间", "diff", "差额"]):
                steps_present = max(steps_present, 1)  # at least claimed steps

        steps_ok = steps_present >= 3
        checks.append({
            "name": "intermediate_steps_recorded",
            "passed": steps_ok,
            "detail": f"Found calculation steps in {steps_present}/5 vendor entries"
        })
        if steps_ok:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "intermediate_steps_recorded", "passed": False, "detail": f"Error: {e}"})

    # ── Final verdict ─────────────────────────────────────────────────────────
    critical_checks = ["benchmark_price_correct", "vendor_price_scores_correct", "coefficient_direction_correct"]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    total_score = min(1.0, total_score)
    passed = critical_passed and total_score >= 0.55

    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))