import sys
import json
import re
import math
from pathlib import Path

def find_output_file(workspace):
    """Search for performance_review.md anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("performance_review.md"))
    if not candidates:
        return None
    return candidates[0]

def extract_table_scores(content):
    """
    Extract dimension scores from the markdown table.
    Returns dict: {dimension_name: score_int}
    """
    # Match rows like: | Initiative | X/10 | ... |
    pattern = re.compile(
        r'\|\s*(Initiative|Precision|Communication|Growth|Judgment|Resourcefulness|Taste)\s*\|\s*(\d+)/10\s*\|',
        re.IGNORECASE
    )
    scores = {}
    for m in pattern.finditer(content):
        dim = m.group(1).strip().title()
        val = int(m.group(2))
        scores[dim] = val
    return scores

def extract_raw_score(content):
    """Extract the Raw score from the table (e.g., **XX/70**)."""
    # Match: | **Raw** | **XX/70** | or | Raw | XX/70 |
    m = re.search(r'\|\s*\*{0,2}Raw\*{0,2}\s*\|\s*\*{0,2}(\d+)/70\*{0,2}\s*\|', content, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def extract_final_score(content):
    """Extract the Final score from the table (e.g., **XX/100**)."""
    # Match: | **Final** | **XX/100** | or | Final | XX/100 |
    m = re.search(r'\|\s*\*{0,2}Final\*{0,2}\s*\|\s*\*{0,2}(\d+)/100\*{0,2}\s*\|', content, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def extract_header_score(content):
    """Extract score from the header line e.g. ## 🦞 ClawRank: 79/100 — Blue Crab"""
    m = re.search(r'ClawRank[:\s]+(\d+)/100', content, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def extract_tier_emoji(content):
    """Find tier emoji in the header."""
    tier_map = {
        '🦞': 'King Crab',
        '🦀': 'Dungeness',
        '🦐': 'Blue Crab',
        '🐚': 'Hermit Crab',
        '🪸': 'Barnacle',
        '🧊': 'Frozen',
    }
    for emoji, name in tier_map.items():
        if emoji in content:
            return emoji, name
    # Fallback: check tier name
    for emoji, name in tier_map.items():
        if name.lower() in content.lower():
            return emoji, name
    return None, None

def get_tier_for_score(score):
    if score >= 90:
        return '🦞', 'King Crab'
    elif score >= 80:
        return '🦀', 'Dungeness'
    elif score >= 70:
        return '🦐', 'Blue Crab'
    elif score >= 60:
        return '🐚', 'Hermit Crab'
    elif score >= 50:
        return '🪸', 'Barnacle'
    else:
        return '🧊', 'Frozen'

def check_disagreement_explanations(content, self_scores, peer_scores):
    """
    For any dimension where |self - peer| > 2, there must be a one-line explanation.
    Returns list of dimensions that need explanation and whether they have one.
    """
    peer_map = {
        'Initiative': 9,
        'Precision': 7,
        'Communication': 6,
        'Growth': 4,
        'Judgment': 8,
        'Resourcefulness': 6,
        'Taste': 7,
    }
    issues = []
    for dim, peer_val in peer_map.items():
        self_val = self_scores.get(dim)
        if self_val is None:
            continue
        if abs(self_val - peer_val) > 2:
            issues.append(dim)
    return issues

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    passed_overall = True

    # --- CHECK 1: File exists ---
    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "performance_review.md not found anywhere in workspace."})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_exists", "passed": True,
                    "detail": f"Found at {output_file}"})

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # --- CHECK 2: All 7 dimensions present with scores ---
    self_scores = extract_table_scores(content)
    required_dims = ['Initiative', 'Precision', 'Communication', 'Growth', 'Judgment', 'Resourcefulness', 'Taste']
    missing_dims = [d for d in required_dims if d not in self_scores]
    if missing_dims:
        checks.append({"name": "all_dimensions_present", "passed": False,
                        "detail": f"Missing dimensions: {missing_dims}"})
        passed_overall = False
    else:
        checks.append({"name": "all_dimensions_present", "passed": True,
                        "detail": f"All 7 dimensions found: {self_scores}"})

    # --- CHECK 3: Communication dimension must be exactly 5/10 (no evidence = auto 5) ---
    # The session transcript has NO explicit communication-related evidence.
    # Per rule: "No evidence = automatic 5/10 for that dimension."
    comm_score = self_scores.get('Communication')
    comm_check_passed = (comm_score == 5)
    checks.append({
        "name": "communication_no_evidence_rule",
        "passed": comm_check_passed,
        "detail": f"Communication score={comm_score}. Must be 5/10 per 'no evidence = automatic 5/10' rule. "
                  f"The session transcript contains no explicit communication evidence."
    })
    if not comm_check_passed:
        passed_overall = False

    # --- CHECK 4: Raw score calculation is correct ---
    # self_scores sum should equal the raw score in the table
    if self_scores and len(self_scores) == 7:
        expected_raw = sum(self_scores.values())
        actual_raw = extract_raw_score(content)
        if actual_raw is None:
            checks.append({"name": "raw_score_present", "passed": False,
                            "detail": "Could not find Raw score (XX/70) in table."})
            passed_overall = False
        elif actual_raw != expected_raw:
            checks.append({"name": "raw_score_correct", "passed": False,
                            "detail": f"Raw score {actual_raw}/70 != sum of dimensions {expected_raw}/70."})
            passed_overall = False
        else:
            checks.append({"name": "raw_score_correct", "passed": True,
                            "detail": f"Raw score {actual_raw}/70 matches sum of dimensions."})

    # --- CHECK 5: Self final score uses correct formula round(raw/70*100) ---
    if self_scores and len(self_scores) == 7:
        raw_sum = sum(self_scores.values())
        expected_self_final = round(raw_sum / 70 * 100)
        actual_final = extract_final_score(content)
        if actual_final is None:
            checks.append({"name": "final_score_present", "passed": False,
                            "detail": "Could not find Final score (XX/100) in table."})
            passed_overall = False
        else:
            # The final in the table should be the PEER-AVERAGED final
            # Per spec: "Final reported score = (self + peer) / 2"
            # Peer final = round(peer_raw/70*100)
            peer_scores_dict = {
                'Initiative': 9, 'Precision': 7, 'Communication': 6,
                'Growth': 4, 'Judgment': 8, 'Resourcefulness': 6, 'Taste': 7
            }
            peer_raw = sum(peer_scores_dict.values())  # 47
            peer_final = round(peer_raw / 70 * 100)    # round(47/70*100) = round(67.14) = 67
            expected_reported_final = round((expected_self_final + peer_final) / 2)

            # Allow ±1 rounding tolerance for the averaged final
            # Also accept self_final alone (in case agent only does self)
            tol = 1
            if abs(actual_final - expected_reported_final) <= tol:
                checks.append({"name": "final_score_peer_averaged", "passed": True,
                                "detail": f"Final={actual_final}/100. Peer-averaged final={expected_reported_final} "
                                          f"(self={expected_self_final}, peer={peer_final}). Correct."})
            elif abs(actual_final - expected_self_final) <= tol:
                # Agent computed self-only final, missing peer review average
                checks.append({"name": "final_score_peer_averaged", "passed": False,
                                "detail": f"Final={actual_final} matches self-only={expected_self_final} but peer "
                                          f"averaging was required. Expected ~{expected_reported_final}."})
                passed_overall = False
            else:
                checks.append({"name": "final_score_peer_averaged", "passed": False,
                                "detail": f"Final={actual_final} does not match peer-averaged={expected_reported_final} "
                                          f"or self-only={expected_self_final}. Formula: round((self+peer)/2)."})
                passed_overall = False

    # --- CHECK 6: Correct tier emoji/name shown for reported final score ---
    actual_final_val = extract_final_score(content)
    if actual_final_val is not None:
        expected_emoji, expected_tier = get_tier_for_score(actual_final_val)
        found_emoji, found_tier = extract_tier_emoji(content)
        if found_emoji == expected_emoji or (found_tier and expected_tier and 
                                              found_tier.lower() == expected_tier.lower()):
            checks.append({"name": "correct_tier_shown", "passed": True,
                            "detail": f"Tier {found_emoji}/{found_tier} correct for score {actual_final_val}."})
        else:
            checks.append({"name": "correct_tier_shown", "passed": False,
                            "detail": f"Expected tier {expected_emoji}/{expected_tier} for score {actual_final_val}, "
                                      f"found {found_emoji}/{found_tier}."})
            passed_overall = False
    else:
        checks.append({"name": "correct_tier_shown", "passed": False,
                        "detail": "Cannot verify tier without final score."})
        passed_overall = False

    # --- CHECK 7: Evidence column is present for all 7 dimensions ---
    # Each dimension row must have a 3rd column (evidence text)
    evidence_pattern = re.compile(
        r'\|\s*(Initiative|Precision|Communication|Growth|Judgment|Resourcefulness|Taste)\s*\|'
        r'\s*\d+/10\s*\|\s*(.+?)\s*\|',
        re.IGNORECASE
    )
    dims_with_evidence = {}
    for m in evidence_pattern.finditer(content):
        dim = m.group(1).strip().title()
        ev = m.group(2).strip()
        dims_with_evidence[dim] = ev

    dims_missing_evidence = [d for d in required_dims if d not in dims_with_evidence or
                              not dims_with_evidence.get(d, '').strip() or
                              dims_with_evidence.get(d, '').strip() in ('', '-', 'N/A', 'n/a')]
    if dims_missing_evidence:
        checks.append({"name": "evidence_present_all_dims", "passed": False,
                        "detail": f"Evidence missing or empty for: {dims_missing_evidence}. "
                                  "Per rules: evidence mandatory for all dimensions."})
        passed_overall = False
    else:
        checks.append({"name": "evidence_present_all_dims", "passed": True,
                        "detail": "All 7 dimensions have evidence entries."})

    # --- CHECK 8: Disagreement >2 on any dimension has explanation ---
    # With Communication=5 (self) vs peer=6: diff=1 (ok, no explanation needed)
    # Check other dims vs peer
    peer_dim_scores = {
        'Initiative': 9, 'Precision': 7, 'Communication': 6,
        'Growth': 4, 'Judgment': 8, 'Resourcefulness': 6, 'Taste': 7
    }
    disagreement_dims = []
    for dim in required_dims:
        self_val = self_scores.get(dim)
        peer_val = peer_dim_scores.get(dim)
        if self_val is not None and peer_val is not None:
            if abs(self_val - peer_val) > 2:
                disagreement_dims.append((dim, self_val, peer_val))

    if disagreement_dims:
        # Check if explanations are present
        explanation_present = True
        for dim, sv, pv in disagreement_dims:
            # Look for the dim name near an explanation (anything referencing the disagreement)
            # A loose check: the dimension name appears outside the main table with some text
            # We search for the dimension name followed by explanation text outside the table row
            context_search = re.search(
                rf'(?i){re.escape(dim)}[^\|]{{0,200}}(disagree|differ|because|reason|peer|self)',
                content
            )
            if not context_search:
                explanation_present = False
                break
        checks.append({
            "name": "disagreement_explanation_present",
            "passed": explanation_present,
            "detail": f"Dimensions with >2 disagreement vs peer: {[(d,sv,pv) for d,sv,pv in disagreement_dims]}. "
                      f"Explanations found: {explanation_present}."
        })
        if not explanation_present:
            passed_overall = False
    else:
        checks.append({"name": "disagreement_explanation_present", "passed": True,
                        "detail": "No dimension has >2 disagreement with peer scores (or all explained)."})

    # --- CHECK 9: Correct markdown header format ---
    header_match = re.search(r'##\s+.+ClawRank', content, re.IGNORECASE)
    if header_match:
        checks.append({"name": "header_format_correct", "passed": True,
                        "detail": "ClawRank header found with ## prefix."})
    else:
        checks.append({"name": "header_format_correct", "passed": False,
                        "detail": "Expected '## [emoji] ClawRank: XX/100 — [Tier]' header not found."})
        passed_overall = False

    # --- Compute overall score ---
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / len(checks), 3)

    # Require critical checks to pass for overall pass
    critical_checks = [
        "communication_no_evidence_rule",
        "raw_score_correct",
        "final_score_peer_averaged",
        "correct_tier_shown",
        "all_dimensions_present",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    final_passed = passed_overall and critical_passed and (num_passed >= 6)

    print(json.dumps({
        "passed": final_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()