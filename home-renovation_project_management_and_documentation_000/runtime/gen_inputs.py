import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/home/user/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create the skill's companion documentation files (referenced in SKILL.md) ---
skill_dir = workspace / "skill_docs"
skill_dir.mkdir(exist_ok=True)

(skill_dir / "setup.md").write_text("""# Setup Guide
Create ~/home-renovation/ directory structure on first use.
The memory.md file serves as the master index for all active projects.
Each project gets its own file under projects/ subdirectory.
Archive completed projects to archive/ subdirectory.
""")

(skill_dir / "memory-template.md").write_text("""# Home Renovation Memory

## Active Projects
| Project | Status | Budget | Next Action |
|---------|--------|--------|-------------|
| (none yet) | - | - | - |

## Notes
- Last updated: (date)
""")

(skill_dir / "projects.md").write_text("""# Project Types & Typical Costs

## Bathroom Remodel
- Low: $8,000
- Mid: $20,000
- High: $40,000+
- Notes: Tile and fixtures vary widely

## Kitchen Remodel
- Low: $15,000
- Mid: $40,000
- High: $80,000+
- Notes: Cabinets drive cost

## Flooring
- Low: $3/sqft
- Mid: $8/sqft
- High: $15+/sqft

## Cost Multipliers
- HCOL area: 1.5-2x
- Historic home: 1.3-1.5x
- Expedited: 1.2-1.5x
""")

(skill_dir / "phases.md").write_text("""# Renovation Phases

1. Planning & permits
2. Demolition
3. Structural/rough-in (electrical, plumbing, HVAC)
4. Insulation & drywall
5. Finishes (paint, flooring, fixtures)
6. Final inspection & punch list

## Phase Rules
- Never start a later phase before earlier ones are complete.
- Permits must be approved before demolition begins.
- Rough-in must be inspected before drywall closes it in.
""")

(skill_dir / "contractors.md").write_text("""# Contractor Evaluation

## Green Flags
- Provides references readily
- Licensed and insured
- Will pull permits
- Asks detailed scope questions
- Mid-range bid

## Red Flags
- Won't provide references
- Demands >30% deposit
- No written contract
- Can start tomorrow (suspiciously available)
- Much lower bid than others
- Pressures quick decision
- No license/insurance proof
- Won't pull permits

## Payment Schedule Best Practices
- Deposit: ≤30% of total contract
- Progress payments tied to milestones
- Final 10-15% held until punch list complete
""")

# --- Create distractor files that simulate a messy real workspace ---

# Old unrelated notes
(workspace / "grocery_list.txt").write_text("milk\neggs\nbread\nbutter\n")

# Old renovation ideas (not a real project file)
(workspace / "renovation_ideas.txt").write_text("""Maybe do the kitchen next year.
The bathroom needs new tile for sure.
Paint the living room?
""")

# A fake old project attempt (wrong location, wrong format)
old_proj = workspace / "old_bathroom_notes"
old_proj.mkdir(exist_ok=True)
(old_proj / "notes.txt").write_text("""Called Mike about bathroom - $6500 total
Wants $3000 upfront
Can start next week
""")

# Confusing finance doc
(workspace / "home_expenses_2023.csv").write_text("""date,category,amount
2023-01-15,mortgage,2100
2023-02-10,utilities,320
2023-03-05,insurance,180
""")

# Random contractor business cards dump
contacts_dir = workspace / "contacts"
contacts_dir.mkdir(exist_ok=True)
(contacts_dir / "plumber_joe.txt").write_text("Joe's Plumbing\n555-0101\nno license on file\n")
(contacts_dir / "tile_guy.txt").write_text("Tony's Tile\n555-0202\ngreat references\n")
(contacts_dir / "general_contractor.txt").write_text("BuildRight LLC\n555-0303\nfully licensed\n")

# Some old receipts
receipts_dir = workspace / "receipts"
receipts_dir.mkdir(exist_ok=True)
(receipts_dir / "home_depot_2023.txt").write_text("Home Depot\nDate: 2023-11-20\nTotal: $342.18\nItems: paint brushes, drop cloth, caulk\n")
(receipts_dir / "lowes_2024.txt").write_text("Lowes\nDate: 2024-01-08\nTotal: $89.45\nItems: misc hardware\n")

# A half-baked budget spreadsheet
(workspace / "rough_budget_scratch.txt").write_text("""bathroom rough budget
tiles: ~2000
labor: no idea
fixtures: 1500?
toilet: 400
vanity: 600-1200
""")

# Misc home files
home_docs = workspace / "home_documents"
home_docs.mkdir(exist_ok=True)
(home_docs / "mortgage_statement.txt").write_text("Mortgage balance as of 2024-06: $187,450\nMonthly payment: $2,100\n")
(home_docs / "home_insurance.txt").write_text("Policy #: HO-9928833\nAnnual premium: $2,160\nCoverage: $450,000 dwelling\n")
(home_docs / "property_tax.txt").write_text("2023 property tax: $4,820\n2024 estimate: $5,100\n")

# The actual problem input: a contractor quote document that the agent must analyze
quote_file = workspace / "contractor_quote_bathroom.txt"
quote_file.write_text("""=== CONTRACTOR QUOTE - BATHROOM REMODEL ===
Date: 2024-06-15
Contractor: FastFix Pro Renovations
Contact: Dave Kowalski, 555-0199

Scope of Work:
- Full gut renovation of master bathroom (75 sq ft)
- Demo existing tile, tub, toilet, vanity
- Install new subway tile (floor and walls)
- Install freestanding soaking tub
- Install new double vanity
- Install new toilet
- Update lighting fixtures (2 overhead, 1 vanity strip)
- Paint walls and ceiling

Quote Total: $11,200

Payment Terms:
- Deposit required to reserve start date: $5,600 (50% of contract)
- Second payment mid-project: $3,360 (30%)
- Final payment on completion: $2,240 (20%)

Availability: Can start this Monday (3 days from now)
License: "We're fully covered, don't worry about it"
References: "All our work speaks for itself, check our Facebook"
Permit note: "Permits are a hassle and add cost - we usually skip for bathrooms"
Timeline: 1 week

Other bids received for same scope:
- Contractor B (BuildRight LLC): $21,500
- Contractor C (Premier Bath): $19,800
""")

# Change order request from contractor (arrives mid-project)
change_order_file = workspace / "change_order_request.txt"
change_order_file.write_text("""=== CHANGE ORDER REQUEST ===
Date: 2024-06-28
From: Dave Kowalski, FastFix Pro
Project: Master Bathroom Remodel

While opening the walls, we found:
1. Corroded supply lines that should be replaced - this was not in original scope
2. Subfloor damage under tub area (about 20 sq ft) needs sistering/repair

Verbal quote from Dave: "It'll be about $2,800 extra, we can handle it today if you give the OK"

Current project status at time of change order:
- Original contract: $11,200 (NOTE: for tracking purposes, use the original quote total)
- Phase completed: Demolition done, rough-in starting
- Amount paid so far: $5,600 (deposit)
""")

print("Workspace generated successfully.")
print(f"Key files created:")
print(f"  {quote_file}")
print(f"  {change_order_file}")
print(f"  {skill_dir}/")
print(f"  (plus {len(list(workspace.rglob('*')))} total files/dirs)")