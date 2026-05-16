import os
import random
from pathlib import Path
from datetime import date

random.seed(42)

workspace = Path("/workspace")

# ─── Distractor files to test contextual awareness ───────────────────────────
distractor_dirs = [
    "workspace/projects/alpha-launch/specs",
    "workspace/projects/alpha-launch/mockups",
    "workspace/projects/beta-redesign",
    "workspace/notes/raw",
    "workspace/notes/archive",
    "workspace/tools/scripts",
    "workspace/clients/acme-corp",
    "workspace/clients/nova-inc/contracts",
    "workspace/research/ux-patterns",
    "workspace/finance/invoices",
]

for d in distractor_dirs:
    Path(f"/workspace/{d}").mkdir(parents=True, exist_ok=True)

distractor_files = {
    "workspace/projects/alpha-launch/specs/requirements_v2.txt": "Feature list (draft):\n- User login\n- Dashboard v3\n- Export to CSV\n",
    "workspace/projects/alpha-launch/specs/timeline_rough.md": "# Rough Timeline\nQ1: Design\nQ2: Dev\nQ3: Launch\n",
    "workspace/projects/beta-redesign/stakeholder_notes.txt": "Stakeholder meeting 2024-03-10: They want dark mode.\n",
    "workspace/notes/raw/dump_jan.txt": "Random thoughts from January - mixed bag of ideas, some actionable some not\n",
    "workspace/notes/raw/dump_feb.txt": "February braindump: pricing strategy, client feedback, tool frustrations\n",
    "workspace/notes/archive/old_tasks_2023.md": "- Buy domain ✓\n- Set up newsletter ✓\n- Launch MVP ✓\n",
    "workspace/tools/scripts/sync_files.sh": "#!/bin/bash\nrsync -avz ./workspace/ backup/\n",
    "workspace/clients/acme-corp/contact.md": "# ACME Corp\nContact: Jane Smith, jane@acme.com\n",
    "workspace/clients/nova-inc/contracts/nda_draft.txt": "NON-DISCLOSURE AGREEMENT DRAFT - NOT SIGNED\n",
    "workspace/research/ux-patterns/card-sorting-results.csv": "Category,Item,Group\nNavigation,Home,A\nNavigation,Search,A\n",
    "workspace/finance/invoices/inv_2024_001.txt": "Invoice #001\nAmount: $4500\nClient: ACME Corp\nDue: 2024-02-01\n",
    "workspace/finance/invoices/inv_2024_002.txt": "Invoice #002\nAmount: $2200\nClient: Nova Inc\nDue: 2024-03-15\n",
}

for path, content in distractor_files.items():
    p = Path(f"/{path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ─── Loci brain template (what git clone would produce) ──────────────────────
loci_root = Path("/root/loci")
loci_root.mkdir(parents=True, exist_ok=True)

# Subdirectory structure from the loci repo template
for d in ["me", "tasks/daily", "decisions", "docs", "people", "journal"]:
    (loci_root / d).mkdir(parents=True, exist_ok=True)

# plan.md with status: template (triggers First-Time Setup)
(loci_root / "plan.md").write_text("""\
---
status: template
---

# My Plan

<!-- Fill in your mission and goals after setup -->

## Mission
(not set)

## Goals
- [ ] (your first goal here)
""")

# inbox.md placeholder
(loci_root / "inbox.md").write_text("""\
# Inbox

<!-- Vague thoughts and unprocessed items land here -->
""")

# tasks/active.md placeholder
(loci_root / "tasks" / "active.md").write_text("""\
# Active Tasks

<!-- Tasks go here -->
""")

# docs/behavior.md (referenced in SKILL.md)
(loci_root / "docs" / "behavior.md").write_text("""\
# Behavior Rules

- Always read L1 files at conversation start
- Distill conclusions, not raw conversations
- Archive, never delete
- Speak human — never expose file paths
""")

# me/ placeholder files
(loci_root / "me" / "identity.md").write_text("""\
# Identity

<!-- Personal facts go here after setup -->
""")

(loci_root / "me" / "learned.md").write_text("""\
# Lessons Learned

<!-- Insights and lessons go here -->
""")

# NOTE: ~/.loci/brain-path does NOT exist yet — agent must create it
# NOTE: git remote is already removed (simulating post-clone state)

# ─── The briefing document the agent must process ────────────────────────────
briefing = Path("/workspace/initial_briefing.md")
briefing.write_text(f"""\
# Initial Briefing — Please Process Everything Below

## About Me
My name is **Marcus Veld**. I'm a freelance product strategist, mostly working with early-stage SaaS startups.
I usually work in the evenings and at night. Preferred language: English.

## My Current Season
Right now my biggest focus is landing a $50K/month retainer client by end of Q3.

## Items to Organize

### Item A
I've decided to stop taking equity-only deals. After three failed startups where I worked for equity 
and got nothing, I've concluded it's not worth my time. Cash only from now on.

### Item B
Need to follow up with Nova Inc about the product roadmap workshop — they're interested but haven't signed.

### Item C
Something I've been noticing: the best product decisions I've seen come from teams that talk to 
customers weekly, not monthly. Weekly cadence changes everything about how you prioritize.

### Item D
Not sure what to do about pricing — I oscillate between project-based and retainer models. 
Still thinking. No conclusion yet.

### Item E
My dog's name is Biscuit. She's a beagle and tends to bark during calls, which clients sometimes 
hear. I should probably mention it upfront as a quirky thing.

## Date Context
Today's date for file naming purposes: {date.today().isoformat()}
""")

print("Workspace setup complete.")
print(f"  - Loci template at: /root/loci (status: template)")
print(f"  - ~/.loci/brain-path: DOES NOT EXIST (agent must create)")
print(f"  - Briefing document: /workspace/initial_briefing.md")
print(f"  - Today's date: {date.today().isoformat()}")