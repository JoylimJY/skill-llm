import os
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create a realistic pre-existing workspace with distractor files
# Simulate a messy freelancer's workspace
distractor_dirs = [
    "client-files/acme-corp/contracts",
    "client-files/acme-corp/assets",
    "client-files/nova-studio/briefs",
    "downloads/references",
    "old-notes/2023",
    "old-notes/2024",
    "scratch",
    "tools/scripts",
    "personal/finances",
    "personal/health-logs",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files that look like they could be part of a notes system
distractors = {
    "client-files/acme-corp/contracts/NDA-signed.md": "# NDA\nSigned 2024-01-15. See legal folder.",
    "client-files/acme-corp/assets/brand-guidelines.txt": "Primary color: #2C3E50\nFont: Inter\n",
    "client-files/nova-studio/briefs/project-brief.md": "# Nova Studio Brief\nDeliverables: 5 screens",
    "downloads/references/ux-laws.txt": "Hick's Law, Fitts's Law, Miller's Law",
    "old-notes/2023/random-ideas.md": "# Random 2023 Ideas\n- Build a portfolio site\n- Learn Figma advanced",
    "old-notes/2024/meetings.txt": "Q1 meetings: ACME kickoff Jan 10, Nova Studio Feb 3",
    "scratch/temp.md": "# Temp\nDelete this later",
    "scratch/phone-numbers.txt": "John: 555-0101\nSarah: 555-0202",
    "tools/scripts/backup.sh": "#!/bin/bash\nrsync -av ~/Documents/ /backup/",
    "personal/finances/invoices.md": "# Invoices 2025\n- Invoice #001: ACME $3,500",
    "personal/health-logs/weekly.md": "Week 1: Ran 3x, slept 7h avg",
    "README-old.txt": "This folder is a mess. Need to organize.",
}

for path, content in distractors.items():
    full_path = workspace / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# THE ACTUAL TASK INPUT: A raw dump of today's captures as a single text file
# The agent must read this and process everything into brainrepo correctly
raw_dump = textwrap.dedent("""\
    # Today's Brain Dump — Process This

    ## Item 1: New Contact
    Met Sarah Chen today — she's a product manager at Meridian Health (a digital health startup).
    We connected at the UX Research Summit. She's interested in collaborating on patient-facing app research.
    Her focus: accessibility and inclusive design. Follow up with her next week.

    ## Item 2: New Project
    Starting a new project called "Meridian Health App Audit". 
    Client is Meridian Health. Deadline is 2025-09-30.
    Goal: audit their mobile app for accessibility compliance and deliver a report.
    First steps: get access to the app, schedule stakeholder interviews.

    ## Item 3: Task
    Need to invoice ACME Corp for the May deliverables. Amount: $4,200. Due end of this month.

    ## Item 4: Reusable Knowledge / Concept
    Learned about "Progressive Disclosure" in UX today — the technique of presenting only the 
    minimum necessary information and revealing more complexity only as users need it.
    This applies broadly across all UI design work, not just this project.

    ## Item 5: External Resource
    Found a great article about accessibility auditing:
    URL: https://www.a11yproject.com/checklist/
    Why it's useful: Comprehensive WCAG 2.1 checklist, will reference for Meridian audit.

    ## Item 6: Journal for today
    Date: 2025-07-14
    Summary: Attended UX Research Summit. Met Sarah Chen. Started thinking about Meridian project.
    Big win: landed the Meridian Health contract!
    
    Make sure to git commit all changes with the right message for a day's processing.
""")

(workspace / "todays-brain-dump.txt").write_text(raw_dump)

# Also create the SKILL.md and references so the agent can read them
skill_dir = workspace / "skill-docs"
skill_dir.mkdir(exist_ok=True)

# Note: per instructions, scripts in SKILL.md already exist. 
# We create reference docs the agent will need.
references_dir = workspace / "skill-docs" / "references"
references_dir.mkdir(exist_ok=True)

assets_templates_dir = workspace / "skill-docs" / "assets" / "templates"
assets_templates_dir.mkdir(parents=True, exist_ok=True)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")