import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    # The task asks for a GEO audit file; look for it
    workspace = Path(workspace_dir)
    
    # Accept geo_audit.md or similar names
    candidates = list(workspace.rglob("geo_audit.md")) + \
                 list(workspace.rglob("geo_audit.txt")) + \
                 list(workspace.rglob("plant_protein_geo_audit.md")) + \
                 list(workspace.rglob("plant_protein_audit.md")) + \
                 list(workspace.rglob("geo_report.md")) + \
                 list(workspace.rglob("audit_report.md"))

    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "No GEO audit output file found. Expected geo_audit.md or similar."})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = candidates[0]
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "output_file_readable", "passed": False,
                        "detail": f"Could not read output file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found output file at: {output_file}"})

    # --- CHECK 1: GEO Audit header present ---
    has_audit_header = bool(re.search(r'##\s*GEO Audit', content, re.IGNORECASE))
    checks.append({"name": "geo_audit_header", "passed": has_audit_header,
                    "detail": "Must contain '## GEO Audit' section header."})

    # --- CHECK 2: Current Score line with /40 format ---
    score_match = re.search(r'Current\s*Score\s*[:\-]\s*(\d+)\s*/\s*40', content, re.IGNORECASE)
    has_score_format = bool(score_match)
    checks.append({"name": "current_score_format", "passed": has_score_format,
                    "detail": "Must include 'Current Score: X/40' with a numeric score and denominator 40."})

    # --- CHECK 3: Score is in a plausible low range (plant_protein_draft is weak: expected 8-18/40) ---
    score_value_ok = False
    score_detail = "Could not extract score."
    if score_match:
        raw_score = int(score_match.group(1))
        if 8 <= raw_score <= 18:
            score_value_ok = True
            score_detail = f"Score {raw_score}/40 is in the expected low range (8-18) for this weak article."
        else:
            score_detail = f"Score {raw_score}/40 is outside expected range 8-18 for this weak draft. The article has no citations, no Q&A, no definitions, no authority signals, no dates — all 8 dimensions should score 1-2."
    checks.append({"name": "score_value_plausible", "passed": score_value_ok, "detail": score_detail})

    # --- CHECK 4: Tier classification present and correct for the score ---
    tier_ok = False
    tier_detail = "Could not find tier classification."
    if score_match:
        raw_score = int(score_match.group(1))
        # For scores 8-18, the tier should be "Major work needed" (16-23 boundary means 16<=x<=23 = major work)
        # Scores 8-15 also fall in major work needed or below minimum. 
        # The rubric: 16-23 = Major work needed; scores below 16 aren't explicitly labeled but imply same.
        has_major_work = bool(re.search(r'major\s+work\s+needed', content, re.IGNORECASE))
        has_needs_opt = bool(re.search(r'needs\s+optim', content, re.IGNORECASE))
        has_ai_ready = bool(re.search(r'ai[\s\-]?ready', content, re.IGNORECASE))

        if raw_score <= 23:
            # Should NOT be "AI-ready" or "Needs optimization" (unless needs_opt tier 24-31)
            if has_major_work and not has_ai_ready:
                tier_ok = True
                tier_detail = f"Correctly classified as 'Major work needed' for score {raw_score}/40."
            elif raw_score >= 24 and has_needs_opt and not has_ai_ready:
                tier_ok = True
                tier_detail = f"Score {raw_score}/40 in needs-optimization tier."
            else:
                tier_detail = f"Score {raw_score}/40 should map to 'Major work needed' but tier classification is missing or incorrect. Found ai_ready={has_ai_ready}, needs_opt={has_needs_opt}, major_work={has_major_work}."
        elif 24 <= raw_score <= 31:
            if has_needs_opt and not has_ai_ready:
                tier_ok = True
                tier_detail = f"Correctly classified as 'Needs optimization' for score {raw_score}/40."
    checks.append({"name": "tier_classification_correct", "passed": tier_ok, "detail": tier_detail})

    # --- CHECK 5: Dimension Scores table with all 8 dimensions ---
    has_dimension_table = bool(re.search(r'Dimension\s*\|\s*Score\s*\|\s*Quick\s*Fix', content, re.IGNORECASE))
    checks.append({"name": "dimension_table_header", "passed": has_dimension_table,
                    "detail": "Must include a table with columns: Dimension | Score | Quick Fix"})

    # Count how many of the 8 dimensions appear in the content
    dimensions = [
        "definition clarity",
        "quotable statements",
        "factual density",
        "source citations",
        "q.?a format",
        "authority signals",
        "content freshness",
        "structural clarity",
    ]
    found_dims = 0
    missing_dims = []
    for dim in dimensions:
        if re.search(dim, content, re.IGNORECASE):
            found_dims += 1
        else:
            missing_dims.append(dim)
    all_dims_present = found_dims == 8
    checks.append({"name": "all_8_dimensions_scored", "passed": all_dims_present,
                    "detail": f"Found {found_dims}/8 dimensions. Missing: {missing_dims}"})

    # --- CHECK 6: Dimension scores are all 1 or 2 (weak article should score low everywhere) ---
    # Extract all score values from the table rows (look for | digit | pattern)
    table_scores = re.findall(r'\|\s*([1-5])\s*\|', content)
    dim_scores_low = False
    dim_scores_detail = "Could not extract dimension scores from table."
    if table_scores:
        int_scores = [int(s) for s in table_scores]
        # Expect at least 8 scores, all should be 1 or 2 for this very weak article
        scores_in_range = [s for s in int_scores[:8] if s in (1, 2)]
        if len(int_scores) >= 8 and len(scores_in_range) >= 6:
            dim_scores_low = True
            dim_scores_detail = f"Dimension scores {int_scores[:8]} appropriately low (mostly 1-2) for weak draft."
        else:
            dim_scores_detail = f"Expected mostly 1-2 scores for all 8 dimensions of this weak draft. Got: {int_scores[:8]}. Article has no citations, no Q&A, no data, no authority — scores should be 1-2 across dimensions."
    checks.append({"name": "dimension_scores_appropriately_low", "passed": dim_scores_low,
                    "detail": dim_scores_detail})

    # --- CHECK 7: Optimized Content Sections present ---
    has_optimized_section = bool(re.search(r'##\s*Optimized\s+Content\s+Sections', content, re.IGNORECASE))
    checks.append({"name": "optimized_content_sections_header", "passed": has_optimized_section,
                    "detail": "Must include '## Optimized Content Sections' header."})

    # --- CHECK 8: Definition section with citable format ---
    has_definition_section = bool(re.search(r'###\s*Definition\s*\(Citable\)', content, re.IGNORECASE))
    checks.append({"name": "definition_citable_section", "passed": has_definition_section,
                    "detail": "Must include '### Definition (Citable)' section."})

    # Definition follows the pattern: [Term] is [category] that [function], [key metric]
    # Look for "protein" near "is a" and a metric/number
    def_pattern = bool(re.search(
        r'plant.based protein.{0,80}is\s+(a|an)\s+\w+.{0,200}\d+',
        content, re.IGNORECASE | re.DOTALL
    ))
    checks.append({"name": "definition_follows_template", "passed": def_pattern,
                    "detail": "Definition should follow: '[Term] is a [category] that [function], [key metric with number].'"})

    # --- CHECK 9: Key Statistics section with sourced stats ---
    has_stats_section = bool(re.search(r'###\s*Key\s+Statistics', content, re.IGNORECASE))
    checks.append({"name": "key_statistics_section", "passed": has_stats_section,
                    "detail": "Must include '### Key Statistics' section."})

    # Stats should have bullet points with numbers and sources/years
    stats_with_sources = re.findall(
        r'[-*]\s+.{0,30}\d+.{0,100}(?:20\d\d|Source|source|\w+,\s*20\d\d)',
        content
    )
    has_sourced_stats = len(stats_with_sources) >= 2
    checks.append({"name": "stats_have_sources_and_dates", "passed": has_sourced_stats,
                    "detail": f"Found {len(stats_with_sources)} sourced statistics. Need at least 2 stats with sources and/or dates."})

    # --- CHECK 10: FAQ Section with 5-7 questions ---
    has_faq_section = bool(re.search(r'###\s*FAQ\s+Section', content, re.IGNORECASE))
    checks.append({"name": "faq_section_present", "passed": has_faq_section,
                    "detail": "Must include '### FAQ Section' section."})

    # Count Q&A pairs — look for **Q: ...** pattern
    qa_pairs = re.findall(r'\*\*Q\s*:\s*.+?\?', content)
    faq_count_ok = 5 <= len(qa_pairs) <= 7
    checks.append({"name": "faq_has_5_to_7_questions", "passed": faq_count_ok,
                    "detail": f"Found {len(qa_pairs)} Q&A pairs in **Q:** format. SKILL.md requires exactly 5-7 questions."})

    # --- Compute final pass/fail ---
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    passed = len(passed_checks)
    final_score = round(passed / total, 3)

    # Must pass at least 10/13 checks to pass overall
    overall_passed = passed >= 10

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))