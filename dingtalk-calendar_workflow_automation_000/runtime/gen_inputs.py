import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory Structure with Distractor Files ---
dirs = [
    "docs/onboarding",
    "docs/policies",
    "team/engineering",
    "team/product",
    "projects/q2_planning",
    "projects/q1_review",
    "meetings/archive",
    "meetings/templates",
    "config/infra",
    "scripts/utils",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "docs/onboarding/welcome.md": "# Welcome\nPlease read company policies before starting.",
    "docs/policies/leave_policy.txt": "Annual leave: 15 days.\nSick leave: 10 days.\nRemote work: 3 days/week.",
    "docs/policies/expense_policy.txt": "Meal allowance: 50 CNY/day.\nTravel: Economy class only.",
    "team/engineering/tech_stack.md": "# Tech Stack\n- Backend: Go\n- Frontend: React\n- DB: PostgreSQL\n- Cache: Redis",
    "team/product/roadmap_q2.md": "# Q2 Roadmap\n- Feature A: User analytics dashboard\n- Feature B: API rate limiting\n- Feature C: SSO integration",
    "projects/q2_planning/requirements.txt": "1. Define OKRs\n2. Assign owners\n3. Set milestones\n4. Budget review",
    "projects/q1_review/retro_notes.txt": "What went well: CI/CD pipeline improved\nWhat to improve: More cross-team syncs needed",
    "meetings/archive/2025_q1_kickoff.json": json.dumps({
        "title": "Q1 Kickoff",
        "date": "2025-01-06",
        "attendees": ["Alice Wang", "Bob Chen"],
        "notes": "Set team goals for Q1"
    }, ensure_ascii=False, indent=2),
    "meetings/templates/standup_template.md": "# Daily Standup\n1. What did you do yesterday?\n2. What will you do today?\n3. Any blockers?",
    "config/infra/k8s_cluster.yaml": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config\ndata:\n  env: production",
    "scripts/utils/timestamp_helper.py": "import time\n\ndef now_ms():\n    return int(time.time() * 1000)\n\nif __name__ == '__main__':\n    print(now_ms())",
    "team/engineering/org_chart.txt": "Engineering Team:\n  - Li Wei (Backend Lead)\n  - Zhang Min (Frontend)\n  - Chen Fang (DevOps)\n  - Wang Hao (QA)",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT ---
# A meeting request file with colleague names (not IDs) and desired date
meeting_request = {
    "requested_by": "Liu Yang",
    "purpose": "Q2 Sprint Planning Kick-off",
    "description": "Align on Q2 engineering priorities and assign sprint owners for the upcoming quarter.",
    "desired_date": "2026-07-14",
    "desired_time_range": "afternoon (13:00-18:00)",
    "duration_hours": 1,
    "required_attendees": ["Li Wei", "Zhang Min"],
    "note": "Please find the first available 1-hour slot when all attendees are free during the afternoon, create the calendar event, and save the result."
}

with open(os.path.join(workspace, "projects/q2_planning/meeting_request.json"), "w", encoding="utf-8") as f:
    json.dump(meeting_request, f, ensure_ascii=False, indent=2)

# --- Mock server data (for reference, not hints) ---
# These are stored server-side in the mock, NOT in the workspace
# User data: Li Wei -> uid_liwei_001, Zhang Min -> uid_zhangmin_002
# Busy slots on 2026-07-14:
#   Li Wei: 13:00-14:00 (busy), 15:00-16:00 (busy)
#   Zhang Min: 13:00-14:30 (busy), 16:00-17:00 (busy)
# Free slot for both: 14:30-15:00 (only 30 min), 14:00-15:00 NOT free for Zhang Min
# Actually let's make it: free for BOTH: 14:30-15:30 (1 hour)
# So the answer: 14:30-15:30 CST on 2026-07-14

print("Workspace generated successfully.")
print("Task: Read meeting_request.json, find user IDs, check busy status, create event.")