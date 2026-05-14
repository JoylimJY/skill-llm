import os
import json
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Distractor files to add realism ───────────────────────────────────────────
(workspace / "SOUL.md").write_text("# Soul\nThis agent values precision and reliability.\n")
(workspace / "USER.md").write_text("# User\nDr. Chen, AI Infrastructure Lead.\n")
(workspace / "AGENTS.md").write_text(
    "# Agents\n\n## Every Session\n1. Read SOUL.md\n2. Read USER.md\n3. Load memory\n"
)
(workspace / "MEMORY.md").write_text(
    "# Core Memory\n\n## Key Insights\n- Agent context overflow is a recurring issue.\n- Flat memory structure is unsustainable beyond 30 days.\n"
)
(workspace / "config.yaml").write_text("model: gpt-4\nmax_tokens: 8192\ntemperature: 0.7\n")
(workspace / "requirements.txt").write_text("python-dateutil\nrequests\n")
(workspace / "README_OLD.md").write_text("Old README. Deprecated.\n")

# ── Distractor directories ────────────────────────────────────────────────────
(workspace / "logs").mkdir(exist_ok=True)
(workspace / "logs" / "system.log").write_text("[2026-01-15 10:00] System started\n[2026-01-16 09:30] Context overflow warning\n")
(workspace / "logs" / "errors.log").write_text("[2026-01-20 14:22] MemoryError: token limit exceeded\n")

(workspace / "backups").mkdir(exist_ok=True)
(workspace / "backups" / "memory_backup_20260101.tar.gz.info").write_text("Backup created 2026-01-01\n")

(workspace / "tools").mkdir(exist_ok=True)
(workspace / "tools" / "summarizer.py").write_text("# Old summarizer - deprecated\nprint('deprecated')\n")
(workspace / "tools" / "indexer.py").write_text("# Old indexer - deprecated\nprint('deprecated')\n")

(workspace / "assets").mkdir(exist_ok=True)

# ── assets/rollup-state.json template (the canonical template to copy from) ──
rollup_state_template = {
    "lastDailyRollup": None,
    "lastWeeklyRollup": None,
    "lastMonthlyRollup": None,
    "currentWeek": "2026-W03",
    "currentMonth": "2026-01"
}
(workspace / "assets" / "rollup-state.json").write_text(
    json.dumps(rollup_state_template, indent=2)
)

# ── assets/heartbeat-state.json template ─────────────────────────────────────
heartbeat_state_template = {
    "lastMoltbookCheck": None
}
(workspace / "assets" / "heartbeat-state.json").write_text(
    json.dumps(heartbeat_state_template, indent=2)
)

# ── Flat daily memory files (old format to migrate) ──────────────────────────
# These exist in the OLD flat location: memory/YYYY-MM-DD.md
flat_memory = workspace / "memory"
flat_memory.mkdir(exist_ok=True)

flat_entries = [
    ("2026-01-13", "## Jan 13\n- Researched context overflow solutions.\n- Tested token budgets.\n- Found fractal memory concept.\n"),
    ("2026-01-14", "## Jan 14\n- Implemented basic daily log system.\n- Context still overflowing after 20 days.\n- Need hierarchical approach.\n"),
    ("2026-01-15", "## Jan 15\n- Reviewed Deva's Fractal Memory v1.0.0.\n- Decided to migrate to hierarchical system.\n- Outlined migration plan.\n"),
    ("2026-01-16", "## Jan 16\n- Set up initial directory structure.\n- Wrote migration scripts draft.\n- Discussed with Dr. Chen.\n"),
    ("2026-01-17", "## Jan 17\n- Tested rollup-daily.py locally.\n- Fixed bug in week number calculation.\n- Weekly file now generates correctly.\n"),
]

for date_str, content in flat_entries:
    (flat_memory / f"{date_str}.md").write_text(content)

# Also add a non-date file to make the migration trickier (distractor)
(flat_memory / "scratch.md").write_text("# Scratch\nTODO: clean this up.\n")
(flat_memory / "ideas.md").write_text("# Ideas\n- Sticky notes for recurring facts.\n- Compress monthly into MEMORY.md\n")

# ── scripts/ directory with the actual Python scripts ────────────────────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# ensure_daily_log.py
(scripts_dir / "ensure_daily_log.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Creates today's daily log if it doesn't exist.\"\"\"
import os
from datetime import date
from pathlib import Path

today = date.today()
year = today.strftime("%Y")
date_str = today.strftime("%Y-%m-%d")

daily_dir = Path(f"memory/diary/{year}/daily")
daily_dir.mkdir(parents=True, exist_ok=True)

log_file = daily_dir / f"{date_str}.md"
if not log_file.exists():
    log_file.write_text(f"## {date_str}\\n\\n_No entries yet._\\n")
    print(f"Created: {log_file}")
else:
    print(f"Already exists: {log_file}")
""")

# append_to_daily.py
(scripts_dir / "append_to_daily.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Append events to today's daily log.\"\"\"
import sys
from datetime import date
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: append_to_daily.py <event>")
    sys.exit(1)

event = sys.argv[1]
today = date.today()
year = today.strftime("%Y")
date_str = today.strftime("%Y-%m-%d")

daily_dir = Path(f"memory/diary/{year}/daily")
daily_dir.mkdir(parents=True, exist_ok=True)
log_file = daily_dir / f"{date_str}.md"

if not log_file.exists():
    log_file.write_text(f"## {date_str}\\n\\n")

with open(log_file, "a") as f:
    f.write(f"- {event}\\n")

print(f"Appended to {log_file}")
""")

# rollup-daily.py
(scripts_dir / "rollup-daily.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Compress today's diary into this week's summary.\"\"\"
import json
import os
from datetime import date, datetime
from pathlib import Path

today = date.today()
year = today.strftime("%Y")
date_str = today.strftime("%Y-%m-%d")
week_num = today.isocalendar()[1]
week_str = f"{year}-W{week_num:02d}"

daily_file = Path(f"memory/diary/{year}/daily/{date_str}.md")
weekly_dir = Path(f"memory/diary/{year}/weekly")
weekly_dir.mkdir(parents=True, exist_ok=True)
weekly_file = weekly_dir / f"{week_str}.md"

if not daily_file.exists():
    print(f"No daily file found: {daily_file}")
else:
    content = daily_file.read_text()
    with open(weekly_file, "a") as f:
        f.write(f"\\n### Rollup from {date_str}\\n")
        f.write(content)
    print(f"Rolled up {daily_file} -> {weekly_file}")

# Update state
state_file = Path("memory/rollup-state.json")
if state_file.exists():
    state = json.loads(state_file.read_text())
else:
    state = {}

state["lastDailyRollup"] = datetime.now().isoformat()
state["currentWeek"] = week_str
state_file.write_text(json.dumps(state, indent=2))
print(f"Updated rollup-state.json: lastDailyRollup={state['lastDailyRollup']}")
""")

# rollup-weekly.py
(scripts_dir / "rollup-weekly.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Compress this week's summary into this month's summary.\"\"\"
import json
import os
from datetime import date, datetime
from pathlib import Path

today = date.today()
year = today.strftime("%Y")
month_str = today.strftime("%Y-%m")
week_num = today.isocalendar()[1]
week_str = f"{year}-W{week_num:02d}"

weekly_file = Path(f"memory/diary/{year}/weekly/{week_str}.md")
monthly_dir = Path(f"memory/diary/{year}/monthly")
monthly_dir.mkdir(parents=True, exist_ok=True)
monthly_file = monthly_dir / f"{month_str}.md"

if not weekly_file.exists():
    print(f"No weekly file found: {weekly_file}")
else:
    content = weekly_file.read_text()
    with open(monthly_file, "a") as f:
        f.write(f"\\n### Weekly Rollup: {week_str}\\n")
        f.write(content)
    print(f"Rolled up {weekly_file} -> {monthly_file}")

# Update state
state_file = Path("memory/rollup-state.json")
if state_file.exists():
    state = json.loads(state_file.read_text())
else:
    state = {}

state["lastWeeklyRollup"] = datetime.now().isoformat()
state["currentMonth"] = month_str
state_file.write_text(json.dumps(state, indent=2))
print(f"Updated rollup-state.json: lastWeeklyRollup={state['lastWeeklyRollup']}")
""")

# rollup-monthly.py
(scripts_dir / "rollup-monthly.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Distill this month's summary into MEMORY.md.\"\"\"
import json
import os
from datetime import date, datetime
from pathlib import Path

today = date.today()
year = today.strftime("%Y")
month_str = today.strftime("%Y-%m")

monthly_file = Path(f"memory/diary/{year}/monthly/{month_str}.md")
memory_file = Path("MEMORY.md")

if not monthly_file.exists():
    print(f"No monthly file found: {monthly_file}")
else:
    content = monthly_file.read_text()
    with open(memory_file, "a") as f:
        f.write(f"\\n## Monthly Rollup: {month_str}\\n")
        f.write(content)
    print(f"Rolled up {monthly_file} -> {memory_file}")

# Update state
state_file = Path("memory/rollup-state.json")
if state_file.exists():
    state = json.loads(state_file.read_text())
else:
    state = {}

state["lastMonthlyRollup"] = datetime.now().isoformat()
state_file.write_text(json.dumps(state, indent=2))
print(f"Updated rollup-state.json: lastMonthlyRollup={state['lastMonthlyRollup']}")
""")

# verify_memory_integrity.py
(scripts_dir / "verify_memory_integrity.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Check memory system integrity and detect anomalies.\"\"\"
import json
from pathlib import Path
from datetime import date

issues = []
today = date.today()
year = today.strftime("%Y")

# Check directory structure
required_dirs = [
    f"memory/diary/{year}/daily",
    f"memory/diary/{year}/weekly",
    f"memory/diary/{year}/monthly",
    "memory/diary/sticky-notes/workflows",
    "memory/diary/sticky-notes/apis",
    "memory/diary/sticky-notes/commands",
    "memory/diary/sticky-notes/facts",
]

for d in required_dirs:
    if not Path(d).exists():
        issues.append(f"Missing directory: {d}")

# Check state files
for sf in ["memory/rollup-state.json", "memory/heartbeat-state.json"]:
    if not Path(sf).exists():
        issues.append(f"Missing state file: {sf}")
    else:
        try:
            json.loads(Path(sf).read_text())
        except json.JSONDecodeError:
            issues.append(f"Invalid JSON in {sf}")

if issues:
    print("INTEGRITY ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Memory integrity: OK")
""")

# update_now.py (referenced in cron docs)
(scripts_dir / "update_now.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Update timestamp tracking.\"\"\"
from datetime import datetime
print(f"Timestamp updated: {datetime.now().isoformat()}")
""")

# ── Make scripts executable (done in setup_script, but write the files) ──────
print("Workspace initialized.")
print("Flat daily files created in memory/")
print("Scripts created in scripts/")
print("Asset templates created in assets/")