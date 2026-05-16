import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Skill directory structure (as described in SKILL.md) ────────────────────
refs = workspace / "references"
refs.mkdir(exist_ok=True)

scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# watch-models.md
(refs / "watch-models.md").write_text("""\
# Watch Models Reference

## 4/4 Watch Model
- 4 hours on watch, 4 hours off watch, rotating around the clock.
- Two watch-keepers alternate: Person A and Person B.
- Typical daily watches: 00-04, 04-08, 08-12, 12-16, 16-20, 20-24 (or offset by first-watch start).
- Sleep strategy: accumulate 2x 3h+ off-watch blocks for core rest. Protect at least one 3h uninterrupted block.
- Total sleep target: 7h/day, minimum 6h/day.
- Cognitively demanding tasks (navigation planning, reports, complex comms) must NOT be scheduled within the first hour after a fragmented sleep block.

## 3/3 Watch Model
- 3 hours on, 3 hours off. Common on short-sea / coastal vessels.
- High fragmentation; minimum sleep protection critical.
- Max 2 cognitively heavy tasks/day.

## 6/6 Watch Model
- 6 hours on, 6 hours off.
- Two blocks per day; easier to protect one 5-6h sleep core.
- Common on tankers and large cargo vessels.

## Solo Cycle
- Single operator, nap-based rotation.
- Must include at least 3 nap blocks of 20-30min.
- Safety scan every 90 min mandatory.
""")

# safety-anchors.md
(refs / "safety-anchors.md").write_text("""\
# Safety Anchors Reference

## Mandatory Safety Elements

### Start-of-Watch Handover Checklist
Every watch transition must include:
- Position fix confirmation
- Course and speed verification
- Traffic / ARPA status
- Weather update
- Outstanding orders from previous watch

### Safety Scans
- Minimum 2, maximum 4 safety scans per 24h period.
- Each scan: visual horizon sweep + instrument check + logbook note.
- Frequency increases in restricted visibility or heavy traffic.

### End-of-Day Log Line
- One mandatory log entry at end of day (23:00-23:59 local or last watch entry).
- Format: "EOD LOG — [date] — position, sea state, incidents, next watch officer."

## Non-Negotiable Anchor Rules
1. No watch handover without completing the full checklist.
2. Safety scans cannot be skipped, even in port.
3. EOD log is mandatory regardless of sea state.
""")

# internet-budgeting.md
(refs / "internet-budgeting.md").write_text("""\
# Internet Budgeting Reference

## Daily Allowance Calculation
- Formula: daily_MB = (weekly_GB * 1024) / 7
- Round down to nearest integer.
- Example: 4 GB/week → (4 * 1024) / 7 = 585 MB/day

## Low-Traffic Day
- Designate exactly one day per week as low-traffic day.
- Low-traffic day limit: 50 MB maximum.
- Recommended day: the crew's rest day or port day.

## Offline-First Policy
- Pre-download charts, routing files, and media during port/high-bandwidth windows.
- Disable cloud sync and autoplay on cellular/satellite connections.
- Use compressed messaging (no attachments > 500 KB via satellite).
- Schedule large uploads (logs, reports) during port windows, not at sea.

## Traffic Budget Output Format
- Line 1: "Daily budget: XXX MB/day (based on Y GB/week)"
- Line 2: "Policy: one low-traffic day capped at 50 MB; offline-first (disable autoplay, no cloud sync at sea)."
""")

# build_marine_plan.py starter script
(scripts_dir / "build_marine_plan.py").write_text("""\
#!/usr/bin/env python3
\"\"\"
Starter plan generator for marine watch planner.
Usage: python scripts/build_marine_plan.py --vessel <type> --role <role> \\
           --timezone <tz> --watch-model <model> --watch-start <HH:MM> \\
           --internet-gb <float> --priorities <comma-separated>
Outputs a skeleton 24h plan to stdout.
\"\"\"
import argparse
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vessel", default="offshore")
    parser.add_argument("--role", default="OOW")
    parser.add_argument("--timezone", default="Europe/Vilnius")
    parser.add_argument("--watch-model", default="4/4")
    parser.add_argument("--watch-start", default="08:00")
    parser.add_argument("--internet-gb", type=float, default=4.0)
    parser.add_argument("--priorities", default="sleep,productivity")
    args = parser.parse_args()

    daily_mb = int((args.internet_gb * 1024) / 7)

    print(f"# Starter Marine Plan")
    print(f"Vessel: {args.vessel} | Role: {args.role} | TZ: {args.timezone}")
    print(f"Watch Model: {args.watch_model} | First Watch: {args.watch_start}")
    print(f"Internet: {args.internet_gb} GB/week → {daily_mb} MB/day")
    print()
    print("## Skeleton 24h Blocks (expand with full anchors and policy)")
    start_h, start_m = map(int, args.watch_start.split(":"))
    blocks = []
    t = start_h * 60 + start_m
    model = args.watch_model
    if model == "4/4":
        pattern = [("ON WATCH", 240), ("OFF/SLEEP", 240)]
    elif model == "3/3":
        pattern = [("ON WATCH", 180), ("OFF/SLEEP", 180)]
    elif model == "6/6":
        pattern = [("ON WATCH", 360), ("OFF/SLEEP", 360)]
    else:
        pattern = [("ON WATCH", 240), ("OFF/SLEEP", 240)]
    pi = 0
    total = 0
    while total < 1440:
        label, dur = pattern[pi % len(pattern)]
        end = (t + dur) % 1440
        blocks.append((t, end, label))
        t = end
        total += dur
        pi += 1
    for (s, e, lbl) in blocks:
        sh, sm = divmod(s, 60)
        eh, em = divmod(e, 60)
        print(f"  {sh:02d}:{sm:02d}–{eh:02d}:{em:02d} — {lbl}")

if __name__ == "__main__":
    main()
""")

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "crew_manifest.csv").write_text("""\
name,rank,nationality,cert_expiry
John Harrington,Chief Officer,UK,2025-11-30
Maria Santos,2nd Officer,Philippines,2026-03-15
Dmitri Volkov,Chief Engineer,Russia,2025-08-01
Fatima Al-Rashidi,Bosun,UAE,2026-07-20
""")

(workspace / "vessel_specs.json").write_text(json.dumps({
    "name": "MV Northern Horizon",
    "type": "Platform Supply Vessel",
    "IMO": "9876543",
    "flag": "Marshall Islands",
    "GRT": 4200,
    "propulsion": "diesel-electric",
    "satcom_provider": "Inmarsat FleetBroadband",
    "max_crew": 14
}, indent=2))

(workspace / "port_calls_log.txt").write_text("""\
2025-01-10 08:00 — Departed Aberdeen, UK. Bound for North Sea Block 32/7.
2025-01-12 14:30 — Arrived platform. DP ops commenced.
2025-01-14 06:00 — Departed platform. Return Aberdeen.
2025-01-16 10:15 — Arrived Aberdeen.
""")

ops = workspace / "ops"
ops.mkdir(exist_ok=True)
(ops / "cargo_manifest_jan.txt").write_text("""\
Cargo Manifest - January Run
Item 1: 40x drilling collars, 2400 kg, Deck A
Item 2: 12x chemical drums (IBC), 1800 L, Hazmat locker
Item 3: Spare parts pallet, 600 kg, Deck B
""")

(ops / "weather_forecast_template.txt").write_text("""\
GRIB FILE PLACEHOLDER
Forecast period: T+0 to T+72
Area: North Sea
Source: ECMWF
(Download latest before departure)
""")

maint = workspace / "maintenance"
maint.mkdir(exist_ok=True)
(maint / "engine_log_week3.txt").write_text("""\
Week 3 Engine Room Log
- Main engine hours: 1842h
- Aux gen 1: Running (load 42%)
- Aux gen 2: Standby
- Fresh water maker: operational
- Bilge alarm: cleared 14:20
""")

(maint / "planned_maintenance_Q1.csv").write_text("""\
system,task,due_date,responsible
Fire suppression,Annual inspection,2025-03-01,Chief Eng
Lifeboat,Motor test,2025-02-15,Bosun
ECDIS,Software update,2025-02-01,OOW
""")

comms = workspace / "comms"
comms.mkdir(exist_ok=True)
(comms / "satcom_contract_summary.txt").write_text("""\
Contract: Inmarsat FleetBroadband - Standard Plan
Allocated: 3 GB / week
Overage: USD 8.50 / 100 MB
Billing cycle: weekly, resets Monday 00:00 UTC
Notes: No guaranteed QoS during solar events.
""")

(comms / "email_drafts.txt").write_text("""\
DRAFT 1: To shore office re: ETA update
DRAFT 2: To charterer re: cargo condition
DRAFT 3: Personal - family update (pending send)
""")

# ── The actual problem input: messy, partially-conflicting briefing ──────────
(workspace / "deployment_briefing.txt").write_text("""\
DEPLOYMENT BRIEFING — MV Northern Horizon — January 2025 Rotation
==================================================================

Officer: John Harrington
Current Rank: Chief Officer (acts as OOW on this vessel)
Vessel Type: Platform Supply Vessel (classify as: offshore)

SCHEDULE REQUEST:
The Chief Officer is starting a new rotation. He needs a full 24-hour
daily routine built for the upcoming offshore transit. 

Operational parameters (some TBD, use best judgement):
  - Watch system: 4 on / 4 off  (standard North Sea PSV rotation)
  - First watch commences: 06:00 local
  - Timezone: America/Los_Angeles   <-- note: vessel is repositioning to 
                                         Pacific coast ops for this rotation
  - Priorities: sleep first, then productivity, then fitness

Internet / Comms:
  The satcom plan is 3 GB per week (see comms/satcom_contract_summary.txt).
  Note: the old contract listed 4 GB/week but that was the previous vessel. 
  Current allocation is confirmed 3 GB/week as per attached contract summary.

Additional notes:
  - Officer has requested that heavy cognitive work (reports, nav planning)
    NOT be placed right after broken sleep. Please honour this.
  - Shore manager wants the schedule as a file called: watch_schedule.md
  - Format should follow company standard (operational, short, no fluff).
""")

# ── Dummy old schedule (distractor) ─────────────────────────────────────────
(workspace / "old_schedule_template.docx.txt").write_text("""\
[OLD TEMPLATE - DO NOT USE]
This is a legacy schedule from the previous rotation (Europe/London timezone).
Watch start: 08:00. 6/6 model. Internet: 4 GB/week.
This file is archived and no longer valid.
""")

(workspace / "rotation_notes_draft.txt").write_text("""\
Rough notes from handover meeting:
- Previous OOW used 6/6 model → too tiring for PSV ops, switching to 4/4
- 4 GB limit was old Inmarsat deal, new contract signed Dec 2024 = 3 GB
- Start time debated: 06:00 or 08:00? Ops manager confirmed 06:00.
- Timezone confusion: London ops finished, now Pacific coast. Use LA time.
""")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")