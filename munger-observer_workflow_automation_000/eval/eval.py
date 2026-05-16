import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # --- Locate the output file ---
    # Agent is told to save as "munger_review_2025-06-12.md" or find it
    target_date = "2025-06-12"
    
    # Search for the output file — could be named munger_review_2025-06-12.md
    candidates = list(workspace.rglob("munger_review_2025-06-12.md"))
    
    output_text = None
    file_found = False
    
    if candidates:
        file_found = True
        output_text = candidates[0].read_text(encoding="utf-8")
    
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found output file at: {candidates[0]}" if file_found else "No file named 'munger_review_2025-06-12.md' found anywhere in workspace."
    })
    
    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # --- Check 1: Header format with emoji and exact date ---
    header_pattern = r"🧠\s+\*\*Munger Observer\*\*\s*—\s*June\s+12,?\s*2025|🧠\s+\*\*Munger Observer\*\*\s*—\s*2025-06-12"
    header_match = bool(re.search(header_pattern, output_text, re.IGNORECASE))
    checks.append({
        "name": "header_format_correct",
        "passed": header_match,
        "detail": f"Header must match '🧠 **Munger Observer** — [Date]' pattern. Found: {output_text[:100].strip()!r}"
    })

    # --- Check 2: Closing quote is present and correctly attributed ---
    # The exact quote: "Invert, always invert." — Carl Jacobi (Munger's favorite)
    # Must have "Invert, always invert" AND some reference to Carl Jacobi or just "Invert, always invert."
    invert_quote = bool(re.search(r"Invert,\s+always\s+invert", output_text, re.IGNORECASE))
    checks.append({
        "name": "closing_invert_quote_present",
        "passed": invert_quote,
        "detail": "Output must contain the closing quote 'Invert, always invert.' as specified in the format."
    })

    # --- Check 3: Carl Jacobi attribution ---
    jacobi_attr = bool(re.search(r"Carl\s+Jacobi", output_text))
    checks.append({
        "name": "carl_jacobi_attribution",
        "passed": jacobi_attr,
        "detail": "The closing quote must be attributed to Carl Jacobi — a proprietary detail from the SKILL.md that generic agents often miss."
    })

    # --- Check 4: At least one named mental model is explicitly applied ---
    mental_models = [
        r"Opportunity Cost",
        r"Second.Order",
        r"Inversion",
        r"Incentive",
        r"Sunk Cost",
        r"Confirmation Bias",
        r"Availability Bias",
        r"Social Proof",
        r"Circle of Competence",
        r"Margin of Safety",
    ]
    found_models = [m for m in mental_models if re.search(m, output_text, re.IGNORECASE)]
    at_least_one_model = len(found_models) >= 1
    checks.append({
        "name": "at_least_one_named_mental_model",
        "passed": at_least_one_model,
        "detail": f"Must explicitly name at least one Munger mental model. Found: {found_models}"
    })

    # --- Check 5: Insights are actually grounded in the memory file content ---
    # The memory file contains very specific decisions; check that at least one is referenced
    memory_anchors = [
        r"SSO|single.sign.on",
        r"postmortem",
        r"analytics.pipeline|refactor",
        r"dark.mode",
        r"Datadog|competitor",
        r"CSV.export|rate.limit",
        r"data.vendor|partnership",
        r"webhook",
        r"sunk.cost|40\s*%",
    ]
    grounded_refs = [a for a in memory_anchors if re.search(a, output_text, re.IGNORECASE)]
    is_grounded = len(grounded_refs) >= 1
    checks.append({
        "name": "insights_grounded_in_memory_file",
        "passed": is_grounded,
        "detail": f"Insights must reference actual decisions from memory/2025-06-12.md. Matched: {grounded_refs}"
    })

    # --- Check 6: Output is NOT just the fallback "All clear" message when there ARE issues ---
    # The memory file clearly has cognitive traps; "All clear" would be wrong
    all_clear = bool(re.search(r"All clear.*no cognitive landmines", output_text, re.IGNORECASE))
    not_all_clear = not all_clear
    checks.append({
        "name": "not_false_all_clear",
        "passed": not_all_clear,
        "detail": "The memory file contains clear cognitive traps. Returning 'All clear' is factually incorrect and fails the review."
    })

    # --- Check 7: Insight count is 1-2 (not a wall of text with 5+ model applications) ---
    # Count bold-labeled insight sections: lines starting with **Something:
    insight_headers = re.findall(r"\*\*[A-Za-z\s\-]+(?:Alert|Check|Warning|Trap|Bias|Cost|Analysis|Note|Review|Concern).*?\*\*", output_text)
    # Also accept plain bold lines that are insight titles
    bold_lines = re.findall(r"^\*\*.+\*\*", output_text, re.MULTILINE)
    total_insight_signals = len(insight_headers) + len([b for b in bold_lines if b not in insight_headers])
    
    # 1-2 insights is ideal; we check that the output is NOT empty content-wise
    has_substantive_content = len(output_text.strip()) > 100
    checks.append({
        "name": "has_substantive_insight_content",
        "passed": has_substantive_content,
        "detail": f"Output must contain substantive insight content (>100 chars). Length: {len(output_text.strip())}"
    })

    # --- Check 8: Correct date used in header (must be 2025-06-12 or June 12, 2025) ---
    date_in_header = bool(re.search(r"2025-06-12|June\s+12,?\s*2025", output_text))
    checks.append({
        "name": "correct_date_in_header",
        "passed": date_in_header,
        "detail": f"Header must reference the review date 2025-06-12 or 'June 12, 2025'. Output start: {output_text[:200]!r}"
    })

    # --- Compute final score ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Hard requirements: file must exist, header must be correct, quote must be present, grounded insights
    hard_requirements = [
        "output_file_exists",
        "header_format_correct",
        "closing_invert_quote_present",
        "carl_jacobi_attribution",
        "insights_grounded_in_memory_file",
        "not_false_all_clear",
    ]
    hard_passed = all(
        c["passed"] for c in checks if c["name"] in hard_requirements
    )

    overall_passed = hard_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    try:
        result = evaluate(sys.argv[1])
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Evaluator crashed: {e}"}]
        }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))