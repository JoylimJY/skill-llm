import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ─── FIND THE OUTPUT FILE ───────────────────────────────────────────────────
    # According to the skill's worked example, the file should be in:
    # projects/{project}/reviews/archie-{topic}-research-{date}.md
    # We search for any .md file in the reviews directory
    
    research_files = list(workspace.rglob("archie-*-research-*.md"))
    # Also accept files in the reviews directory that are markdown
    review_dir_files = list((workspace / "projects" / "cloudlens" / "reviews").glob("*.md"))
    # Filter out .gitkeep
    review_dir_files = [f for f in review_dir_files if f.name != ".gitkeep"]
    
    all_candidates = list(set(research_files + review_dir_files))
    
    if not all_candidates:
        add_check("output_file_exists", False, "No research .md file found under projects/cloudlens/reviews/ or matching archie-*-research-*.md pattern")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Pick the best candidate (prefer archie-* naming convention)
    archie_named = [f for f in all_candidates if f.name.startswith("archie-")]
    target_file = archie_named[0] if archie_named else all_candidates[0]
    
    add_check("output_file_exists", True, f"Found research file: {target_file.relative_to(workspace)}")
    
    # ─── READ CONTENT ───────────────────────────────────────────────────────────
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("file_readable", True, f"File read successfully, {len(content)} characters")
    
    content_lower = content.lower()
    
    # ─── CHECK 1: CORRECT FILE LOCATION (in reviews directory) ─────────────────
    in_reviews_dir = "reviews" in str(target_file)
    add_check(
        "file_in_reviews_directory",
        in_reviews_dir,
        f"File path: {target_file.relative_to(workspace)}"
    )
    
    # ─── CHECK 2: ARCHIE NAMING CONVENTION ──────────────────────────────────────
    archie_naming = target_file.name.startswith("archie-") and target_file.name.endswith(".md")
    add_check(
        "archie_naming_convention",
        archie_naming,
        f"Filename: {target_file.name} — should match archie-*-research-YYYY-MM-DD.md"
    )
    
    # ─── CHECK 3: DATE IN FILENAME (YYYY-MM-DD) ──────────────────────────────────
    date_in_name = bool(re.search(r'\d{4}-\d{2}-\d{2}', target_file.name))
    add_check(
        "date_in_filename",
        date_in_name,
        f"Date pattern YYYY-MM-DD {'found' if date_in_name else 'NOT found'} in filename"
    )
    
    # ─── CHECK 4: REQUIRED SECTIONS PRESENT ──────────────────────────────────────
    required_sections = [
        ("executive summary", r"##\s+executive summary"),
        ("comparison dimensions", r"##\s+comparison dimensions"),
        ("case studies", r"##\s+case studies"),
        ("scoring table", r"##\s+scoring table"),
        ("recommendations", r"##\s+recommendations"),
        ("what we got right", r"##\s+what we got right"),
    ]
    
    missing_sections = []
    for section_name, pattern in required_sections:
        if not re.search(pattern, content_lower):
            missing_sections.append(section_name)
    
    all_sections_present = len(missing_sections) == 0
    add_check(
        "all_required_sections_present",
        all_sections_present,
        f"Missing sections: {missing_sections}" if missing_sections else "All required sections found"
    )
    
    # ─── CHECK 5: ANALYST HEADER (Archie) ────────────────────────────────────────
    has_analyst = bool(re.search(r'analyst:\s*archie', content_lower))
    add_check(
        "analyst_archie_in_header",
        has_analyst,
        "Header must include 'Analyst: Archie'"
    )
    
    # ─── CHECK 6: DATE IN HEADER (YYYY-MM-DD format) ─────────────────────────────
    has_date_header = bool(re.search(r'date:\s*\d{4}-\d{2}-\d{2}', content_lower))
    add_check(
        "date_in_header",
        has_date_header,
        "Header must include 'Date: YYYY-MM-DD'"
    )
    
    # ─── CHECK 7: COMP COUNT (4–6 platforms) ──────────────────────────────────────
    # Count case study headers: ### [Platform]
    case_study_headers = re.findall(r'^###\s+\S+', content, re.MULTILINE)
    comp_count = len(case_study_headers)
    comp_count_valid = 4 <= comp_count <= 6
    add_check(
        "comp_count_4_to_6",
        comp_count_valid,
        f"Found {comp_count} case study entries (### headers). Required: 4–6."
    )
    
    # ─── CHECK 8: CASE STUDY FORMAT (What they did / When / Key lesson) ──────────
    has_what_they_did = bool(re.search(r'\*\*what they did', content_lower))
    has_when = bool(re.search(r'\*\*when', content_lower))
    has_key_lesson = bool(re.search(r'\*\*key lesson', content_lower))
    
    case_study_format_ok = has_what_they_did and has_when and has_key_lesson
    add_check(
        "case_study_format_correct",
        case_study_format_ok,
        f"Case study sub-bullets: 'What they did'={has_what_they_did}, 'When'={has_when}, 'Key lesson'={has_key_lesson}"
    )
    
    # ─── CHECK 9: SCORING TABLE WITH 1-5 SCORES ────────────────────────────────────
    # Check for a markdown table and that it contains numeric scores 1-5
    has_table = bool(re.search(r'\|.*\|.*\|', content))
    has_scores_in_table = bool(re.search(r'\|\s*[1-5]\s*[\|/]', content))
    
    scoring_table_ok = has_table and has_scores_in_table
    add_check(
        "scoring_table_with_1_to_5_scores",
        scoring_table_ok,
        f"Markdown table found: {has_table}. Contains 1-5 scores: {has_scores_in_table}"
    )
    
    # ─── CHECK 10: AT LEAST ONE LOW SCORE (honest scoring, not flattering) ────────
    # Extract all score values from table rows - look for "| X |" or "| X/5 |" patterns
    score_matches = re.findall(r'\|\s*(\d)\s*(?:/5)?\s*\|', content)
    score_values = [int(s) for s in score_matches if s.isdigit() and 1 <= int(s) <= 5]
    
    has_low_score = any(s <= 2 for s in score_values)
    add_check(
        "honest_scoring_includes_low_score",
        has_low_score,
        f"Score values found: {score_values}. At least one score ≤2 required (honest scoring, not flattering). "
        f"Skill states: 'A scoring table where everything is 3–4/5 is useless.'"
    )
    
    # ─── CHECK 11: RECOMMENDATIONS RANKED BY IMPACT ───────────────────────────────
    # Check that recommendations section exists and has numbered/ranked entries
    rec_section_match = re.search(r'##\s+recommendations[^\n]*\n(.*?)(?=##|\Z)', content, re.IGNORECASE | re.DOTALL)
    has_ranked_recs = False
    rec_count = 0
    if rec_section_match:
        rec_body = rec_section_match.group(1)
        ranked_items = re.findall(r'^\d+\.\s+\*\*', rec_body, re.MULTILINE)
        rec_count = len(ranked_items)
        has_ranked_recs = rec_count >= 1
    
    add_check(
        "recommendations_are_numbered_and_ranked",
        has_ranked_recs,
        f"Found {rec_count} numbered bold recommendations. At least 1 required."
    )
    
    # ─── CHECK 12: EFFORT LABELS IN RECOMMENDATIONS ───────────────────────────────
    # The skill specifies: "one-line fix / section rewrite / new feature"
    effort_patterns = [
        r'one.line fix',
        r'section rewrite',
        r'new feature',
        r'one-line',
    ]
    has_effort_labels = any(bool(re.search(p, content_lower)) for p in effort_patterns)
    add_check(
        "recommendations_include_effort_labels",
        has_effort_labels,
        f"Effort labels (one-line fix / section rewrite / new feature) {'found' if has_effort_labels else 'NOT found'} in recommendations"
    )
    
    # ─── CHECK 13: STRUCTURAL ANALOGUES NOT JUST DIRECT COMPETITORS ──────────────
    # CloudLens is a cloud cost tool. Direct competitors would be: Apptio, CloudHealth, Spot.io, Infracost
    # The old-competitor-notes.md distractor lists these explicitly.
    # A good agent should pick structural analogues (usage-based pricing / developer-facing / SaaS pricing transparency)
    # We check that the agent used at least some well-known structural analogues
    good_analogues = [
        'stripe', 'datadog', 'twilio', 'aws', 'heroku', 'snowflake', 
        'segment', 'vercel', 'render', 'planetscale', 'neon', 'supabase',
        'replicate', 'hugging face', 'mongodb', 'elastic', 'confluent',
        'pagerduty', 'sendgrid', 'fastly', 'cloudflare'
    ]
    
    found_analogues = [a for a in good_analogues if a in content_lower]
    
    # Direct competitors from the distractor file that should NOT dominate
    direct_comps = ['apptio', 'cloudhealth', 'spot.io', 'infracost']
    found_direct = [d for d in direct_comps if d in content_lower]
    
    uses_structural_analogues = len(found_analogues) >= 2
    add_check(
        "uses_structural_analogues_not_direct_competitors",
        uses_structural_analogues,
        f"Structural analogues found: {found_analogues}. Direct competitors mentioned: {found_direct}. "
        f"Skill requires prioritizing structural analogues over direct competitors."
    )
    
    # ─── CHECK 14: EXECUTIVE SUMMARY IS SUBSTANTIVE ───────────────────────────────
    exec_match = re.search(r'##\s+executive summary\n+(.*?)(?=##)', content, re.IGNORECASE | re.DOTALL)
    exec_len = 0
    if exec_match:
        exec_text = exec_match.group(1).strip()
        exec_len = len(exec_text)
    
    exec_substantive = exec_len >= 100
    add_check(
        "executive_summary_substantive",
        exec_substantive,
        f"Executive summary length: {exec_len} characters. Need ≥100 for substantive 3-4 sentence summary."
    )
    
    # ─── CHECK 15: COMPARISON DIMENSIONS (3-5 defined) ────────────────────────────
    dim_section_match = re.search(r'##\s+comparison dimensions\n+(.*?)(?=##)', content, re.IGNORECASE | re.DOTALL)
    dim_count = 0
    if dim_section_match:
        dim_text = dim_section_match.group(1)
        # Count bullet points or numbered items
        bullets = re.findall(r'^[-*\d.]\s+\S+', dim_text, re.MULTILINE)
        dim_count = len(bullets)
    
    dims_valid = 3 <= dim_count <= 5
    add_check(
        "comparison_dimensions_3_to_5",
        dims_valid,
        f"Found {dim_count} dimension bullets. Required: 3–5 per skill definition."
    )
    
    # ─── SCORING ──────────────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 3)
    
    # Hard gates: file must exist, be readable, have all sections, and have honest scoring
    hard_gates = [
        "output_file_exists",
        "file_readable",
        "all_required_sections_present",
        "honest_scoring_includes_low_score",
        "uses_structural_analogues_not_direct_competitors",
    ]
    
    hard_gates_passed = all(
        any(c["name"] == g and c["passed"] for c in checks)
        for g in hard_gates
    )
    
    final_passed = hard_gates_passed and score >= 0.75
    
    return {
        "passed": final_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))