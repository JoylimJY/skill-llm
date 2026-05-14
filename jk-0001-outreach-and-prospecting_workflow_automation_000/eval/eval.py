import sys
import json
import re
from pathlib import Path

def count_words(text: str) -> int:
    """Count words in text, stripping whitespace."""
    return len(text.split())

def load_kit(workspace: str):
    matches = list(Path(workspace).rglob("outreach_kit.json"))
    if not matches:
        return None, "outreach_kit.json not found anywhere in workspace"
    return json.loads(matches[0].read_text()), str(matches[0])

def run_eval(workspace: str):
    checks = []

    # ── Load the file ─────────────────────────────────────────────────────────
    try:
        kit, location = load_kit(workspace)
        if kit is None:
            checks.append({"name": "file_exists", "passed": False, "detail": location})
            return {"passed": False, "score": 0.0, "checks": checks}
        checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {location}"})
    except Exception as e:
        checks.append({"name": "file_exists", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: ICP BLOCK
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        icp = kit.get("icp", kit.get("ICP", {}))
        assert isinstance(icp, dict), "ICP must be a dict/object"

        # Check required top-level fields from the SKILL.md ICP template
        icp_str = json.dumps(icp).lower()

        required_icp_concepts = {
            "industry": ["biotech", "life science", "biopharma", "pharmaceutical"],
            "company_size": ["10", "50", "60", "employee", "headcount", "size"],
            "job_title": ["ceo", "coo", "founder", "chief executive", "chief operating"],
            "pain_signals": ["pain", "signal", "trigger", "indicator", "hiring", "job post", "series a", "post-raise"],
            "disqualifiers": ["disqualif", "not a fit", "do not", "avoid", "exclude", "pre-seed", "bootstrap"],
        }

        icp_concept_results = {}
        for concept, keywords in required_icp_concepts.items():
            found = any(kw in icp_str for kw in keywords)
            icp_concept_results[concept] = found

        icp_all_passed = all(icp_concept_results.values())
        checks.append({
            "name": "icp_required_fields",
            "passed": icp_all_passed,
            "detail": f"Concept coverage: {icp_concept_results}"
        })
    except Exception as e:
        checks.append({"name": "icp_required_fields", "passed": False, "detail": str(e)})

    # Check disqualifiers is a list with at least 2 items
    try:
        icp = kit.get("icp", kit.get("ICP", {}))
        disq = None
        for key in icp:
            if "disqualif" in key.lower() or "not_" in key.lower() or "exclude" in key.lower():
                disq = icp[key]
                break
        if disq is None:
            # try nested
            for v in icp.values():
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        if "disqualif" in k2.lower():
                            disq = v2
        has_disq = (isinstance(disq, list) and len(disq) >= 2) or \
                   (isinstance(disq, str) and len(disq.split("\n")) >= 2) or \
                   (isinstance(disq, str) and len(disq) > 40)
        checks.append({
            "name": "icp_disqualifiers_populated",
            "passed": bool(has_disq),
            "detail": f"Disqualifiers found: {repr(disq)[:200] if disq else 'None'}"
        })
    except Exception as e:
        checks.append({"name": "icp_disqualifiers_populated", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: COLD EMAIL
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        email_block = None
        for key in kit:
            if "email" in key.lower() or "cold_email" in key.lower():
                email_block = kit[key]
                break

        assert email_block is not None, "No cold_email key found in kit"

        # Extract subject and body
        if isinstance(email_block, dict):
            subject = str(email_block.get("subject", email_block.get("subject_line", "")))
            body = str(email_block.get("body", email_block.get("email_body", "")))
            if not body:
                # try concatenating all non-subject fields
                body = " ".join(str(v) for k, v in email_block.items() if "subject" not in k.lower())
        else:
            # Plain string — split on newline
            full_text = str(email_block)
            lines = full_text.strip().split("\n")
            subject = lines[0] if lines else ""
            body = "\n".join(lines[1:])

        checks.append({"name": "cold_email_exists", "passed": True, "detail": f"Subject: {subject[:80]}"})
    except Exception as e:
        checks.append({"name": "cold_email_exists", "passed": False, "detail": str(e)})
        checks.append({"name": "cold_email_under_100_words", "passed": False, "detail": "Email block missing"})
        checks.append({"name": "cold_email_subject_not_generic", "passed": False, "detail": "Email block missing"})
        checks.append({"name": "cold_email_first_name_signoff", "passed": False, "detail": "Email block missing"})
        checks.append({"name": "cold_email_personalized_hook", "passed": False, "detail": "Email block missing"})
        checks.append({"name": "cold_email_low_commitment_ask", "passed": False, "detail": "Email block missing"})
        email_block = None

    if email_block is not None:
        # Word count under 100
        try:
            body_words = count_words(body)
            passed_wc = body_words <= 100
            checks.append({
                "name": "cold_email_under_100_words",
                "passed": passed_wc,
                "detail": f"Body word count: {body_words} (must be ≤100)"
            })
        except Exception as e:
            checks.append({"name": "cold_email_under_100_words", "passed": False, "detail": str(e)})

        # Subject line: not generic/spammy
        try:
            banned_subjects = ["quick question", "synergy", "intro", "opportunity", "hope this finds you", "following up"]
            subject_lower = subject.lower()
            is_bad_subject = any(b in subject_lower for b in banned_subjects)
            # Must reference something specific (Alex, QuantumCell, Series A, VP Finance, post-raise, etc.)
            good_signals = ["quantumcell", "alex", "series a", "vp finance", "post-raise", "november", "hiring", "job", "funding"]
            has_specificity = any(g in subject_lower for g in good_signals)
            passed_subj = (not is_bad_subject) and has_specificity
            checks.append({
                "name": "cold_email_subject_not_generic",
                "passed": passed_subj,
                "detail": f"Subject: '{subject}' | Bad pattern: {is_bad_subject} | Specific: {has_specificity}"
            })
        except Exception as e:
            checks.append({"name": "cold_email_subject_not_generic", "passed": False, "detail": str(e)})

        # Sign-off: first name only (no title, no company name)
        try:
            full_email_text = subject + "\n" + body
            # Check for title-style sign-offs: CPA, CFA, "LLC", "Advisory", job title
            bad_signoff_patterns = [
                r'\bCPA\b', r'\bCFA\b', r'\bMBA\b', r'\bLLC\b', r'\bAdvisory\b',
                r'Best regards,\s*\n.*\n', r'Sincerely,\s*\n.*\n',
                r'VP\b', r'Chief\b', r'Director\b', r'Fractional CFO\n'
            ]
            signoff_violation = any(re.search(p, full_email_text, re.IGNORECASE) for p in bad_signoff_patterns)

            # Must have a first-name sign-off
            signoff_area = body[-200:] if len(body) > 200 else body
            has_first_name = bool(re.search(r'\b(Jordan|Alex|John|Sam)\b', signoff_area))
            # More flexible: check that sign-off is short (1-2 words after a comma)
            has_short_signoff = bool(re.search(r'(?:^|\n)\s*[-–]?\s*[A-Z][a-z]+\s*$', signoff_area, re.MULTILINE))

            passed_signoff = (not signoff_violation) and (has_first_name or has_short_signoff)
            checks.append({
                "name": "cold_email_first_name_signoff",
                "passed": passed_signoff,
                "detail": f"Violation patterns found: {signoff_violation} | First name present: {has_first_name} | Short sign-off: {has_short_signoff}"
            })
        except Exception as e:
            checks.append({"name": "cold_email_first_name_signoff", "passed": False, "detail": str(e)})

        # Personalized hook (references QuantumCell, Alex, Series A, job posting, or post)
        try:
            body_lower = body.lower()
            hook_signals = ["quantumcell", "alex", "series a", "vp finance", "hired", "hiring", "job post",
                            "post-raise", "november", "$9m", "9m", "post last week", "exciting and terrifying"]
            has_hook = any(s in body_lower for s in hook_signals)
            checks.append({
                "name": "cold_email_personalized_hook",
                "passed": has_hook,
                "detail": f"Body preview: {body[:200]}"
            })
        except Exception as e:
            checks.append({"name": "cold_email_personalized_hook", "passed": False, "detail": str(e)})

        # Low-commitment ask (not "30-min call", "schedule a meeting", "45-min")
        try:
            body_lower = body.lower()
            bad_asks = ["30-min", "30 min", "45-min", "45 min", "schedule a meeting", "let's connect",
                        "at your earliest convenience", "i'd love to", "hop on a call this week"]
            good_asks = ["10-min", "10 min", "worth a quick", "send over", "quick example", 
                         "relevant", "if this is relevant", "quick chat"]
            has_bad_ask = any(b in body_lower for b in bad_asks)
            has_good_ask = any(g in body_lower for g in good_asks)
            passed_ask = (not has_bad_ask) and has_good_ask
            checks.append({
                "name": "cold_email_low_commitment_ask",
                "passed": passed_ask,
                "detail": f"Bad ask found: {has_bad_ask} | Good ask found: {has_good_ask}"
            })
        except Exception as e:
            checks.append({"name": "cold_email_low_commitment_ask", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: MULTI-TOUCH SEQUENCE
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        seq = None
        for key in kit:
            if "sequence" in key.lower() or "multi" in key.lower() or "touch" in key.lower():
                seq = kit[key]
                break
        assert seq is not None, "No sequence key found in kit"

        if isinstance(seq, list):
            touchpoints = seq
        elif isinstance(seq, dict):
            # Could be {day_1: ..., day_3: ...} or {touchpoints: [...]}
            if "touchpoints" in seq:
                touchpoints = seq["touchpoints"]
            else:
                touchpoints = list(seq.values())
        else:
            touchpoints = []

        checks.append({
            "name": "sequence_exists",
            "passed": True,
            "detail": f"Sequence found with {len(touchpoints)} items"
        })
    except Exception as e:
        checks.append({"name": "sequence_exists", "passed": False, "detail": str(e)})
        for c in ["sequence_5_touchpoints", "sequence_correct_days", "sequence_multi_channel",
                  "sequence_final_clean_exit", "sequence_no_repeat_channel_per_week"]:
            checks.append({"name": c, "passed": False, "detail": "Sequence missing"})
        touchpoints = None
        seq = None

    if touchpoints is not None:
        # 5 touchpoints (3-5 acceptable per skill doc, exact from example is 6 items but rule says 3-5)
        try:
            n = len(touchpoints)
            passed_n = 3 <= n <= 6  # 5 from example, allow slight variation
            checks.append({
                "name": "sequence_5_touchpoints",
                "passed": passed_n,
                "detail": f"Number of touchpoints: {n} (expected 3-6)"
            })
        except Exception as e:
            checks.append({"name": "sequence_5_touchpoints", "passed": False, "detail": str(e)})

        # Correct days: must include Day 1, Day 5 (cold email day), Day 14, Day 21
        try:
            seq_str = json.dumps(seq).lower()
            required_days = {
                "day_1": ["day 1", "day1", "day_1"],
                "day_5": ["day 5", "day5", "day_5"],
                "day_14": ["day 14", "day14", "day_14"],
                "day_21": ["day 21", "day21", "day_21"],
            }
            day_hits = {d: any(pat in seq_str for pat in pats) for d, pats in required_days.items()}
            passed_days = sum(day_hits.values()) >= 3
            checks.append({
                "name": "sequence_correct_days",
                "passed": passed_days,
                "detail": f"Day markers found: {day_hits}"
            })
        except Exception as e:
            checks.append({"name": "sequence_correct_days", "passed": False, "detail": str(e)})

        # Multi-channel: must include both LinkedIn and email
        try:
            seq_str = json.dumps(seq).lower()
            has_linkedin = "linkedin" in seq_str
            has_email = "email" in seq_str
            passed_channels = has_linkedin and has_email
            checks.append({
                "name": "sequence_multi_channel",
                "passed": passed_channels,
                "detail": f"LinkedIn: {has_linkedin}, Email: {has_email}"
            })
        except Exception as e:
            checks.append({"name": "sequence_multi_channel", "passed": False, "detail": str(e)})

        # Final touchpoint must be a "clean exit" message
        try:
            seq_str = json.dumps(seq).lower()
            clean_exit_signals = [
                "last note", "last message", "last touch", "final note",
                "timing isn't right", "timing is not right", "totally understand",
                "happy to reconnect", "no pressure", "clean exit", "won't reach out",
                "last time", "no guilt", "leaving it here"
            ]
            has_clean_exit = any(s in seq_str for s in clean_exit_signals)
            checks.append({
                "name": "sequence_final_clean_exit",
                "passed": has_clean_exit,
                "detail": f"Clean exit language found: {has_clean_exit}"
            })
        except Exception as e:
            checks.append({"name": "sequence_final_clean_exit", "passed": False, "detail": str(e)})

        # No same channel twice per week (check that Day 3 and Day 5 are different channels from Day 1)
        try:
            seq_str = json.dumps(seq).lower()
            # Day 1 = LinkedIn connection request
            # Day 3 = LinkedIn message (so Day 1 and Day 3 are both LinkedIn, same week but different type — OK per skill)
            # Day 5 = Cold email (different channel) — MUST be present
            # The rule is no more than one touchpoint per channel per WEEK
            # Day 1 (LinkedIn) and Day 3 (LinkedIn message) = same channel 2x in week 1 → violates rule?
            # Actually: "Never more than one touchpoint per channel per week"
            # Day 1 and Day 3 are 2 LinkedIn touches in week 1 → strict reading = violation
            # But the example sequence in the skill itself does this (Day 1 LinkedIn, Day 3 LinkedIn)
            # So the rule is aspirational / the example is the authoritative guide
            # We test: that by Day 14, the email follow-up is email (not LinkedIn) and Day 10 is LinkedIn
            day14_region = seq_str[max(0, seq_str.find("day 14") - 20):seq_str.find("day 14") + 200] if "day 14" in seq_str else ""
            day10_region = seq_str[max(0, seq_str.find("day 10") - 20):seq_str.find("day 10") + 200] if "day 10" in seq_str else ""
            # Day 10 should be LinkedIn, Day 14 should be email
            day10_is_linkedin = "linkedin" in day10_region
            day14_is_email = "email" in day14_region or "follow" in day14_region
            passed_channel_rule = day14_is_email  # lenient: just check day 14 is email
            checks.append({
                "name": "sequence_no_repeat_channel_per_week",
                "passed": passed_channel_rule,
                "detail": f"Day 10 LinkedIn: {day10_is_linkedin}, Day 14 Email: {day14_is_email}"
            })
        except Exception as e:
            checks.append({"name": "sequence_no_repeat_channel_per_week", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: LINKEDIN CONNECTION REQUEST
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        li_block = None
        for key in kit:
            if "linkedin" in key.lower() and "connect" in key.lower():
                li_block = kit[key]
                break
        if li_block is None:
            # try searching in nested sequence
            seq_str_full = json.dumps(kit)
            # Look for connection request text in sequence
            for key in kit:
                if "sequence" in key.lower() or "touch" in key.lower():
                    block = kit[key]
                    block_str = json.dumps(block).lower()
                    if "connection" in block_str and "request" in block_str:
                        li_block = block
                        break

        if li_block is None:
            checks.append({
                "name": "linkedin_connection_request",
                "passed": False,
                "detail": "No linkedin_connection_request key found in kit"
            })
        else:
            li_str = json.dumps(li_block) if not isinstance(li_block, str) else li_block
            li_lower = li_str.lower()

            # Must NOT say "I'd love to connect" or generic openers
            banned_li = ["i'd love to connect", "i would love to connect", "i hope this message finds you"]
            has_banned = any(b in li_lower for b in banned_li)

            # Must be short (1-2 sentences = roughly under 40 words for the actual message)
            li_word_count = count_words(li_str)
            # Allow some overhead for JSON keys
            is_short = li_word_count <= 60

            # Must reference the specific trigger (post, Series A, hiring)
            specific_signals = ["post", "series a", "linkedin", "hiring", "quantumcell", "alex", "comment", "vp finance"]
            has_specific = any(s in li_lower for s in specific_signals)

            passed_li = (not has_banned) and is_short and has_specific
            checks.append({
                "name": "linkedin_connection_request",
                "passed": passed_li,
                "detail": f"Banned phrase: {has_banned} | Word count: {li_word_count} (≤60) | Specific: {has_specific}"
            })
    except Exception as e:
        checks.append({"name": "linkedin_connection_request", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: PIPELINE ENTRY
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        pipeline = None
        for key in kit:
            if "pipeline" in key.lower() or "stage" in key.lower() or "track" in key.lower() or "crm" in key.lower():
                pipeline = kit[key]
                break

        assert pipeline is not None, "No pipeline/tracking key found"
        pipeline_str = json.dumps(pipeline).lower()

        # Must include the correct stage (Identified or Contacted — first stage after identification)
        valid_stages = ["identified", "contacted", "replied", "in conversation", "proposal sent",
                        "closed won", "closed lost", "not now"]
        stage_found = any(s in pipeline_str for s in valid_stages)

        # Must include required columns/fields: Lead Name, Company, Source, Date First Contacted, Stage, Next Action
        required_fields = {
            "lead_name": ["lead name", "name", "alex", "turner"],
            "company": ["company", "quantumcell"],
            "source": ["source", "crunchbase", "job post", "linkedin", "funding"],
            "stage": ["stage", "identified", "contacted"],
            "next_action": ["next action", "next_action", "action"],
        }
        field_hits = {f: any(kw in pipeline_str for kw in kws) for f, kws in required_fields.items()}
        all_fields = all(field_hits.values())

        passed_pipeline = stage_found and all_fields
        checks.append({
            "name": "pipeline_entry_correct",
            "passed": passed_pipeline,
            "detail": f"Valid stage: {stage_found} | Field hits: {field_hits}"
        })
    except Exception as e:
        checks.append({"name": "pipeline_entry_correct", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ═══════════════════════════════════════════════════════════════════════════
    weights = {
        "file_exists": 0.05,
        "icp_required_fields": 0.08,
        "icp_disqualifiers_populated": 0.05,
        "cold_email_exists": 0.03,
        "cold_email_under_100_words": 0.12,
        "cold_email_subject_not_generic": 0.08,
        "cold_email_first_name_signoff": 0.10,
        "cold_email_personalized_hook": 0.08,
        "cold_email_low_commitment_ask": 0.10,
        "sequence_exists": 0.03,
        "sequence_5_touchpoints": 0.05,
        "sequence_correct_days": 0.07,
        "sequence_multi_channel": 0.04,
        "sequence_final_clean_exit": 0.05,
        "sequence_no_repeat_channel_per_week": 0.03,
        "linkedin_connection_request": 0.06,
        "pipeline_entry_correct": 0.05,
    }

    check_map = {c["name"]: c["passed"] for c in checks}
    score = sum(weights.get(name, 0.0) * (1.0 if passed else 0.0)
                for name, passed in check_map.items())
    score = round(min(score, 1.0), 4)

    overall = (score >= 0.65) and check_map.get("file_exists", False)

    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))