import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 0.0


def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight


def find_deliverable(pattern):
    """Search workspace for a file matching glob pattern."""
    results = list(workspace.rglob(pattern))
    return results[0] if results else None


def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None


# ═══════════════════════════════════════════════════════════════════════
# DELIVERABLE 1: Exit Survey Design (exit_survey_design.md or .json or .txt)
# ═══════════════════════════════════════════════════════════════════════

survey_file = find_deliverable("exit_survey_design.*")
if survey_file is None:
    survey_file = find_deliverable("*exit_survey*")

survey_text = read_file(survey_file) if survey_file else None

if survey_text is None:
    add_check("exit_survey_file_exists", False, "No exit survey design file found in workspace.", weight=2)
    # Add placeholder failures for sub-checks
    for name in [
        "exit_survey_reason_count",
        "exit_survey_each_reason_one_offer",
        "exit_survey_just_testing_no_offer",
        "exit_survey_discount_not_for_adoption_feature",
        "exit_survey_pause_for_seasonal",
    ]:
        add_check(name, False, "No exit survey file to evaluate.", weight=1)
else:
    add_check("exit_survey_file_exists", True, f"Found: {survey_file.name}", weight=2)

    # Count distinct reason categories (look for bullet/numbered/table rows with reasons)
    # We look for lines that appear to be reason entries
    reason_indicators = [
        r"too expensive", r"not using", r"missing.*feature", r"switching.*competitor",
        r"project.*end|seasonal", r"too complicated|hard to use", r"just testing|never needed",
        r"other"
    ]
    found_reasons = []
    survey_lower = survey_text.lower()
    for pat in reason_indicators:
        if re.search(pat, survey_lower):
            found_reasons.append(pat)

    reason_count = len(found_reasons)
    # Must have 6-8 reasons
    count_ok = 6 <= reason_count <= 8
    add_check(
        "exit_survey_reason_count",
        count_ok,
        f"Found ~{reason_count} distinct reason categories. Required: 6-8. Matched: {found_reasons}",
        weight=2
    )

    # Each reason maps to exactly one offer type — check that the doc mentions mapping
    has_mapping = bool(re.search(r"(offer|save offer|primary offer|map)", survey_lower))
    add_check(
        "exit_survey_each_reason_one_offer",
        has_mapping,
        "Document must show explicit offer mapping for each reason category.",
        weight=1
    )

    # "Just testing" / "never needed" → NO OFFER (skip)
    just_testing_section = re.search(
        r"(just testing|never needed|wrong fit)[^\n]{0,200}",
        survey_lower
    )
    just_testing_no_offer = False
    if just_testing_section:
        snippet = just_testing_section.group(0)
        # Should indicate skip/no offer, NOT a discount or pause
        no_offer_keywords = ["no offer", "skip", "let them go", "always skip", "none"]
        just_testing_no_offer = any(kw in snippet for kw in no_offer_keywords)

    add_check(
        "exit_survey_just_testing_no_offer",
        just_testing_no_offer,
        (
            "'Just testing / never needed' must map to NO save offer (skip). "
            f"Found snippet: {just_testing_section.group(0)[:120] if just_testing_section else 'not found'}"
        ),
        weight=2
    )

    # Discount must NOT be mapped to adoption/feature issues
    # Check that discount is only for price objection
    discount_for_adoption = bool(re.search(
        r"(not using|adoption|missing.*feature|too complicated)[^\n]{0,150}discount",
        survey_lower
    ))
    add_check(
        "exit_survey_discount_not_for_adoption_feature",
        not discount_for_adoption,
        (
            "Discount offer must NOT be shown for adoption failures or missing-feature reasons. "
            "A generic discount for all reasons is explicitly prohibited."
        ),
        weight=2
    )

    # Pause for seasonal/project-ended
    pause_for_seasonal = bool(re.search(
        r"(project.*end|seasonal|not using)[^\n]{0,150}pause",
        survey_lower
    ))
    add_check(
        "exit_survey_pause_for_seasonal",
        pause_for_seasonal,
        "Pause offer must be mapped to 'project ended / seasonal' and/or 'not using enough' reasons.",
        weight=1
    )

# ═══════════════════════════════════════════════════════════════════════
# DELIVERABLE 2: Dunning Email Sequence (dunning_sequence.md or similar)
# ═══════════════════════════════════════════════════════════════════════

dunning_file = find_deliverable("dunning_sequence.*")
if dunning_file is None:
    dunning_file = find_deliverable("*dunning*")
if dunning_file is None:
    dunning_file = find_deliverable("*payment_recovery*")

dunning_text = read_file(dunning_file) if dunning_file else None

if dunning_text is None:
    add_check("dunning_file_exists", False, "No dunning sequence file found in workspace.", weight=2)
    for name in [
        "dunning_five_emails",
        "dunning_correct_days_0_3_7_12_16",
        "dunning_day2_preview_before_retry",
        "dunning_no_retry_fraudulent_lost_stolen",
        "dunning_cta_payment_page_not_dashboard",
        "dunning_no_guilt_tone",
        "dunning_smart_retries_recommendation",
    ]:
        add_check(name, False, "No dunning file to evaluate.", weight=1)
else:
    add_check("dunning_file_exists", True, f"Found: {dunning_file.name}", weight=2)

    dunning_lower = dunning_text.lower()

    # Must have 5 emails
    email_count_matches = len(re.findall(
        r"(email [1-5]|day 0|day 3|day 7|day 12|day 16|payment failed.*subject|action needed|account at risk|final notice|account.*cancelled)",
        dunning_lower
    ))
    has_five_emails = email_count_matches >= 4  # at least 4 of these markers present
    add_check(
        "dunning_five_emails",
        has_five_emails,
        f"Expected 5 emails in the sequence. Found {email_count_matches} key markers.",
        weight=2
    )

    # Correct days: 0, 3, 7, 12, 16 (NOT 0,1,3,5,10 or similar)
    day_0 = bool(re.search(r"day\s*0", dunning_lower))
    day_3 = bool(re.search(r"day\s*3", dunning_lower))
    day_7 = bool(re.search(r"day\s*7", dunning_lower))
    day_12 = bool(re.search(r"day\s*12", dunning_lower))
    day_16 = bool(re.search(r"day\s*16", dunning_lower))
    correct_days = all([day_0, day_3, day_7, day_12, day_16])
    add_check(
        "dunning_correct_days_0_3_7_12_16",
        correct_days,
        (
            f"Days must be 0, 3, 7, 12, 16. "
            f"Found: day0={day_0}, day3={day_3}, day7={day_7}, day12={day_12}, day16={day_16}. "
            "Wrong days (e.g. 0,3,5,7,10) indicate generic guessing."
        ),
        weight=3
    )

    # Day-before-retry: Email 2 goes out the day BEFORE retry 1 (so customer can update card)
    day_before_retry = bool(re.search(
        r"(day before|before.*retry|before the retry|update.*before|retry.*tomorrow)",
        dunning_lower
    ))
    add_check(
        "dunning_day2_preview_before_retry",
        day_before_retry,
        (
            "Email 2 (day 2/3) must be framed as a heads-up sent BEFORE the retry attempt, "
            "so customers can update their card first. "
            "Generic agents typically send it ON the retry day."
        ),
        weight=2
    )

    # Must NOT retry fraudulent, lost, stolen cards
    no_retry_rule = bool(re.search(
        r"(never retry|do not retry|don.t retry).{0,100}(fraud|lost|stolen)",
        dunning_lower
    )) or bool(re.search(
        r"(fraud|lost.*card|stolen).{0,100}(never retry|do not retry|don.t retry|no retry)",
        dunning_lower
    ))
    add_check(
        "dunning_no_retry_fraudulent_lost_stolen",
        no_retry_rule,
        (
            "Must explicitly state: never retry fraudulent, lost_card, or stolen_card declines. "
            "This is a proprietary rule from the failure mode taxonomy."
        ),
        weight=2
    )

    # CTA must link to payment update page, NOT dashboard
    cta_payment_not_dashboard = bool(re.search(
        r"(update.*payment|payment.*update|payment.*method|update.*card|card.*update)",
        dunning_lower
    )) and not bool(re.search(
        r"link(s)? to (the )?dashboard",
        dunning_lower
    ))
    add_check(
        "dunning_cta_payment_page_not_dashboard",
        cta_payment_not_dashboard,
        (
            "Every dunning email CTA must link directly to the payment update page, "
            "NOT the generic dashboard. This is an explicit rule in the skill."
        ),
        weight=1
    )

    # No guilt/shame language — check for presence of a no-guilt note
    no_guilt = bool(re.search(
        r"(no guilt|no shame|not a scolding|treat.*adult|adult|happen(s)?|operational|matter.of.fact)",
        dunning_lower
    ))
    add_check(
        "dunning_no_guilt_tone",
        no_guilt,
        "Dunning emails must explicitly avoid guilt/shame language. Document should note this tone rule.",
        weight=1
    )

    # Recommend Smart Retries (Stripe) OR note retry conflict
    smart_retries = bool(re.search(r"smart ret(ry|ries)", dunning_lower))
    add_check(
        "dunning_smart_retries_recommendation",
        smart_retries,
        "Should recommend enabling Stripe Smart Retries (currently disabled per stripe_integration_notes.md).",
        weight=1
    )

# ═══════════════════════════════════════════════════════════════════════
# DELIVERABLE 3: Cancel Flow Audit Scorecard (cancel_flow_audit.json)
# ═══════════════════════════════════════════════════════════════════════

audit_file = find_deliverable("cancel_flow_audit.json")
if audit_file is None:
    audit_file = find_deliverable("*audit*.json")

audit_text = read_file(audit_file) if audit_file else None
audit_data = None

if audit_text is None:
    add_check("audit_file_exists", False, "No cancel_flow_audit.json found.", weight=2)
    for name in [
        "audit_seven_dimensions",
        "audit_scores_0_5_or_10_only",
        "audit_total_score_correct",
        "audit_score_interpretation_correct",
        "audit_prioritized_fixes_present",
        "audit_accessibility_score_correct",
        "audit_exit_survey_score_correct",
        "audit_save_offer_score_correct",
        "audit_confirmation_score_correct",
        "audit_post_cancel_score_correct",
        "audit_dunning_score_correct",
        "audit_analytics_score_correct",
    ]:
        add_check(name, False, "No audit file to evaluate.", weight=1)
else:
    try:
        audit_data = json.loads(audit_text)
        add_check("audit_file_exists", True, f"Found and parsed: {audit_file.name}", weight=2)
    except json.JSONDecodeError as e:
        add_check("audit_file_exists", False, f"File found but invalid JSON: {e}", weight=2)
        audit_data = None
        for name in [
            "audit_seven_dimensions", "audit_scores_0_5_or_10_only",
            "audit_total_score_correct", "audit_score_interpretation_correct",
            "audit_prioritized_fixes_present",
            "audit_accessibility_score_correct", "audit_exit_survey_score_correct",
            "audit_save_offer_score_correct", "audit_confirmation_score_correct",
            "audit_post_cancel_score_correct", "audit_dunning_score_correct",
            "audit_analytics_score_correct",
        ]:
            add_check(name, False, "Invalid JSON, cannot evaluate.", weight=1)

if audit_data is not None:
    # Expected scores based on the broken flow description + scorecard rubric:
    #
    # Accessibility: cancel buried in Advanced > Danger Zone, not visible from main settings → 0
    # Exit survey: 12 questions, optional, not routed to offers → 0 (it exists but wrong)
    #   Actually "optional, multi-question" = 5 pts per rubric
    # Save offers: generic discount for everyone, not mapped → 5 (offers exist but not mapped)
    # Confirmation clarity: pre-checked boxes, confusing terms, data deleted immediately (not 90 days) → 0
    # Post-cancel sequence: no confirmation email, no re-engagement → 0
    # Dunning: no emails, immediate retry (not smart), smart retries disabled → 0
    # Analytics: only total cancellation count → 0
    #
    # Rubric mapping from cancel-flow-playbook.md:
    # Accessibility 0: cancel requires support ticket / 5: in settings but buried / 10: clearly visible
    #   → buried in Advanced > Danger Zone = 0 or 5; "buried" = 5 per rubric
    # Exit survey 0: none / 5: optional multi-question / 10: required single question mapped to offers
    #   → optional, 12-question, not mapped = 5
    # Save offers 0: none / 5: exist but not mapped / 10: matched to exit reasons
    #   → generic discount for all = 5
    # Confirmation 0: confusing / 5: mentions access end date / 10: clear date + data policy + reactivation
    #   → pre-checked boxes, data deleted immediately = 0
    # Post-cancel 0: nothing / 5: one generic email / 10: confirmation + 7-day re-engagement
    #   → no email = 0
    # Dunning 0: none / 5: basic retry only / 10: retry + email sequence + card updater
    #   → immediate retry only, no emails = 5
    # Analytics 0: no tracking / 5: basic cancellation count / 10: reason tracking + save rate + recovery rate
    #   → total cancellations only = 5
    #
    # Total: 5 + 5 + 5 + 0 + 0 + 5 + 5 = 25 → interpretation: <40 = Major opportunity, build from scratch
    
    EXPECTED_SCORES = {
        "accessibility": 0,   # buried deep, mobile broken — score is 0 not 5; requires support-level effort to find
        "exit_survey": 5,      # optional, multi-question = 5
        "save_offers": 5,      # exist but not mapped = 5
        "confirmation_clarity": 0,  # pre-checked boxes, data deleted immediately, confusing = 0
        "post_cancel_sequence": 0,  # nothing = 0
        "dunning": 5,          # basic retry only (even if poorly timed) = 5
        "analytics": 5,        # basic cancellation count = 5
    }

    # Accessibility: The flow requires Advanced > Danger Zone; mobile is collapsed.
    # This maps to 0: "Cancel requires support ticket" (effectively hidden) 
    # OR 5: "Cancel in settings, but buried"
    # The rubric says 5 = "Cancel in settings, but buried" which fits.
    # However "mobile frequently missed" and "support tickets" suggest near-0.
    # We'll accept 0 OR 5 for accessibility (border case).
    ACCESSIBILITY_ACCEPTABLE = {0, 5}

    # Dunning: immediate retry + 1 day retry then cancel = some retry logic = 5 (basic retry only)
    # No email sequence = can't be 10; has retries = can't be 0.
    DUNNING_EXPECTED = 5

    # Analytics: total cancellations tracked only = 5 (basic cancellation count)
    ANALYTICS_EXPECTED = 5

    # ── Check: 7 dimensions present ──────────────────────────────────────
    required_keys = ["accessibility", "exit_survey", "save_offers",
                     "confirmation_clarity", "post_cancel_sequence", "dunning", "analytics"]
    
    # Try to find scores — could be nested or flat
    def extract_scores(data):
        """Try multiple JSON shapes to find dimension scores."""
        # Shape 1: {"scores": {"accessibility": 5, ...}}
        # Shape 2: {"dimensions": [{"name": "accessibility", "score": 5}]}
        # Shape 3: {"accessibility": 5, ...} flat
        scores = {}
        if isinstance(data, dict):
            # Try "scores" key
            if "scores" in data and isinstance(data["scores"], dict):
                scores = {k.lower().replace(" ", "_"): v for k, v in data["scores"].items()}
            # Try "dimensions" list
            elif "dimensions" in data and isinstance(data["dimensions"], list):
                for item in data["dimensions"]:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("dimension", "")).lower().replace(" ", "_")
                        score = item.get("score", item.get("points", None))
                        if name and score is not None:
                            scores[name] = score
            # Try flat — look for numeric values with known keys
            else:
                for key, val in data.items():
                    k = key.lower().replace(" ", "_").replace("-", "_")
                    if isinstance(val, (int, float)):
                        scores[k] = val
                    elif isinstance(val, dict) and "score" in val:
                        scores[k] = val["score"]
        return scores

    extracted = extract_scores(audit_data)
    
    # Normalize keys (handle variations)
    normalized = {}
    key_map = {
        "accessibility": "accessibility",
        "exit_survey": "exit_survey",
        "exit survey": "exit_survey",
        "save_offers": "save_offers",
        "save offers": "save_offers",
        "save_offer": "save_offers",
        "confirmation_clarity": "confirmation_clarity",
        "confirmation clarity": "confirmation_clarity",
        "confirmation": "confirmation_clarity",
        "post_cancel_sequence": "post_cancel_sequence",
        "post cancel sequence": "post_cancel_sequence",
        "post-cancel sequence": "post_cancel_sequence",
        "post_cancel": "post_cancel_sequence",
        "dunning": "dunning",
        "analytics": "analytics",
    }
    for k, v in extracted.items():
        mapped = key_map.get(k, k)
        normalized[mapped] = v

    dims_found = [k for k in required_keys if k in normalized]
    has_seven = len(dims_found) == 7
    add_check(
        "audit_seven_dimensions",
        has_seven,
        f"Required 7 dimensions. Found: {dims_found}. Missing: {[k for k in required_keys if k not in dims_found]}",
        weight=2
    )

    # ── Check: scores are only 0, 5, or 10 ──────────────────────────────
    valid_values = {0, 5, 10}
    invalid_scores = {k: v for k, v in normalized.items() if k in required_keys and v not in valid_values}
    scores_valid = len(invalid_scores) == 0 and len(dims_found) > 0
    add_check(
        "audit_scores_0_5_or_10_only",
        scores_valid,
        (
            f"All scores must be 0, 5, or 10 per the audit rubric. "
            f"Invalid scores found: {invalid_scores}. "
            f"Scores given: {normalized}"
        ),
        weight=3
    )

    # ── Check: total score calculation ───────────────────────────────────
    # Expected total: depends on exact dimension scores (border cases exist for accessibility)
    actual_total = sum(normalized.get(k, -1) for k in required_keys if k in normalized)
    # Acceptable totals: if accessibility=0 → 20, if accessibility=5 → 25
    total_ok = actual_total in range(15, 36)  # reasonable range given border cases
    
    # More strictly: confirm it's the SUM of the dimension scores
    computed_total = sum(normalized.get(k, 0) for k in required_keys if k in normalized)
    total_reported = None
    if isinstance(audit_data, dict):
        for key in ["total", "total_score", "score", "overall_score", "overall"]:
            if key in audit_data:
                total_reported = audit_data[key]
                break

    total_consistent = (total_reported is None) or (abs(total_reported - computed_total) <= 2)
    add_check(
        "audit_total_score_correct",
        total_consistent and len(dims_found) >= 5,
        (
            f"Total score must equal sum of dimension scores. "
            f"Computed: {computed_total}, Reported: {total_reported}. "
            f"Dimension scores: {normalized}"
        ),
        weight=2
    )

    # ── Check: score interpretation ───────────────────────────────────────
    audit_text_lower = audit_text.lower() if audit_text else ""
    # Total <40 → "Major opportunity. Build from scratch."
    # Actual total will be 20-25, so interpretation must be "<40" bucket
    correct_interpretation = bool(re.search(
        r"(major opportunity|build from scratch|<\s*40|under 40|below 40)",
        audit_text_lower
    ))
    add_check(
        "audit_score_interpretation_correct",
        correct_interpretation,
        (
            "Score <40 must be interpreted as 'Major opportunity. Build from scratch using this playbook.' "
            "The audit's total score should fall in this bucket."
        ),
        weight=2
    )

    # ── Check: prioritized fixes present ─────────────────────────────────
    has_fixes = bool(re.search(
        r"(prioriti|fix|action|recommend|next step)",
        audit_text_lower
    ))
    add_check(
        "audit_prioritized_fixes_present",
        has_fixes,
        "Scorecard must include prioritized fixes / recommendations, not just raw scores.",
        weight=1
    )

    # ── Per-dimension score checks ────────────────────────────────────────
    # Accessibility: 0 or 5 acceptable (buried)
    acc_score = normalized.get("accessibility")
    add_check(
        "audit_accessibility_score_correct",
        acc_score in ACCESSIBILITY_ACCEPTABLE,
        (
            f"Accessibility: buried in Advanced > Danger Zone. "
            f"Rubric: 0=requires support ticket, 5=in settings but buried, 10=clearly visible. "
            f"Expected 0 or 5. Got: {acc_score}"
        ),
        weight=1
    )

    # Exit survey: optional, 12-question, not mapped → score 5 ("Optional, multi-question")
    survey_score = normalized.get("exit_survey")
    add_check(
        "audit_exit_survey_score_correct",
        survey_score == 5,
        (
            f"Exit survey: optional, 12 questions, not routed to offers. "
            f"Rubric: 5 = 'Optional, multi-question'. Expected 5. Got: {survey_score}"
        ),
        weight=2
    )

    # Save offers: generic discount for everyone → 5 ("Offers exist but not mapped")
    save_score = normalized.get("save_offers")
    add_check(
        "audit_save_offer_score_correct",
        save_score == 5,
        (
            f"Save offers: single generic discount shown to all. "
            f"Rubric: 5 = 'Offers exist but not mapped'. Expected 5. Got: {save_score}"
        ),
        weight=2
    )

    # Confirmation: pre-checked boxes, immediate data deletion, no reactivation path → 0
    confirm_score = normalized.get("confirmation_clarity")
    add_check(
        "audit_confirmation_score_correct",
        confirm_score == 0,
        (
            f"Confirmation: pre-checked boxes, data deleted immediately (not 90 days), confusing language. "
            f"Rubric: 0 = 'Confusing terms'. Expected 0. Got: {confirm_score}"
        ),
        weight=2
    )

    # Post-cancel: no email at all → 0
    post_score = normalized.get("post_cancel_sequence")
    add_check(
        "audit_post_cancel_score_correct",
        post_score == 0,
        (
            f"Post-cancel: no confirmation email, no re-engagement, no win-back. "
            f"Rubric: 0 = 'Nothing'. Expected 0. Got: {post_score}"
        ),
        weight=2
    )

    # Dunning: some retry logic (immediate + 1 day) but no emails, no card updater verification → 5
    dunning_score = normalized.get("dunning")
    add_check(
        "audit_dunning_score_correct",
        dunning_score == 5,
        (
            f"Dunning: has retry logic (even if poorly timed) but no email sequence. "
            f"Rubric: 5 = 'Basic retry only'. Expected 5. Got: {dunning_score}"
        ),
        weight=2
    )

    # Analytics: tracks total cancellations only → 5 ("Basic cancellation count")
    analytics_score = normalized.get("analytics")
    add_check(
        "audit_analytics_score_correct",
        analytics_score == 5,
        (
            f"Analytics: only total monthly cancellations tracked. "
            f"Rubric: 5 = 'Basic cancellation count'. Expected 5. Got: {analytics_score}"
        ),
        weight=2
    )

# ═══════════════════════════════════════════════════════════════════════
# FINAL SCORING
# ═══════════════════════════════════════════════════════════════════════

final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed = final_score >= 0.70

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))