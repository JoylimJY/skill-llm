import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create realistic directory structure with distractor files ---
dirs = [
    "scripts",
    "data/listings",
    "data/clients",
    "data/archives",
    "logs",
    "config",
    "reports/weekly",
    "reports/monthly",
    "tmp_old",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_listings = [
    {
        "listing_id": "LST-001",
        "address": "42 Birchwood Lane, Portland, OR 97201",
        "office_phone": "+15035550101",
        "agent": "Sandra Okafor",
        "price": 489000,
        "status": "active"
    },
    {
        "listing_id": "LST-002",
        "address": "7 Maple Court, Seattle, WA 98101",
        "office_phone": "+12065550177",
        "agent": "James Cho",
        "price": 625000,
        "status": "pending"
    },
]
with open(os.path.join(workspace, "data/listings/active_listings.json"), "w") as f:
    json.dump(distractor_listings, f, indent=2)

with open(os.path.join(workspace, "data/listings/sold_q1.json"), "w") as f:
    json.dump([{"listing_id": "LST-000", "address": "1 Main St", "status": "sold"}], f, indent=2)

distractor_clients = [
    {"client_id": "C-090", "name": "Alicia Torres", "email": "alicia@example.com", "budget": 500000},
    {"client_id": "C-091", "name": "Marcus Webb", "email": "marcus@example.com", "budget": 700000},
]
with open(os.path.join(workspace, "data/clients/active_clients.json"), "w") as f:
    json.dump(distractor_clients, f, indent=2)

with open(os.path.join(workspace, "data/archives/old_bookings_2023.json"), "w") as f:
    json.dump([{"job_id": "OLD-001", "status": "confirmed", "slot": "2023-05-12T14:00:00"}], f, indent=2)

with open(os.path.join(workspace, "logs/call_log_2024-01.txt"), "w") as f:
    f.write("2024-01-15 09:32 - Call placed to +15035550101 - outcome: confirmed\n")
    f.write("2024-01-16 11:00 - Call placed to +12065550177 - outcome: pending_callback\n")

with open(os.path.join(workspace, "config/call_settings.yaml"), "w") as f:
    f.write("# Call configuration\nmax_retries: 3\ndefault_mode: dry-run\ntimezone_default: America/Los_Angeles\n")

with open(os.path.join(workspace, "reports/weekly/week4_summary.txt"), "w") as f:
    f.write("Week 4 Summary\n==============\nTotal calls: 12\nConfirmed: 8\nPending: 3\nFailed: 1\n")

with open(os.path.join(workspace, "reports/monthly/jan_report.json"), "w") as f:
    json.dump({"month": "January", "total_bookings": 34, "confirmed_rate": 0.71}, f, indent=2)

with open(os.path.join(workspace, "tmp_old/call-payload-backup.json"), "w") as f:
    json.dump({"stale": True, "note": "do not use - old format"}, f, indent=2)

with open(os.path.join(workspace, "docs/workflow_notes.txt"), "w") as f:
    f.write("General workflow notes (outdated).\nSee SKILL.md for current process.\n")

# --- The actual problem input: a raw job request file (messy but valid enough) ---
# This represents a realistic intake record that the agent needs to process through the full pipeline.
job_data = {
    "job_id": "JOB-2024-0342",
    "client_name": "Priya Nair",
    "listing": {
        "address": "318 Elmwood Drive, Austin, TX 78701",
        "office_phone": "+15125550248"
    },
    "preferred_windows_text": "Weekday mornings between 9am and 12pm, or Saturday afternoon after 2pm",
    "timezone": "America/Chicago",
    # Distractor noise fields that should be ignored:
    "internal_note": "Client is pre-approved. Urgent - follow up by EOD.",
    "assigned_agent": "Derek Fontaine",
    "crm_ref": "CRM-78821",
    "last_contact": "2024-07-10"
}

with open(os.path.join(workspace, "data/job_intake.json"), "w") as f:
    json.dump(job_data, f, indent=2)

# --- Create the actual scripts that the agent needs to invoke ---
# prepare_call_payload.py
prepare_script = '''\
#!/usr/bin/env python3
"""Build a normalized call payload from a job JSON."""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.job) as f:
        job = json.load(f)

    required_fields = ["job_id", "client_name", "listing", "preferred_windows_text", "timezone"]
    for field in required_fields:
        if field not in job:
            print(f"ERROR: missing required field: {field}", file=sys.stderr)
            sys.exit(1)

    listing = job["listing"]
    if "address" not in listing or "office_phone" not in listing:
        print("ERROR: listing must contain address and office_phone", file=sys.stderr)
        sys.exit(1)

    payload = {
        "job_id": job["job_id"],
        "client_name": job["client_name"],
        "listing_address": listing["address"],
        "office_phone": listing["office_phone"],
        "preferred_windows_text": job["preferred_windows_text"],
        "timezone": job["timezone"],
        "call_prompt": (
            f"Hello, this is an AI assistant calling on behalf of realtor Derek Fontaine. "
            f"I am scheduling a property showing for our client {job['client_name']} "
            f"at {listing['address']}. "
            f"The preferred viewing windows are: {job['preferred_windows_text']} ({job['timezone']}). "
            f"Could you please confirm available slots within those windows? "
            f"If those are unavailable, we are open to alternatives. "
            f"We would appreciate a confirmed date and local time before ending this call."
        ),
        "guardrails": {
            "disclose_ai": True,
            "confirm_slot_before_hangup": True,
            "fallback_if_unavailable": "request_alternatives",
            "if_cannot_confirm": "pending_callback"
        }
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Payload written to {args.output}")

if __name__ == "__main__":
    main()
'''

# place_outbound_call.py
place_script = '''\
#!/usr/bin/env python3
"""Simulate or place an outbound call."""
import argparse, json, sys, time, random
from pathlib import Path

random.seed(7)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--output", required=True)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true")
    mode_group.add_argument("--live", action="store_true")
    args = parser.parse_args()

    with open(args.payload) as f:
        payload = json.load(f)

    if args.live:
        print("ERROR: Live mode requires ELEVENLABS_API_KEY env variable - not set.", file=sys.stderr)
        sys.exit(2)

    # dry-run: produce a synthetic call result
    result = {
        "job_id": payload["job_id"],
        "mode": "dry_run",
        "call_id": f"DRYRUN-{payload['job_id']}-001",
        "to_number": payload["office_phone"],
        "status_raw": "completed",
        "transcript_summary": (
            f"AI assistant disclosed AI nature upfront. "
            f"Office staff offered slot: Wednesday 10:00 AM {payload['timezone']}. "
            f"Slot confirmed before call end."
        ),
        "confirmed_slot": "2024-07-17T10:00:00",
        "confirmed_timezone": payload["timezone"],
        "callback_required": False,
        "callback_notes": None,
        "duration_seconds": 47
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Dry-run call result written to {args.output}")

if __name__ == "__main__":
    main()
'''

# parse_call_result.py
parse_script = '''\
#!/usr/bin/env python3
"""Parse a raw call result into a normalized booking outcome."""
import argparse, json, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input) as f:
        result = json.load(f)

    # Determine booking status
    if result.get("callback_required"):
        booking_status = "pending_callback"
        callback_info = result.get("callback_notes", "")
    elif result.get("confirmed_slot"):
        booking_status = "confirmed"
        callback_info = None
    else:
        booking_status = "failed"
        callback_info = None

    outcome = {
        "job_id": result["job_id"],
        "booking_status": booking_status,
        "confirmed_slot": result.get("confirmed_slot"),
        "confirmed_timezone": result.get("confirmed_timezone"),
        "call_id": result.get("call_id"),
        "call_mode": result.get("mode"),
        "callback_info": callback_info,
        "source_transcript_summary": result.get("transcript_summary")
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(outcome, f, indent=2)

    print(f"Booking outcome written to {args.output}")

if __name__ == "__main__":
    main()
'''

scripts_dir = os.path.join(workspace, "scripts")
with open(os.path.join(scripts_dir, "prepare_call_payload.py"), "w") as f:
    f.write(prepare_script)
with open(os.path.join(scripts_dir, "place_outbound_call.py"), "w") as f:
    f.write(place_script)
with open(os.path.join(scripts_dir, "parse_call_result.py"), "w") as f:
    f.write(parse_script)

print("Workspace initialized successfully.")