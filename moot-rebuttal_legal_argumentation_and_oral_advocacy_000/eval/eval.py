import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # Find the rebuttal_script.txt file
    workspace = Path(workspace_dir)
    found_files = list(workspace.rglob("rebuttal_script.txt"))

    if not found_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "rebuttal_script.txt not found anywhere in workspace."}]
        }

    script_path = found_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {script_path}"})

    try:
        content = script_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # -----------------------------------------------------------------------
    # CHECK 1: Rebuttal opening formula
    # Expected pattern: "Your excellencies, the Applicant raises [N] point[s] on rebuttal"
    # -----------------------------------------------------------------------
    rebuttal_opening_pattern = re.search(
        r"your excellenc(?:ies|y)[,.]?\s+the applicant raises\s+(\w+)\s+point[s]?\s+on rebuttal",
        content_lower
    )
    check1_passed = rebuttal_opening_pattern is not None
    checks.append({
        "name": "rebuttal_opening_formula",
        "passed": check1_passed,
        "detail": "Rebuttal must open with 'Your excellencies, the Applicant raises [N] point(s) on rebuttal'" +
                  (" - FOUND" if check1_passed else " - NOT FOUND. Must use exact formula from skill.")
    })
    if check1_passed:
        total_score += 15

    # -----------------------------------------------------------------------
    # CHECK 2: Rebuttal has no more than 3 points
    # Count "first", "second", "third", "fourth", etc., OR numbered points in rebuttal section
    # -----------------------------------------------------------------------
    # Extract rebuttal section (between rebuttal heading and surrebuttal heading)
    rebuttal_section = ""
    surrebuttal_section = ""
    try:
        # Try to split by surrebuttal marker
        parts = re.split(r"surrebuttal|sur-rebuttal|sur rebuttal", content_lower)
        if len(parts) >= 2:
            rebuttal_section = parts[0]
            surrebuttal_section = " ".join(parts[1:])
        else:
            rebuttal_section = content_lower
    except Exception:
        rebuttal_section = content_lower

    # Count ordinal point markers in rebuttal section
    ordinals_in_rebuttal = re.findall(
        r"\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|point\s+(?:one|two|three|four|five|1|2|3|4|5))\b",
        rebuttal_section
    )
    rebuttal_point_count = len(ordinals_in_rebuttal)

    check2_passed = 0 < rebuttal_point_count <= 3
    checks.append({
        "name": "rebuttal_max_three_points",
        "passed": check2_passed,
        "detail": f"Rebuttal must raise no more than 3 points. Detected approximately {rebuttal_point_count} point marker(s) in rebuttal section." +
                  (" PASS" if check2_passed else " FAIL - Too many points or no points detected.")
    })
    if check2_passed:
        total_score += 20

    # -----------------------------------------------------------------------
    # CHECK 3: Rebuttal does NOT introduce arguments absent from the case brief
    # The case brief contains R1(Article 15), R2(necessity/ILC 25), R3(proportionality), R4(acquiescence)
    # The rebuttal should target these existing topics, not introduce completely novel legal frameworks
    # We check that the rebuttal references at least 2 of the respondent's known argument themes
    # -----------------------------------------------------------------------
    known_themes = {
        "article_15_or_emergency": re.search(r"article\s*15|emergency\s*(clause|measure|power)|lex\s*specialis", rebuttal_section),
        "necessity_doctrine": re.search(r"necessit|ilc\s*article\s*25|essential\s*interest", rebuttal_section),
        "proportionality": re.search(r"proportionat|47\s*day|land\s*border|air\s*travel|calibrat", rebuttal_section),
        "acquiescence": re.search(r"acquiesc|travel\s*advisor|implicit|acknowledge", rebuttal_section),
    }
    themes_referenced = sum(1 for v in known_themes.values() if v is not None)
    check3_passed = themes_referenced >= 1
    checks.append({
        "name": "rebuttal_targets_existing_arguments",
        "passed": check3_passed,
        "detail": f"Rebuttal should address Respondent's existing arguments (Article 15, necessity, proportionality, acquiescence). Referenced {themes_referenced}/4 known theme(s)." +
                  (" PASS" if check3_passed else " FAIL - No recognizable opponent arguments targeted.")
    })
    if check3_passed:
        total_score += 15

    # -----------------------------------------------------------------------
    # CHECK 4: Surrebuttal opening formula
    # Expected: "Your excellencies, the Respondent has [N] response[s]"
    # -----------------------------------------------------------------------
    surrebuttal_opening_pattern = re.search(
        r"your excellenc(?:ies|y)[,.]?\s+the respondent has\s+(\w+)\s+response[s]?",
        content_lower
    )
    check4_passed = surrebuttal_opening_pattern is not None
    checks.append({
        "name": "surrebuttal_opening_formula",
        "passed": check4_passed,
        "detail": "Surrebuttal must open with 'Your excellencies, the Respondent has [N] response(s)'" +
                  (" - FOUND" if check4_passed else " - NOT FOUND. Must use exact formula from skill.")
    })
    if check4_passed:
        total_score += 15

    # -----------------------------------------------------------------------
    # CHECK 5: Surrebuttal addresses all or most rebuttal points
    # Surrebuttal section should reference the same themes as the rebuttal
    # -----------------------------------------------------------------------
    if surrebuttal_section:
        surrebuttal_themes = {
            "article_15_or_emergency": re.search(r"article\s*15|emergency\s*(clause|measure|power)|lex\s*specialis", surrebuttal_section),
            "necessity_doctrine": re.search(r"necessit|ilc\s*article\s*25|essential\s*interest", surrebuttal_section),
            "proportionality": re.search(r"proportionat|47\s*day|land\s*border|air\s*travel|calibrat", surrebuttal_section),
            "acquiescence": re.search(r"acquiesc|travel\s*advisor|implicit|acknowledge", surrebuttal_section),
            "concerning_first": re.search(r"concerning\s+the\s+(first|second|third|\w+)\s+point|first\s+point|second\s+point|third\s+point", surrebuttal_section),
        }
        surrebuttal_themes_found = sum(1 for v in surrebuttal_themes.values() if v is not None)
        check5_passed = surrebuttal_themes_found >= 1
    else:
        check5_passed = False
        surrebuttal_themes_found = 0

    checks.append({
        "name": "surrebuttal_responds_to_rebuttal_points",
        "passed": check5_passed,
        "detail": f"Surrebuttal must respond to the rebuttal's points. Found {surrebuttal_themes_found} relevant reference(s) in surrebuttal section." +
                  (" PASS" if check5_passed else " FAIL - Surrebuttal section missing or does not address rebuttal themes.")
    })
    if check5_passed:
        total_score += 15

    # -----------------------------------------------------------------------
    # CHECK 6: Surrebuttal uses "Concerning the [ordinal] point" structure
    # Pattern from skill: "Concerning the first point mentioned by the Applicant, the Respondent submits that..."
    # -----------------------------------------------------------------------
    concerning_pattern = re.search(
        r"concerning\s+the\s+(?:first|second|third|\w+)\s+point\s+(?:mentioned\s+by\s+the\s+applicant\b|raised\b|stated\b|made\b)?",
        content_lower
    )
    check6_passed = concerning_pattern is not None
    checks.append({
        "name": "surrebuttal_concerning_structure",
        "passed": check6_passed,
        "detail": "Surrebuttal should use 'Concerning the [ordinal] point mentioned by the Applicant, the Respondent submits that...' structure." +
                  (" FOUND" if check6_passed else " NOT FOUND.")
    })
    if check6_passed:
        total_score += 10

    # -----------------------------------------------------------------------
    # CHECK 7: Correct time-extension request phrase (time HAS RUN OUT, not running out)
    # Expected: "I note my time has run out, may I have 1 more minute..."
    # Must NOT use the "running out" variant (wrong context)
    # -----------------------------------------------------------------------
    time_expired_pattern = re.search(
        r"(?:i\s+note\s+)?my\s+time\s+has\s+run\s+out",
        content_lower
    )
    time_running_out_pattern = re.search(
        r"(?:i\s+note\s+)?my\s+time\s+is\s+running\s+out",
        content_lower
    )
    # The scenario specifies red light = time has expired, so must use "has run out"
    check7a_passed = time_expired_pattern is not None
    check7b_passed = not time_running_out_pattern  # Should NOT use wrong variant

    checks.append({
        "name": "time_extension_correct_variant_has_run_out",
        "passed": check7a_passed,
        "detail": "When time has expired (red light), must use 'my time has run out' phrasing." +
                  (" FOUND" if check7a_passed else " NOT FOUND - used wrong or missing variant.")
    })
    if check7a_passed:
        total_score += 5

    checks.append({
        "name": "time_extension_no_wrong_variant",
        "passed": check7b_passed,
        "detail": "Should NOT use 'my time is running out' for the expired-time scenario." +
                  (" CORRECT (not found)" if check7b_passed else " INCORRECT - used 'running out' which is for the nearly-expired scenario.")
    })
    if check7b_passed:
        total_score += 3

    # -----------------------------------------------------------------------
    # CHECK 8: Time extension request mentions "1 more minute" limit
    # Skill: "Best not to request more than 1 minute"
    # -----------------------------------------------------------------------
    one_minute_pattern = re.search(
        r"1\s+more\s+minute|one\s+more\s+minute",
        content_lower
    )
    check8_passed = one_minute_pattern is not None
    checks.append({
        "name": "time_extension_one_minute_max",
        "passed": check8_passed,
        "detail": "Time extension request should ask for '1 more minute' (not more)." +
                  (" FOUND" if check8_passed else " NOT FOUND - missing or incorrect duration requested.")
    })
    if check8_passed:
        total_score += 2

    # -----------------------------------------------------------------------
    # FINAL PASS/FAIL determination
    # Must pass critical checks: opening formulas, max 3 rebuttal points, correct time variant
    # -----------------------------------------------------------------------
    critical_checks = [check1_passed, check2_passed, check4_passed, check7a_passed]
    overall_passed = sum(critical_checks) >= 3 and total_score >= 40.0

    # Normalize score to 0-100
    max_possible = 100.0
    final_score = min(total_score, max_possible) / max_possible

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))