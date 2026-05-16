#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
    home = Path(os.path.expanduser("~"))
    state_dir = home / ".openclaw" / "workspace" / "mock_state"
    
    checks = []
    total_score = 0.0
    weights = []

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        weights.append(weight)
        return passed

    # ── Load mock state files ────────────────────────────────────────────────
    try:
        created_events = load_json(state_dir / "created_events.json")
    except Exception as e:
        created_events = []
        check("state_files_readable", False, f"Could not read created_events.json: {e}", weight=2.0)

    try:
        sent_emails = load_json(state_dir / "sent_emails.json")
    except Exception as e:
        sent_emails = []

    try:
        activity_log = load_json(state_dir / "activity_log.json")
    except Exception as e:
        activity_log = []

    try:
        pending_log = load_json(state_dir / "pending_log.json")
    except Exception as e:
        pending_log = []

    try:
        session_state = load_json(state_dir / "session_state.json")
    except Exception as e:
        session_state = {}

    try:
        index = load_json(home / ".openclaw" / "workspace" / "memory" / "email-extractions" / "index.json")
    except Exception as e:
        index = {"extractions": []}

    # ── CHECK 1: Used wrapper scripts (create_event.sh), not direct gog ──────
    # We verify indirectly: events should appear in the mock state written by create_event.sh
    email_id = "msg_4a7f9c2b1d8e3f56"
    events_for_email = [e for e in created_events if e.get("email_id") == email_id]
    used_wrapper = len(events_for_email) >= 1
    check(
        "used_create_event_wrapper",
        used_wrapper,
        f"create_event.sh wrapper was {'called (found events in mock state)' if used_wrapper else 'NOT called — events missing from mock state. Agent may have called gog directly.'}",
        weight=2.0
    )

    # ── CHECK 2: Session lifecycle (activity_log start-session + end-session) ─
    cmds = [e.get("cmd") for e in activity_log]
    started = "start-session" in cmds
    ended = "end-session" in cmds
    session_ok = started and ended
    check(
        "activity_log_session_lifecycle",
        session_ok,
        f"activity_log.sh: start-session={'yes' if started else 'NO'}, end-session={'yes' if ended else 'NO'}",
        weight=1.0
    )

    # ── CHECK 3: Index.json was consulted (email not double-processed) ────────
    # The email was NOT in index before processing; after processing it must appear
    processed_in_index = any(
        e.get("email_id") == email_id for e in index.get("extractions", [])
    )
    check(
        "email_tracked_in_index",
        processed_in_index,
        f"Email '{email_id}' {'found' if processed_in_index else 'NOT found'} in index.json after processing",
        weight=1.0
    )

    # ── CHECK 4: Main event created (Spring Showcase Concert, April 11) ───────
    main_event = None
    for e in events_for_email:
        title = e.get("title", "").lower()
        date = e.get("date", "").lower()
        if ("concert" in title or "showcase" in title or "spring" in title) and \
           ("DEADLINE" not in e.get("title", "")):
            # Also check date contains April / 04 / 4
            if any(x in date for x in ["april", "apr", "04", "4"]) or "11" in date:
                main_event = e
                break
    # Fallback: find any non-deadline event
    if main_event is None:
        non_deadline = [e for e in events_for_email if "DEADLINE" not in e.get("title","").upper() and "deadline" not in e.get("title","").lower()]
        if non_deadline:
            main_event = non_deadline[0]

    check(
        "main_event_created",
        main_event is not None,
        f"Main concert event {'found' if main_event else 'NOT found'}. Events created: {[e.get('title') for e in events_for_email]}",
        weight=2.0
    )

    # ── CHECK 5: Main event has ACTION REQUIRED warning in description ─────────
    if main_event:
        desc = main_event.get("description", "")
        has_action_warning = "ACTION REQUIRED" in desc.upper() and "MARCH 20" in desc.upper() or \
                             "ACTION REQUIRED" in desc.upper() and "MAR 20" in desc.upper() or \
                             "ACTION REQUIRED" in desc.upper() and "20" in desc
        # More lenient: just check ACTION REQUIRED is present and before other content
        has_action_warning = "ACTION REQUIRED" in desc.upper()
        first_content = desc.strip()[:50].upper()
        action_is_first = "ACTION REQUIRED" in first_content or "***" in first_content
        check(
            "main_event_has_action_warning",
            has_action_warning,
            f"Description {'contains' if has_action_warning else 'MISSING'} ACTION REQUIRED warning. First 100 chars: {desc[:100]!r}",
            weight=1.5
        )
        check(
            "action_warning_at_top",
            action_is_first,
            f"ACTION REQUIRED {'is' if action_is_first else 'is NOT'} at the top of description. First 50 chars: {first_content!r}",
            weight=1.0
        )
    else:
        check("main_event_has_action_warning", False, "No main event found to check description", weight=1.5)
        check("action_warning_at_top", False, "No main event found to check description order", weight=1.0)

    # ── CHECK 6: Main event description contains event URL ────────────────────
    if main_event:
        desc = main_event.get("description", "")
        has_url = "lincolnelementary.edu/spring-concert" in desc
        check(
            "main_event_has_url",
            has_url,
            f"Event URL {'present' if has_url else 'MISSING'} in main event description",
            weight=1.0
        )
    else:
        check("main_event_has_url", False, "No main event to check URL", weight=1.0)

    # ── CHECK 7: Main event has correct time (7 PM) ────────────────────────────
    if main_event:
        start = main_event.get("start_time", "").lower()
        # Accept: 7:00 PM, 19:00, 7pm, etc.
        correct_time = any(x in start for x in ["7:00", "7 pm", "7pm", "19:00", "19h"])
        check(
            "main_event_correct_time",
            correct_time,
            f"Main event start time: '{main_event.get('start_time')}' — expected around 7:00 PM / 19:00",
            weight=1.0
        )
    else:
        check("main_event_correct_time", False, "No main event to check time", weight=1.0)

    # ── CHECK 8: Main event has correct attendees ─────────────────────────────
    if main_event:
        attendees_str = main_event.get("attendees", "")
        has_parent = "parent@familymail.com" in attendees_str
        has_spouse = "spouse@familymail.com" in attendees_str
        check(
            "main_event_has_configured_attendees",
            has_parent and has_spouse,
            f"Attendees: '{attendees_str}'. Expected parent@familymail.com AND spouse@familymail.com",
            weight=1.5
        )
    else:
        check("main_event_has_configured_attendees", False, "No main event to check attendees", weight=1.5)

    # ── CHECK 9: Deadline reminder event created ──────────────────────────────
    deadline_event = None
    for e in events_for_email:
        title = e.get("title", "")
        if "DEADLINE" in title.upper():
            deadline_event = e
            break

    check(
        "deadline_reminder_event_created",
        deadline_event is not None,
        f"Deadline reminder event {'found' if deadline_event else 'NOT found'}. All titles: {[e.get('title') for e in events_for_email]}",
        weight=2.0
    )

    # ── CHECK 10: Deadline event title format ─────────────────────────────────
    if deadline_event:
        title = deadline_event.get("title", "")
        # Must start with DEADLINE: and reference the concert/action
        title_ok = title.upper().startswith("DEADLINE:") and (
            "ticket" in title.lower() or "rsvp" in title.lower() or "concert" in title.lower() or "spring" in title.lower()
        )
        check(
            "deadline_event_title_format",
            title_ok,
            f"Deadline event title: '{title}'. Expected 'DEADLINE: [action] for [Event Name]' format",
            weight=1.5
        )
    else:
        check("deadline_event_title_format", False, "No deadline event found", weight=1.5)

    # ── CHECK 11: Deadline event on correct date (March 20) ───────────────────
    if deadline_event:
        date_str = deadline_event.get("date", "").lower()
        # March 20, 2026 or 2026-03-20 or march 20
        correct_date = any(x in date_str for x in ["march 20", "mar 20", "2026-03-20", "03/20", "20 march"])
        check(
            "deadline_event_correct_date",
            correct_date,
            f"Deadline event date: '{deadline_event.get('date')}'. Expected March 20, 2026",
            weight=1.5
        )
    else:
        check("deadline_event_correct_date", False, "No deadline event to check date", weight=1.5)

    # ── CHECK 12: Deadline event at 9:00 AM, 30-minute duration ───────────────
    if deadline_event:
        start = deadline_event.get("start_time", "").lower()
        end = deadline_event.get("end_time", "").lower()
        start_ok = any(x in start for x in ["9:00", "09:00", "9 am", "9am"])
        end_ok = any(x in end for x in ["9:30", "09:30"])
        check(
            "deadline_event_correct_timing",
            start_ok and end_ok,
            f"Deadline event start='{deadline_event.get('start_time')}' end='{deadline_event.get('end_time')}'. Expected 9:00 AM - 9:30 AM",
            weight=1.0
        )
    else:
        check("deadline_event_correct_timing", False, "No deadline event to check timing", weight=1.0)

    # ── CHECK 13: Fundraiser event NOT created (matches ignore_pattern) ────────
    fundraiser_created = any(
        "fundraiser" in e.get("title", "").lower() or "gala" in e.get("title", "").lower()
        for e in created_events
    )
    check(
        "fundraiser_ignored",
        not fundraiser_created,
        f"Fundraiser event {'was WRONGLY created' if fundraiser_created else 'was correctly ignored'} (matches ignore_pattern 'fundraiser')",
        weight=2.0
    )

    # ── CHECK 14: Notification email sent ─────────────────────────────────────
    # deadline_notifications.enabled = true in config
    notif_sent = len(sent_emails) > 0
    if notif_sent:
        email = sent_emails[0]
        to_ok = email.get("to", "") == "parent@familymail.com"
        subj = email.get("subject", "").upper()
        subj_ok = "ACTION" in subj or "DEADLINE" in subj or "RSVP" in subj or "TICKET" in subj
        check(
            "notification_email_sent",
            True,
            f"Notification email sent. to='{email.get('to')}', subject='{email.get('subject')}'",
            weight=1.5
        )
        check(
            "notification_email_correct_recipient",
            to_ok,
            f"Email recipient '{email.get('to')}' — expected 'parent@familymail.com'",
            weight=1.0
        )
        check(
            "notification_email_subject_relevant",
            subj_ok,
            f"Email subject '{email.get('subject')}' {'mentions deadline/action' if subj_ok else 'does not mention deadline/action'}",
            weight=0.5
        )
    else:
        check("notification_email_sent", False, "No notification email sent via email_send.sh (deadline_notifications.enabled=true requires this)", weight=1.5)
        check("notification_email_correct_recipient", False, "No email to check recipient", weight=1.0)
        check("notification_email_subject_relevant", False, "No email to check subject", weight=0.5)

    # ── CHECK 15: Pending invite recorded ─────────────────────────────────────
    pending_recorded = len(pending_log) > 0
    if pending_recorded:
        entry = pending_log[0]
        has_email_id = entry.get("email_id") == email_id
        check(
            "pending_invite_recorded",
            True,
            f"Pending invite recorded for email_id='{entry.get('email_id')}'",
            weight=1.0
        )
        check(
            "pending_invite_correct_email_id",
            has_email_id,
            f"Pending invite email_id='{entry.get('email_id')}' — expected '{email_id}'",
            weight=0.5
        )
    else:
        check("pending_invite_recorded", False, "No pending invites recorded via add_pending.sh", weight=1.0)
        check("pending_invite_correct_email_id", False, "No pending invites to check email_id", weight=0.5)

    # ── CHECK 16: Calendar ID correct ─────────────────────────────────────────
    if events_for_email:
        calendar_ids = set(e.get("calendar_id") for e in events_for_email)
        correct_cal = "family_primary" in calendar_ids
        check(
            "correct_calendar_id_used",
            correct_cal,
            f"Calendar IDs used: {calendar_ids}. Expected 'family_primary' from config",
            weight=1.0
        )
    else:
        check("correct_calendar_id_used", False, "No events created to check calendar ID", weight=1.0)

    # ── Compute final score ───────────────────────────────────────────────────
    total_weight = sum(weights)
    earned = sum(w for c, w in zip(checks, weights) if c["passed"])
    score = round(earned / total_weight, 3) if total_weight > 0 else 0.0

    result = {
        "passed": score >= 0.75,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()