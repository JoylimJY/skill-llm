import sys
import json
import os
from pathlib import Path

def load_guide(workspace: str):
    """Find the output file rope_work_guide.json anywhere in the workspace."""
    matches = list(Path(workspace).rglob("rope_work_guide.json"))
    if not matches:
        return None, "File rope_work_guide.json not found in workspace"
    return matches[0], None

def run_checks(workspace: str):
    checks = []
    total_weight = 0.0

    guide_path, err = load_guide(workspace)
    if err:
        checks.append({"name": "file_exists", "passed": False, "detail": err})
        return checks, 0.0

    checks.append({"name": "file_exists", "passed": True, "detail": str(guide_path)})

    try:
        with open(guide_path) as f:
            guide = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return checks, 0.0

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})

    scenarios = guide.get("scenarios", guide) if isinstance(guide, dict) else {}
    # Support top-level list or dict with "scenarios" key
    if isinstance(guide, list):
        scenario_list = guide
    elif isinstance(guide, dict) and "scenarios" in guide:
        scenario_list = guide["scenarios"]
    else:
        scenario_list = list(guide.values()) if isinstance(guide, dict) else []

    def find_scenario(sid):
        for s in scenario_list:
            if isinstance(s, dict):
                if s.get("scenario_id") == sid or s.get("id") == sid:
                    return s
        return None

    # ── CHECK S1: Trucker's Hitch ──────────────────────────────────────────
    s1 = find_scenario("S1")
    s1_passed = False
    s1_detail = "S1 not found in output"
    if s1:
        text = json.dumps(s1).lower()
        has_truckers = "trucker" in text or "trucker's hitch" in text or "truckers hitch" in text
        # Working load check: 2000 kg breaking strength, knot reduces 25-50%
        # After knot reduction: 1000-1500 kg effective. Working load (1/5 to 1/10): 100-300 kg
        # 480 kg load — must flag that this EXCEEDS safe working load
        has_load_warning = (
            "exceed" in text or "too heavy" in text or "unsafe" in text
            or "over" in text or "warning" in text or "caution" in text
            or "exceeds" in text or "limit" in text or "safe working" in text
            or "working load" in text or "break" in text
        )
        s1_passed = has_truckers and has_load_warning
        s1_detail = (
            f"Trucker's hitch mentioned: {has_truckers}; "
            f"Load safety warning present: {has_load_warning}; "
            f"(480kg load on 2000kg rope with knot reduction and 1/5-1/10 WL ratio requires warning)"
        )
    checks.append({"name": "S1_truckers_hitch_and_load_warning", "passed": s1_passed, "detail": s1_detail})
    total_weight += 2.0 if s1_passed else 0.0

    # ── CHECK S2: Taut-line Hitch + Polypropylene warning ─────────────────
    s2 = find_scenario("S2")
    s2_passed = False
    s2_detail = "S2 not found in output"
    if s2:
        text = json.dumps(s2).lower()
        has_tautline = (
            "taut-line" in text or "taut line" in text or "tautline" in text
            or "midshipman" in text
        )
        # SKILL.md says polypropylene may not hold — add extra wrap
        has_poly_warning = (
            "polypropylene" in text or "slippery" in text or "extra wrap" in text
            or "slip" in text or "synthetic" in text or "half-hitch" in text
            or "additional" in text or "extra" in text
        )
        # Must mention TWO inner wraps
        has_two_wraps = (
            "two" in text or "2" in text or "double" in text or "wrap" in text
        )
        s2_passed = has_tautline and has_poly_warning
        s2_detail = (
            f"Taut-line hitch mentioned: {has_tautline}; "
            f"Polypropylene/slippery rope warning: {has_poly_warning}; "
            f"Wrap count info: {has_two_wraps}"
        )
    checks.append({"name": "S2_tautline_hitch_poly_warning", "passed": s2_passed, "detail": s2_detail})
    total_weight += 1.5 if s2_passed else 0.0

    # ── CHECK S3: Sheet Bend + same-side tail detail ───────────────────────
    s3 = find_scenario("S3")
    s3_passed = False
    s3_detail = "S3 not found in output"
    if s3:
        text = json.dumps(s3).lower()
        has_sheet_bend = "sheet bend" in text or "sheet-bend" in text
        # Critical detail: both ends same side; OR double sheet bend for different diameters
        has_critical_detail = (
            "same side" in text or "double sheet bend" in text
            or "double sheet" in text or "both ends" in text
            or "thicker" in text or "diameter" in text
            or "bight" in text
        )
        # Must NOT recommend square knot for this
        recommends_square_knot_wrong = (
            "square knot" in text and "join" in text and "load" in text
            and "warning" not in text and "not" not in text
        )
        s3_passed = has_sheet_bend and has_critical_detail and not recommends_square_knot_wrong
        s3_detail = (
            f"Sheet bend mentioned: {has_sheet_bend}; "
            f"Critical same-side/diameter detail: {has_critical_detail}; "
            f"Incorrect square knot for load join: {recommends_square_knot_wrong}"
        )
    checks.append({"name": "S3_sheet_bend_critical_detail", "passed": s3_passed, "detail": s3_detail})
    total_weight += 1.5 if s3_passed else 0.0

    # ── CHECK S4: Square lashing (right angles) + Diagonal lashing (bracing) ──
    s4 = find_scenario("S4")
    s4_passed = False
    s4_detail = "S4 not found in output"
    if s4:
        text = json.dumps(s4).lower()
        has_square_lashing = "square lashing" in text
        has_diagonal_lashing = "diagonal lashing" in text
        # Square lashing must start with clove hitch
        has_clove_start = "clove hitch" in text or "clove" in text
        # Diagonal lashing must start with timber hitch (NOT clove hitch for diagonal)
        has_timber_start = "timber hitch" in text or "timber" in text
        # Must mention frapping turns
        has_frapping = "frapping" in text or "frap" in text
        s4_passed = (
            has_square_lashing and has_diagonal_lashing
            and has_timber_start and has_frapping
        )
        s4_detail = (
            f"Square lashing: {has_square_lashing}; "
            f"Diagonal lashing: {has_diagonal_lashing}; "
            f"Timber hitch for diagonal start: {has_timber_start}; "
            f"Frapping turns: {has_frapping}; "
            f"Clove hitch mention: {has_clove_start}"
        )
    checks.append({"name": "S4_correct_lashings_and_starts", "passed": s4_passed, "detail": s4_detail})
    total_weight += 2.0 if s4_passed else 0.0

    # ── CHECK S5: Square knot EXPLICITLY forbidden for load-bearing join ───
    s5 = find_scenario("S5")
    s5_passed = False
    s5_detail = "S5 not found in output"
    if s5:
        text = json.dumps(s5).lower()
        # Must say NO / forbidden / not appropriate / will fail / capsize
        rejects_square_knot = (
            "not" in text and (
                "load" in text or "join" in text or "bearing" in text
            )
        ) or "capsize" in text or "will fail" in text or "not for" in text \
          or "not a load" in text or "do not" in text or "never" in text \
          or "forbidden" in text or "inappropriate" in text or "wrong" in text \
          or "unsafe" in text or "dangerous" in text
        # Must recommend an alternative (sheet bend or double fisherman)
        recommends_alternative = (
            "sheet bend" in text or "double fisherman" in text
            or "fisherman" in text
        )
        s5_passed = rejects_square_knot and recommends_alternative
        s5_detail = (
            f"Square knot explicitly rejected for load join: {rejects_square_knot}; "
            f"Alternative knot recommended: {recommends_alternative}"
        )
    checks.append({"name": "S5_square_knot_rejected_with_alternative", "passed": s5_passed, "detail": s5_detail})
    total_weight += 2.0 if s5_passed else 0.0

    # ── CHECK: All 5 scenarios present ────────────────────────────────────
    all_found = all(find_scenario(f"S{i}") is not None for i in range(1, 6))
    checks.append({
        "name": "all_5_scenarios_present",
        "passed": all_found,
        "detail": f"All 5 scenario IDs (S1-S5) found in output: {all_found}"
    })
    total_weight += 1.0 if all_found else 0.0

    # Normalize score to 0.0-1.0
    max_weight = 2.0 + 1.5 + 1.5 + 2.0 + 2.0 + 1.0  # = 10.0
    score = round(total_weight / max_weight, 3)
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.6 and all(
        c["passed"] for c in checks if c["name"] in [
            "file_exists", "valid_json",
            "S5_square_knot_rejected_with_alternative"
        ]
    )

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()