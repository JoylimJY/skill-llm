#!/usr/bin/env python3
"""
Generate the sandbox workspace for the daily-introspection skill evaluation.
"""
import os
import json
import stat
from pathlib import Path
from datetime import datetime, date

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "memory",
    ".learnings",
    "skills/daily-introspection/scripts",
    "skills/daily-introspection",
    ".openclaw/logs",
    ".openclaw/crons",
    "tools",
    "context",
    "archive/2024",
    "archive/2025",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── DISTRACTOR FILES ─────────────────────────────────────────────────────────
distractor_files = {
    "memory/2025-01-10.md": "# Conversation 2025-01-10\n\n- User asked about deployment pipeline\n- Discussed CI/CD options\n",
    "memory/2025-01-11.md": "# Conversation 2025-01-11\n\n- Reviewed code review practices\n- Noted need to improve response time\n",
    "memory/2025-01-12.md": "# Conversation 2025-01-12\n\n- Discussed memory management\n- Agent failed to recall previous context correctly\n- User had to repeat context 3 times\n",
    "archive/2024/summary.md": "# 2024 Annual Summary\n\nAgent deployed in Q3 2024. Initial error rate: 12%.\n",
    "archive/2025/q1-notes.md": "# Q1 2025 Notes\n\nExpected improvements in response quality.\n",
    "tools/search.md": "# Search Tool\n\nUsage: search(query) -> results\n",
    "tools/memory.md": "# Memory Tool\n\nPersists structured data across sessions.\n",
    "context/project-overview.md": "# Project Overview\n\nAutonomous agent for internal developer tooling.\n",
    ".openclaw/logs/session-2025-01-12.log": "session_id=main ts=2025-01-12T14:23:11 event=user_message\n",
    ".openclaw/logs/session-2025-01-13.log": "session_id=main ts=2025-01-13T09:05:42 event=user_message\nsession_id=main ts=2025-01-13T09:06:10 event=agent_reply\n",
}
for relpath, content in distractor_files.items():
    p = WORKSPACE / relpath
    p.write_text(content, encoding="utf-8")

# ── THE ACTUAL INPUT: Jan 13 conversation log ────────────────────────────────
(WORKSPACE / "memory/2025-01-13.md").write_text(
    """# Conversation Log — 2025-01-13

## Session: main

### 09:05 User
Can you summarize the deployment checklist for the staging environment?

### 09:06 Agent
The staging deployment checklist includes:
1. Run unit tests (pytest)
2. Build Docker image
3. Push to registry
4. Apply k8s manifests

Note: I incorrectly stated that linting must happen before tests — linting is optional at this stage.

### 10:14 User
What was the error we saw last Tuesday?

### 10:15 Agent
I don't have access to last Tuesday's logs in my current context.
(This is a memory retrieval failure — I should have checked memory/2025-01-07.md)

### 14:30 User
Run the performance benchmark script.

### 14:31 Agent
Executed: python3 benchmarks/perf.py
Result: p99 latency = 142ms (within SLA)

### 16:00 User
Remind me of the rule about promoting learnings to AGENTS.md.

### 16:01 Agent
I stated: "Promote any learning after 3 days without recurrence."
This is INCORRECT. The actual rule is: promote only after >1 week without recurrence.
""",
    encoding="utf-8",
)

# ── ERRORS.md with messy, real-world data ────────────────────────────────────
(WORKSPACE / ".learnings/ERRORS.md").write_text(
    """# Error Log

## E001 — Wrong linting order stated
- Date: 2025-01-08
- Description: Told user linting must precede tests. Incorrect.
- Corrective Rule: Linting is optional pre-test; do not assert mandatory order.
- Status: Recorded, corrective rule added 2025-01-08
- Last recurrence: 2025-01-13 (see today's session)

## E002 — Memory retrieval failure
- Date: 2025-01-06
- Description: Failed to check memory file for historical context.
- Corrective Rule: Always check memory/YYYY-MM-DD.md before stating "I don't have access".
- Status: Recorded, corrective rule added 2025-01-06
- Last recurrence: 2025-01-13 (today's session confirms recurrence)

## E003 — Wrong promotion threshold stated
- Date: 2025-01-13
- Description: Stated 3-day rule for promotions; actual rule is >1 week.
- Corrective Rule: Promotion requires >1 week without recurrence.
- Status: Newly recorded today
""",
    encoding="utf-8",
)

# ── FEATURES.md ──────────────────────────────────────────────────────────────
(WORKSPACE / ".learnings/FEATURES.md").write_text(
    """# Feature Learnings

## F001 — Benchmark automation
- Date: 2025-01-13
- Description: Performance benchmarks can be triggered inline during sessions.
- Value: Reduces context switches for the user.
""",
    encoding="utf-8",
)

# ── Proactive mechanism files ────────────────────────────────────────────────
(WORKSPACE / "SESSION-STATE.md").write_text(
    """# Session State
session_id: main
status: active
last_activity: 2025-01-13T16:01:00
pending_actions: []
""",
    encoding="utf-8",
)

(WORKSPACE / "HEARTBEAT.md").write_text(
    """# Heartbeat
last_ping: 2025-01-13T16:30:00
interval_seconds: 300
healthy: true
""",
    encoding="utf-8",
)

(WORKSPACE / "working-buffer.md").write_text(
    """# Working Buffer
## Active task
Awaiting daily introspection trigger.
""",
    encoding="utf-8",
)

# ── AGENTS.md / MEMORY.md / TOOLS.md (target promotion files) ────────────────
(WORKSPACE / "AGENTS.md").write_text(
    """# Agent Rules

## Core Behaviour
- Always confirm destructive operations before executing.
- Respond in the user's language.
- Log all tool calls with their arguments and results.

## Memory
- Summarize sessions longer than 50 turns.
""",
    encoding="utf-8",
)

(WORKSPACE / "MEMORY.md").write_text(
    """# Memory Rules

## Retrieval
- Always search memory before stating lack of context.
- Prefer the most recent entry when multiple entries match.
""",
    encoding="utf-8",
)

(WORKSPACE / "TOOLS.md").write_text(
    """# Tool Usage Rules

## General
- Validate all tool inputs before calling.
- Handle tool errors gracefully with user-facing messages.
""",
    encoding="utf-8",
)

# ── Mock scripts ─────────────────────────────────────────────────────────────
# scripts/daily-introspect.py
(WORKSPACE / "skills/daily-introspection/scripts/daily-introspect.py").write_text(
    r'''#!/usr/bin/env python3
"""
Daily introspection script — reads conversation log and learning files,
prints a summary for LLM analysis, and creates a skeleton output file
in workspace/.daily-introspection/ if not already present.
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import date

def main():
    parser = argparse.ArgumentParser(description="Daily self-introspection")
    parser.add_argument("--date", default=None, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()

    target_date = args.date if args.date else date.today().strftime("%Y-%m-%d")

    workspace = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))

    # Locate source files
    conv_log = workspace / "memory" / f"{target_date}.md"
    learnings_dir = workspace / ".learnings"
    session_state = workspace / "SESSION-STATE.md"
    heartbeat = workspace / "HEARTBEAT.md"
    working_buffer = workspace / "working-buffer.md"

    print(f"=== Daily Introspection Script ===")
    print(f"Target date: {target_date}")
    print()

    # Read conversation log
    if conv_log.exists():
        print(f"--- Conversation Log: {conv_log} ---")
        print(conv_log.read_text())
    else:
        print(f"[WARN] No conversation log found at {conv_log}")

    # Read learnings
    if learnings_dir.exists():
        for f in sorted(learnings_dir.glob("*.md")):
            print(f"--- Learning File: {f.name} ---")
            print(f.read_text())

    # Read proactive files
    for probe in [session_state, heartbeat, working_buffer]:
        if probe.exists():
            print(f"--- {probe.name} ---")
            print(probe.read_text())

    # Create output dir
    out_dir = workspace / ".daily-introspection"
    out_dir.mkdir(exist_ok=True)

    out_file = out_dir / f"introspection-{target_date}.md"
    if not out_file.exists():
        skeleton = f"""# Daily Introspection — {target_date}

## Sources Collected
- Conversation log: memory/{target_date}.md
- Learnings: .learnings/*.md
- Proactive files: SESSION-STATE.md, HEARTBEAT.md, working-buffer.md

## Analysis
<!-- Agent: fill in introspection analysis below -->

## Errors Identified Today
<!-- List errors found in today's conversation -->

## Classification
<!-- one-time mistake / repeat pattern / new rule -->

## Improvement Suggestions
<!-- Concrete actionable improvements -->
"""
        out_file.write_text(skeleton)
        print(f"\n[INFO] Created skeleton introspection file: {out_file}")
    else:
        print(f"\n[INFO] Introspection file already exists: {out_file}")

    print("\n=== Script complete. Agent should now perform LLM introspection. ===")

if __name__ == "__main__":
    main()
''',
    encoding="utf-8",
)

# scripts/weekly-promote.py
(WORKSPACE / "skills/daily-introspection/scripts/weekly-promote.py").write_text(
    r'''#!/usr/bin/env python3
"""
Weekly promotion script — reads all daily introspection records from the
current (or specified) week and prints aggregated patterns for LLM analysis.
"""
import argparse
import sys
import os
import re
from pathlib import Path
from datetime import date, timedelta

def iso_week_to_yyww(d: date) -> str:
    """Return YYWW string for the ISO week containing date d."""
    iso = d.isocalendar()  # (year, week, weekday)
    return f"{str(iso[0])[2:]}{iso[1]:02d}"

def week_dates(yyww: str):
    """Return all dates in the ISO week specified by YYWW string."""
    year = int("20" + yyww[:2])
    week = int(yyww[2:])
    # ISO week: Monday = day 1
    jan4 = date(year, 1, 4)  # Jan 4 is always in week 1
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=week - 1)
    return [monday + timedelta(days=i) for i in range(7)]

def main():
    parser = argparse.ArgumentParser(description="Weekly promotion aggregator")
    parser.add_argument("--week", default=None, help="Week in YYWW format (e.g. 2502)")
    args = parser.parse_args()

    workspace = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))
    intro_dir = workspace / ".daily-introspection"

    if args.week:
        yyww = args.week
    else:
        yyww = iso_week_to_yyww(date.today())

    dates = week_dates(yyww)
    print(f"=== Weekly Promotion Script ===")
    print(f"Week: {yyww}  ({dates[0]} to {dates[-1]})")
    print()

    found = []
    for d in dates:
        fname = intro_dir / f"introspection-{d.strftime('%Y-%m-%d')}.md"
        if fname.exists():
            found.append(fname)
            print(f"--- {fname.name} ---")
            print(fname.read_text())

    if not found:
        print("[WARN] No introspection files found for this week.")

    print(f"\n[INFO] Found {len(found)} introspection file(s) for week {yyww}.")
    print("=== Agent should now: ===")
    print("  1. Identify repeated patterns (no recurrence >1 week)")
    print("  2. Promote mature rules to AGENTS.md / MEMORY.md / TOOLS.md")
    print("  3. Verify each promotion by re-reading the target file")
    print(f"  4. Write evolution report to .daily-introspection/evolution-{yyww}.md")

if __name__ == "__main__":
    main()
''',
    encoding="utf-8",
)

# Make scripts executable
for script in [
    "skills/daily-introspection/scripts/daily-introspect.py",
    "skills/daily-introspection/scripts/weekly-promote.py",
]:
    p = WORKSPACE / script
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ── Also place scripts at the canonical path used in SKILL.md ────────────────
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(exist_ok=True)
import shutil
shutil.copy(
    WORKSPACE / "skills/daily-introspection/scripts/daily-introspect.py",
    WORKSPACE / "scripts/daily-introspect.py",
)
shutil.copy(
    WORKSPACE / "skills/daily-introspection/scripts/weekly-promote.py",
    WORKSPACE / "scripts/weekly-promote.py",
)
for s in ["scripts/daily-introspect.py", "scripts/weekly-promote.py"]:
    p = WORKSPACE / s
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ── Mock openclaw CLI ─────────────────────────────────────────────────────────
# Records all commands to .openclaw/crons/cron_registry.json for eval
(WORKSPACE / "scripts/openclaw").write_text(
    r'''#!/usr/bin/env python3
"""Mock OpenClaw CLI — records cron add commands for evaluation."""
import sys
import json
import os
from pathlib import Path

workspace = Path(os.environ.get("WORKSPACE_ROOT", "/workspace"))
registry_path = workspace / ".openclaw/crons/cron_registry.json"

# Load existing registry
if registry_path.exists():
    with open(registry_path) as f:
        registry = json.load(f)
else:
    registry = {"crons": []}

args = sys.argv[1:]

if len(args) >= 2 and args[0] == "cron" and args[1] == "add":
    # Parse flags
    entry = {}
    i = 2
    while i < len(args):
        if args[i].startswith("--"):
            flag = args[i][2:]
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                entry[flag] = args[i+1]
                i += 2
            else:
                entry[flag] = True
                i += 1
        else:
            i += 1
    registry["crons"].append(entry)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"[openclaw] Cron registered: {entry.get('name', 'unnamed')}")
elif len(args) >= 2 and args[0] == "cron" and args[1] == "list":
    print(json.dumps(registry, indent=2))
else:
    print(f"[openclaw] Command recorded: {' '.join(args)}")
''',
    encoding="utf-8",
)

p = WORKSPACE / "scripts/openclaw"
p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Workspace generated successfully.")