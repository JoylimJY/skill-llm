import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "ops/daily",
    "ops/trips",
    "ops/vendors",
    "projects/eventX",
    "projects/eventX/assets",
    "projects/eventY",
    "archive/2024/Q1",
    "archive/2024/Q3",
    "inbox",
    "comms/drafts",
    "comms/sent",
    "finance/invoices",
    "finance/budgets",
]
for d in dirs:
    Path(f"{WORKSPACE}/{d}").mkdir(parents=True, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: austine-daily-ops
description: Daily execution and trip-ops command system for Austine. Use when asked to run daily brief/checklist/status workflows, track priorities, or plan and procure trip logistics (transport, lodging, reservations, vendor quotes, recommendation + decision handoff).
---

# Austine Daily Ops

## Overview
Run Austine's day-to-day operating cadence with concise, action-first outputs, and handle travel operations like a sourcing assistant (options scan, quote gathering, recommendation, and execution handoff).

## Core Capabilities

### 1) Daily execution cadence
Use this pattern for daily operations asks.
- Output max 5 bullets unless user asks for depth.
- Always include: current status, blocker (or "No blocker"), next action.
- Prefer concrete actions over commentary.

When asked for daily planning:
1. List Top 3 priorities.
2. List next 72h critical deadlines/reminders.
3. Suggest one automation and one quick win (<15 min).
4. End with "next action I'll take."

### 2) Trip operations management
Use this for travel planning/procurement tasks.

Workflow:
1. **Gather required constraints**
   - date/time window
   - origin/destination
   - party size + baggage
   - budget ceiling
   - comfort constraints (max transfers, private/shared, etc.)
2. **Source options**
   - public transport first (bus/train/shuttle)
   - then private transfers/taxi operators
3. **Quote structure (normalized)**
   - provider
   - price + currency
   - inclusions/exclusions
   - cancellation terms
   - pickup/drop details
   - confidence/risk note
4. **Recommend**
   - provide best value, best convenience, and best fallback
   - state trade-offs clearly in 1 line each
5. **Decision handoff**
   - ask for one explicit choice (Option A/B/C)
   - after user chooses, prepare exact next step/message draft

### 3) Vendor follow-up mode
When waiting for confirmations (driver details, seat confirmations, check-in QR, etc.):
- Keep a short pending list with owner + due date.
- Trigger reminders with time buffer (day-before or earlier for critical items).
- Escalate if no response by cutoff.

## Output Rules
- Bullet-first, concise, high signal.
- No fluff.
- If data is uncertain, say so explicitly.
- For recommendations, always include one fallback.

## References
- For trip transport procurement templates and comparison format, read `references/transport-procurement.md`.
- For daily operating output templates, read `references/daily-ops-templates.md`.
"""

Path(f"{WORKSPACE}/SKILL.md").write_text(skill_md)

# ── references/transport-procurement.md ─────────────────────────────────────
transport_procurement_md = """\
# Transport Procurement Template

## Quote Comparison Table

Use this normalized format for every transport option sourced:

| Field               | Details                                     |
|---------------------|---------------------------------------------|
| Provider            | Name of company or operator                 |
| Price + Currency    | Total cost in local currency (e.g., MYR 180)|
| Inclusions          | What is included (toll, luggage, meet-greet)|
| Exclusions          | What is NOT included (tips, parking, extras)|
| Cancellation Terms  | Free cancellation window or penalty details |
| Pickup/Drop Details | Exact pickup point, terminal, timing        |
| Confidence/Risk     | Reliability rating or known risk (e.g., surge pricing likely) |

## Sourcing Order
1. Public transport options (bus, train, shuttle, ferry) — list first.
2. Private transfer / taxi / rideshare — list second.

## Recommendation Block
After the quote table, add a recommendation section:

### Best Value
- [Option name] — [one-line trade-off]

### Best Convenience
- [Option name] — [one-line trade-off]

### Best Fallback
- [Option name] — [one-line trade-off]

## Decision Handoff
End with:
> Please choose: Option A / Option B / Option C

## Notes
- Always flag uncertain prices with "(estimated)" or "(unconfirmed)".
- If a vendor has not confirmed, note "Pending confirmation" in the Confidence/Risk field.
"""

Path(f"{WORKSPACE}/references/transport-procurement.md").write_text(transport_procurement_md)

# ── references/daily-ops-templates.md ────────────────────────────────────────
daily_ops_templates_md = """\
# Daily Ops Output Templates

## Daily Planning Template

Use this exact structure when generating a daily plan:

---
## Daily Brief — [DATE]

### Top 3 Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

### Next 72h Critical Deadlines / Reminders
- [Deadline or reminder with date/time]
- [Deadline or reminder with date/time]

### Automation Suggestion
- [One specific automation idea]

### Quick Win (<15 min)
- [One quick win action]

### Next Action I'll Take
- [Concrete next action]
---

## Daily Status Update Template

Use when giving a quick status (not full planning):

- **Status:** [current status]
- **Blocker:** [blocker or "No blocker"]
- **Next Action:** [concrete next action]

(Max 5 bullets total.)

## Vendor Pending List Template

| Item                    | Owner     | Due Date   | Status            |
|-------------------------|-----------|------------|-------------------|
| [Confirmation item]     | [Vendor]  | [Date]     | [Pending/Done]    |

### Reminder Rule
- Trigger reminder 1 day before due date (or earlier for critical items).
- Escalate if no response by cutoff date.
"""

Path(f"{WORKSPACE}/references/daily-ops-templates.md").write_text(daily_ops_templates_md)

# ── Raw messy input: priorities_inbox.txt ────────────────────────────────────
priorities_raw = """\
things to handle this week (messy notes - tuesday morning)

- need to confirm venue lighting rig with KL Lightworks... they said they'll send quote by Wednesday EOD. critical for EventX.
- finish sponsorship deck for EventX... deadline is Thursday 5pm, half done
- follow up with caterring guy (Ahmad Catering) re: final headcount confirmation, he went quiet since Friday... due latest Wednesday noon
- EventY advance payment to venue - wire by Thursday morning or we lose the slot
- check if Jess submitted the crew call sheet for weekend shoot... hasn't replied since yesterday
- also outstanding: insurance certificate from BrightShield needed before Saturday event, Liyana is handling but no update
- review contract for new AV vendor (SoundPro), low urgency but been sitting for 2 weeks
- team sync is tomorrow 10am - need to prep agenda
- personal: dentist appt Thursday 3pm (don't forget)
"""
Path(f"{WORKSPACE}/inbox/priorities_inbox.txt").write_text(priorities_raw)

# ── Raw messy input: trip_request.txt ────────────────────────────────────────
trip_request_raw = """\
trip planning notes (voice-to-text, rough)

Need to get from KL Sentral to Putrajaya Convention Centre on Thursday morning
Event setup starts at 8am, so need to be there by 7:45am latest
Just me + one road case (medium-sized, about 20kg), no other bags
Budget: prefer under MYR 80 one-way, can stretch to MYR 120 if necessary
No more than 1 transfer if taking public transport
Prefer to be dropped at main entrance, not carpark

Options I've heard about:
- KTM Komuter + shuttle bus (someone said ~MYR 8-10 but not sure if there's luggage space)
- ERL to Putrajaya/Cyberjaya station then cab (heard it's about MYR 35-40 total?)
- Grab car direct (usually MYR 50-70 but surge possible in morning)
- Private transfer via "AzizDrive" operator (colleague used them, quoted MYR 90 flat, meet-and-greet, door to door)

No idea on cancellation terms or exact pickup points for any of these.
Need to book latest by Wednesday night.
"""
Path(f"{WORKSPACE}/inbox/trip_request.txt").write_text(trip_request_raw)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "ops/daily/old_brief_2024-03-10.txt": "Daily brief from March - archive only.\nStatus: all done.",
    "ops/daily/template_draft_v1.txt": "OLD TEMPLATE - DO NOT USE\nThis was the v1 format before we switched systems.",
    "ops/trips/trip_bali_2024.txt": "Bali trip April 2024 - completed. Flights: AirAsia. Hotel: Aloft. Total: MYR 2200.",
    "ops/vendors/vendor_list_partial.csv": "vendor,contact,last_used\nKL Lightworks,lightworks@example.com,2025-01-10\nAhmad Catering,ahmad@example.com,2025-02-01\nBrightShield,liyana@brightshield.example.com,2025-01-05",
    "ops/vendors/sla_notes.txt": "Vendor SLA notes: Ahmad Catering - 48h response. KL Lightworks - 72h. BrightShield - 24h.",
    "projects/eventX/brief.txt": "EventX - Corporate gala, 300pax, Saturday. Venue: Grand Ballroom KL. Theme: Futuristic.",
    "projects/eventX/assets/moodboard_notes.txt": "Colour: Electric blue + gold. Lighting rig: truss + LED wash. Need haze machine.",
    "projects/eventY/brief.txt": "EventY - Product launch, 150pax, following Wednesday. Venue: Putrajaya Convention Centre.",
    "archive/2024/Q1/q1_summary.txt": "Q1 2024 summary: 4 events executed. Revenue: MYR 380,000. Top vendor: Ahmad Catering.",
    "archive/2024/Q3/q3_summary.txt": "Q3 2024 summary: 6 events. Revenue: MYR 610,000. Blocker: staffing.",
    "comms/drafts/draft_vendor_email.txt": "Hi [VENDOR],\nJust following up on the pending quote...\n[DRAFT - NOT SENT]",
    "comms/sent/sent_log.txt": "2025-06-01: Sent quote request to KL Lightworks\n2025-06-02: Sent headcount to Ahmad Catering",
    "finance/invoices/inv_001.txt": "Invoice #001 - SoundPro AV - MYR 4500 - PENDING APPROVAL",
    "finance/budgets/eventX_budget.txt": "EventX Budget\nVenue: MYR 15000\nCatering: MYR 12000\nAV: MYR 8000\nLighting: MYR 5000\nMisc: MYR 2000\nTotal: MYR 42000",
}

for rel_path, content in distractors.items():
    p = Path(f"{WORKSPACE}/{rel_path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

print("Workspace generated successfully.")