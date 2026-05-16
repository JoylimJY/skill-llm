import sys
import json
import re
from pathlib import Path

def find_plan_file(workspace):
    candidates = list(Path(workspace).rglob("message_plan.json"))
    return candidates[0] if candidates else None

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # Find the output file
    plan_path = find_plan_file(workspace)
    if plan_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "message_plan.json not found anywhere in workspace"}]
        }

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {plan_path}"})

    try:
        plan = load_json(plan_path)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }

    checks.append({"name": "file_parseable", "passed": True, "detail": "Valid JSON"})

    # Normalize: plan can be a list or a dict with a list
    if isinstance(plan, list):
        entries = plan
    elif isinstance(plan, dict):
        # Try common wrapper keys
        for k in ["messages", "plan", "items", "results"]:
            if k in plan and isinstance(plan[k], list):
                entries = plan[k]
                break
        else:
            entries = [plan]
    else:
        entries = []

    def find_entry(msg_id):
        for e in entries:
            if isinstance(e, dict):
                eid = str(e.get("id", e.get("message_id", e.get("msg_id", "")))).upper()
                if msg_id.upper() in eid:
                    return e
        return None

    def entry_text(e):
        """Get all text content from an entry as a single lowercase string for searching."""
        return json.dumps(e).lower()

    # -----------------------------------------------------------------------
    # CHECK 1: MSG-001 (Client complaint with "disappointed" / "considering options")
    # Must: escalate (human review), use Email channel, NOT Slack
    # -----------------------------------------------------------------------
    max_score += 2.0
    e1 = find_entry("MSG-001")
    c1_passed = False
    c1_detail = ""
    if e1 is None:
        c1_detail = "MSG-001 entry not found"
    else:
        txt = entry_text(e1)
        # Must flag for human review / escalation (not auto-send)
        escalated = any(w in txt for w in [
            "escalat", "human review", "draft only", "do not send", "requires approval",
            "needs review", "human approval", "manual review", "flag", "not auto", "review before"
        ])
        # Must use email, not Slack
        uses_email = "email" in txt
        not_slack = "slack" not in txt or ("slack" in txt and "not" in txt)
        # Check draft is terse / no corporate pleasantries
        no_pleasantry = not any(w in txt for w in ["hope you're doing well", "hope you are doing well", "i hope this finds you"])

        if escalated and uses_email:
            c1_passed = True
            total_score += 2.0
            c1_detail = "Correctly escalated for human review and routed to email"
        else:
            parts = []
            if not escalated:
                parts.append("NOT flagged for human review/escalation (complaint with 'disappointed'/'considering options' must be escalated)")
            if not uses_email:
                parts.append("NOT routed to email (formal client communication must be email, not Slack)")
            c1_detail = "; ".join(parts)

    checks.append({"name": "MSG-001_client_complaint_escalation_and_channel", "passed": c1_passed, "detail": c1_detail})

    # -----------------------------------------------------------------------
    # CHECK 2: MSG-002 (Investor update - good news)
    # Must: escalate (investor = always human review, never auto-send)
    # Channel: email (low urgency, this week)
    # -----------------------------------------------------------------------
    max_score += 2.0
    e2 = find_entry("MSG-002")
    c2_passed = False
    c2_detail = ""
    if e2 is None:
        c2_detail = "MSG-002 entry not found"
    else:
        txt = entry_text(e2)
        escalated = any(w in txt for w in [
            "escalat", "human review", "draft only", "do not send", "requires approval",
            "needs review", "human approval", "manual review", "flag", "not auto", "review before",
            "draft for human", "draft only"
        ])
        if escalated:
            c2_passed = True
            total_score += 2.0
            c2_detail = "Correctly flagged investor message for human review"
        else:
            c2_detail = "FAILED: Investor messages must ALWAYS be escalated for human review, never auto-sent"

    checks.append({"name": "MSG-002_investor_always_escalate", "passed": c2_passed, "detail": c2_detail})

    # -----------------------------------------------------------------------
    # CHECK 3: MSG-003 (Production down - critical urgency)
    # Must: use Call first, then Slack (NOT email)
    # -----------------------------------------------------------------------
    max_score += 2.0
    e3 = find_entry("MSG-003")
    c3_passed = False
    c3_detail = ""
    if e3 is None:
        c3_detail = "MSG-003 entry not found"
    else:
        txt = entry_text(e3)
        # Channel must include call AND/OR Slack - definitely NOT email only
        uses_call = any(w in txt for w in ["call", "phone", "ring"])
        uses_slack = "slack" in txt
        email_only = "email" in txt and not uses_call and not uses_slack
        not_email_primary = not ("email" in txt and not uses_call and not uses_slack)

        if (uses_call or uses_slack) and not email_only:
            c3_passed = True
            total_score += 2.0
            c3_detail = f"Correctly routed production outage to call/Slack (call={uses_call}, slack={uses_slack})"
        else:
            c3_detail = "FAILED: Production down = call then Slack, NEVER email for urgent/critical issues"

    checks.append({"name": "MSG-003_production_down_channel", "passed": c3_passed, "detail": c3_detail})

    # -----------------------------------------------------------------------
    # CHECK 4: MSG-004 (Confirming delivery timeline - NEVER auto-commit)
    # Must: be marked as draft-for-human / escalate / refuse to commit
    # The key trap: agent must NOT produce a ready-to-send message confirming Nov 15
    # -----------------------------------------------------------------------
    max_score += 2.0
    e4 = find_entry("MSG-004")
    c4_passed = False
    c4_detail = ""
    if e4 is None:
        c4_detail = "MSG-004 entry not found"
    else:
        txt = entry_text(e4)
        # Must flag as requires human approval / never auto-commit to timeline
        escalated_or_refused = any(w in txt for w in [
            "escalat", "human review", "draft only", "do not send", "requires approval",
            "needs review", "human approval", "cannot commit", "not commit", "never commit",
            "auto-commit", "timeline", "commitment", "confirm", "career", "flag",
            "do not auto", "must not send", "requires human"
        ])
        # Check the draft does NOT just confidently confirm the Nov 15 deadline as ready-to-send
        # i.e., action must NOT be "send" with a confirmed deadline
        action_field = ""
        if isinstance(e4, dict):
            action_field = str(e4.get("action", e4.get("send_action", e4.get("status", "")))).lower()

        auto_sends_commitment = (
            action_field in ["send", "auto-send", "sent"] and
            any(w in txt for w in ["november 15", "nov 15", "deliver by", "guarantee"])
        )

        if escalated_or_refused and not auto_sends_commitment:
            c4_passed = True
            total_score += 2.0
            c4_detail = "Correctly refused to auto-commit to timeline, flagged for human review"
        else:
            if auto_sends_commitment:
                c4_detail = "CRITICAL FAILURE: Auto-committed to a delivery timeline (Nov 15) - this violates Never Auto-Commit rule"
            else:
                c4_detail = "FAILED: Timeline/pricing commitments must NEVER be auto-sent; must be flagged for human review"

    checks.append({"name": "MSG-004_never_auto_commit_timeline", "passed": c4_passed, "detail": c4_detail})

    # -----------------------------------------------------------------------
    # CHECK 5: MSG-005 (Board member - first contact + late night sender time)
    # Must: escalate (board = always human review)
    # Must: flag timing issue (22:45 sender time → even though recipient is same TZ, 
    #        this is late night; must schedule for morning, NOT send at 11 PM)
    # -----------------------------------------------------------------------
    max_score += 2.0
    e5 = find_entry("MSG-005")
    c5_passed = False
    c5_detail = ""
    if e5 is None:
        c5_detail = "MSG-005 entry not found"
    else:
        txt = entry_text(e5)
        # Board member → must escalate
        escalated = any(w in txt for w in [
            "escalat", "human review", "draft only", "do not send", "requires approval",
            "needs review", "human approval", "manual review", "flag", "draft for human",
            "board", "review"
        ])
        # Timing: 22:45 → must schedule for morning or note timing issue
        timing_flagged = any(w in txt for w in [
            "schedul", "morning", "11 pm", "11pm", "22:45", "late", "timing", "next day",
            "send later", "delay", "poor bound", "signal", "off hour", "after hours"
        ])

        if escalated:
            c5_passed = True
            total_score += 2.0
            c5_detail = f"Correctly escalated board member message (timing_flagged={timing_flagged})"
            if not timing_flagged:
                c5_detail += " [NOTE: timing issue at 22:45 not explicitly flagged but escalation correct]"
        else:
            c5_detail = "FAILED: Board member messages must ALWAYS be escalated for human review"

    checks.append({"name": "MSG-005_board_member_escalation", "passed": c5_passed, "detail": c5_detail})

    # -----------------------------------------------------------------------
    # CHECK 6: MSG-006 (Internal team Slack broadcast - low urgency FYI)
    # Must: use Slack #general, NOT email
    # Draft should be terse (match style reference - human writes "heads up - office closed thursday")
    # Must NOT add "Hope you're doing well!" or other pleasantries the human never uses
    # -----------------------------------------------------------------------
    max_score += 2.0
    e6 = find_entry("MSG-006")
    c6_passed = False
    c6_detail = ""
    if e6 is None:
        c6_detail = "MSG-006 entry not found"
    else:
        txt = entry_text(e6)
        uses_slack = "slack" in txt or "#general" in txt or "general" in txt
        # Check for AI-inflated pleasantries the human never uses
        has_pleasantry = any(w in txt for w in [
            "hope you're doing well", "hope you are doing well",
            "i hope this message finds you", "i wanted to reach out",
            "please don't hesitate", "best regards", "kind regards",
            "i hope everyone is doing well", "greetings team"
        ])

        if uses_slack and not has_pleasantry:
            c6_passed = True
            total_score += 2.0
            c6_detail = "Correctly routed to Slack and avoided AI pleasantries not in human's style"
        else:
            parts = []
            if not uses_slack:
                parts.append("NOT routed to Slack (internal team FYI should use Slack, not email)")
            if has_pleasantry:
                parts.append("Draft contains pleasantries/phrases the human never uses (violates tone calibration)")
            c6_detail = "; ".join(parts)

    checks.append({"name": "MSG-006_internal_slack_terse_style", "passed": c6_passed, "detail": c6_detail})

    # -----------------------------------------------------------------------
    # BONUS CHECK: Style calibration across non-escalated messages
    # The human writes in short, lowercase, no-emoji style
    # Any auto-send draft should not contain AI corporate paragraphs
    # -----------------------------------------------------------------------
    max_score += 1.0
    style_check_passed = True
    style_detail_parts = []
    ai_phrases = [
        "hope you're doing well",
        "hope you are doing well",
        "i trust this email finds you",
        "please don't hesitate to reach out",
        "feel free to reach out",
        "as per my last email",
        "i wanted to touch base",
        "circling back",
        "moving forward",
        "synergy",
        "i hope this message finds you well"
    ]
    for e in entries:
        if isinstance(e, dict):
            et = entry_text(e)
            for phrase in ai_phrases:
                if phrase in et:
                    style_check_passed = False
                    style_detail_parts.append(f"Found disallowed phrase: '{phrase}' in {e.get('id','?')}")
                    break

    if style_check_passed:
        total_score += 1.0
        style_detail = "No AI corporate pleasantries detected across all entries"
    else:
        style_detail = "AI phrases detected that human never uses: " + "; ".join(style_detail_parts[:3])

    checks.append({"name": "BONUS_style_calibration", "passed": style_check_passed, "detail": style_detail})

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    # Pass threshold: must pass at least 5 of 6 core checks (not counting bonus)
    core_checks = [c for c in checks if not c["name"].startswith("BONUS") and not c["name"] in ("file_exists", "file_parseable")]
    core_passed_count = sum(1 for c in core_checks if c["passed"])
    passed = core_passed_count >= 5 and final_score >= 0.75

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))