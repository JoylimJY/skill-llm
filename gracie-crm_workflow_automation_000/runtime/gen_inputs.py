import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

# ─── Directory skeleton ───────────────────────────────────────────────────────
base = Path("/root/StudioBrain")

dirs = [
    "00_SYSTEM/skills/gracie-crm",
    "00_SYSTEM/skills/scheduler",
    "00_SYSTEM/skills/email-responder",
    "00_SYSTEM/config",
    "00_SYSTEM/logs",
    "01_LEADS/raw_exports",
    "01_LEADS/processed",
    "02_CAMPAIGNS/q1_2026",
    "02_CAMPAIGNS/q2_2026",
    "03_REPORTS/weekly",
    "03_REPORTS/monthly",
    "04_SCRIPTS/automation",
    "04_SCRIPTS/utils",
    "05_ARCHIVE/2025",
]

for d in dirs:
    (base / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "00_SYSTEM/config/app_config.yaml": "app_name: StudioBrain\nversion: 2.1.0\ndebug: false\n",
    "00_SYSTEM/logs/system.log": "2026-01-15 08:00:01 INFO System started\n2026-01-15 08:01:22 INFO Scheduler loaded\n",
    "00_SYSTEM/skills/scheduler/scheduler.py": "# Scheduler skill placeholder\ndef run(): pass\n",
    "00_SYSTEM/skills/email-responder/responder.py": "# Email responder skill\ndef respond(msg): return 'Auto-reply'\n",
    "01_LEADS/raw_exports/export_jan2026.csv": "name,phone,type\nSunrise HVAC,212-555-0101,hvac\nBrooklyn Smiles,718-555-0202,dental\n",
    "01_LEADS/processed/leads_q4_2025.json": json.dumps([{"name": "Old Lead", "status": "closed_lost"}], indent=2),
    "02_CAMPAIGNS/q1_2026/targets.txt": "Focus: auto shops and dental offices in NYC metro\nGoal: 50 demos by March 31\n",
    "02_CAMPAIGNS/q2_2026/budget.txt": "Q2 Budget: $12,000\nChannels: outbound calls, email sequences\n",
    "03_REPORTS/weekly/week_05_2026.txt": "Calls made: 23\nInterested: 4\nDemos sent: 1\n",
    "03_REPORTS/monthly/january_2026.txt": "Total leads added: 87\nClosed won: 3\nClosed lost: 12\n",
    "04_SCRIPTS/automation/daily_sync.sh": "#!/bin/bash\necho 'Syncing data...'\n",
    "04_SCRIPTS/utils/format_numbers.py": "def format_phone(n):\n    return n.strip()\n",
    "05_ARCHIVE/2025/q3_leads.json": json.dumps([{"name": "Archived Co", "status": "closed_won"}], indent=2),
    "00_SYSTEM/config/categories_reference.txt": "Known business types: restaurants, retail, auto, medical, legal, dental, hvac\n",
}

for rel_path, content in distractors.items():
    p = base / rel_path
    p.write_text(content)

# ─── Core CRM scaffold ────────────────────────────────────────────────────────
crm_dir = base / "00_SYSTEM/skills/gracie-crm"

# Empty initial CRM data store
(crm_dir / "crm.json").write_text("[]")

# The actual crm.py tool
crm_py = r'''#!/usr/bin/env python3
"""Gracie CRM - Lead tracking CLI for Gracie AI Receptionist sales."""

import json
import argparse
import sys
from pathlib import Path
from datetime import date, datetime

CRM_FILE = Path(__file__).parent / "crm.json"

VALID_STATUSES = ["new", "called", "no_answer", "interested", "demo_sent", "closed_won", "closed_lost"]
VALID_CATEGORIES = ["auto", "hvac", "dental", "insurance", "medical", "legal", "other"]

def load():
    if CRM_FILE.exists():
        return json.loads(CRM_FILE.read_text())
    return []

def save(data):
    CRM_FILE.write_text(json.dumps(data, indent=2))

def next_id(data):
    if not data:
        return 1
    return max(l["id"] for l in data) + 1

def cmd_list(args):
    data = load()
    if not data:
        print("No leads found.")
        return
    sorted_leads = sorted(data, key=lambda x: x.get("followup_date") or "9999-99-99")
    for l in sorted_leads:
        print(f"[{l['id']}] {l['name']} | {l['category']} | {l['status']} | followup: {l.get('followup_date', 'none')}")

def cmd_add(args):
    data = load()
    if args.category not in VALID_CATEGORIES:
        print(f"ERROR: Invalid category '{args.category}'. Must be one of: {', '.join(VALID_CATEGORIES)}")
        sys.exit(1)
    lead = {
        "id": next_id(data),
        "name": args.name,
        "phone": args.phone,
        "category": args.category,
        "status": "new",
        "calls": [],
        "notes": [],
        "followup_date": None,
        "added": str(date.today())
    }
    data.append(lead)
    save(data)
    print(f"Added lead [{lead['id']}]: {lead['name']}")

def cmd_call(args):
    data = load()
    lead = next((l for l in data if l["id"] == args.id), None)
    if not lead:
        print(f"ERROR: Lead ID {args.id} not found.")
        sys.exit(1)
    outcome = args.outcome.lower().strip()
    # Map outcome strings to statuses
    status_map = {
        "no answer": "no_answer",
        "no_answer": "no_answer",
        "interested": "interested",
        "called": "called",
        "demo sent": "demo_sent",
        "demo_sent": "demo_sent",
        "closed won": "closed_won",
        "closed_won": "closed_won",
        "closed lost": "closed_lost",
        "closed_lost": "closed_lost",
    }
    new_status = status_map.get(outcome, "called")
    lead["status"] = new_status
    lead["calls"].append({
        "date": str(date.today()),
        "outcome": outcome,
        "notes": ""
    })
    if args.followup:
        lead["followup_date"] = args.followup
    save(data)
    print(f"Logged call for [{lead['id']}] {lead['name']}: outcome={outcome}, status={new_status}, followup={args.followup}")

def cmd_note(args):
    data = load()
    lead = next((l for l in data if l["id"] == args.id), None)
    if not lead:
        print(f"ERROR: Lead ID {args.id} not found.")
        sys.exit(1)
    lead["notes"].append(args.text)
    save(data)
    print(f"Note added to [{lead['id']}] {lead['name']}: {args.text}")

def cmd_today(args):
    data = load()
    today = str(date.today())
    due = [l for l in data if l.get("followup_date") and l["followup_date"] <= today]
    if not due:
        print("No leads due today.")
        return
    for l in due:
        print(f"[{l['id']}] {l['name']} | {l['status']} | due: {l['followup_date']}")

def cmd_pipeline(args):
    data = load()
    from collections import Counter
    counts = Counter(l["status"] for l in data)
    print("=== Pipeline Summary ===")
    for status in VALID_STATUSES:
        print(f"  {status}: {counts.get(status, 0)}")
    print(f"  TOTAL: {len(data)}")

def cmd_import(args):
    master = Path(__file__).parent.parent.parent.parent / "MASTER_LEAD_LIST.md"
    if not master.exists():
        print("MASTER_LEAD_LIST.md not found.")
        return
    print(f"Importing from {master}...")
    # Stub: real import logic would parse the markdown
    print("Import complete.")

def main():
    parser = argparse.ArgumentParser(description="Gracie CRM")
    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list")

    # add
    p_add = sub.add_parser("add")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--phone", required=True)
    p_add.add_argument("--category", required=True)

    # call
    p_call = sub.add_parser("call")
    p_call.add_argument("id", type=int)
    p_call.add_argument("--outcome", required=True)
    p_call.add_argument("--followup", default=None)

    # note
    p_note = sub.add_parser("note")
    p_note.add_argument("id", type=int)
    p_note.add_argument("text")

    # today
    sub.add_parser("today")

    # pipeline
    sub.add_parser("pipeline")

    # import
    sub.add_parser("import")

    args = parser.parse_args()
    if args.command == "list":       cmd_list(args)
    elif args.command == "add":      cmd_add(args)
    elif args.command == "call":     cmd_call(args)
    elif args.command == "note":     cmd_note(args)
    elif args.command == "today":    cmd_today(args)
    elif args.command == "pipeline": cmd_pipeline(args)
    elif args.command == "import":   cmd_import(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

(crm_dir / "crm.py").write_text(crm_py)

# ─── Sales briefing file (the "messy input" the agent must interpret) ─────────
# This is NOT a README or hint; it's raw business data the agent must process
briefing = """\
OUTBOUND CALL BRIEFING — Week of 2026-03-10
Prepared by: Jay's Sales Ops Team

NEW PROSPECTS TO ENTER:
1. ProTech Auto Service | (347) 555-0191 | auto repair shop in Queens
2. Arctic Comfort HVAC | (646) 555-0374 | heating/cooling contractor
3. Bayside Family Dental | (718) 555-0852 | dental practice, Dr. Rivera

CALL LOG — Results from yesterday's session:
- ProTech Auto Service: Left voicemail, no callback. Schedule follow-up for 2026-03-15.
- Arctic Comfort HVAC: Spoke with owner Linda Park — very interested! Schedule follow-up for 2026-03-12.
- Bayside Family Dental: Receptionist said call back after 10am. Schedule follow-up for 2026-03-11.

NOTES TO ATTACH:
- For Arctic Comfort HVAC: "Owner is Linda Park, very warm lead, mentioned pain point with missed calls after hours"
- For Bayside Family Dental: "Front desk contact is Maria, best time to call is after 10am"
"""

(base / "01_LEADS/raw_exports/call_briefing_2026-03-10.txt").write_text(briefing)

print("Workspace generated successfully.")
print(f"CRM dir: {crm_dir}")
print(f"crm.json initialized with empty array.")