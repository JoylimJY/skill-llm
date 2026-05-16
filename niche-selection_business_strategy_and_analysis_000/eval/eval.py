import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output file ---
    report_files = list(workspace.rglob("niche_report.json"))
    
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "niche_report.json not found anywhere in workspace"}]
        }
    
    report_path = report_files[0]
    
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_parseable", "passed": False, "detail": f"Could not parse niche_report.json as JSON: {e}"}]
        }

    # Expected weighted scores (ground truth):
    # Weights: pain=0.25, advantage=0.20, market=0.20, monetization=0.15, competition=0.10, growth=0.10
    expected_scores = {
        1: 4.00,  # IOLTA trust accounting
        2: 4.05,  # Client intake immigration
        3: 3.75,  # Court deadline family law
        4: 3.70,  # AI contract review startup
        5: 3.55,  # Invoice follow-up
        6: 2.65,  # Document template marketplace
        7: 2.60,  # Deposition scheduling
        8: 4.10,  # Client portal estate planning
        9: 2.65,  # CLE tracking
        10: 3.50, # Flat-fee billing builder
    }
    
    # Top 3 by weighted score: 8 (4.10), 2 (4.05), 1 (4.00)
    expected_top3 = {8, 2, 1}
    
    # Kill check: niches failing 2+ validation checks are killed
    # Niche 8: 0 failed → SURVIVES
    # Niche 2: 2 failed → KILLED (exactly 2 = "fails 2+ checks")
    # Niche 1: 2 failed → KILLED (exactly 2 = "fails 2+ checks")
    # Only niche 8 survives
    expected_survivor = 8
    expected_killed = {1, 2}

    # ---- CHECK 1: All 10 niches scored ----
    try:
        scored_niches = report.get("scored_niches", report.get("all_niches", report.get("niches", [])))
        
        if isinstance(scored_niches, list):
            niche_count = len(scored_niches)
        elif isinstance(scored_niches, dict):
            niche_count = len(scored_niches)
        else:
            niche_count = 0
        
        all_10_present = niche_count == 10
        checks.append({
            "name": "all_10_niches_scored",
            "passed": all_10_present,
            "detail": f"Found {niche_count} scored niches, expected 10"
        })
    except Exception as e:
        checks.append({
            "name": "all_10_niches_scored",
            "passed": False,
            "detail": f"Error checking scored niches: {e}"
        })

    # ---- CHECK 2: Correct weighted scores (within tolerance of ±0.05) ----
    try:
        score_errors = []
        # Try to find individual niche scores in the report
        scored_niches_data = report.get("scored_niches", report.get("all_niches", report.get("niches", [])))
        
        if isinstance(scored_niches_data, list):
            for item in scored_niches_data:
                niche_id = item.get("id")
                weighted_score = item.get("weighted_score", item.get("score", item.get("total_score")))
                if niche_id in expected_scores and weighted_score is not None:
                    expected = expected_scores[niche_id]
                    if abs(float(weighted_score) - expected) > 0.06:
                        score_errors.append(f"Niche {niche_id}: got {weighted_score}, expected ~{expected}")
        elif isinstance(scored_niches_data, dict):
            for key, item in scored_niches_data.items():
                if isinstance(item, dict):
                    niche_id = item.get("id")
                    weighted_score = item.get("weighted_score", item.get("score", item.get("total_score")))
                    if niche_id in expected_scores and weighted_score is not None:
                        expected = expected_scores[niche_id]
                        if abs(float(weighted_score) - expected) > 0.06:
                            score_errors.append(f"Niche {niche_id}: got {weighted_score}, expected ~{expected}")
        
        weights_correct = len(score_errors) == 0
        # Partial credit: check top scores specifically
        # Look for niche 8 having highest score
        top_score_id = None
        if isinstance(scored_niches_data, list) and scored_niches_data:
            try:
                sorted_niches = sorted(scored_niches_data, 
                    key=lambda x: float(x.get("weighted_score", x.get("score", x.get("total_score", 0)))), 
                    reverse=True)
                top_score_id = sorted_niches[0].get("id") if sorted_niches else None
            except:
                pass
        
        checks.append({
            "name": "correct_weighted_scores",
            "passed": weights_correct,
            "detail": f"Score errors: {score_errors}" if score_errors else f"All found scores within tolerance. Top niche id: {top_score_id}"
        })
    except Exception as e:
        checks.append({
            "name": "correct_weighted_scores",
            "passed": False,
            "detail": f"Error validating weighted scores: {e}"
        })

    # ---- CHECK 3: Top 3 correctly identified ----
    try:
        top3 = report.get("top_3_candidates", report.get("top_candidates", report.get("top3", [])))
        
        if isinstance(top3, list):
            top3_ids = set()
            for item in top3:
                if isinstance(item, dict):
                    niche_id = item.get("id")
                    if niche_id:
                        top3_ids.add(int(niche_id))
                elif isinstance(item, int):
                    top3_ids.add(item)
            top3_correct = top3_ids == expected_top3
        else:
            top3_ids = set()
            top3_correct = False
        
        checks.append({
            "name": "top_3_correctly_identified",
            "passed": top3_correct,
            "detail": f"Top 3 IDs found: {top3_ids}, expected: {expected_top3}"
        })
    except Exception as e:
        checks.append({
            "name": "top_3_correctly_identified",
            "passed": False,
            "detail": f"Error checking top 3: {e}"
        })

    # ---- CHECK 4: Kill check correctly applied ----
    # Niches 1 and 2 fail 2+ validation checks → must be killed
    # Only niche 8 should survive
    try:
        # Look for the final/committed niche
        final_niche = report.get("final_niche", report.get("committed_niche", report.get("winner", report.get("selected_niche"))))
        
        # Also look for killed/rejected niches
        killed = report.get("killed_niches", report.get("rejected_niches", report.get("eliminated_niches", [])))
        
        final_niche_id = None
        if isinstance(final_niche, dict):
            final_niche_id = final_niche.get("id")
        elif isinstance(final_niche, int):
            final_niche_id = final_niche
        
        killed_ids = set()
        if isinstance(killed, list):
            for item in killed:
                if isinstance(item, dict):
                    kid = item.get("id")
                    if kid:
                        killed_ids.add(int(kid))
                elif isinstance(item, int):
                    killed_ids.add(item)
        
        # The kill check should eliminate niches 1 and 2 (each failed 2 checks)
        kill_check_correct = False
        kill_detail = ""
        
        if final_niche_id is not None:
            if int(final_niche_id) == expected_survivor:
                kill_check_correct = True
                kill_detail = f"Correctly selected niche {expected_survivor} as sole survivor after kill check"
            else:
                kill_detail = f"Final niche is {final_niche_id}, expected niche {expected_survivor}"
        elif killed_ids:
            if expected_killed.issubset(killed_ids):
                kill_check_correct = True
                kill_detail = f"Correctly killed niches {killed_ids} which includes required kills {expected_killed}"
            else:
                kill_detail = f"Killed niches {killed_ids} but expected to kill {expected_killed}"
        else:
            # Fall back: check full report text for evidence
            report_text = json.dumps(report).lower()
            niche2_killed = any(phrase in report_text for phrase in ["niche 2 killed", "niche_2 killed", "killed.*niche 2", "niche 2.*fail", "immigration.*kill"])
            niche1_killed = any(phrase in report_text for phrase in ["niche 1 killed", "niche_1 killed", "killed.*niche 1", "niche 1.*fail", "iolta.*kill"])
            kill_detail = f"Could not find structured kill data. Niche1 evidence: {niche1_killed}, Niche2 evidence: {niche2_killed}"
        
        checks.append({
            "name": "kill_check_correctly_applied",
            "passed": kill_check_correct,
            "detail": kill_detail
        })
    except Exception as e:
        checks.append({
            "name": "kill_check_correctly_applied",
            "passed": False,
            "detail": f"Error checking kill rule: {e}"
        })

    # ---- CHECK 5: Positioning statement present ----
    try:
        positioning = report.get("positioning_statement", report.get("position_statement", report.get("positioning", "")))
        
        if isinstance(positioning, dict):
            positioning_text = positioning.get("statement", positioning.get("text", str(positioning)))
        else:
            positioning_text = str(positioning) if positioning else ""
        
        has_positioning = len(positioning_text.strip()) > 50
        checks.append({
            "name": "positioning_statement_present",
            "passed": has_positioning,
            "detail": f"Positioning statement length: {len(positioning_text)} chars. Preview: {positioning_text[:100]}"
        })
    except Exception as e:
        checks.append({
            "name": "positioning_statement_present",
            "passed": False,
            "detail": f"Error checking positioning statement: {e}"
        })

    # ---- CHECK 6: Positioning uses Who+What+Why formula ----
    try:
        positioning = report.get("positioning_statement", report.get("position_statement", report.get("positioning", "")))
        if isinstance(positioning, dict):
            positioning_text = positioning.get("statement", positioning.get("text", str(positioning)))
        else:
            positioning_text = str(positioning) if positioning else ""
        
        text_lower = positioning_text.lower()
        
        # Must reference estate planning or solo attorneys (niche 8)
        targets_right_niche = any(phrase in text_lower for phrase in [
            "estate planning", "estate attorney", "estate plan", "solo attorney", "estate"
        ])
        
        # Must contain "struggling with" or similar problem framing
        has_problem_framing = any(phrase in text_lower for phrase in [
            "struggling with", "struggle with", "who struggle", "dealing with", "faced with"
        ])
        
        # Must contain "who need" or outcome framing
        has_outcome_framing = any(phrase in text_lower for phrase in [
            "who need", "need ", "in order to", "so they can", "to achieve"
        ])
        
        # Must contain gap framing ("current solutions", "fall short", "because", "existing")
        has_gap_framing = any(phrase in text_lower for phrase in [
            "current solution", "fall short", "because", "existing tool", "existing solution",
            "generic", "too heavy", "don't", "do not", "lack", "fail to"
        ])
        
        formula_components = [targets_right_niche, has_problem_framing, has_outcome_framing, has_gap_framing]
        formula_score = sum(formula_components)
        formula_correct = formula_score >= 3
        
        checks.append({
            "name": "positioning_uses_who_what_why_formula",
            "passed": formula_correct,
            "detail": (
                f"Formula components: targets_right_niche={targets_right_niche}, "
                f"problem_framing={has_problem_framing}, outcome_framing={has_outcome_framing}, "
                f"gap_framing={has_gap_framing}. Score: {formula_score}/4"
            )
        })
    except Exception as e:
        checks.append({
            "name": "positioning_uses_who_what_why_formula",
            "passed": False,
            "detail": f"Error checking positioning formula: {e}"
        })

    # ---- CHECK 7: Positioning statement is ≤ 2 sentences ----
    try:
        positioning = report.get("positioning_statement", report.get("position_statement", report.get("positioning", "")))
        if isinstance(positioning, dict):
            positioning_text = positioning.get("statement", positioning.get("text", str(positioning)))
        else:
            positioning_text = str(positioning) if positioning else ""
        
        # Count sentences (split on . ! ? but be lenient about abbreviations)
        sentences = [s.strip() for s in re.split(r'[.!?]+', positioning_text) if len(s.strip()) > 10]
        sentence_count = len(sentences)
        within_limit = sentence_count <= 2
        
        checks.append({
            "name": "positioning_within_2_sentences",
            "passed": within_limit,
            "detail": f"Detected {sentence_count} sentences in positioning statement. Limit is 2."
        })
    except Exception as e:
        checks.append({
            "name": "positioning_within_2_sentences",
            "passed": False,
            "detail": f"Error checking sentence count: {e}"
        })

    # ---- CHECK 8: Correct weights evidence in report ----
    # The report should show evidence of the correct weighting (25/20/20/15/10/10)
    try:
        report_text = json.dumps(report)
        
        weight_patterns = [
            (r'0\.25|25%|25 %', "pain_weight_25pct"),
            (r'0\.20|20%|20 %', "advantage_market_weight_20pct"),
            (r'0\.15|15%|15 %', "monetization_weight_15pct"),
            (r'0\.10|10%|10 %', "competition_growth_weight_10pct"),
        ]
        
        weights_found = []
        for pattern, label in weight_patterns:
            if re.search(pattern, report_text):
                weights_found.append(label)
        
        weights_evidence = len(weights_found) >= 3
        checks.append({
            "name": "correct_weights_used_in_scoring",
            "passed": weights_evidence,
            "detail": f"Weight evidence found: {weights_found}"
        })
    except Exception as e:
        checks.append({
            "name": "correct_weights_used_in_scoring",
            "passed": False,
            "detail": f"Error checking weights: {e}"
        })

    # ---- Final Score Calculation ----
    # Weight the checks
    check_weights = {
        "all_10_niches_scored": 0.10,
        "correct_weighted_scores": 0.20,
        "top_3_correctly_identified": 0.15,
        "kill_check_correctly_applied": 0.20,
        "positioning_statement_present": 0.05,
        "positioning_uses_who_what_why_formula": 0.15,
        "positioning_within_2_sentences": 0.05,
        "correct_weights_used_in_scoring": 0.10,
    }
    
    total_score = 0.0
    for check in checks:
        weight = check_weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += weight
    
    # Must pass kill check and positioning formula at minimum to pass overall
    critical_checks = ["kill_check_correctly_applied", "correct_weighted_scores", "top_3_correctly_identified"]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and total_score >= 0.65
    
    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))