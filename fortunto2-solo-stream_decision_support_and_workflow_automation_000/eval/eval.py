import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    
    # =========================================================
    # CHECK 1: File exists in docs/decisions/ with correct name
    # =========================================================
    target_filename = "2024-06-12-novaBiomics-pivot-decision.md"
    decisions_dir = workspace / "docs" / "decisions"
    
    # Search for the file
    found_files = list(workspace.rglob(target_filename))
    # Also accept case-insensitive or slight naming variation but prefer exact
    exact_match = decisions_dir / target_filename
    
    file_found = exact_match.exists()
    if not file_found and found_files:
        # Accept if found anywhere but penalize location
        target_file = found_files[0]
        file_found = True
        in_correct_dir = str(found_files[0].parent).endswith("docs/decisions")
    else:
        target_file = exact_match
        in_correct_dir = file_found
    
    checks.append({
        "name": "decision_file_exists",
        "passed": file_found,
        "detail": f"File '{target_filename}' {'found' if file_found else 'NOT found'} in workspace."
    })
    
    checks.append({
        "name": "file_in_correct_directory",
        "passed": in_correct_dir,
        "detail": f"File must be in docs/decisions/. {'Correct.' if in_correct_dir else 'File found elsewhere or missing.'}"
    })
    
    if not file_found:
        # All remaining checks fail
        for name in ["has_stream_framework_label", "has_date_header", "has_all_six_layers_in_table",
                     "layer_names_correct", "scores_are_numeric", "overall_score_line_present",
                     "verdict_correct_threshold", "has_recommendation_section", "has_next_actions_section",
                     "decision_topic_relevant"]:
            checks.append({"name": name, "passed": False, "detail": "File not found — cannot evaluate."})
        total = sum(1 for c in checks if c["passed"])
        return {"passed": False, "score": total / len(checks), "checks": checks}
    
    # Read file content
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # =========================================================
    # CHECK 3: Contains framework label "STREAM 6-layer"
    # =========================================================
    has_stream_label = bool(re.search(r'STREAM\s+6-layer', content, re.IGNORECASE))
    checks.append({
        "name": "has_stream_framework_label",
        "passed": has_stream_label,
        "detail": f"'STREAM 6-layer' framework label {'found' if has_stream_label else 'NOT found'} in document."
    })
    
    # =========================================================
    # CHECK 4: Contains a date header (2024-06-12 or "today")
    # =========================================================
    has_date = bool(re.search(r'2024-06-12|Date.*2024', content, re.IGNORECASE))
    # Also accept any date-like string in a Date field
    has_date_field = bool(re.search(r'\*\*Date:\*\*|\*\*date:\*\*|Date:', content))
    checks.append({
        "name": "has_date_header",
        "passed": has_date or has_date_field,
        "detail": f"Date field {'found' if (has_date or has_date_field) else 'NOT found'} in document."
    })
    
    # =========================================================
    # CHECK 5: All 6 STREAM layers appear in a markdown table
    # =========================================================
    required_layers = [
        "Epistemological",
        "Temporal",
        "Action",
        "Stakes",
        "Social",
        "Meta"
    ]
    
    layers_found = {layer: bool(re.search(re.escape(layer), content, re.IGNORECASE)) for layer in required_layers}
    all_layers_present = all(layers_found.values())
    missing_layers = [l for l, found in layers_found.items() if not found]
    
    checks.append({
        "name": "has_all_six_layers_in_table",
        "passed": all_layers_present,
        "detail": f"All 6 STREAM layers {'present' if all_layers_present else 'MISSING: ' + str(missing_layers)}."
    })
    
    # =========================================================
    # CHECK 6: Layer names match SKILL.md exactly (not generic)
    # =========================================================
    exact_layer_names_correct = (
        "Epistemological" in content and
        "Temporal" in content and
        "Action" in content and
        "Stakes" in content and
        "Social" in content and
        "Meta" in content
    )
    checks.append({
        "name": "layer_names_correct",
        "passed": exact_layer_names_correct,
        "detail": "All proprietary STREAM layer names (Epistemological, Temporal, Action, Stakes, Social, Meta) must appear verbatim."
    })
    
    # =========================================================
    # CHECK 7: Scores are numeric (X/10 format) for each layer
    # =========================================================
    score_pattern = re.findall(r'\b([0-9]|10)\s*/\s*10', content)
    # Need at least 6 scores (one per layer) + 1 overall
    has_enough_scores = len(score_pattern) >= 6
    checks.append({
        "name": "scores_are_numeric",
        "passed": has_enough_scores,
        "detail": f"Found {len(score_pattern)} numeric X/10 scores. Need at least 6 (one per layer)."
    })
    
    # =========================================================
    # CHECK 8: Overall STREAM Score line present
    # =========================================================
    overall_score_match = re.search(
        r'Overall\s+STREAM\s+Score[:\s]+([0-9]+(?:\.[0-9]+)?)\s*/\s*10',
        content, re.IGNORECASE
    )
    has_overall_score = overall_score_match is not None
    checks.append({
        "name": "overall_score_line_present",
        "passed": has_overall_score,
        "detail": f"'Overall STREAM Score: X/10' line {'found' if has_overall_score else 'NOT found'}."
    })
    
    # =========================================================
    # CHECK 9: Verdict matches proprietary thresholds
    # GO > 7, PAUSE 5-7, NO-GO < 5
    # Based on scenario analysis, NovaBiomics pivot is strongly positive
    # Score should be >= 7 → GO verdict
    # We check that the verdict is present and consistent with the score
    # =========================================================
    verdict_match = re.search(r'\b(GO|PAUSE|NO-GO|NO GO)\b', content, re.IGNORECASE)
    has_verdict = verdict_match is not None
    
    verdict_threshold_correct = False
    verdict_detail = "No verdict found."
    
    if has_verdict and has_overall_score:
        try:
            overall_score = float(overall_score_match.group(1))
            verdict_text = verdict_match.group(1).upper().replace(" ", "-")
            
            if overall_score > 7:
                expected_verdict = "GO"
            elif overall_score >= 5:
                expected_verdict = "PAUSE"
            else:
                expected_verdict = "NO-GO"
            
            # Normalize: "NO GO" == "NO-GO"
            verdict_normalized = verdict_text.replace(" ", "-")
            # But also check: "GO" should not match "NO-GO"
            # Find the verdict closest to the overall score line
            verdict_in_score_line = re.search(
                r'Overall\s+STREAM\s+Score.*?(GO|PAUSE|NO-GO|NO\s*GO)',
                content, re.IGNORECASE
            )
            if verdict_in_score_line:
                line_verdict = verdict_in_score_line.group(1).upper().replace(" ", "-")
                verdict_threshold_correct = (line_verdict == expected_verdict) or \
                    (expected_verdict == "GO" and line_verdict == "GO")
                verdict_detail = f"Score={overall_score}, Expected={expected_verdict}, Found in score line={line_verdict}. {'✓' if verdict_threshold_correct else '✗'}"
            else:
                # Accept if verdict appears anywhere and is consistent with score
                verdict_threshold_correct = (verdict_normalized == expected_verdict) or \
                    (expected_verdict == "GO" and verdict_normalized == "GO")
                verdict_detail = f"Score={overall_score}, Expected={expected_verdict}, Found verdict={verdict_normalized}. Score line not found."
        except Exception as e:
            verdict_detail = f"Error parsing score/verdict: {e}"
    elif has_verdict and not has_overall_score:
        verdict_detail = "Verdict found but overall score line missing — cannot validate threshold."
    
    checks.append({
        "name": "verdict_correct_threshold",
        "passed": verdict_threshold_correct,
        "detail": verdict_detail
    })
    
    # =========================================================
    # CHECK 10: Has ### Recommendation section
    # =========================================================
    has_recommendation = bool(re.search(r'###\s+Recommendation', content, re.IGNORECASE))
    checks.append({
        "name": "has_recommendation_section",
        "passed": has_recommendation,
        "detail": f"'### Recommendation' section {'found' if has_recommendation else 'NOT found'}."
    })
    
    # =========================================================
    # CHECK 11: Has ### Next Actions section with numbered items
    # =========================================================
    has_next_actions = bool(re.search(r'###\s+Next\s+Actions', content, re.IGNORECASE))
    has_numbered_actions = bool(re.search(r'###\s+Next\s+Actions.*?(\n\s*\d+\.)', content, re.IGNORECASE | re.DOTALL))
    checks.append({
        "name": "has_next_actions_section",
        "passed": has_next_actions and has_numbered_actions,
        "detail": f"'### Next Actions' with numbered items: {'found' if (has_next_actions and has_numbered_actions) else 'NOT found or no numbered items'}."
    })
    
    # =========================================================
    # CHECK 12: Decision topic is relevant (NovaBiomics / pivot / clinical)
    # =========================================================
    topic_keywords = ["pivot", "clinical", "novaBiomics", "NovaBiomics", "B2B", "b2b", "enterprise", "CRO", "PulseCheck"]
    topic_found = any(kw.lower() in content.lower() for kw in topic_keywords)
    checks.append({
        "name": "decision_topic_relevant",
        "passed": topic_found,
        "detail": f"Decision topic relevance (pivot/clinical/NovaBiomics): {'confirmed' if topic_found else 'NOT found — may be a generic template'}."
    })
    
    # =========================================================
    # OVERALL SCORING
    # =========================================================
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "decision_file_exists",
        "file_in_correct_directory", 
        "has_stream_framework_label",
        "has_all_six_layers_in_table",
        "layer_names_correct",
        "scores_are_numeric",
        "verdict_correct_threshold",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))