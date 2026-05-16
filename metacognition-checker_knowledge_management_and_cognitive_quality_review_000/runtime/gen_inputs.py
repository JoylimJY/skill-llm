import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create a deeply nested distractor directory structure ---
distractor_dirs = [
    "workspace/team_docs/q3_reviews",
    "workspace/team_docs/q3_reviews/archive",
    "workspace/team_docs/onboarding",
    "workspace/team_docs/onboarding/materials",
    "workspace/projects/alpha",
    "workspace/projects/alpha/notes",
    "workspace/projects/beta/decisions",
    "workspace/reports/2024",
    "workspace/reports/2024/monthly",
    "workspace/admin/policies",
]
for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/team_docs/q3_reviews/performance_template.md": "# Q3 Performance Review Template\n\n## Goals\n## Achievements\n## Areas for Improvement\n",
    "workspace/team_docs/q3_reviews/archive/old_template_v1.txt": "Legacy template - do not use\n",
    "workspace/team_docs/onboarding/welcome.md": "# Welcome to the Team\nPlease read all materials before your first day.\n",
    "workspace/team_docs/onboarding/materials/checklist.txt": "Day 1:\n- Setup laptop\n- Meet team\n- Read docs\n",
    "workspace/projects/alpha/notes/meeting_2024_01.txt": "Discussed timeline. No major blockers.\n",
    "workspace/projects/alpha/notes/todo.md": "- Finalize spec\n- Review PRs\n- Update stakeholders\n",
    "workspace/projects/beta/decisions/decision_log.csv": "date,decision,owner\n2024-03-01,Adopt new DB schema,Alice\n2024-04-15,Delay release by 2 weeks,Bob\n",
    "workspace/reports/2024/monthly/kpi_june.txt": "KPIs for June:\n- Uptime: 99.8%\n- Tickets closed: 147\n",
    "workspace/reports/2024/summary.md": "Annual summary placeholder. TBD.\n",
    "workspace/admin/policies/leave_policy.txt": "Annual leave: 20 days\nSick leave: 10 days\nMaternity: 26 weeks\n",
}
for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT: messy cognitive review entries ---
# These are intentionally messy: missing fields, mixed languages, informal tone
# The agent must parse these and apply the metacognition checker template
cognitive_entries = [
    {
        "id": "entry_001",
        "submitter": "Zhang Wei",
        "role": "Backend Engineer",
        "date": "2024-06-10",
        "raw_text": """
        I'm pretty sure the performance bottleneck in our API is the database query on the orders table.
        I saw some slow query logs last week and one DBA mentioned indexes might help.
        Confidence: 80%
        What I'm most unsure about: whether it's really the DB or maybe the network layer.
        """,
    },
    {
        "id": "entry_002",
        "submitter": "Priya Nair",
        "role": "Product Manager",
        "date": "2024-06-11",
        "raw_text": """
        Our users don't like the new checkout flow. I've decided we need to roll it back.
        Evidence: 3 support tickets complaining about it, and my gut says it's worse.
        Confidence: 90%
        Biggest uncertainty: not sure if these 3 tickets are representative or just loud minority.
        """,
    },
    {
        "id": "entry_003",
        "submitter": "Carlos Mendez",
        "role": "Data Analyst",
        "date": "2024-06-12",
        "raw_text": """
        I understand how our recommendation algorithm works now. I read through the code and it makes sense to me.
        Basis: I went through the main recommendation.py file and the comments seem clear.
        Confidence level: 75%
        Uncertainty: I haven't actually run it or traced a real user's path through it.
        """,
    },
    {
        "id": "entry_004",
        "submitter": "Fatima Al-Rashid",
        "role": "Security Engineer",
        "date": "2024-06-13",
        "raw_text": """
        We're not vulnerable to the new JWT exploit that was published last week.
        I read the CVE description and I think our implementation doesn't match the vulnerable pattern.
        Confidence: 85%
        Most uncertain about: I haven't checked the exact library version we're using or whether our token validation path actually follows what I think it does.
        """,
    },
]

# Save to workspace
input_path = "workspace/cognitive_entries.json"
with open(input_path, "w", encoding="utf-8") as f:
    json.dump(cognitive_entries, f, ensure_ascii=False, indent=2)

print(f"Generated {len(cognitive_entries)} cognitive entries at {input_path}")
print("Distractor files created.")
print("Workspace ready.")