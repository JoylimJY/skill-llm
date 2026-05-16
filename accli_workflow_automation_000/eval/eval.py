#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    # Helper to add check result
    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # -----------------------------------------------------------------------
    # 1. Find meeting_report.json
    # -----------------------------------------------------------------------
    report_files = list(Path(workspace).rglob("meeting_report.json"))
    if not report_files:
        add_check("meeting_report.json exists", False, "File meeting_report.json not found anywhere in workspace.")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = report_files[0]
    add_check("meeting_report.json exists", True, f"Found at {report_path}")

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        add_check("meeting_report.json is valid JSON", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("meeting_report.json is valid JSON", True, "Parsed successfully.")

    # -----------------------------------------------------------------------
    # 2. Load accli mock storage to verify actual CLI operations were performed
    # -----------------------------------------------------------------------
    storage_path = "/tmp/accli_mock_storage.json"
    try:
        with open(storage_path) as f:
            storage = json.load(f)
    except Exception as e:
        add_check("accli storage accessible", False, f"Could not load mock storage: {e}")
        storage = None

    if storage is None:
        add_check("accli storage accessible", False, "Storage file missing - no CLI operations performed.")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("accli storage accessible", True, "Mock storage loaded.")

    # -----------------------------------------------------------------------
    # 3. Check that Sprint 43 Planning Session was created in Engineering calendar
    # -----------------------------------------------------------------------
    ENG_CAL_ID = "cal-eng-i9j0k1l2-persistent"
    eng_events = storage.get("events", {}).get(ENG_CAL_ID, [])
    
    sprint_event = None
    for ev in eng_events:
        if "Sprint 43 Planning" in ev.get("summary", ""):
            sprint_event = ev
            break
    
    if sprint_event is None:
        add_check("Sprint 43 Planning Session created in Engineering calendar", False,
                  "No event with 'Sprint 43 Planning' found in Engineering calendar.")
    else:
        add_check("Sprint 43 Planning Session created in Engineering calendar", True,
                  f"Found event: id={sprint_event['id']}, start={sprint_event['start']}")

    # -----------------------------------------------------------------------
    # 4. Check that the new Sprint 43 event is scheduled on 2025-03-12 in a FREE slot
    #    Free slots on 2025-03-12 for Engineering: the busy times are:
    #    11:30-13:00 (Production Deploy), 15:00-16:30 (Architecture Review)
    #    The Work calendar (which agent should check) has: 09:00-10:00, 10:00-11:30, 14:00-15:00
    #    A 90-min meeting that fits: e.g., 16:30-18:00 is free in Engineering
    #    But agent must check Engineering calendar's freebusy and find a valid free slot
    # -----------------------------------------------------------------------
    if sprint_event:
        ev_start = sprint_event.get("start", "")
        ev_end = sprint_event.get("end", "")
        
        # Check date is 2025-03-12
        if not ev_start.startswith("2025-03-12"):
            add_check("Sprint event scheduled on correct date (2025-03-12)", False,
                      f"Event start '{ev_start}' is not on 2025-03-12.")
        else:
            add_check("Sprint event scheduled on correct date (2025-03-12)", True,
                      f"Event on correct date: {ev_start}")
        
        # Verify 90-minute duration
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M"
            if ":" in ev_start[11:]:
                start_dt = datetime.strptime(ev_start[:16], fmt)
                end_dt = datetime.strptime(ev_end[:16], fmt)
                duration_min = (end_dt - start_dt).total_seconds() / 60
                if abs(duration_min - 90) <= 1:
                    add_check("Sprint event duration is 90 minutes", True, f"Duration: {duration_min} min")
                else:
                    add_check("Sprint event duration is 90 minutes", False, f"Duration: {duration_min} min, expected 90")
            else:
                add_check("Sprint event duration is 90 minutes", False, "Could not parse event times.")
        except Exception as e:
            add_check("Sprint event duration is 90 minutes", False, f"Error computing duration: {e}")
        
        # Verify no conflict with Engineering calendar busy times on 2025-03-12
        # Existing Engineering events: 11:30-13:00 and 15:00-16:30
        eng_busy = [
            ("2025-03-12T11:30", "2025-03-12T13:00"),
            ("2025-03-12T15:00", "2025-03-12T16:30"),
        ]
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M"
            new_start = datetime.strptime(ev_start[:16], fmt)
            new_end = datetime.strptime(ev_end[:16], fmt)
            conflict = False
            conflict_detail = ""
            for (bs, be) in eng_busy:
                busy_start = datetime.strptime(bs, fmt)
                busy_end = datetime.strptime(be, fmt)
                # Overlap check: new event overlaps if new_start < busy_end AND new_end > busy_start
                if new_start < busy_end and new_end > busy_start:
                    conflict = True
                    conflict_detail = f"Conflicts with {bs}-{be}"
                    break
            
            if conflict:
                add_check("Sprint event has no conflict in Engineering calendar", False, conflict_detail)
            else:
                add_check("Sprint event has no conflict in Engineering calendar", True,
                          "No overlap with existing Engineering events.")
        except Exception as e:
            add_check("Sprint event has no conflict in Engineering calendar", False, f"Error: {e}")
        
        # Verify within business hours 09:00-18:00
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M"
            new_start = datetime.strptime(ev_start[:16], fmt)
            new_end = datetime.strptime(ev_end[:16], fmt)
            biz_start = datetime.strptime("2025-03-12T09:00", fmt)
            biz_end = datetime.strptime("2025-03-12T18:00", fmt)
            if new_start >= biz_start and new_end <= biz_end:
                add_check("Sprint event within business hours (09:00-18:00)", True,
                          f"{ev_start} to {ev_end}")
            else:
                add_check("Sprint event within business hours (09:00-18:00)", False,
                          f"{ev_start} to {ev_end} is outside 09:00-18:00")
        except Exception as e:
            add_check("Sprint event within business hours (09:00-18:00)", False, f"Error: {e}")
        
        # Verify location and description
        location_ok = "Engineering War Room" in sprint_event.get("location", "")
        add_check("Sprint event has correct location (Engineering War Room)", location_ok,
                  f"Location: '{sprint_event.get('location', '')}'")
        
        desc_ok = "Sprint 43" in sprint_event.get("description", "") or "engineers" in sprint_event.get("description", "").lower() or "Kickoff" in sprint_event.get("description", "")
        add_check("Sprint event has a description", desc_ok if sprint_event.get("description") else False,
                  f"Description: '{sprint_event.get('description', '')}'")

    else:
        # Sprint event not found - fail all related checks
        for check_name in [
            "Sprint event scheduled on correct date (2025-03-12)",
            "Sprint event duration is 90 minutes",
            "Sprint event has no conflict in Engineering calendar",
            "Sprint event within business hours (09:00-18:00)",
            "Sprint event has correct location (Engineering War Room)",
            "Sprint event has a description"
        ]:
            add_check(check_name, False, "Sprint event not found.")

    # -----------------------------------------------------------------------
    # 5. Check that the Stakeholder Sync event in Work calendar has updated description
    # -----------------------------------------------------------------------
    WORK_CAL_ID = "cal-work-a1b2c3d4-persistent"
    work_events = storage.get("events", {}).get(WORK_CAL_ID, [])
    
    stakeholder_event = None
    for ev in work_events:
        if "Stakeholder Sync" in ev.get("summary", ""):
            stakeholder_event = ev
            break
    
    if stakeholder_event is None:
        add_check("Stakeholder Sync event found in Work calendar", False,
                  "Could not find Stakeholder Sync event.")
    else:
        add_check("Stakeholder Sync event found in Work calendar", True,
                  f"Found: id={stakeholder_event['id']}")
        
        expected_desc = "Updated: Video call via Zoom at https://zoom.us/j/999888777. Passcode: sprint43"
        actual_desc = stakeholder_event.get("description", "")
        
        if actual_desc == expected_desc:
            add_check("Stakeholder Sync description updated correctly (exact match)", True,
                      f"Description matches exactly.")
        elif "zoom.us/j/999888777" in actual_desc and "sprint43" in actual_desc:
            add_check("Stakeholder Sync description updated correctly (exact match)", True,
                      f"Description contains required content: '{actual_desc}'")
        else:
            add_check("Stakeholder Sync description updated correctly (exact match)", False,
                      f"Expected to contain Zoom link and passcode. Got: '{actual_desc}'")

    # -----------------------------------------------------------------------
    # 6. Check meeting_report.json structure - must capture both event IDs
    # -----------------------------------------------------------------------
    try:
        # Check sprint event ID in report
        report_str = json.dumps(report)
        
        sprint_id_in_report = False
        if sprint_event:
            sprint_id_in_report = sprint_event["id"] in report_str
        
        add_check("meeting_report.json references created sprint event ID", sprint_id_in_report,
                  f"Sprint event ID '{sprint_event['id'] if sprint_event else 'N/A'}' found in report: {sprint_id_in_report}")
        
        stakeholder_id_in_report = False
        if stakeholder_event:
            stakeholder_id_in_report = stakeholder_event["id"] in report_str or "Stakeholder" in report_str
        
        add_check("meeting_report.json references stakeholder event", stakeholder_id_in_report,
                  f"Stakeholder event referenced in report: {stakeholder_id_in_report}")
        
        # Check that report has some reasonable structure (not empty)
        has_structure = isinstance(report, dict) and len(report) >= 2
        add_check("meeting_report.json has meaningful structure (dict with >=2 keys)", has_structure,
                  f"Keys: {list(report.keys()) if isinstance(report, dict) else 'not a dict'}")
        
    except Exception as e:
        add_check("meeting_report.json content validation", False, f"Error: {e}")

    # -----------------------------------------------------------------------
    # Compute score
    # -----------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    return {
        "passed": all(c["passed"] for c in checks),
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))