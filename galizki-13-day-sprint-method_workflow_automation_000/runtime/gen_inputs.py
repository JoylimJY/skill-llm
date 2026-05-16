import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "project_alpha/planning",
    "project_alpha/retrospectives",
    "project_alpha/releases",
    "project_beta/docs",
    "project_beta/standups",
    "team_docs/agile",
    "team_docs/templates",
    "archive/2025/Q4",
    "archive/2025/Q3",
    "tools/scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - plausible but irrelevant to the task
distractor_files = {
    "project_alpha/planning/velocity_chart.csv": "sprint,points_completed\n1,42\n2,38\n3,51\n4,45\n",
    "project_alpha/retrospectives/retro_notes_q2.txt": "Things that went well:\n- Better communication\n- Faster deploys\nThings to improve:\n- Documentation lag\n- Testing coverage\n",
    "project_alpha/releases/changelog_v2.md": "## v2.0.0\n- New dashboard\n- Performance improvements\n- Bug fixes\n",
    "project_beta/docs/architecture.md": "# System Architecture\n\nMicroservices pattern with event-driven communication.\n",
    "project_beta/standups/standup_log.txt": "2026-07-01: Alice working on auth module\n2026-07-02: Bob reviewing PRs\n",
    "team_docs/agile/scrum_guide_reference.txt": "Sprint duration: 2 weeks\nDaily standups: 15 minutes max\nRetrospective: Last day of sprint\n",
    "team_docs/templates/standup_template.md": "## Standup Template\n- Yesterday:\n- Today:\n- Blockers:\n",
    "archive/2025/Q4/sprint_summary_q4.json": json.dumps({"total_sprints": 6, "avg_velocity": 44, "bugs_closed": 23}),
    "archive/2025/Q3/old_roadmap.txt": "Q3 2025 targets:\n- Feature X\n- Performance audit\n- Security review\n",
    "tools/scripts/deploy.sh": "#!/bin/bash\necho 'Deploying to production...'\ngit push origin main\n",
    "project_alpha/planning/risk_register.md": "| Risk | Likelihood | Impact |\n|------|-----------|--------|\n| Key developer leaves | Medium | High |\n| Scope creep | High | Medium |\n",
    "team_docs/agile/definition_of_done.txt": "- All tests pass\n- Code reviewed\n- Documentation updated\n- Deployed to staging\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE CORE INPUT: A list of project milestone dates the PM wants analyzed ---
# These dates are carefully chosen to test edge cases:
# - Cross-month sprint boundaries
# - Dates in Reflection Phase (tones 11-13)
# - A date that is Tone 1 (Magnetic) - goal-setting day
# - Mid-sprint Action phase dates
# - A date early in the year (Sprint 1 oddity: starts at Tone 10)

milestones = [
    {
        "id": "M1",
        "name": "Alpha Feature Freeze",
        "date": "2026-07-15",
        "owner": "Alice",
        "description": "All alpha features must be code-complete"
    },
    {
        "id": "M2",
        "name": "Beta Public Release",
        "date": "2026-09-05",
        "owner": "Bob",
        "description": "Public beta launch announcement"
    },
    {
        "id": "M3",
        "name": "Stakeholder Review Meeting",
        "date": "2026-08-07",
        "owner": "Carol",
        "description": "Quarterly review with board members"
    },
    {
        "id": "M4",
        "name": "Post-Launch Cleanup Sprint",
        "date": "2026-10-28",
        "owner": "Team",
        "description": "Technical debt and cleanup work"
    },
    {
        "id": "M5",
        "name": "Year-End Retrospective",
        "date": "2026-12-21",
        "owner": "Team",
        "description": "Full year lessons learned session"
    },
    {
        "id": "M6",
        "name": "New Product Goal Setting",
        "date": "2026-11-13",
        "owner": "PM",
        "description": "Define product vision for next cycle"
    }
]

with open(os.path.join(workspace, "project_milestones.json"), "w") as f:
    json.dump({"project": "Helios Platform", "milestones": milestones}, f, indent=2)

print("Workspace generated successfully.")
print(f"Created {len(distractor_files)} distractor files across {len(dirs)} directories.")
print("Core input file: project_milestones.json")