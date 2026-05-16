import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# === Create the skill directory structure (as specified in SKILL.md) ===
skill_root = workspace / ".openclaw" / "skills" / "adhd-daily-planner"
(skill_root / "daily").mkdir(parents=True, exist_ok=True)
(skill_root / "monthly").mkdir(parents=True, exist_ok=True)
(skill_root / "collections").mkdir(parents=True, exist_ok=True)
(skill_root / "templates").mkdir(parents=True, exist_ok=True)

# === Distractor files to simulate a real messy workspace ===
distractor_dirs = [
    workspace / "projects" / "saas-app" / "src",
    workspace / "projects" / "saas-app" / "tests",
    workspace / "notes" / "meetings",
    workspace / "notes" / "ideas",
    workspace / "finance" / "invoices",
    workspace / "finance" / "expenses",
    workspace / "personal" / "fitness",
    workspace / "personal" / "reading",
    workspace / ".config" / "editor",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = [
    (workspace / "projects" / "saas-app" / "src" / "main.py", "# SaaS main entry\nprint('hello')"),
    (workspace / "projects" / "saas-app" / "src" / "config.py", "DEBUG=True\nDB_URL='sqlite:///dev.db'"),
    (workspace / "projects" / "saas-app" / "tests" / "test_main.py", "def test_pass(): assert True"),
    (workspace / "notes" / "meetings" / "2025-06-01-standup.md", "# Standup\n- Discussed Q2 roadmap"),
    (workspace / "notes" / "meetings" / "2025-06-03-investor.md", "# Investor call\n- Follow up needed"),
    (workspace / "notes" / "ideas" / "product-ideas.md", "- AI scheduling\n- Focus timer\n- Pomodoro SaaS"),
    (workspace / "finance" / "invoices" / "INV-0042.txt", "Client: Acme Corp\nAmount: $4,200"),
    (workspace / "finance" / "expenses" / "june-2025.csv", "date,amount,category\n2025-06-01,49.00,SaaS tools"),
    (workspace / "personal" / "fitness" / "log.txt", "2025-06-04: 30min run\n2025-06-05: rest day"),
    (workspace / "personal" / "reading" / "booklist.md", "- Atomic Habits\n- Building a Second Brain"),
    (workspace / ".config" / "editor" / "settings.json", '{"theme": "dark", "fontSize": 14}'),
    (workspace / "projects" / "saas-app" / "README_OLD.txt", "Old readme - ignore"),
]
for path, content in distractor_files:
    path.write_text(content)

# === PRIOR DAY'S LOG (messy, incomplete) ===
# This is the previous day's daily log that needs migration
# Date: 2025-06-09 (yesterday, so today is 2025-06-10)
prior_day_log = skill_root / "daily" / "2025-06-09.md"
prior_day_log.write_text("""\
# Daily Log - 2025-06-09

## 🎯 MUST HAPPEN
★ • Launch the beta invite page

## 🔥 HIGH ENERGY
• Write onboarding email sequence ⏳60+ min
× Refactor authentication module 🕐30 min
• Record intro video for product ⏳60+ min

## 💧 MEDIUM ENERGY
× Schedule call with accountant ⏱️15 min
• Reply to all Slack messages from investors 🕐30 min
• Review and respond to beta user feedback ⏱️15 min

## ❄️ LOW ENERGY
× Update expense spreadsheet ⚡5 min
• File quarterly tax documents 💀 ⏳60+ min
• Organize Notion workspace ⏱️15 min

## 🚫 NOT TODAY
• Plan team offsite for August

---
## Evening Reflection
(not completed - ran out of time)
""")

# === TODAY'S BRAIN DUMP (raw, messy, unstructured input) ===
# Date: 2025-06-10
brain_dump = workspace / "todays_brain_dump.txt"
brain_dump.write_text("""\
TODAY IS 2025-06-10

Things rattling around in my head this morning:

- I MUST send the investor update email today - this is the critical one, blocks everything else
- fix the payment webhook bug (this is a dread task, been avoiding it for a week)
- do my weekly revenue review - medium effort
- reply to that potential enterprise customer (Sarah from TechCorp) - just a quick email
- brainstorm Q3 feature roadmap - need high focus for this
- cancel the unused Zapier subscription - takes 5 minutes max
- read that article about ADHD and entrepreneurship someone sent me
- deep dive into competitor analysis for the new pricing page - big task
- send thank you note to advisor Marcus - quick
- update my LinkedIn bio - low effort, been putting it off
- attend async standup on Slack - medium task
- figure out why the onboarding funnel drop-off rate jumped last week - need full brain for this

My energy today: I feel pretty good actually, like a 7/10. Decent sleep.

What I want as a reward when I finish my ONE thing: go for a 20 minute walk outside

I also want to note: file quarterly tax documents is a DREAD task I've been avoiding - this will never happen until I get help. Drop it. And "plan team offsite for August" - still not relevant yet, keep it deferred.
""")

# === A distractor "todo" file that looks tempting but is wrong format ===
(workspace / "notes" / "ideas" / "quick-todos.txt").write_text("""\
Random todos:
- buy more coffee
- fix laptop charger
- water the plants
""")

# === Monthly overview file (distractor - already exists) ===
(skill_root / "monthly" / "2025-06.md").write_text("""\
# Monthly Overview - June 2025

## Focus Theme: Beta Launch

## Key Projects
- Beta invite system
- Investor relations
- Payment infrastructure

## Migration Pool
(tasks that keep not getting done)
""")

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Prior day log: {prior_day_log}")
print(f"Brain dump: {brain_dump}")