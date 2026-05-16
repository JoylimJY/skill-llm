import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # --- Locate the review file ---
    review_files = list(workspace.rglob("proposal_review.md"))
    
    if not review_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [
                {"name": "file_exists", "passed": False, "detail": "Could not find 'proposal_review.md' anywhere in workspace."}
            ]
        }
    
    review_file = review_files[0]
    try:
        content = review_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [
                {"name": "file_readable", "passed": False, "detail": f"File found but could not be read: {e}"}
            ]
        }

    # Check 1: Top-level header "## Caring Review"
    has_header = bool(re.search(r"##\s+Caring Review", content))
    checks.append({
        "name": "has_caring_review_header",
        "passed": has_header,
        "detail": "Found '## Caring Review' header." if has_header else "Missing required '## Caring Review' header."
    })

    # Check 2: Verdict line present and uses correct format
    verdict_match = re.search(r"\*\*Verdict:\*\*\s*(.+)", content)
    verdict_present = bool(verdict_match)
    checks.append({
        "name": "has_verdict_line",
        "passed": verdict_present,
        "detail": f"Found Verdict line: '{verdict_match.group(0).strip()}'" if verdict_present else "Missing '**Verdict:**' line."
    })

    # Check 3: Verdict must be exactly "Half-Assed" (the proposal is clearly half-assed)
    verdict_value = verdict_match.group(1).strip() if verdict_match else ""
    verdict_correct = "Half-Assed" in verdict_value
    checks.append({
        "name": "verdict_is_half_assed",
        "passed": verdict_correct,
        "detail": f"Verdict correctly identified as 'Half-Assed'." if verdict_correct else (
            f"Expected verdict 'Half-Assed' for this clearly inadequate proposal, got: '{verdict_value}'. "
            "The skill requires not softening the verdict to spare feelings."
        )
    })

    # Check 4: "**What's working:**" section present
    has_working = bool(re.search(r"\*\*What's working:\*\*", content))
    checks.append({
        "name": "has_whats_working_section",
        "passed": has_working,
        "detail": "Found '**What's working:**' section." if has_working else "Missing '**What's working:**' section."
    })

    # Check 5: "**What needs attention:**" section present
    has_attention = bool(re.search(r"\*\*What needs attention:\*\*", content))
    checks.append({
        "name": "has_what_needs_attention_section",
        "passed": has_attention,
        "detail": "Found '**What needs attention:**' section." if has_attention else "Missing '**What needs attention:**' section."
    })

    # Check 6: "**The excellence move:**" section present (proprietary name - trap for generic agents)
    has_excellence = bool(re.search(r"\*\*The excellence move:\*\*", content))
    checks.append({
        "name": "has_excellence_move_section",
        "passed": has_excellence,
        "detail": "Found '**The excellence move:**' section." if has_excellence else (
            "Missing '**The excellence move:**' section. This is the proprietary section name required by the review format. "
            "Generic labels like 'Recommendations' or 'Next Steps' do not qualify."
        )
    })

    # Check 7: What needs attention has bullet points (multiple specific issues)
    attention_section = ""
    attention_match = re.search(
        r"\*\*What needs attention:\*\*\s*(.*?)(?=\*\*The excellence move:|$)",
        content, re.DOTALL
    )
    if attention_match:
        attention_section = attention_match.group(1)
    
    bullet_count = len(re.findall(r"^\s*[-*•]\s+.{20,}", attention_section, re.MULTILINE))
    has_multiple_bullets = bullet_count >= 3
    checks.append({
        "name": "attention_has_specific_bullets",
        "passed": has_multiple_bullets,
        "detail": f"Found {bullet_count} substantive bullet(s) in 'What needs attention'. Need at least 3 specific issues." if not has_multiple_bullets else f"Found {bullet_count} specific issue bullets — good coverage."
    })

    # Check 8: Review addresses specific content from the proposal (not generic)
    # Must reference concrete problems: vague budget, no timeline, missing problem quantification
    specificity_keywords = [
        r"budget",
        r"timeline",
        r"vendor",
        r"problem\s+statement|quantif|specif|metric|number|data",
        r"risk",
    ]
    content_lower = content.lower()
    specificity_hits = sum(1 for kw in specificity_keywords if re.search(kw, content_lower))
    is_specific = specificity_hits >= 3
    checks.append({
        "name": "review_is_proposal_specific",
        "passed": is_specific,
        "detail": (
            f"Review references {specificity_hits}/5 key proposal-specific topics (budget, timeline, vendor, problem quantification, risks). "
            "A caring review must be specific to the actual content, not generic."
        ) if not is_specific else (
            f"Review demonstrates specificity — references {specificity_hits}/5 key topics from the actual proposal."
        )
    })

    # Check 9: Excellence move is singular and specific (not a list, has >30 chars of content)
    excellence_section = ""
    excellence_match = re.search(
        r"\*\*The excellence move:\*\*\s*(.*?)$",
        content, re.DOTALL
    )
    if excellence_match:
        excellence_section = excellence_match.group(1).strip()
    excellence_specific = len(excellence_section) > 30 and len(excellence_section) < 2000
    checks.append({
        "name": "excellence_move_is_specific",
        "passed": excellence_specific,
        "detail": f"Excellence move has {len(excellence_section)} chars of content — {'sufficient' if excellence_specific else 'too short or missing'}."
    })

    # Check 10: Review does NOT soften verdict with weasel words alongside Half-Assed
    # If verdict is Half-Assed, there shouldn't be extensive apologetic language immediately after verdict
    weasel_in_verdict_area = False
    if verdict_match:
        verdict_context = content[max(0, verdict_match.start()-20):verdict_match.end()+200]
        weasel_patterns = [r"but overall", r"not bad", r"with some polish", r"mostly good", r"fairly solid"]
        weasel_in_verdict_area = any(re.search(p, verdict_context, re.IGNORECASE) for p in weasel_patterns)
    
    checks.append({
        "name": "verdict_not_softened",
        "passed": not weasel_in_verdict_area,
        "detail": "Verdict is not softened with weasel words." if not weasel_in_verdict_area else "Verdict is being softened with hedging language — the skill requires honest, unsoftened verdicts."
    })

    # --- Scoring ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)

    # Must pass: header, correct Half-Assed verdict, all three section names, specific bullets
    critical_checks = [
        "has_caring_review_header",
        "verdict_is_half_assed",
        "has_whats_working_section",
        "has_what_needs_attention_section",
        "has_excellence_move_section",
        "attention_has_specific_bullets",
    ]
    all_critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = all_critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))