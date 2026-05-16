#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir):
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find the output file (meeting_result.json) ──────────────────────────
    result_files = list(Path(workspace_dir).rglob("meeting_result.json"))
    
    if not result_files:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "meeting_result.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    result_file = result_files[0]
    total_score += add_check("output_file_exists", True,
                              f"Found meeting_result.json at {result_file}")

    # ── 2. Parse the output file ────────────────────────────────────────────────
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)
    except Exception as e:
        checks.append({"name": "output_file_parseable", "passed": False,
                        "detail": f"Failed to parse JSON: {e}"})
        return {"passed": False, "score": total_score / 7.0, "checks": checks}

    total_score += add_check("output_file_parseable", True, "JSON parsed successfully")

    # Helper: extract the event object (may be nested or top-level)
    def find_event(data):
        if isinstance(data, dict):
            if "eventId" in data:
                return data
            if "event" in data and isinstance(data["event"], dict):
                return data["event"]
            # Search nested
            for v in data.values():
                found = find_event(v)
                if found:
                    return found
        return None

    event = find_event(result_data)
    
    if event is None:
        checks.append({"name": "event_object_present", "passed": False,
                        "detail": f"No event object with eventId found in meeting_result.json. Content: {str(result_data)[:300]}"})
        return {"passed": False, "score": total_score / 7.0, "checks": checks}

    total_score += add_check("event_object_present", True,
                              f"Event object found with eventId={event.get('eventId')}")

    # ── 3. Verify event was actually created on mock server ─────────────────────
    try:
        with open("/tmp/created_events.json", "r") as f:
            server_events = json.load(f)
        
        event_id = event.get("eventId", "")
        server_event = server_events.get(event_id)
        
        if server_event:
            total_score += add_check("event_registered_on_server", True,
                                      f"Event {event_id} confirmed in mock server store")
        else:
            total_score += add_check("event_registered_on_server", False,
                                      f"EventId '{event_id}' not found in mock server. Available: {list(server_events.keys())}")
    except Exception as e:
        total_score += add_check("event_registered_on_server", False,
                                  f"Could not read mock server store: {e}")

    # ── 4. Verify correct attendees (both Li Wei and Zhang Min by userId) ───────
    EXPECTED_UIDS = {"uid_liwei_001", "uid_zhangmin_002"}
    attendees = event.get("attendees", [])
    
    # attendees could be list of strings or list of dicts
    attendee_ids = set()
    for a in attendees:
        if isinstance(a, str):
            attendee_ids.add(a)
        elif isinstance(a, dict):
            attendee_ids.add(a.get("userId", a.get("id", "")))
    
    # Also check server-side event
    try:
        srv_evt = server_events.get(event.get("eventId", ""), {})
        srv_attendees = srv_evt.get("attendees", [])
        for a in srv_attendees:
            if isinstance(a, str):
                attendee_ids.add(a)
            elif isinstance(a, dict):
                attendee_ids.add(a.get("userId", ""))
    except Exception:
        pass

    attendees_correct = EXPECTED_UIDS.issubset(attendee_ids)
    total_score += add_check(
        "correct_attendees_by_uid",
        attendees_correct,
        f"Expected user IDs {EXPECTED_UIDS}, found {attendee_ids}. "
        f"Agent must have used search_user_by_key_word to resolve names to IDs."
    )

    # ── 5. Verify datetime format is ISO-8601 (not timestamps) ─────────────────
    import re
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
    
    start_dt = event.get("startDateTime", "")
    end_dt = event.get("endDateTime", "")
    
    start_iso_ok = bool(iso_pattern.match(str(start_dt)))
    end_iso_ok = bool(iso_pattern.match(str(end_dt)))
    iso_ok = start_iso_ok and end_iso_ok
    
    total_score += add_check(
        "datetime_format_iso8601",
        iso_ok,
        f"startDateTime='{start_dt}' (valid={start_iso_ok}), "
        f"endDateTime='{end_dt}' (valid={end_iso_ok}). "
        f"Must use ISO-8601 like 2026-07-14T14:30:00+08:00, not ms timestamps."
    )

    # ── 6. Verify the meeting time is within the free window (14:30-15:30 CST) ──
    # Both free: 14:30-15:30 on 2026-07-14 CST
    # Li Wei busy: 13:00-14:00, 15:30-16:30
    # Zhang Min busy: 13:00-14:30, 17:00-18:00
    # Valid 1-hour window: 14:30-15:30 exactly

    def parse_dt(dt_str):
        """Parse ISO-8601 datetime to total minutes since midnight in local tz."""
        try:
            # Extract time component
            time_part = dt_str[11:16]  # HH:MM
            h, m = int(time_part[:2]), int(time_part[3:5])
            date_part = dt_str[:10]  # YYYY-MM-DD
            return date_part, h * 60 + m
        except Exception:
            return None, None

    start_date, start_mins = parse_dt(start_dt)
    end_date, end_mins = parse_dt(end_dt)

    # Check date is correct
    date_correct = (start_date == "2026-07-14" and end_date == "2026-07-14")

    # Check time is within free window: start >= 14:30 (870 min), end <= 15:30 (930 min)
    # Duration must be 60 minutes
    time_valid = False
    time_detail = ""
    
    if start_mins is not None and end_mins is not None:
        duration = end_mins - start_mins
        # Free window: 14:30 (870) to 15:30 (930)
        in_free_window = (start_mins >= 870 and end_mins <= 930 and duration == 60)
        time_valid = date_correct and in_free_window
        time_detail = (
            f"date={start_date}, start={start_mins//60:02d}:{start_mins%60:02d}, "
            f"end={end_mins//60:02d}:{end_mins%60:02d}, duration={duration}min. "
            f"Required: 2026-07-14, 14:30-15:30 (both attendees free, 1h slot)."
        )
    else:
        time_detail = f"Could not parse time from '{start_dt}' / '{end_dt}'"

    total_score += add_check("meeting_time_in_free_window", time_valid, time_detail)

    # ── 7. Verify summary contains meaningful title ─────────────────────────────
    summary = event.get("summary", "")
    summary_ok = len(summary.strip()) >= 3
    total_score += add_check(
        "event_has_summary",
        summary_ok,
        f"Event summary: '{summary}' (must be non-empty, >= 3 chars)"
    )

    # ── Final scoring ────────────────────────────────────────────────────────────
    max_score = 7.0
    normalized_score = total_score / max_score
    overall_passed = (
        checks[0]["passed"] and  # file exists
        checks[1]["passed"] and  # parseable
        checks[2]["passed"] and  # event present
        checks[4]["passed"] and  # correct attendees (by UID, requires search)
        checks[5]["passed"] and  # ISO-8601 format
        checks[6]["passed"]      # correct time window
    )

    return {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))