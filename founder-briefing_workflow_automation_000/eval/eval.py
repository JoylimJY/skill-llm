import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: str) -> Path | None:
    """Search for the output file lead_followup_plan.md anywhere in workspace."""
    candidates = list(Path(workspace).rglob("lead_followup_plan.md"))
    if candidates:
        return candidates[0]
    return None

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []

    # --- Locate output file ---
    output_path = find_output_file(workspace)
    if output_path is None:
        checks.append(check("output_file_exists", False, "lead_followup_plan.md not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append(check("output_file_exists", True, f"Found at {output_path}"))

    try:
        content = output_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, str(e)))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_readable", True, f"File size: {len(content)} chars"))
    content_lower = content.lower()

    # =========================================================
    # SECTION 1: Priority Queue presence
    # =========================================================
    has_priority_section = bool(re.search(r'priority\s*queue', content_lower))
    checks.append(check("section_priority_queue_present", has_priority_section,
                         "Document must contain a 'Priority Queue' section"))

    # Hot leads: Marcus and Yolanda must both be classified Hot
    marcus_hot = bool(re.search(r'hot[^\n]*marcus|marcus[^\n]*hot', content_lower))
    yolanda_hot = bool(re.search(r'hot[^\n]*yolanda|yolanda[^\n]*hot', content_lower))
    checks.append(check("marcus_classified_hot", marcus_hot,
                         "Marcus T. must appear under Hot (2+ signals: pre-approved, specific area+budget+timeline, wants tour this week, replied <24h)"))
    checks.append(check("yolanda_classified_hot", yolanda_hot,
                         "Yolanda K. must appear under Hot (2+ signals: cash buyer, specific area+budget, 60-day close, replied <24h)"))

    # Amara: Hot or Warm (pre-approved + timeline 6 weeks + wants tour = 2+ signals → should be Hot)
    amara_hot_or_warm = bool(re.search(r'(hot|warm)[^\n]*amara|amara[^\n]*(hot|warm)', content_lower))
    checks.append(check("amara_classified_hot_or_warm", amara_hot_or_warm,
                         "Amara J. must appear under Hot or Warm (pre-approved, 6-week timeline, wants tour Thursday)"))

    # Priya: Warm (some intent, incomplete details, next few months)
    priya_warm = bool(re.search(r'warm[^\n]*priya|priya[^\n]*warm', content_lower))
    checks.append(check("priya_classified_warm", priya_warm,
                         "Priya S. must appear under Warm (some intent but incomplete details, next few months)"))

    # Tom/Derek: Cold
    tom_cold = bool(re.search(r'cold[^\n]*tom|tom[^\n]*cold', content_lower))
    derek_cold = bool(re.search(r'cold[^\n]*derek|derek[^\n]*cold', content_lower))
    checks.append(check("tom_classified_cold", tom_cold,
                         "Tom V. must appear under Cold (no timeline, no budget, low intent)"))
    checks.append(check("derek_classified_cold", derek_cold,
                         "Derek N. must appear under Cold (no timeline, just browsing, no contact)"))

    # Derek needs-data: no contact info recovered
    derek_needs_data = bool(re.search(r'needs.?data[^\n]*derek|derek[^\n]*needs.?data|no.contact[^\n]*derek|derek[^\n]*no.contact|contact[^\n]*missing[^\n]*derek|derek[^\n]*contact[^\n]*missing|smudged|no contact info', content_lower))
    checks.append(check("derek_needs_data_flagged", derek_needs_data,
                         "Derek's contact info was smudged/unrecoverable; should be flagged as Needs Data or noted as missing contact"))

    # =========================================================
    # SECTION 2: Lead-by-Lead Follow-Up Kit
    # =========================================================
    has_followup_kit = bool(re.search(r'follow.?up\s*kit|lead.by.lead|follow.?up\s*plan', content_lower))
    checks.append(check("section_followup_kit_present", has_followup_kit,
                         "Document must contain a Lead-by-Lead Follow-Up Kit section"))

    # SMS drafts present
    sms_count = len(re.findall(r'\bsms\b', content_lower))
    has_sms_drafts = sms_count >= 3
    checks.append(check("sms_drafts_present", has_sms_drafts,
                         f"Multiple SMS drafts expected (found 'sms' {sms_count} times, need ≥3)"))

    # Email drafts present
    email_count = len(re.findall(r'\bemail\b', content_lower))
    has_email_drafts = email_count >= 3
    checks.append(check("email_drafts_present", has_email_drafts,
                         f"Multiple email drafts expected (found 'email' {email_count} times, need ≥3)"))

    # Objection reply for Derek or rates objection mentioned
    has_objection_reply = bool(re.search(r'objection|rates.*high|high.*rates|wait.*rates|rates.*wait', content_lower))
    checks.append(check("objection_reply_present", has_objection_reply,
                         "An objection reply must be drafted (Derek/Jess mentioned rates are too high)"))

    # Next-best action present for multiple leads
    nba_count = len(re.findall(r'next.best.action|next action|next step', content_lower))
    has_nba = nba_count >= 2
    checks.append(check("next_best_action_present", has_nba,
                         f"Next-best action must appear per lead (found {nba_count} instances, need ≥2)"))

    # =========================================================
    # SECTION 3: 7-Day Cadence with correct non-sequential day numbers
    # =========================================================
    has_cadence = bool(re.search(r'7.day\s*cadence|cadence', content_lower))
    checks.append(check("section_7day_cadence_present", has_cadence,
                         "Document must contain a 7-Day Cadence section"))

    # PROPRIETARY TRAP: Days must be 0, 1, 3, 5, 7 — NOT sequential 1-7
    day0 = bool(re.search(r'day\s*0', content_lower))
    day1 = bool(re.search(r'day\s*1', content_lower))
    day3 = bool(re.search(r'day\s*3', content_lower))
    day5 = bool(re.search(r'day\s*5', content_lower))
    day7 = bool(re.search(r'day\s*7', content_lower))
    correct_day_structure = day0 and day1 and day3 and day5 and day7
    checks.append(check("cadence_uses_correct_days_0_1_3_5_7", correct_day_structure,
                         f"Cadence must use Day 0/1/3/5/7 (non-sequential per SKILL.md). Found: day0={day0}, day1={day1}, day3={day3}, day5={day5}, day7={day7}"))

    # =========================================================
    # SECTION 4: CRM Paste Block
    # =========================================================
    has_crm_block = bool(re.search(r'crm\s*paste|crm\s*block|crm\s*note', content_lower))
    checks.append(check("section_crm_paste_block_present", has_crm_block,
                         "Document must contain a CRM Paste Block section"))

    # CRM block sub-fields
    has_status_field = bool(re.search(r'\bstatus\s*:', content_lower))
    has_timeline_field = bool(re.search(r'\btimeline\s*:', content_lower))
    has_pain_point_field = bool(re.search(r'key\s*pain\s*point\s*:', content_lower))
    has_last_contact_field = bool(re.search(r'last\s*contact\s*:', content_lower))
    has_next_action_field = bool(re.search(r'next\s*action\s*:', content_lower))

    crm_fields_ok = has_status_field and has_timeline_field and has_pain_point_field and has_last_contact_field and has_next_action_field
    checks.append(check("crm_block_has_required_fields", crm_fields_ok,
                         f"CRM Paste Block must include: Status, Timeline, Key pain point, Last contact, Next action. "
                         f"Found: status={has_status_field}, timeline={has_timeline_field}, "
                         f"pain_point={has_pain_point_field}, last_contact={has_last_contact_field}, next_action={has_next_action_field}"))

    # =========================================================
    # SECTION 5: Writing Rules compliance
    # =========================================================
    # Must NOT fabricate specific rate numbers (e.g., "3.5%", "7.2% rate") as facts
    fabricated_rate = bool(re.search(r'\b[3-8]\.[0-9]+\s*%\s*(rate|APR|mortgage|interest)', content_lower))
    no_fabricated_rates = not fabricated_rate
    checks.append(check("no_fabricated_rate_facts", no_fabricated_rates,
                         "Writing rules forbid fabricating specific mortgage rate figures (e.g., '6.8% rate')"))

    # Unknown contact (smudged/anonymous SMS) should NOT be given a made-up name
    # Check that the unknown SMS contact isn't given a fabricated identity label like "Jane" or "John"
    # We just verify "unknown" or "anonymous" appears somewhere
    unknown_acknowledged = bool(re.search(r'unknown|anonymous|unidentified|no name|unverified', content_lower))
    checks.append(check("unknown_contact_acknowledged", unknown_acknowledged,
                         "The anonymous inbound SMS must be acknowledged as unknown/unverified, not given a fabricated name"))

    # =========================================================
    # SCORING
    # =========================================================
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 4)

    # Must pass all critical checks to overall pass
    critical = [
        "output_file_exists",
        "section_priority_queue_present",
        "marcus_classified_hot",
        "yolanda_classified_hot",
        "cadence_uses_correct_days_0_1_3_5_7",
        "section_7day_cadence_present",
        "section_crm_paste_block_present",
        "crm_block_has_required_fields",
    ]
    critical_passed = all(
        any(c["name"] == cname and c["passed"] for c in checks)
        for cname in critical
    )

    overall_passed = critical_passed and score >= 0.72

    return {"passed": overall_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))