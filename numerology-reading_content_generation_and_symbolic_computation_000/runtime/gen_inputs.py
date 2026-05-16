import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "app/src/components",
    "app/src/utils",
    "app/tests/unit",
    "app/tests/integration",
    "data/raw/users",
    "data/processed",
    "docs/internal",
    "docs/public",
    "config/dev",
    "config/prod",
    "scripts/migration",
    "scripts/cleanup",
    "reports/q1",
    "reports/q2",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "app/src/components/UserCard.jsx": "export default function UserCard({name}) { return <div>{name}</div>; }",
    "app/src/utils/dateHelper.js": "export const formatDate = (d) => d.toISOString().split('T')[0];",
    "app/tests/unit/userCard.test.js": "test('renders name', () => { expect(true).toBe(true); });",
    "app/tests/integration/flow.test.js": "// integration test placeholder",
    "data/raw/users/user_001.csv": "id,name,dob\n1,Alice,1990-01-01\n2,Bob,1985-06-15",
    "data/raw/users/user_002.csv": "id,name,dob\n3,Charlie,2000-11-22\n4,Diana,1978-03-09",
    "data/processed/cleaned_users.json": '[{"id":1,"name":"Alice","score":7},{"id":2,"name":"Bob","score":3}]',
    "docs/internal/onboarding.txt": "Welcome to the team. Please read the company wiki before starting.",
    "docs/public/faq.md": "# FAQ\n\nQ: What is this app?\nA: A wellness companion for daily reflection.",
    "config/dev/settings.yaml": "debug: true\ndatabase: sqlite\nport: 8000",
    "config/prod/settings.yaml": "debug: false\ndatabase: postgres\nport: 443",
    "scripts/migration/v1_to_v2.sh": "#!/bin/bash\necho 'Migrating schema v1 to v2...'",
    "scripts/cleanup/remove_duplicates.py": "# Script to remove duplicate records\nprint('done')",
    "reports/q1/summary.txt": "Q1 user growth: +12%\nRetention: 68%\nNPS: 42",
    "reports/q2/summary.txt": "Q2 user growth: +18%\nRetention: 71%\nNPS: 47",
    "app/src/utils/numerics.js": "export const sum = (...args) => args.reduce((a,b)=>a+b, 0);",
    "data/raw/users/anomalies.log": "2024-01-05 WARN: duplicate entry for user_id=99\n2024-01-06 ERROR: invalid dob format for user_id=102",
    "config/dev/feature_flags.json": '{"new_profile_page": true, "beta_numerology": false}',
    "docs/internal/meeting_notes_2024_03.txt": "Discussed beta feature rollout. Numerology profile sample needed for UX review.",
    "reports/q2/user_feedback.csv": "user_id,comment\n5,Love the daily prompts!\n6,Would like more personalization.",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE PROBLEM: messy user profile request ---
# The agent must process this file to produce the numerology snapshot
request_content = """\
BETA USER PROFILE REQUEST — Numerology Snapshot Needed
=======================================================

Requested by: Content Coordination Team
Priority: High (UX review scheduled Friday)

User Details (from registration form — raw export, not cleaned):
  Full legal name  :  Héléna Vögel-Moraes
  Date of birth    :  29 / 02 / 1988

Notes from QA team:
- Name contains accented characters (exported as-is from UTF-8 form)
- DOB verified against ID: February 29, 1988 is valid (1988 is a leap year)
- We need the FULL numerology profile: life path AND expression number
- Output must be a self-contained markdown file for the design team to embed

Please generate the numerology snapshot and save it as: numerology_snapshot.md

Additional context from product owner:
  "Make sure the calculations are transparent so our users can
   follow along themselves. Show every step of the math."
"""

request_path = os.path.join(workspace, "data", "raw", "users", "beta_user_request.txt")
with open(request_path, "w", encoding="utf-8") as f:
    f.write(request_content)

print("Workspace scaffold complete.")
print(f"Problem file: {request_path}")