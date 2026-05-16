import os
import random
import datetime

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "projects/alpha/docs",
    "projects/alpha/src",
    "projects/beta/specs",
    "archives/2025/Q1",
    "archives/2025/Q2",
    "notes/personal",
    "notes/work",
    "config",
    "logs",
    "memory/temp",   # correct location, but empty
    "memory",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "projects/alpha/docs/requirements.txt": "Feature A: user login\nFeature B: dashboard\nFeature C: reporting\n",
    "projects/alpha/src/main.py": "# Main entry point\nprint('hello world')\n",
    "projects/beta/specs/architecture.md": "# Architecture\nMicroservices pattern with REST APIs.\n",
    "archives/2025/Q1/report_jan.md": "# January Report\nRevenue: $120,000\n",
    "archives/2025/Q2/report_apr.md": "# April Report\nRevenue: $145,000\n",
    "notes/personal/ideas.md": "- Learn Rust\n- Read 'Thinking Fast and Slow'\n",
    "notes/work/meeting_notes.md": "## Meeting 2025-04-01\nDiscussed Q2 targets.\n",
    "config/settings.json": '{"theme": "dark", "language": "zh-CN", "notifications": true}\n',
    "logs/access.log": "2025-04-01 10:00:01 GET /api/users 200\n2025-04-01 10:01:23 POST /api/data 201\n",
    "logs/error.log": "2025-04-03 14:22:01 ERROR NullPointerException in module auth\n",
}
for rel_path, content in distractor_files.items():
    with open(os.path.join(workspace, rel_path), "w", encoding="utf-8") as f:
        f.write(content)

# --- RAW CONVERSATION LOGS (the messy input the agent must process) ---
# These are 5 raw conversation logs from a consulting firm AI assistant
# They are intentionally unstructured and need to be converted into proper session files

raw_logs_dir = os.path.join(workspace, "raw_conversations")
os.makedirs(raw_logs_dir, exist_ok=True)

raw_logs = {
    "conv_001.txt": """[2026-03-09 09:15]
User: We need to review the Henderson contract before Friday.
AI: I'll help you review it. Key clause 7 limits liability to $500k.
User: We should negotiate that up to $1M. Make a note.
AI: Noted. I also see clause 12 has an auto-renewal - do you want a reminder?
User: Yes, set reminder 60 days before renewal date which is June 30.
User: Also I hate receiving PDF reports, always send Excel instead.
AI: Got it - Excel format for all future reports.
""",
    "conv_002.txt": """[2026-03-09 11:30]
User: The Jenkins pipeline failed again because we forgot to set ENV variables.
AI: I see - this happened last month too. The fix is to add DEPLOY_ENV and DB_HOST to the CI config.
User: Right. We need to document this so it never happens again.
AI: I'll create a checklist. Also, the staging server needs a restart every Monday.
User: Add that to the weekly ops checklist.
User: I feel frustrated this keeps happening.
""",
    "conv_003.txt": """[2026-03-09 14:00]
User: Decision: we're moving from AWS to GCP for the main database. Cost savings of 40%.
AI: Understood. Migration timeline should be Q3 2026. I'll note the reasoning.
User: The main reason is vendor lock-in concerns plus the 40% cost reduction.
User: Schedule a technical review with the infra team for next week.
""",
    "conv_004.txt": """[2026-03-09 16:45]
User: Quick note - learned today that our biggest client Acme Corp prefers morning calls only, never after 2pm.
AI: Noted, I'll always schedule Acme Corp calls before 14:00.
User: Also they hate slide decks with more than 10 slides.
AI: Got it - max 10 slides for Acme Corp presentations.
""",
    "conv_005.txt": """[2026-03-09 17:50]
User: Today I finally learned how to use the new CRM system's bulk import feature.
AI: Great progress! That will save about 2 hours per week.
User: Yes! And I figured out the API integration with Salesforce too.
User: Make sure to remember this was a big win this week.
AI: Absolutely noted as a skill milestone.
""",
}

for filename, content in raw_logs.items():
    with open(os.path.join(raw_logs_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)

# --- Stale daily report files (older than 30 days, should be cleaned by weekly distillation) ---
# These simulate old memory files that should be purged
stale_date = datetime.date(2026, 2, 5)  # More than 30 days before 2026-03-09
stale_memory_file = os.path.join(workspace, "memory", f"{stale_date}.md")
with open(stale_memory_file, "w", encoding="utf-8") as f:
    f.write(f"# Daily Summary {stale_date}\n\n## 今天完成的任务\n- Old task from February\n\n## 学到的新知识\n- Nothing special\n\n## 重要决策记录\n- None\n\n## 明日待办事项\n- Continue old project\n")

# Another stale file
stale_date2 = datetime.date(2026, 2, 1)
stale_memory_file2 = os.path.join(workspace, "memory", f"{stale_date2}.md")
with open(stale_memory_file2, "w", encoding="utf-8") as f:
    f.write(f"# Daily Summary {stale_date2}\n\n## 今天完成的任务\n- Early February task\n\n## 学到的新知识\n- Python decorators\n\n## 重要决策记录\n- Chose framework X\n\n## 明日待办事项\n- Deploy to staging\n")

# --- A task manifest file explaining what needs to be done ---
manifest = """# Memory Pipeline Task

## Context
Date: 2026-03-09 (Sunday)
You are setting up the AI memory management system for the consulting firm.

## Raw Input
The raw conversation logs are in: raw_conversations/
Conversation dates: all from 2026-03-09

## What needs to happen
Process all 5 conversations from 2026-03-09 through the complete memory pipeline.
The system should be fully set up with all outputs in place.
"""
with open(os.path.join(workspace, "TASK_CONTEXT.md"), "w", encoding="utf-8") as f:
    f.write(manifest)

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files")
print(f"Created {len(raw_logs)} raw conversation logs")
print("Created 2 stale memory files (>30 days old)")