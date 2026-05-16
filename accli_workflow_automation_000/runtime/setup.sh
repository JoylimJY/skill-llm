#!/bin/bash
set -e

# Create a mock accli binary that simulates realistic Apple Calendar CLI behavior
cat > /usr/local/bin/accli << 'MOCK_EOF'
#!/usr/bin/env python3
import sys
import json
import os
import hashlib
import re
from datetime import datetime

STORAGE_FILE = "/tmp/accli_mock_storage.json"

def load_storage():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE) as f:
            return json.load(f)
    # Initialize with realistic default data
    storage = {
        "calendars": [
            {"name": "Work", "id": "cal-work-a1b2c3d4-persistent", "description": "Work calendar", "color": "blue"},
            {"name": "Personal", "id": "cal-personal-e5f6g7h8-persistent", "description": "Personal calendar", "color": "green"},
            {"name": "Engineering", "id": "cal-eng-i9j0k1l2-persistent", "description": "Engineering team calendar", "color": "orange"},
            {"name": "Holidays", "id": "cal-holiday-m3n4o5p6-persistent", "description": "Public holidays", "color": "red"},
        ],
        "events": {
            "cal-work-a1b2c3d4-persistent": [
                {
                    "id": "evt-work-stakeholder-aabbcc",
                    "summary": "Stakeholder Sync",
                    "start": "2025-03-12T14:00:00",
                    "end": "2025-03-12T15:00:00",
                    "location": "Conference Room B",
                    "description": "Weekly sync with stakeholders on product progress.",
                    "allDay": False,
                    "status": "confirmed"
                },
                {
                    "id": "evt-work-budget-ddeeff",
                    "summary": "Budget Review Q1",
                    "start": "2025-03-12T10:00:00",
                    "end": "2025-03-12T11:30:00",
                    "location": "Finance Office",
                    "description": "Q1 budget review with finance team.",
                    "allDay": False,
                    "status": "confirmed"
                },
                {
                    "id": "evt-work-allhands-gg1122",
                    "summary": "All Hands Meeting",
                    "start": "2025-03-12T09:00:00",
                    "end": "2025-03-12T10:00:00",
                    "location": "Main Auditorium",
                    "description": "Monthly all-hands company meeting.",
                    "allDay": False,
                    "status": "confirmed"
                }
            ],
            "cal-personal-e5f6g7h8-persistent": [
                {
                    "id": "evt-personal-dentist-pp9900",
                    "summary": "Dentist Appointment",
                    "start": "2025-03-12T13:00:00",
                    "end": "2025-03-12T14:00:00",
                    "location": "Downtown Dental Clinic",
                    "description": "",
                    "allDay": False,
                    "status": "confirmed"
                }
            ],
            "cal-eng-i9j0k1l2-persistent": [
                {
                    "id": "evt-eng-deploy-qq1234",
                    "summary": "Production Deploy Window",
                    "start": "2025-03-12T11:30:00",
                    "end": "2025-03-12T13:00:00",
                    "location": "",
                    "description": "Scheduled maintenance and deployment window.",
                    "allDay": False,
                    "status": "confirmed"
                },
                {
                    "id": "evt-eng-review-rr5678",
                    "summary": "Architecture Review",
                    "start": "2025-03-12T15:00:00",
                    "end": "2025-03-12T16:30:00",
                    "location": "Zoom",
                    "description": "Review of new microservices architecture proposal.",
                    "allDay": False,
                    "status": "confirmed"
                }
            ],
            "cal-holiday-m3n4o5p6-persistent": []
        },
        "config": {}
    }
    save_storage(storage)
    return storage

def save_storage(storage):
    with open(STORAGE_FILE, "w") as f:
        json.dump(storage, f, indent=2)

def find_calendar_by_name_or_id(storage, identifier):
    for cal in storage["calendars"]:
        if cal["name"] == identifier or cal["id"] == identifier:
            return cal
    return None

def get_events_for_calendar(storage, cal_id, from_dt=None, to_dt=None, query=None, max_n=50):
    events = storage["events"].get(cal_id, [])
    result = []
    for ev in events:
        ev_start = ev["start"][:10] if ev["allDay"] else ev["start"]
        ev_end = ev["end"][:10] if ev["allDay"] else ev["end"]
        
        if from_dt:
            if ev["allDay"]:
                if ev_start < from_dt[:10]:
                    continue
            else:
                if ev["end"] <= from_dt:
                    continue
        if to_dt:
            if ev["allDay"]:
                if ev_end > to_dt[:10]:
                    continue
            else:
                if ev["start"] >= to_dt:
                    continue
        if query:
            q = query.lower()
            if not (q in ev.get("summary","").lower() or 
                    q in ev.get("location","").lower() or 
                    q in ev.get("description","").lower()):
                continue
        result.append(ev)
    return result[:max_n]

def parse_args(args):
    parsed = {"flags": [], "options": {}, "positional": []}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            key = a[2:]
            # Check if next arg is a value
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                # Special boolean flags
                if key in ["json", "all-day", "no-all-day", "help"]:
                    parsed["flags"].append(key)
                else:
                    # multi-value options
                    if key in parsed["options"]:
                        existing = parsed["options"][key]
                        if isinstance(existing, list):
                            existing.append(args[i+1])
                        else:
                            parsed["options"][key] = [existing, args[i+1]]
                    else:
                        parsed["options"][key] = args[i+1]
                    i += 1
            else:
                parsed["flags"].append(key)
        else:
            parsed["positional"].append(a)
        i += 1
    return parsed

def cmd_calendars(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    if use_json:
        print(json.dumps(storage["calendars"], indent=2))
    else:
        for cal in storage["calendars"]:
            print(f"{cal['name']} ({cal['id']})")

def cmd_events(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    
    cal_name = parsed["positional"][0] if parsed["positional"] else None
    cal_id_opt = parsed["options"].get("calendar-id")
    
    cal = None
    if cal_id_opt:
        cal = find_calendar_by_name_or_id(storage, cal_id_opt)
    elif cal_name:
        cal = find_calendar_by_name_or_id(storage, cal_name)
    
    if not cal:
        print(json.dumps({"error": "Calendar not found"}) if use_json else "Error: Calendar not found", file=sys.stderr)
        sys.exit(1)
    
    from_dt = parsed["options"].get("from")
    to_dt = parsed["options"].get("to")
    query = parsed["options"].get("query")
    max_n = int(parsed["options"].get("max", 50))
    
    events = get_events_for_calendar(storage, cal["id"], from_dt, to_dt, query, max_n)
    
    if use_json:
        print(json.dumps(events, indent=2))
    else:
        for ev in events:
            print(f"{ev['start']} - {ev['summary']}")

def cmd_event(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    
    cal_name = parsed["positional"][0] if len(parsed["positional"]) > 0 else None
    event_id = parsed["positional"][1] if len(parsed["positional"]) > 1 else None
    
    cal = find_calendar_by_name_or_id(storage, cal_name)
    if not cal:
        print(json.dumps({"error": "Calendar not found"}) if use_json else "Error: Calendar not found", file=sys.stderr)
        sys.exit(1)
    
    events = storage["events"].get(cal["id"], [])
    ev = next((e for e in events if e["id"] == event_id), None)
    if not ev:
        print(json.dumps({"error": "Event not found"}) if use_json else "Error: Event not found", file=sys.stderr)
        sys.exit(1)
    
    if use_json:
        print(json.dumps(ev, indent=2))
    else:
        print(f"{ev['start']} - {ev['summary']}")

def cmd_create(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    is_all_day = "all-day" in parsed["flags"]
    
    cal_name = parsed["positional"][0] if parsed["positional"] else None
    cal = find_calendar_by_name_or_id(storage, cal_name)
    
    if not cal:
        print(json.dumps({"error": f"Calendar not found: {cal_name}"}) if use_json else f"Error: Calendar not found: {cal_name}", file=sys.stderr)
        sys.exit(1)
    
    summary = parsed["options"].get("summary")
    start = parsed["options"].get("start")
    end = parsed["options"].get("end")
    location = parsed["options"].get("location", "")
    description = parsed["options"].get("description", "")
    
    if not summary or not start or not end:
        print(json.dumps({"error": "Missing required fields: summary, start, end"}) if use_json else "Error: Missing required fields", file=sys.stderr)
        sys.exit(1)
    
    # Validate datetime format
    if is_all_day:
        # Should be YYYY-MM-DD
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', start):
            print(json.dumps({"error": "All-day events require YYYY-MM-DD format"}) if use_json else "Error: format issue", file=sys.stderr)
            sys.exit(1)
    else:
        # Should be YYYY-MM-DDTHH:mm or YYYY-MM-DDTHH:mm:ss
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', start):
            print(json.dumps({"error": "Timed events require YYYY-MM-DDTHH:mm format"}) if use_json else "Error: format issue", file=sys.stderr)
            sys.exit(1)
    
    # Generate deterministic event ID
    ev_id = f"evt-created-{hashlib.md5((cal['id'] + summary + start).encode()).hexdigest()[:12]}"
    
    new_event = {
        "id": ev_id,
        "summary": summary,
        "start": start,
        "end": end,
        "location": location,
        "description": description,
        "allDay": is_all_day,
        "status": "confirmed"
    }
    
    if cal["id"] not in storage["events"]:
        storage["events"][cal["id"]] = []
    storage["events"][cal["id"]].append(new_event)
    save_storage(storage)
    
    if use_json:
        print(json.dumps(new_event, indent=2))
    else:
        print(f"Created: {ev_id} - {summary}")

def cmd_update(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    
    cal_name = parsed["positional"][0] if len(parsed["positional"]) > 0 else None
    event_id = parsed["positional"][1] if len(parsed["positional"]) > 1 else None
    
    cal = find_calendar_by_name_or_id(storage, cal_name)
    if not cal:
        print(json.dumps({"error": "Calendar not found"}) if use_json else "Error: Calendar not found", file=sys.stderr)
        sys.exit(1)
    
    events = storage["events"].get(cal["id"], [])
    ev = next((e for e in events if e["id"] == event_id), None)
    if not ev:
        print(json.dumps({"error": f"Event not found: {event_id}"}) if use_json else "Error: Event not found", file=sys.stderr)
        sys.exit(1)
    
    if "summary" in parsed["options"]:
        ev["summary"] = parsed["options"]["summary"]
    if "start" in parsed["options"]:
        ev["start"] = parsed["options"]["start"]
    if "end" in parsed["options"]:
        ev["end"] = parsed["options"]["end"]
    if "location" in parsed["options"]:
        ev["location"] = parsed["options"]["location"]
    if "description" in parsed["options"]:
        ev["description"] = parsed["options"]["description"]
    if "all-day" in parsed["flags"]:
        ev["allDay"] = True
    if "no-all-day" in parsed["flags"]:
        ev["allDay"] = False
    
    save_storage(storage)
    
    if use_json:
        print(json.dumps(ev, indent=2))
    else:
        print(f"Updated: {event_id}")

def cmd_delete(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    
    cal_name = parsed["positional"][0] if len(parsed["positional"]) > 0 else None
    event_id = parsed["positional"][1] if len(parsed["positional"]) > 1 else None
    
    cal = find_calendar_by_name_or_id(storage, cal_name)
    if not cal:
        print(json.dumps({"error": "Calendar not found"}) if use_json else "Error: Calendar not found", file=sys.stderr)
        sys.exit(1)
    
    events = storage["events"].get(cal["id"], [])
    original_len = len(events)
    storage["events"][cal["id"]] = [e for e in events if e["id"] != event_id]
    
    if len(storage["events"][cal["id"]]) == original_len:
        print(json.dumps({"error": "Event not found"}) if use_json else "Error: Event not found", file=sys.stderr)
        sys.exit(1)
    
    save_storage(storage)
    
    result = {"deleted": True, "eventId": event_id}
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Deleted: {event_id}")

def cmd_freebusy(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    
    from_dt = parsed["options"].get("from")
    to_dt = parsed["options"].get("to")
    
    if not from_dt or not to_dt:
        print(json.dumps({"error": "freebusy requires --from and --to"}) if use_json else "Error: missing --from/--to", file=sys.stderr)
        sys.exit(1)
    
    # Collect calendars - can use --calendar (name) or --calendar-id
    calendar_refs = parsed["options"].get("calendar", [])
    calendar_id_refs = parsed["options"].get("calendar-id", [])
    
    if isinstance(calendar_refs, str):
        calendar_refs = [calendar_refs]
    if isinstance(calendar_id_refs, str):
        calendar_id_refs = [calendar_id_refs]
    
    busy_slots = []
    
    for ref in calendar_refs:
        cal = find_calendar_by_name_or_id(storage, ref)
        if cal:
            events = get_events_for_calendar(storage, cal["id"], from_dt, to_dt)
            for ev in events:
                if ev.get("status") not in ["cancelled", "declined"] and not ev.get("transparent"):
                    busy_slots.append({
                        "calendar": cal["name"],
                        "calendarId": cal["id"],
                        "start": ev["start"],
                        "end": ev["end"],
                        "summary": ev["summary"]
                    })
    
    for ref in calendar_id_refs:
        cal = find_calendar_by_name_or_id(storage, ref)
        if cal:
            # Avoid double-counting if same calendar
            already_counted = any(b["calendarId"] == cal["id"] for b in busy_slots)
            if not already_counted:
                events = get_events_for_calendar(storage, cal["id"], from_dt, to_dt)
                for ev in events:
                    if ev.get("status") not in ["cancelled", "declined"] and not ev.get("transparent"):
                        busy_slots.append({
                            "calendar": cal["name"],
                            "calendarId": cal["id"],
                            "start": ev["start"],
                            "end": ev["end"],
                            "summary": ev["summary"]
                        })
    
    # Sort by start
    busy_slots.sort(key=lambda x: x["start"])
    
    result = {
        "from": from_dt,
        "to": to_dt,
        "busy": busy_slots
    }
    
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        for slot in busy_slots:
            print(f"BUSY: {slot['start']} - {slot['end']} ({slot['calendar']}): {slot['summary']}")

def cmd_config(args, storage):
    parsed = parse_args(args)
    use_json = "json" in parsed["flags"]
    
    sub = parsed["positional"][0] if parsed["positional"] else None
    
    if sub == "show":
        result = storage.get("config", {})
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print(result)
    elif sub == "set-default":
        cal_name = parsed["options"].get("calendar")
        if cal_name:
            cal = find_calendar_by_name_or_id(storage, cal_name)
            if cal:
                storage["config"]["default_calendar"] = cal["id"]
                storage["config"]["default_calendar_name"] = cal["name"]
                save_storage(storage)
                print(f"Default calendar set to: {cal['name']}")
            else:
                print("Calendar not found", file=sys.stderr)
                sys.exit(1)
        else:
            print("Interactive mode not supported in mock. Use --calendar flag.")
    elif sub == "clear":
        storage["config"] = {}
        save_storage(storage)
        print("Config cleared.")

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: accli <command> [options]")
        sys.exit(0)
    
    storage = load_storage()
    cmd = args[0]
    rest = args[1:]
    
    if cmd == "calendars":
        cmd_calendars(rest, storage)
    elif cmd == "events":
        cmd_events(rest, storage)
    elif cmd == "event":
        cmd_event(rest, storage)
    elif cmd == "create":
        cmd_create(rest, storage)
    elif cmd == "update":
        cmd_update(rest, storage)
    elif cmd == "delete":
        cmd_delete(rest, storage)
    elif cmd == "freebusy":
        cmd_freebusy(rest, storage)
    elif cmd == "config":
        cmd_config(rest, storage)
    elif cmd == "--help" or cmd == "help":
        print("accli - Apple Calendar CLI\nCommands: calendars, events, event, create, update, delete, freebusy, config")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
MOCK_EOF

chmod +x /usr/local/bin/accli

# Verify mock works
accli calendars --json > /dev/null && echo "Mock accli installed successfully"