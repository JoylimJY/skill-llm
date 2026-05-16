import sys
import json
import math
from pathlib import Path

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # --- Locate the output file ---
    output_files = list(workspace.rglob("memory_health_report.json"))
    if not output_files:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "memory_health_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = output_files[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})

    try:
        with open(output_file) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "output_file_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_parseable", "passed": True, "detail": "Valid JSON"})

    # --- Helper: Ebbinghaus decay ---
    HALF_LIVES = {"short_term": 3.0, "procedural": 7.0, "long_term": 90.0}
    MIN_STRENGTH = 0.1
    BASE_INTERVAL = 1.0
    STRENGTH_FACTOR = 1.5
    EASY_FACTOR = 1.3
    HARD_FACTOR = 0.8

    def calc_decayed_strength(strength, age_days, tier):
        hl = HALF_LIVES[tier]
        decay = math.pow(2, -age_days / hl)
        return max(strength * decay, MIN_STRENGTH)

    def calc_next_review(decayed_strength):
        return BASE_INTERVAL * math.pow(decayed_strength, STRENGTH_FACTOR)

    def calc_updated_strength(decayed_strength, last_result):
        if last_result == "success":
            return min(1.0, decayed_strength + 0.15)
        elif last_result == "easy":
            return min(1.0, decayed_strength * EASY_FACTOR)
        elif last_result == "hard":
            return min(1.0, decayed_strength * HARD_FACTOR + 0.1)
        elif last_result == "fail":
            return max(MIN_STRENGTH, decayed_strength * HARD_FACTOR)
        return decayed_strength

    # Load input data
    try:
        with open(workspace / "data" / "raw" / "vocabulary_review_session.json") as f:
            input_data = json.load(f)
        items = input_data["items"]
    except Exception as e:
        checks.append({"name": "input_data_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check report structure ---
    if not isinstance(report, dict):
        checks.append({"name": "report_is_dict", "passed": False, "detail": "Report must be a JSON object"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Find items array - support multiple possible keys
    report_items = None
    for key in ["items", "vocabulary_items", "results", "words"]:
        if key in report:
            report_items = report[key]
            break

    if report_items is None:
        checks.append({"name": "report_has_items", "passed": False, "detail": f"Report must have an 'items' (or similar) array. Keys found: {list(report.keys())}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_has_items", "passed": True, "detail": f"Found items under key, count={len(report_items)}"})

    # Index report items by word_id
    report_by_id = {}
    for ri in report_items:
        if isinstance(ri, dict) and "word_id" in ri:
            report_by_id[ri["word_id"]] = ri

    # --- Per-item checks ---
    TOLERANCE = 1e-4
    item_scores = []

    for item in items:
        wid = item["word_id"]
        tier = item["tier"]
        strength = item["strength"]
        age_days = item["age_days"]
        last_result = item["last_result"]

        expected_decayed = calc_decayed_strength(strength, age_days, tier)
        expected_next_review = calc_next_review(expected_decayed)
        expected_updated = calc_updated_strength(expected_decayed, last_result)

        if wid not in report_by_id:
            checks.append({
                "name": f"item_{wid}_present",
                "passed": False,
                "detail": f"word_id {wid} not found in report"
            })
            item_scores.append(0.0)
            continue

        ri = report_by_id[wid]
        item_pass = True
        item_details = []

        # Check decayed_strength
        decayed_val = ri.get("decayed_strength")
        if decayed_val is None:
            item_pass = False
            item_details.append(f"missing decayed_strength (expected ~{expected_decayed:.4f})")
        elif abs(float(decayed_val) - expected_decayed) > TOLERANCE:
            item_pass = False
            item_details.append(f"decayed_strength={decayed_val:.4f}, expected={expected_decayed:.4f} (tier={tier}, hl={HALF_LIVES[tier]})")

        # Check next_review_days
        review_val = ri.get("next_review_days")
        if review_val is None:
            item_pass = False
            item_details.append(f"missing next_review_days (expected ~{expected_next_review:.4f})")
        elif abs(float(review_val) - expected_next_review) > TOLERANCE:
            item_pass = False
            item_details.append(f"next_review_days={review_val:.4f}, expected={expected_next_review:.4f}")

        # Check updated_strength
        updated_val = ri.get("updated_strength")
        if updated_val is None:
            item_pass = False
            item_details.append(f"missing updated_strength (expected ~{expected_updated:.4f})")
        elif abs(float(updated_val) - expected_updated) > TOLERANCE:
            item_pass = False
            item_details.append(f"updated_strength={updated_val:.4f}, expected={expected_updated:.4f} (result={last_result})")

        checks.append({
            "name": f"item_{wid}_correct",
            "passed": item_pass,
            "detail": "; ".join(item_details) if item_details else f"All values correct for {wid} (tier={tier})"
        })
        item_scores.append(1.0 if item_pass else 0.0)

    # --- Check tier-specific half-life usage ---
    # Verify short_term vs long_term items have distinctly different decay rates
    st_items = [i for i in items if i["tier"] == "short_term"]
    lt_items = [i for i in items if i["tier"] == "long_term"]

    tier_check_passed = True
    tier_check_detail = []

    for si in st_items:
        wid = si["word_id"]
        if wid in report_by_id:
            ri = report_by_id[wid]
            decayed_val = ri.get("decayed_strength")
            if decayed_val is not None:
                expected_st = calc_decayed_strength(si["strength"], si["age_days"], "short_term")
                wrong_lt = calc_decayed_strength(si["strength"], si["age_days"], "long_term")
                if abs(float(decayed_val) - wrong_lt) < TOLERANCE and abs(float(decayed_val) - expected_st) > TOLERANCE:
                    tier_check_passed = False
                    tier_check_detail.append(f"{wid}: used long_term half-life instead of short_term")

    checks.append({
        "name": "tier_specific_half_lives_used",
        "passed": tier_check_passed,
        "detail": "; ".join(tier_check_detail) if tier_check_detail else "Tier-specific half-lives correctly applied"
    })

    # --- Check minimum_strength clamp ---
    # w012 long_term, strength=0.50, age=200 days: decay = 2^(-200/90) = 0.2143, decayed=0.1072 > 0.1 -- fine
    # w004 short_term, strength=0.45, age=6 days: decay = 2^(-6/3) = 0.25, decayed=0.1125 > 0.1 -- fine
    # Let's compute w004 carefully
    w004_expected = calc_decayed_strength(0.45, 6, "short_term")  # should be 0.1125
    w004_ri = report_by_id.get("w004", {})
    w004_decayed = w004_ri.get("decayed_strength")
    min_strength_check = False
    min_detail = ""
    if w004_decayed is not None:
        if abs(float(w004_decayed) - w004_expected) <= TOLERANCE:
            min_strength_check = True
            min_detail = f"w004 decayed_strength correctly computed as {w004_expected:.4f}"
        else:
            min_detail = f"w004 decayed_strength={w004_decayed:.4f}, expected={w004_expected:.4f}"
    else:
        min_detail = "w004 not found in report"
    checks.append({"name": "minimum_strength_boundary", "passed": min_strength_check, "detail": min_detail})

    # --- Final scoring ---
    correct_items = sum(item_scores)
    total_items = len(items)
    item_fraction = correct_items / total_items if total_items > 0 else 0

    bonus_checks = [c for c in checks if c["name"] in ["tier_specific_half_lives_used", "minimum_strength_boundary"]]
    bonus_score = sum(1 for c in bonus_checks if c["passed"]) / len(bonus_checks) if bonus_checks else 0

    final_score = round(0.75 * item_fraction + 0.25 * bonus_score, 4)

    all_passed = (item_fraction == 1.0) and all(c["passed"] for c in bonus_checks)

    return {
        "passed": all_passed and final_score >= 0.9,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))