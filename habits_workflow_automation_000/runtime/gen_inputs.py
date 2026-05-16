#!/usr/bin/env python3
"""
Generate the sandbox workspace: raw messy activity logs that the agent must
transform into a proper ~/habits/ tracking workspace.
"""
import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/root")

# ── Create distractor directories and files ──────────────────────────────────
distractors = [
    "projects/client_alpha/proposal_v1.txt",
    "projects/client_alpha/proposal_v2.txt",
    "projects/client_beta/contract_draft.txt",
    "projects/client_beta/invoice_march.txt",
    "notes/meeting_notes_2024.txt",
    "notes/random_ideas.txt",
    "notes/phone_numbers.txt",
    "docs/wellness_framework.txt",
    "docs/pricing_strategy.txt",
    "docs/session_templates/template_A.txt",
    "docs/session_templates/template_B.txt",
    "archive/old_tracker_2022.csv",
    "archive/goals_2023.txt",
]

for rel_path in distractors:
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"Distractor file: {rel_path}\nNothing useful here.\n")

# ── Raw activity log (the messy input the agent must process) ────────────────
# This is a plain-text dump the "wellness coach" kept in a notebook-style file.
# It is intentionally messy: mixed date formats, casual language, no structure.
raw_log_path = workspace / "raw_activity_log.txt"
raw_log_content = """\
=== MY ACTIVITY LOG (raw notes) ===

Habits I want to track:
1. "client_calls"   - I target weekdays only (Mon-Fri), every weekday.
2. "journaling"     - I want to do this daily (every single day).
3. "exercise"       - I aim for 3 times per week (any 3 days, flexible).

---- LOG ENTRIES (most recent first) ----

2024-03-15 (Friday)    : client_calls=YES, journaling=YES, exercise=NO
2024-03-14 (Thursday)  : client_calls=YES, journaling=YES, exercise=YES
2024-03-13 (Wednesday) : client_calls=NO,  journaling=YES, exercise=NO
2024-03-12 (Tuesday)   : client_calls=YES, journaling=NO,  exercise=YES
2024-03-11 (Monday)    : client_calls=YES, journaling=YES, exercise=NO
2024-03-10 (Sunday)    : client_calls=N/A, journaling=NO,  exercise=YES
2024-03-09 (Saturday)  : client_calls=N/A, journaling=YES, exercise=NO
2024-03-08 (Friday)    : client_calls=YES, journaling=YES, exercise=NO
2024-03-07 (Thursday)  : client_calls=YES, journaling=YES, exercise=YES
2024-03-06 (Wednesday) : client_calls=YES, journaling=YES, exercise=YES
2024-03-05 (Tuesday)   : client_calls=YES, journaling=YES, exercise=NO
2024-03-04 (Monday)    : client_calls=NO,  journaling=YES, exercise=YES
2024-03-03 (Sunday)    : client_calls=N/A, journaling=YES, exercise=NO
2024-03-02 (Saturday)  : client_calls=N/A, journaling=YES, exercise=NO
2024-03-01 (Friday)    : client_calls=YES, journaling=NO,  exercise=YES

Notes:
- client_calls: I skipped Mar 13 because of illness, and Mar 4 because I forgot.
- journaling: Missed Mar 12 and Mar 1 — just got busy.
- exercise: Flexible days, just need 3 per week.
"""
raw_log_path.write_text(raw_log_content)

print("Workspace generated successfully.")
print(f"Raw log: {raw_log_path}")
print(f"Distractor files: {len(distractors)}")