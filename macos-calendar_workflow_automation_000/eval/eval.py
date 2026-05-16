#!/usr/bin/env python3
import sys
import json
import datetime
from pathlib import Path

def load_capture(workspace: Path):
    capture_path = workspace / "skills" / "macos-calendar" / "logs" / "capture.jsonl"
    if not capture_path.exists():
        return []
    lines = []
    for line in capture_path.read_text().strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return lines

def compute_expected_wednesday_offset():
    """Compute days until next Wednesday from today (ISO weekday 3), with zero-guard."""
    today = datetime.date.today()
    today_iso = today.isoweekday()  # 1=Mon, 7=Sun
    target = 3  # Wednesday
    offset = (target - today_iso + 7) % 7
    if offset == 0:
        offset = 7
    return offset

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # Load all captured events
    try:
        records = load_capture(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "capture_file_readable", "passed": False, "detail": str(e)}]
        }))
        return

    # -------------------------------------------------------
    # CHECK 1: list-calendars was called before any create-event
    # -------------------------------------------------------
    list_cal_indices = [i for i, r in enumerate(records) if r.get("cmd") == "list-calendars" or r.get("_cmd") == "list-calendars"]
    create_indices = [i for i, r in enumerate(records) if r.get("_cmd") == "create-event"]

    list_cal_called = len(list_cal_indices) > 0
    list_cal_before_create = False
    if list_cal_called and len(create_indices) > 0:
        list_cal_before_create = min(list_cal_indices) < min(create_indices)
    elif list_cal_called and len(create_indices) == 0:
        list_cal_before_create = True  # partial credit setup

    checks.append({
        "name": "list_calendars_called_first",
        "passed": list_cal_called and (list_cal_before_create if create_indices else True),
        "detail": f"list-calendars calls: {len(list_cal_indices)}, create-event calls: {len(create_indices)}, order correct: {list_cal_before_create}"
    })

    # -------------------------------------------------------
    # CHECK 2: Exactly two create-event calls
    # -------------------------------------------------------
    create_events = [r for r in records if r.get("_cmd") == "create-event"]
    checks.append({
        "name": "two_events_created",
        "passed": len(create_events) >= 2,
        "detail": f"Found {len(create_events)} create-event records (need at least 2)"
    })

    if len(create_events) < 2:
        # Still output partial results
        checks.append({"name": "kickoff_event_valid", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "kickoff_correct_calendar", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "kickoff_offset_days_correct", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "kickoff_time_and_duration", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "kickoff_alarm", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "sprint_review_recurrence", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "sprint_review_calendar", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "sprint_review_time_duration", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "sprint_review_alarm", "passed": False, "detail": "Not enough events created"})
        checks.append({"name": "no_readonly_calendar_used", "passed": False, "detail": "Not enough events created"})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        print(json.dumps({"passed": False, "score": round(score, 2), "checks": checks}))
        return

    # Identify kickoff event (non-recurring, ~next Wednesday, 90 min) vs sprint review (recurring)
    kickoff = None
    sprint_review = None
    for ev in create_events:
        if ev.get("recurrence"):
            if sprint_review is None:
                sprint_review = ev
        else:
            if kickoff is None:
                kickoff = ev

    # Fallback: if both have recurrence or neither, try heuristics by duration
    if kickoff is None or sprint_review is None:
        for ev in create_events:
            dur = ev.get("duration_minutes", 30)
            if dur == 90 and kickoff is None:
                kickoff = ev
            elif dur != 90 and sprint_review is None:
                sprint_review = ev
        if kickoff is None:
            kickoff = create_events[0]
        if sprint_review is None:
            sprint_review = create_events[1] if len(create_events) > 1 else create_events[0]

    # -------------------------------------------------------
    # CHECK 3: Kickoff event — correct calendar (Work)
    # -------------------------------------------------------
    kickoff_calendar = (kickoff.get("calendar", "") or "").strip()
    checks.append({
        "name": "kickoff_correct_calendar",
        "passed": kickoff_calendar.lower() == "work",
        "detail": f"kickoff calendar='{kickoff_calendar}' (expected 'Work')"
    })

    # -------------------------------------------------------
    # CHECK 4: Kickoff event — offset_days for next Wednesday (with zero-guard)
    # -------------------------------------------------------
    expected_offset = compute_expected_wednesday_offset()
    kickoff_offset = kickoff.get("offset_days")
    # Also accept iso_date if it resolves to the correct Wednesday
    kickoff_iso = kickoff.get("iso_date", "")
    offset_correct = False
    offset_detail = ""
    if kickoff_offset is not None:
        try:
            kickoff_offset_int = int(kickoff_offset)
            offset_correct = (kickoff_offset_int == expected_offset)
            offset_detail = f"offset_days={kickoff_offset_int}, expected={expected_offset}"
        except (ValueError, TypeError):
            offset_detail = f"offset_days could not be parsed: {kickoff_offset}"
    if not offset_correct and kickoff_iso:
        try:
            iso_date = datetime.date.fromisoformat(kickoff_iso)
            today = datetime.date.today()
            computed_offset = (iso_date - today).days
            # Allow ±1 day tolerance for timezone edge cases, and must be Wednesday
            if iso_date.isoweekday() == 3 and computed_offset == expected_offset:
                offset_correct = True
                offset_detail = f"iso_date={kickoff_iso} resolves to offset={computed_offset}, expected={expected_offset}"
        except Exception as ex:
            offset_detail += f" | iso_date parse error: {ex}"

    checks.append({
        "name": "kickoff_offset_days_correct",
        "passed": offset_correct,
        "detail": offset_detail if offset_detail else f"Neither offset_days nor iso_date provided. Expected offset={expected_offset} (next Wednesday)"
    })

    # -------------------------------------------------------
    # CHECK 5: Kickoff event — hour=10, duration=90
    # -------------------------------------------------------
    kickoff_hour = kickoff.get("hour", 9)
    kickoff_dur = kickoff.get("duration_minutes", 30)
    time_ok = (int(kickoff_hour) == 10) and (int(kickoff_dur) == 90)
    checks.append({
        "name": "kickoff_time_and_duration",
        "passed": time_ok,
        "detail": f"hour={kickoff_hour} (expected 10), duration_minutes={kickoff_dur} (expected 90)"
    })

    # -------------------------------------------------------
    # CHECK 6: Kickoff event — alarm_minutes=15
    # -------------------------------------------------------
    kickoff_alarm = kickoff.get("alarm_minutes", 0)
    checks.append({
        "name": "kickoff_alarm",
        "passed": int(kickoff_alarm) == 15,
        "detail": f"alarm_minutes={kickoff_alarm} (expected 15)"
    })

    # -------------------------------------------------------
    # CHECK 7: Sprint review — recurrence RRULE correctness
    # Must contain: FREQ=WEEKLY, INTERVAL=2, BYDAY=FR, COUNT=8
    # -------------------------------------------------------
    sr_recurrence = (sprint_review.get("recurrence", "") or "").strip().upper()
    rrule_parts = {p.split("=")[0]: p.split("=")[1] for p in sr_recurrence.split(";") if "=" in p}

    has_freq_weekly = rrule_parts.get("FREQ") == "WEEKLY"
    has_interval_2 = rrule_parts.get("INTERVAL") == "2"
    has_byday_fr = rrule_parts.get("BYDAY") == "FR"
    has_count_8 = rrule_parts.get("COUNT") == "8"

    recurrence_ok = has_freq_weekly and has_interval_2 and has_byday_fr and has_count_8
    checks.append({
        "name": "sprint_review_recurrence",
        "passed": recurrence_ok,
        "detail": (
            f"recurrence='{sr_recurrence}' | "
            f"FREQ=WEEKLY:{has_freq_weekly}, INTERVAL=2:{has_interval_2}, "
            f"BYDAY=FR:{has_byday_fr}, COUNT=8:{has_count_8}"
        )
    })

    # -------------------------------------------------------
    # CHECK 8: Sprint review — correct calendar (Work)
    # -------------------------------------------------------
    sr_calendar = (sprint_review.get("calendar", "") or "").strip()
    checks.append({
        "name": "sprint_review_calendar",
        "passed": sr_calendar.lower() == "work",
        "detail": f"sprint review calendar='{sr_calendar}' (expected 'Work')"
    })

    # -------------------------------------------------------
    # CHECK 9: Sprint review — hour=15, duration=30
    # -------------------------------------------------------
    sr_hour = sprint_review.get("hour", 9)
    sr_dur = sprint_review.get("duration_minutes", 30)
    sr_time_ok = (int(sr_hour) == 15) and (int(sr_dur) == 30)
    checks.append({
        "name": "sprint_review_time_duration",
        "passed": sr_time_ok,
        "detail": f"hour={sr_hour} (expected 15), duration_minutes={sr_dur} (expected 30)"
    })

    # -------------------------------------------------------
    # CHECK 10: Sprint review — alarm_minutes=5
    # -------------------------------------------------------
    sr_alarm = sprint_review.get("alarm_minutes", 0)
    checks.append({
        "name": "sprint_review_alarm",
        "passed": int(sr_alarm) == 5,
        "detail": f"alarm_minutes={sr_alarm} (expected 5)"
    })

    # -------------------------------------------------------
    # CHECK 11: No read-only calendar used
    # -------------------------------------------------------
    readonly_keywords = ["personal", "birthdays", "read-only"]
    all_calendars_used = [r.get("calendar", "").lower() for r in create_events]
    no_readonly_used = not any(
        any(kw in cal for kw in readonly_keywords)
        for cal in all_calendars_used
    )
    checks.append({
        "name": "no_readonly_calendar_used",
        "passed": no_readonly_used,
        "detail": f"Calendars used: {all_calendars_used}"
    })

    # -------------------------------------------------------
    # Final scoring
    # -------------------------------------------------------
    n = len(checks)
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / n, 2)
    overall_passed = n_passed == n

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()