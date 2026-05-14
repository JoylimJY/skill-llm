import sys
import json
import re
from pathlib import Path

def count_words(text):
    return len(text.split())

def find_proposal_file(workspace):
    """Search for the proposal bid package file."""
    candidates = list(Path(workspace).rglob("upwork_bid_package.md")) + \
                 list(Path(workspace).rglob("upwork_bid_package.txt"))
    return candidates[0] if candidates else None

def run_checks(workspace):
    checks = []
    score_parts = []

    proposal_file = find_proposal_file(workspace)

    # Check 1: File exists
    file_exists = proposal_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found at {proposal_file}" if file_exists else "upwork_bid_package.md/.txt not found in workspace"
    })
    if not file_exists:
        return checks, 0.0

    try:
        content = proposal_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    content_lower = content.lower()

    # --- PROPOSAL BODY EXTRACTION ---
    # Try to isolate the proposal body (the main pitch text) from the full document
    # We'll look for a section between the opening hook and end of CTA
    # For word count: count words in the full proposal section, excluding pricing/tips/questions/followup

    # Split content into sections for analysis
    proposal_section_match = re.search(
        r'(opening hook|hook|proposal body|the proposal|---proposal---|^[A-Z])',
        content, re.IGNORECASE | re.MULTILINE
    )

    # ======== PROPOSAL STRUCTURE CHECKS ========

    # Check 2: Does NOT start with "I" (first non-whitespace word of the proposal)
    # Find the actual proposal text start (after any headers/labels)
    lines = [l for l in content.split('\n') if l.strip()]
    proposal_start_line = ""
    for line in lines:
        stripped = line.strip()
        # Skip markdown headers and metadata lines
        if stripped.startswith('#') or ':' in stripped[:30] or stripped.startswith('**') and stripped.endswith('**'):
            continue
        if len(stripped) > 10:
            proposal_start_line = stripped
            break

    starts_with_i = False
    if proposal_start_line:
        # Remove markdown bold/italic markers
        clean_start = re.sub(r'[\*_>#]', '', proposal_start_line).strip()
        first_word = clean_start.split()[0] if clean_start.split() else ""
        starts_with_i = first_word.lower() == "i"

    checks.append({
        "name": "does_not_start_with_I",
        "passed": not starts_with_i,
        "detail": f"Proposal opening line: '{proposal_start_line[:80]}'" if proposal_start_line else "Could not determine opening"
    })

    # Check 3: Banned phrases not present
    banned_phrases = [
        "i am writing to express my interest",
        "i am confident that",
        "i look forward to hearing from you",
        "dear sir/madam",
        "dear sir or madam",
        "i have x years of experience",
        "i have [0-9]+ years of experience",
        "my name is",
        "i'm a ",
    ]
    found_banned = []
    for phrase in banned_phrases:
        if re.search(phrase, content_lower):
            found_banned.append(phrase)

    checks.append({
        "name": "no_banned_template_phrases",
        "passed": len(found_banned) == 0,
        "detail": f"Found banned phrases: {found_banned}" if found_banned else "No banned phrases detected"
    })

    # Check 4: References specific job details (Salesforce, Stripe, PostgreSQL, Tableau, ETL)
    job_specifics = ["salesforce", "stripe", "postgresql", "tableau", "etl", "mrr", "churn", "saas"]
    found_specifics = [kw for kw in job_specifics if kw in content_lower]
    has_specifics = len(found_specifics) >= 4

    checks.append({
        "name": "references_specific_job_details",
        "passed": has_specifics,
        "detail": f"Found {len(found_specifics)}/4+ required job-specific terms: {found_specifics}"
    })

    # Check 5: Proposal body word count (150-500 words for proposal section)
    # We'll count the proposal body section (not the full document with tips/pricing)
    # Heuristic: find the first substantial paragraph block before pricing/tips sections
    proposal_body_text = content

    # Try to extract just the proposal body (before Pricing/Tips/Questions sections)
    sections_delimiter = re.split(
        r'\n#+\s*(pricing|rate|platform.{0,20}tip|clarifying question|follow.up|questions to ask)',
        content, flags=re.IGNORECASE
    )
    proposal_body_text = sections_delimiter[0] if sections_delimiter else content

    proposal_word_count = count_words(proposal_body_text)
    # The full document will be longer, proposal body should be 150-500 words
    word_count_ok = 150 <= proposal_word_count <= 600  # generous upper bound for full doc
    checks.append({
        "name": "proposal_body_word_count_reasonable",
        "passed": word_count_ok,
        "detail": f"Proposal body section word count: {proposal_word_count} (expected 150-500 for proposal + some metadata)"
    })

    # Check 6: Upwork-specific tip present (under 300 words / platform-specific advice)
    has_platform_tip = bool(re.search(
        r'(upwork|300 word|keep.{0,20}(short|concise|brief|under)|platform.{0,30}tip)',
        content_lower
    ))
    checks.append({
        "name": "upwork_platform_tip_present",
        "passed": has_platform_tip,
        "detail": "Found Upwork/platform-specific tip" if has_platform_tip else "No Upwork platform tip found"
    })

    # Check 7: Pricing section with recommended rate AND justification
    has_pricing = bool(re.search(
        r'(pricing|rate|per hour|/hr|\$\d+)',
        content_lower
    ))
    has_rate_number = bool(re.search(r'\$\s*\d{2,4}', content))
    checks.append({
        "name": "pricing_section_with_rate",
        "passed": has_pricing and has_rate_number,
        "detail": f"Pricing present: {has_pricing}, Rate number found: {has_rate_number}"
    })

    # Check 8: Phased/MVP approach mentioned (required for budget-conscious or as alternative)
    has_phased = bool(re.search(
        r'(phase[d]?|milestone|mvp|minimum viable|staged|scope|reduced scope|alternative|option\s*[12ab])',
        content_lower
    ))
    checks.append({
        "name": "phased_or_alternative_pricing_mentioned",
        "passed": has_phased,
        "detail": "Found phased/milestone/MVP alternative" if has_phased else "No phased approach or alternative pricing found"
    })

    # Check 9: Clarifying questions present (2+ questions)
    question_marks = content.count('?')
    # At least 2 genuine questions
    has_questions = question_marks >= 2
    checks.append({
        "name": "clarifying_questions_present",
        "passed": has_questions,
        "detail": f"Found {question_marks} question marks (need ≥2 for clarifying questions)"
    })

    # Check 10: Follow-up message template present
    has_followup = bool(re.search(
        r'(follow.?up|48.?hour|no\s+response|follow\s+up\s+(message|template)|if\s+(you|they)\s+(haven.t|haven.t|don.t)\s+(heard|respond))',
        content_lower
    ))
    checks.append({
        "name": "followup_message_template_present",
        "passed": has_followup,
        "detail": "Follow-up message template found" if has_followup else "No follow-up template found (required per skill spec)"
    })

    # Check 11: Approach section has bullet points (specific steps)
    bullet_count = len(re.findall(r'^\s*[-*•]\s+\S', content, re.MULTILINE))
    has_bullets = bullet_count >= 3
    checks.append({
        "name": "approach_has_bullet_points",
        "passed": has_bullets,
        "detail": f"Found {bullet_count} bullet points (need ≥3 for approach steps)"
    })

    # Check 12: Experience section references quantified outcomes
    has_quantified = bool(re.search(
        r'(\d+\s*%|\d+x|\d+\s*(hour|day|week|month)|\d+k|\$\d+|\d+\s*client|\d+\s*project)',
        content_lower
    ))
    checks.append({
        "name": "quantified_results_in_experience",
        "passed": has_quantified,
        "detail": "Found quantified outcome in experience section" if has_quantified else "No quantified results found"
    })

    # Check 13: Call to action present (suggests next step)
    has_cta = bool(re.search(
        r'(quick call|schedule|start (today|immediately|now|this week)|happy to|reach out|let.s (talk|connect|discuss)|available|can start)',
        content_lower
    ))
    checks.append({
        "name": "call_to_action_present",
        "passed": has_cta,
        "detail": "CTA found" if has_cta else "No call to action detected"
    })

    # Check 14: Technical language appropriate for technical client
    tech_terms = ["api", "pipeline", "schema", "etl", "postgresql", "tableau", "python", "requirements.txt", "twbx", "normali"]
    found_tech = [t for t in tech_terms if t in content_lower]
    has_technical_language = len(found_tech) >= 5
    checks.append({
        "name": "technical_language_for_technical_client",
        "passed": has_technical_language,
        "detail": f"Found {len(found_tech)}/5+ technical terms: {found_tech}"
    })

    # --- SCORING ---
    # Weight critical checks more heavily
    critical_checks = [
        "does_not_start_with_I",
        "no_banned_template_phrases",
        "references_specific_job_details",
        "pricing_section_with_rate",
        "followup_message_template_present",
        "upwork_platform_tip_present",
    ]
    standard_checks = [
        "output_file_exists",
        "proposal_body_word_count_reasonable",
        "phased_or_alternative_pricing_mentioned",
        "clarifying_questions_present",
        "approach_has_bullet_points",
        "quantified_results_in_experience",
        "call_to_action_present",
        "technical_language_for_technical_client",
    ]

    check_map = {c["name"]: c["passed"] for c in checks}

    critical_score = sum(1.5 for name in critical_checks if check_map.get(name, False))
    standard_score = sum(1.0 for name in standard_checks if check_map.get(name, False))
    max_score = len(critical_checks) * 1.5 + len(standard_checks) * 1.0
    raw_score = (critical_score + standard_score) / max_score

    return checks, round(raw_score, 3)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.65

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()