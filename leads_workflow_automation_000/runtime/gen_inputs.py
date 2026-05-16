import os
import random
import json
from pathlib import Path

random.seed(42)

# --- Workspace root ---
workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# --- Simulate the leads skill being installed ---
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# Write the actual leads script (script.sh) - this is the installed skill
script_content = r'''#!/usr/bin/env bash
set -euo pipefail

LEADS_DIR="${HOME}/.leads"
LEADS_FILE="${LEADS_DIR}/leads.json"

mkdir -p "$LEADS_DIR"

if [ ! -f "$LEADS_FILE" ]; then
    echo "[]" > "$LEADS_FILE"
fi

_uuid() {
    python3 -c "import uuid; print(str(uuid.uuid4())[:8])"
}

_now() {
    date +"%Y-%m-%dT%H:%M:%S"
}

_month() {
    date +"%Y-%m"
}

cmd="${1:-}"
shift || true

case "$cmd" in

add)
    name="${1:?'name required'}"
    email="${2:?'email required'}"
    company="${3:?'company required'}"
    source="${4:-direct}"

    id=$(_uuid)
    created=$(_now)
    month=$(echo "$created" | cut -c1-7)

    python3 - <<PYEOF
import json, sys
with open("$LEADS_FILE") as f:
    leads = json.load(f)
new_lead = {
    "id": "$id",
    "name": "$name",
    "email": "$email",
    "company": "$company",
    "source": "$source",
    "status": "new",
    "score": 0,
    "deal_value": None,
    "follow_up": None,
    "follow_up_note": None,
    "created": "$created",
    "month": "$month"
}
leads.append(new_lead)
with open("$LEADS_FILE", "w") as f:
    json.dump(leads, f, indent=2)
print(f"Lead added: $id | $name | $company | source=$source")
PYEOF
    ;;

list)
    status_filter="${1:-}"
    sort_by="${2:-}"

    python3 - <<PYEOF
import json, sys
with open("$LEADS_FILE") as f:
    leads = json.load(f)
status_filter = "$status_filter"
sort_by = "$sort_by"
if status_filter and status_filter != "--sort":
    leads = [l for l in leads if l["status"] == status_filter]
if "--sort" in ["$status_filter", "$sort_by"]:
    sort_key = "$sort_by" if "$sort_by" not in ["", "--sort"] else "$status_filter"
    sort_key = sort_key.replace("--sort", "").strip() or "date"
    if "score" in sort_key:
        leads = sorted(leads, key=lambda x: x["score"], reverse=True)
    else:
        leads = sorted(leads, key=lambda x: x["created"], reverse=True)
for l in leads:
    fu = l.get("follow_up") or "-"
    print(f"[{l['id']}] {l['name']} <{l['email']}> | {l['company']} | status={l['status']} score={l['score']} follow_up={fu}")
PYEOF
    ;;

score)
    lead_id="${1:?'lead_id required'}"
    points="${2:?'points required'}"
    reason="${3:-}"

    python3 - <<PYEOF
import json, sys
with open("$LEADS_FILE") as f:
    leads = json.load(f)
found = False
for l in leads:
    if l["id"] == "$lead_id":
        old_score = l["score"]
        new_score = old_score + int("$points")
        new_score = max(0, min(100, new_score))
        l["score"] = new_score
        found = True
        print(f"Score updated: $lead_id | {old_score} -> {new_score} | reason=$reason")
        break
if not found:
    print(f"Error: lead $lead_id not found", file=sys.stderr)
    sys.exit(1)
with open("$LEADS_FILE", "w") as f:
    json.dump(leads, f, indent=2)
PYEOF
    ;;

follow-up)
    lead_id="${1:?'lead_id required'}"
    date_val="${2:?'date required'}"
    note="${3:?'note required'}"

    python3 - <<PYEOF
import json, sys
with open("$LEADS_FILE") as f:
    leads = json.load(f)
found = False
for l in leads:
    if l["id"] == "$lead_id":
        l["follow_up"] = "$date_val"
        l["follow_up_note"] = "$note"
        found = True
        print(f"Follow-up set: $lead_id | $date_val | $note")
        break
if not found:
    print(f"Error: lead $lead_id not found", file=sys.stderr)
    sys.exit(1)
with open("$LEADS_FILE", "w") as f:
    json.dump(leads, f, indent=2)
PYEOF
    ;;

convert)
    lead_id="${1:?'lead_id required'}"
    deal_value="${2:-}"

    python3 - <<PYEOF
import json, sys
with open("$LEADS_FILE") as f:
    leads = json.load(f)
found = False
for l in leads:
    if l["id"] == "$lead_id":
        l["status"] = "converted"
        if "$deal_value":
            try:
                l["deal_value"] = float("$deal_value")
            except:
                l["deal_value"] = None
        found = True
        print(f"Converted: $lead_id | {l['name']} | deal_value={l['deal_value']}")
        break
if not found:
    print(f"Error: lead $lead_id not found", file=sys.stderr)
    sys.exit(1)
with open("$LEADS_FILE", "w") as f:
    json.dump(leads, f, indent=2)
PYEOF
    ;;

pipeline)
    month_filter="${1:-$(_month)}"

    python3 - <<PYEOF
import json
with open("$LEADS_FILE") as f:
    leads = json.load(f)
month = "$month_filter"
monthly = [l for l in leads if l.get("month","").startswith(month)]
statuses = ["new","contacted","qualified","converted","lost"]
total = len(monthly)
print(f"Pipeline Report: {month}")
print(f"Total leads: {total}")
for s in statuses:
    count = sum(1 for l in monthly if l["status"] == s)
    rate = (count/total*100) if total > 0 else 0
    print(f"  {s}: {count} ({rate:.1f}%)")
converted = sum(1 for l in monthly if l["status"] == "converted")
conv_rate = (converted/total*100) if total > 0 else 0
print(f"Conversion rate: {conv_rate:.1f}%")
total_value = sum(l["deal_value"] for l in monthly if l["status"]=="converted" and l["deal_value"])
print(f"Total deal value: {total_value:.2f}")
PYEOF
    ;;

*)
    echo "Unknown command: $cmd"
    echo "Usage: $0 <add|list|score|follow-up|convert|pipeline> [args...]"
    exit 1
    ;;
esac
'''

with open(scripts_dir / "script.sh", "w") as f:
    f.write(script_content)

# --- SKILL.md ---
skill_md = """---
name: leads
description: "Manage sales leads locally. Use when adding prospects, scoring leads, setting follow-ups, tracking conversions, or viewing funnels."
version: "3.4.0"
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
tags:
  - sales
  - crm
  - leads
  - pipeline
  - follow-up
---

# Leads — Sales Lead CRM

Manage sales leads through their lifecycle: add, score, follow up, convert, and report on your pipeline.

## Commands

### add — Add a new lead

```bash
bash scripts/script.sh add "<name>" "<email>" "<company>" "[source]"
```

Creates a new lead with status `new`. Source defaults to `direct`.

### list — View leads

```bash
bash scripts/script.sh list [status] [--sort score|date]
```

Lists all leads, optionally filtered by status (`new`, `contacted`, `qualified`, `converted`, `lost`). Sort by score or date.

### score — Score a lead

```bash
bash scripts/script.sh score "<lead_id>" <points> "[reason]"
```

Assigns or adds score points to a lead. Score range: 0-100. Higher = more likely to convert.

### follow-up — Set follow-up reminder

```bash
bash scripts/script.sh follow-up "<lead_id>" "<YYYY-MM-DD>" "<note>"
```

Schedules a follow-up action for a lead on the specified date with a note.

### convert — Mark lead as converted

```bash
bash scripts/script.sh convert "<lead_id>" "[deal_value]"
```

Changes lead status to `converted` and optionally records deal value.

### pipeline — Sales funnel report

```bash
bash scripts/script.sh pipeline [YYYY-MM]
```

Shows a funnel breakdown of leads by status with counts and conversion rates. Defaults to current month.

## Output

All commands print plain text to stdout. Data is stored in `~/.leads/leads.json`.


## Requirements
- bash 4+
- python3 (standard library only)

## Feedback

Report issues or suggestions: [https://bytesagain.com/feedback/](https://bytesagain.com/feedback/)

---

Powered by BytesAgain | bytesagain.com
"""

with open(workspace / "SKILL.md", "w") as f:
    f.write(skill_md)

# --- Distractor files to increase realism ---
# Sales team raw data dump (messy CSV, not a usable format)
raw_prospects_csv = """prospect_name,email,org,channel,est_value,priority_score,notes
Alice Nguyen,alice@shieldcorp.io,ShieldCorp,LinkedIn,45000,87,"Interested in EDR suite; follow-up after Q3 budget cycle"
Bob Tran,bob.tran@fortifytech.com,FortifyTech,conference,120000,92,"CISO contact; needs custom pricing; very hot"
Carol Mehta,carol@nexusdefense.net,NexusDefense,referral,30000,55,"Mid-market; evaluating 3 vendors"
David Park,d.park@sentinelwave.com,SentinelWave,webinar,75000,78,"Attended product demo; requested trial"
Eve Okonkwo,eve.o@cyberfortress.biz,CyberFortress,direct,200000,95,"Enterprise deal; legal review ongoing"
Frank Lee,frank@infraguard.co,InfraGuard,direct,15000,40,"Small team; budget constrained"
"""

with open(workspace / "raw_prospects.csv", "w") as f:
    f.write(raw_prospects_csv)

# Old scoring rubric doc
scoring_rubric = (
    "# Lead Scoring Rubric v2 (DEPRECATED - see new CRM system)\n"
    "Company size >500 employees: +30\n"
    "Has dedicated security budget: +25\n"
    "Attended demo: +20\n"
    "Referred by existing customer: +15\n"
    "Responded within 48h: +10\n"
)
with open(workspace / "scoring_rubric_v2.md", "w") as f:
    f.write(scoring_rubric)

# Sales ops directory with noise
sales_ops_dir = workspace / "sales_ops"
sales_ops_dir.mkdir(exist_ok=True)

with open(sales_ops_dir / "q3_targets.txt", "w") as f:
    f.write("Q3 2024 Targets\nNew Leads: 50\nConverted: 10\nPipeline Value: $1M\n")

with open(sales_ops_dir / "team_roster.csv", "w") as f:
    f.write("rep_name,region,quota\nJane Smith,APAC,250000\nMark Jones,EMEA,300000\nSarah Kim,AMER,400000\n")

with open(sales_ops_dir / "lost_reasons_analysis.txt", "w") as f:
    f.write("Top lost reasons:\n1. Price too high (42%)\n2. Chose competitor (31%)\n3. No budget (18%)\n4. No response (9%)\n")

# Config noise
config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)

with open(config_dir / "crm_export_schema.json", "w") as f:
    json.dump({
        "version": "1.2",
        "fields": ["id","name","email","company","source","status","score","deal_value"],
        "export_format": "json"
    }, f, indent=2)

with open(config_dir / "integrations.yaml", "w") as f:
    f.write("# Placeholder - integrations not yet configured\nslack: disabled\nhubspot: disabled\nsalesforce: disabled\n")

# Reports directory
reports_dir = workspace / "reports"
reports_dir.mkdir(exist_ok=True)

with open(reports_dir / "monthly_template.txt", "w") as f:
    f.write("MONTHLY PIPELINE REPORT\nDate: {{date}}\nTotal: {{total}}\nConverted: {{converted}}\nRevenue: {{revenue}}\n")

with open(reports_dir / "last_month_summary.txt", "w") as f:
    f.write("June 2024 Summary\nTotal leads: 22\nConverted: 4\nRevenue: $185,000\n")

# Follow-up schedule (noise, not to be used directly)
with open(workspace / "followup_schedule.txt", "w") as f:
    f.write("""Planned follow-up dates (manual tracking):
Alice Nguyen - 2024-08-15 - Send EDR pricing sheet
Bob Tran - 2024-08-10 - Legal call re: enterprise contract
Carol Mehta - 2024-08-20 - Check vendor shortlist status
David Park - 2024-08-12 - Trial access setup
Eve Okonkwo - 2024-08-08 - Legal review follow-up
Frank Lee - 2024-09-01 - Re-engage after budget review
""")

# A fake pipeline snapshot
with open(workspace / "pipeline_snapshot_june.json", "w") as f:
    json.dump([
        {"name": "Alice", "status": "qualified", "score": 87},
        {"name": "Bob", "status": "converted", "deal": 120000},
    ], f, indent=2)

# The task instructions
task_instructions = """# Sales Lead Onboarding Task

Your mission: Process the 6 prospects from raw_prospects.csv into the lead management system.

See the details below for priority_score and est_value -- you'll need them.

Follow the standard onboarding protocol:
1. Add all 6 prospects as leads (use the 'channel' field as source)
2. Score them (use priority_score from CSV -- remember scores are additive)
3. Set follow-up dates and notes (use followup_schedule.txt)
4. Convert Eve Okonkwo (est_value: 200000) and Bob Tran (est_value: 120000)
5. Pull the pipeline report for the current month

Save the final pipeline report output to: pipeline_report.txt
"""

with open(workspace / "task_instructions.txt", "w") as f:
    f.write(task_instructions)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")