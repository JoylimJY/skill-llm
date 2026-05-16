import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("email_sequences.md"))
    if candidates:
        return candidates[0]
    return None

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1]
    checks = []

    # --- Find the output file ---
    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append(check("output_file_exists", False, "email_sequences.md not found anywhere in workspace"))
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append(check("output_file_exists", True, f"Found at {output_file}"))

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append(check("file_readable", True, f"File size: {len(content)} chars"))
    content_lower = content.lower()

    # ===========================================================
    # CHECK 1: Email Strategy Overview section exists
    # ===========================================================
    has_strategy_overview = bool(re.search(
        r'email\s+strategy\s+overview',
        content_lower
    ))
    checks.append(check(
        "section_email_strategy_overview",
        has_strategy_overview,
        "Must contain an 'Email Strategy Overview' section" if not has_strategy_overview else "Found"
    ))

    # CHECK 1a: Strategy mentions behavioral triggers
    has_behavioral = bool(re.search(r'behavioral', content_lower))
    checks.append(check(
        "strategy_mentions_behavioral_triggers",
        has_behavioral,
        "Strategy overview must distinguish behavioral vs. time-based triggers" if not has_behavioral else "Found behavioral trigger mention"
    ))

    # CHECK 1b: Strategy mentions key metrics
    has_metrics = bool(re.search(r'metric|kpi|open rate|click.?through|conversion rate', content_lower))
    checks.append(check(
        "strategy_mentions_key_metrics",
        has_metrics,
        "Strategy overview must include key metrics to track" if not has_metrics else "Found metrics mention"
    ))

    # ===========================================================
    # CHECK 2: Onboarding Email Sequence section exists
    # ===========================================================
    has_onboarding_section = bool(re.search(
        r'onboarding\s+email\s+sequence',
        content_lower
    ))
    checks.append(check(
        "section_onboarding_sequence",
        has_onboarding_section,
        "Must contain an 'Onboarding Email Sequence' section" if not has_onboarding_section else "Found"
    ))

    # CHECK 2a: 5-7 distinct emails in onboarding sequence
    # Look for email numbering patterns: "Email 1", "Email 2", etc. or "#1", "1.", etc.
    email_numbers = re.findall(
        r'(?:email\s*[#\-]?\s*([1-9])|^\s*([1-9])\.\s+(?:welcome|guide|social|feature|check))',
        content_lower,
        re.MULTILINE
    )
    # More robust: count "Email N:" or "Email N -" patterns
    numbered_emails = re.findall(
        r'email\s+(?:no\.?\s*)?([1-9])\b',
        content_lower
    )
    unique_email_nums = set(numbered_emails)
    email_count = len(unique_email_nums)
    onboarding_email_count_ok = 5 <= email_count <= 7
    checks.append(check(
        "onboarding_sequence_5_to_7_emails",
        onboarding_email_count_ok,
        f"Found {email_count} numbered emails (Email 1..N); need 5-7" if not onboarding_email_count_ok else f"Found {email_count} emails"
    ))

    # CHECK 2b: Welcome email present (Email 1 must relate to welcome/next step)
    has_welcome_email = bool(re.search(
        r'(?:email\s+1[^0-9].*?welcome|welcome.*?email\s+1)',
        content_lower,
        re.DOTALL
    )) or bool(re.search(r'welcome.*?single.*?(?:next\s+step|important\s+action)', content_lower, re.DOTALL))
    # Looser: email 1 contains welcome
    has_welcome_loose = bool(re.search(r'email\s+1', content_lower)) and bool(re.search(r'welcome', content_lower))
    checks.append(check(
        "onboarding_email1_welcome",
        has_welcome_loose,
        "Email 1 should be a Welcome email" if not has_welcome_loose else "Found"
    ))

    # CHECK 2c: Social proof / success story email present
    has_social_proof = bool(re.search(
        r'social\s+proof|success\s+stor|case\s+stud|customer\s+stor|testimonial',
        content_lower
    ))
    checks.append(check(
        "onboarding_email_social_proof",
        has_social_proof,
        "Must include a social proof / success story email in onboarding sequence" if not has_social_proof else "Found"
    ))

    # CHECK 2d: Each email has a subject line
    subject_line_count = len(re.findall(
        r'subject(?:\s+line)?[:\s]+["\']?[A-Za-z]',
        content,
        re.IGNORECASE
    ))
    has_enough_subjects = subject_line_count >= 4
    checks.append(check(
        "emails_include_subject_lines",
        has_enough_subjects,
        f"Found {subject_line_count} subject lines; each email needs a subject line (need ≥4)" if not has_enough_subjects else f"Found {subject_line_count} subject lines"
    ))

    # CHECK 2e: Timing specified for emails
    timing_mentions = re.findall(
        r'(?:day\s+\d|hour\s+\d|\d+\s+(?:days?|hours?)\s+after|send\s+(?:at|on|after)|delay|timing)',
        content_lower
    )
    has_timing = len(timing_mentions) >= 3
    checks.append(check(
        "emails_include_timing",
        has_timing,
        f"Found {len(timing_mentions)} timing references; emails need explicit timing (need ≥3)" if not has_timing else f"Found timing info"
    ))

    # CHECK 2f: Behavioral triggers specified
    trigger_mentions = re.findall(
        r'trigger|(?:if\s+user|when\s+user|unless\s+user|has\s+not|hasn\'t|did\s+not|didn\'t)',
        content_lower
    )
    has_triggers = len(trigger_mentions) >= 3
    checks.append(check(
        "emails_include_behavioral_triggers",
        has_triggers,
        f"Found {len(trigger_mentions)} trigger references; each email needs behavioral triggers (need ≥3)" if not has_triggers else f"Found {len(trigger_mentions)} trigger mentions"
    ))

    # ===========================================================
    # CHECK 3: Trial-to-Paid Conversion Sequence section
    # ===========================================================
    has_trial_section = bool(re.search(
        r'trial.{0,10}(?:to|2).{0,10}paid|trial.{0,10}conversion|conversion\s+sequence',
        content_lower
    ))
    checks.append(check(
        "section_trial_to_paid",
        has_trial_section,
        "Must contain a Trial-to-Paid Conversion Sequence section" if not has_trial_section else "Found"
    ))

    # CHECK 3a: Trial expiration reminder
    has_expiry_reminder = bool(re.search(
        r'trial\s+expir|expir(?:ation|ing)\s+reminder|days?\s+left\s+(?:in|on)\s+(?:your\s+)?trial',
        content_lower
    ))
    checks.append(check(
        "trial_conversion_expiry_reminder",
        has_expiry_reminder,
        "Trial-to-Paid must include a trial expiration reminder" if not has_expiry_reminder else "Found"
    ))

    # CHECK 3b: Value recap
    has_value_recap = bool(re.search(
        r'value\s+recap|what\s+(?:you\'?ve?|they\'?ve?)\s+accomplished|accomplishment|recap\s+of\s+(?:what|value)',
        content_lower
    ))
    checks.append(check(
        "trial_conversion_value_recap",
        has_value_recap,
        "Trial-to-Paid must include a value recap (what they've accomplished)" if not has_value_recap else "Found"
    ))

    # CHECK 3c: Urgency or scarcity
    has_urgency = bool(re.search(
        r'urgency|scarcity|limited\s+(?:time|offer)|act\s+now|last\s+chance|deadline',
        content_lower
    ))
    checks.append(check(
        "trial_conversion_urgency_scarcity",
        has_urgency,
        "Trial-to-Paid must include urgency/scarcity component" if not has_urgency else "Found"
    ))

    # CHECK 3d: Free vs. paid comparison
    has_comparison = bool(re.search(
        r'free\s+vs\.?\s+paid|free\s+plan\s+vs|paid\s+(?:plan|tier|features?)\s+vs|comparison|free\s+tier.*paid\s+tier|paid.*?vs.*?free',
        content_lower
    ))
    checks.append(check(
        "trial_conversion_free_vs_paid_comparison",
        has_comparison,
        "Trial-to-Paid must include free vs. paid comparison" if not has_comparison else "Found"
    ))

    # ===========================================================
    # CHECK 4: Retention & Re-engagement section
    # ===========================================================
    has_retention_section = bool(re.search(
        r'retention|re.?engagement|win.?back',
        content_lower
    ))
    checks.append(check(
        "section_retention_reengagement",
        has_retention_section,
        "Must contain a Retention & Re-engagement section" if not has_retention_section else "Found"
    ))

    # CHECK 4a: Win-back sequence for inactive users
    has_winback = bool(re.search(
        r'win.?back|inactive\s+user|re.?engage\s+inactive|lapsed\s+user',
        content_lower
    ))
    checks.append(check(
        "retention_winback_sequence",
        has_winback,
        "Retention section must include a win-back sequence for inactive users" if not has_winback else "Found"
    ))

    # CHECK 4b: Feature announcement template
    has_feature_announcement = bool(re.search(
        r'feature\s+announcement|new\s+feature.*?template|announcement\s+(?:template|email)',
        content_lower
    ))
    checks.append(check(
        "retention_feature_announcement",
        has_feature_announcement,
        "Retention section must include a feature announcement template" if not has_feature_announcement else "Found"
    ))

    # CHECK 4c: Feedback request email
    has_feedback = bool(re.search(
        r'feedback\s+(?:request|email)|request.*?feedback|survey|nps',
        content_lower
    ))
    checks.append(check(
        "retention_feedback_request",
        has_feedback,
        "Retention section must include a feedback request email" if not has_feedback else "Found"
    ))

    # ===========================================================
    # CHECK 5: Email Best Practices section
    # ===========================================================
    has_best_practices = bool(re.search(
        r'best\s+practices?|subject\s+line\s+formula|send\s+time|plain\s+text',
        content_lower
    ))
    checks.append(check(
        "section_email_best_practices",
        has_best_practices,
        "Must contain an Email Best Practices section" if not has_best_practices else "Found"
    ))

    # CHECK 5a: Subject line formulas
    has_subject_formulas = bool(re.search(
        r'subject\s+line\s+(?:formula|tip|best|pattern|example)|formula.*subject',
        content_lower
    ))
    checks.append(check(
        "best_practices_subject_line_formulas",
        has_subject_formulas,
        "Best practices must include subject line formulas" if not has_subject_formulas else "Found"
    ))

    # CHECK 5b: Plain text vs designed email
    has_plain_text = bool(re.search(
        r'plain\s+text|plain-text|html\s+email|designed\s+email',
        content_lower
    ))
    checks.append(check(
        "best_practices_plain_text_vs_designed",
        has_plain_text,
        "Best practices must address plain text vs designed emails" if not has_plain_text else "Found"
    ))

    # ===========================================================
    # CHECK 6: Action Plan - must be a numbered checklist
    # ===========================================================
    has_action_plan = bool(re.search(
        r'action\s+plan',
        content_lower
    ))
    checks.append(check(
        "section_action_plan",
        has_action_plan,
        "Must contain an Action Plan section" if not has_action_plan else "Found"
    ))

    # Check it's a numbered list (at least 3 numbered items)
    numbered_items = re.findall(
        r'^\s*\d+[\.\)]\s+\S',
        content,
        re.MULTILINE
    )
    has_numbered_checklist = len(numbered_items) >= 3
    checks.append(check(
        "action_plan_is_numbered_checklist",
        has_numbered_checklist,
        f"Action Plan must be a numbered checklist (found {len(numbered_items)} numbered items, need ≥3)" if not has_numbered_checklist else f"Found {len(numbered_items)} numbered items"
    ))

    # ===========================================================
    # CHECK 7: Further Reading with required URLs (proprietary trap)
    # ===========================================================
    has_further_reading = bool(re.search(
        r'further\s+reading|resources?|references?',
        content_lower
    ))
    checks.append(check(
        "section_further_reading",
        has_further_reading,
        "Must contain a Further Reading / Resources section" if not has_further_reading else "Found"
    ))

    # Specific required URLs from SKILL.md - these are the proprietary trap
    required_urls = [
        ("saasplaybook.co", "https://saasplaybook.co/"),
        ("userlist.com/worksheets", "https://userlist.com/worksheets/"),
    ]
    for url_fragment, full_url in required_urls:
        has_url = url_fragment in content_lower or url_fragment in content
        checks.append(check(
            f"further_reading_url_{url_fragment.replace('/', '_').replace('.', '_')}",
            has_url,
            f"Further Reading must include {full_url}" if not has_url else f"Found URL: {url_fragment}"
        ))

    # At least 3 external URLs total in Further Reading
    all_urls = re.findall(r'https?://\S+', content)
    has_enough_urls = len(all_urls) >= 3
    checks.append(check(
        "further_reading_has_at_least_3_urls",
        has_enough_urls,
        f"Further Reading should have ≥3 resource URLs (found {len(all_urls)})" if not has_enough_urls else f"Found {len(all_urls)} URLs"
    ))

    # ===========================================================
    # CHECK 8: Context-specificity — must reference TaskFlow's actual context
    # ===========================================================
    has_taskflow = bool(re.search(r'taskflow|sprint|project\s+management|customer\.io|segment', content_lower))
    checks.append(check(
        "content_is_taskflow_specific",
        has_taskflow,
        "Output must be tailored to the TaskFlow context from context_brief.txt" if not has_taskflow else "Found TaskFlow-specific content"
    ))

    # Must mention reverse trial (specific business model from brief)
    has_reverse_trial = bool(re.search(r'reverse\s+trial', content_lower))
    checks.append(check(
        "content_addresses_reverse_trial_model",
        has_reverse_trial,
        "Must address the reverse trial business model from the brief" if not has_reverse_trial else "Found reverse trial mention"
    ))

    # ===========================================================
    # SCORING
    # ===========================================================
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Must pass these critical checks to overall pass
    critical_checks = [
        "output_file_exists",
        "section_onboarding_sequence",
        "onboarding_sequence_5_to_7_emails",
        "emails_include_subject_lines",
        "emails_include_behavioral_triggers",
        "section_trial_to_paid",
        "section_retention_reengagement",
        "section_action_plan",
        "action_plan_is_numbered_checklist",
        "section_further_reading",
        "further_reading_url_saasplaybook_co",
        "content_is_taskflow_specific",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.72

    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()