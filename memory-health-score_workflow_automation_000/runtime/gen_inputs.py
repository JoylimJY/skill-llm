#!/usr/bin/env python3
"""
Generate a realistic, messy agent memory workspace for the health-score task.
Target score: 60 / 100  →  grade: 警告
"""
import os
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

random.seed(42)

WORKSPACE = Path("/workspace")

# ── helpers ──────────────────────────────────────────────────────────────────

def write(path: Path, content: str, mtime_delta_days: float = 0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if mtime_delta_days != 0:
        now = datetime.now().timestamp()
        t = now - mtime_delta_days * 86400
        os.utime(path, (t, t))

now = datetime.now(timezone.utc)
today_str = now.strftime("%Y-%m-%d")

# ── MEMORY.md — 480 lines, only 2 P0 items, modified 3 days ago ─────────────
lines = []
lines.append("# Agent Memory\n")
lines.append("\n## Core Facts\n")
# Only 2 P0 items (need ≥3 for full score)
lines.append("- [P0] Primary database endpoint: postgres://prod-db:5432/agentdb\n")
lines.append("- [P0] Auth token refresh interval: 3600s\n")
lines.append("- [P1] Preferred response language: zh-CN\n")
lines.append("- [P1] Max context window: 128000 tokens\n")
lines.append("- [P2] Default timezone: Asia/Shanghai\n")
lines.append("\n## Project Context\n")
for i in range(1, 51):
    lines.append(f"- Project module {i}: handles subsystem-{i} with retry logic and backoff\n")
lines.append("\n## Historical Decisions\n")
for i in range(1, 81):
    lines.append(f"- Decision {i:03d}: chose approach-{chr(65 + i%26)} over approach-{chr(66 + i%26)} due to latency constraints\n")
lines.append("\n## Known Issues\n")
for i in range(1, 31):
    lines.append(f"- Issue {i}: intermittent timeout in service-{i} (tracked in issue-{i:03d})\n")
lines.append("\n## Resolved Items\n")
for i in range(1, 101):
    lines.append(f"- Resolved: bug-{i:04d} — fixed null pointer in handler-{i}\n")
lines.append("\n## Vendor Notes\n")
for i in range(1, 61):
    lines.append(f"- Vendor {i}: SLA is {85 + i%10}%, contact vendor-support-{i}@example.com\n")
lines.append("\n## Deployment Notes\n")
for i in range(1, 81):
    lines.append(f"- Deploy step {i}: run migration-{i:03d}.sql before restarting service\n")
lines.append("\n## Misc\n")
for i in range(1, 51):
    lines.append(f"- Note {i}: environment variable ENV_{i} controls feature flag {i}\n")

# count and pad to exactly 480 lines
while len(lines) < 480:
    lines.append(f"- Padding note {len(lines)}: placeholder for future memory entries\n")
lines = lines[:480]

memory_content = "".join(lines)
write(WORKSPACE / "MEMORY.md", memory_content, mtime_delta_days=3)

# ── memory/INDEX.md — exists, modified 4 days ago (outside 3-day window) ────
# References items in MEMORY.md but also includes a non-existent item
# Also references issue-099 which doesn't exist in .issues/
index_content = """\
# Memory Index

## Core References
- Primary database endpoint → MEMORY.md#core-facts
- Auth token refresh interval → MEMORY.md#core-facts
- Preferred response language → MEMORY.md#core-facts
- Max context window → MEMORY.md#core-facts
- Default timezone → MEMORY.md#core-facts

## Project Modules
- Module subsystem-1 → MEMORY.md#project-context
- Module subsystem-5 → MEMORY.md#project-context
- Module subsystem-10 → MEMORY.md#project-context

## Active Issues
- issue-001 → .issues/issue-001.md
- issue-002 → .issues/issue-002.md
- issue-099 → .issues/issue-099.md  [DOES NOT EXIST — intentional mismatch]

## Recently Resolved
- bug-0001 through bug-0010 → MEMORY.md#resolved-items

## GHOST ENTRY (not in MEMORY.md)
- Quantum encryption key rotation schedule → MEMORY.md#security (section does not exist)
- Legacy API migration deadline: 2025-12-31 → MEMORY.md#roadmap (section does not exist)
"""
write(WORKSPACE / "memory" / "INDEX.md", index_content, mtime_delta_days=4)

# ── memory/logs/ — 6 days of logs, NO today's log ───────────────────────────
# Average line count designed to be ~10 lines (below 20 threshold)
for d in range(1, 7):          # days 1..6 ago  — today (d=0) is intentionally absent
    date_str = (now - timedelta(days=d)).strftime("%Y-%m-%d")
    if d <= 2:
        # very short logs to drag average down
        log_content = "\n".join([
            f"# Log {date_str}",
            "## Tasks",
            f"- Processed batch {d}",
            f"- Wrote results to output-{d}.json",
            "## Errors",
            "- None",
        ]) + "\n"
    elif d <= 4:
        # slightly longer but still short
        log_content = "\n".join(
            [f"# Log {date_str}", "## Tasks"] +
            [f"- Task {i}: completed" for i in range(1, 9)] +
            ["## Errors", "- None", "## Notes", "- All nominal"]
        ) + "\n"
    else:
        # longer logs
        log_content = "\n".join(
            [f"# Log {date_str}", "## Tasks"] +
            [f"- Task {i}: completed with metrics latency={i*10}ms" for i in range(1, 16)] +
            ["## Errors"] +
            [f"- Error {i}: minor warning in subsystem-{i}" for i in range(1, 4)] +
            ["## Summary", "- Day completed successfully"]
        ) + "\n"
    write(WORKSPACE / "memory" / "logs" / f"{date_str}.md", log_content)

# ── .issues/ — directory exists, only 2 open issues, heartbeat correct ──────
(WORKSPACE / ".issues").mkdir(parents=True, exist_ok=True)

# 2 open issues (need ≥3)
for i in range(1, 3):
    issue_content = f"""\
# Issue {i:03d}
status: open
priority: P1
created: {(now - timedelta(days=10+i)).strftime("%Y-%m-%d")}

## Description
Service-{i} shows intermittent timeouts under high load.

## Steps to Reproduce
1. Send >1000 req/s to service-{i}
2. Observe 5xx responses after 30s

## Resolution
Pending investigation.
"""
    write(WORKSPACE / ".issues" / f"issue-{i:03d}.md", issue_content)

# 3 closed issues (do NOT count as open)
for i in range(3, 6):
    issue_content = f"""\
# Issue {i:03d}
status: closed
priority: P2
created: {(now - timedelta(days=20+i)).strftime("%Y-%m-%d")}
closed: {(now - timedelta(days=5)).strftime("%Y-%m-%d")}

## Description
Minor configuration drift in service-{i}.

## Resolution
Fixed by redeploying with correct env vars.
"""
    write(WORKSPACE / ".issues" / f"issue-{i:03d}.md", issue_content)

# NOTE: issue-099.md deliberately does NOT exist (INDEX.md references it)

# Heartbeat config — correctly formed
heartbeat_content = """\
{
  "enabled": true,
  "interval_minutes": 60,
  "alert_threshold_minutes": 120,
  "last_beat": "auto",
  "notify_on_failure": true
}
"""
write(WORKSPACE / ".issues" / "heartbeat.json", heartbeat_content)

# ── Distractor files — realistic noise ───────────────────────────────────────
write(WORKSPACE / "config" / "agent.yaml", """\
agent:
  name: main
  version: 2.1.0
  model: gpt-4o
  max_retries: 3
  timeout_seconds: 30
""")

write(WORKSPACE / "config" / "prompts.yaml", """\
system_prompt: |
  You are a helpful AI assistant managing complex workflows.
  Always respond in the user's language.
tools_config:
  web_search: enabled
  code_execution: sandboxed
""")

write(WORKSPACE / "scripts" / "bootstrap.sh", """\
#!/bin/bash
echo "Bootstrapping agent environment..."
mkdir -p memory/logs .issues
touch memory/INDEX.md
echo "Done."
""")

write(WORKSPACE / "scripts" / "compress_memory.py", """\
#!/usr/bin/env python3
\"\"\"Compress MEMORY.md by removing duplicate entries.\"\"\"
from pathlib import Path
import re

memory = Path('MEMORY.md').read_text()
lines = memory.splitlines()
seen = set()
deduped = []
for line in lines:
    key = re.sub(r'\\s+', ' ', line.strip().lower())
    if key not in seen:
        seen.add(key)
        deduped.append(line)
Path('MEMORY.md').write_text('\\n'.join(deduped))
print(f"Compressed: {len(lines)} → {len(deduped)} lines")
""")

write(WORKSPACE / "scripts" / "rebuild_index.py", """\
#!/usr/bin/env python3
\"\"\"Rebuild memory/INDEX.md from MEMORY.md content.\"\"\"
from pathlib import Path
import re

memory_lines = Path('MEMORY.md').read_text().splitlines()
p0_items = [l for l in memory_lines if '[P0]' in l]

index = ['# Memory Index (Auto-rebuilt)\\n']
index.append('## P0 Items\\n')
for item in p0_items:
    index.append(f'{item}\\n')

Path('memory/INDEX.md').write_text(''.join(index))
print('INDEX.md rebuilt.')
""")

write(WORKSPACE / "docs" / "architecture.md", """\
# System Architecture

## Components
- Agent Core: handles task routing and memory management
- Memory Subsystem: MEMORY.md + INDEX.md + logs
- Issue Tracker: .issues/ directory
- Cron System: openclaw cron scheduler

## Data Flow
1. Agent receives task
2. Loads context from MEMORY.md
3. Executes task
4. Writes log entry
5. Updates MEMORY.md if needed
""")

write(WORKSPACE / "docs" / "runbook.md", """\
# Operational Runbook

## Daily Operations
- Check memory health score at 09:00
- Review open issues in .issues/
- Archive logs older than 30 days

## Weekly Operations  
- Compress MEMORY.md if >400 lines
- Rebuild INDEX.md
- Close resolved issues

## Emergency Procedures
- If memory corrupted: restore from last backup
- If issues directory missing: run bootstrap.sh
""")

write(WORKSPACE / "output" / "last_run.json", """\
{
  "run_id": "run-2024-abc123",
  "status": "completed",
  "tasks_processed": 47,
  "duration_seconds": 342,
  "errors": 0
}
""")

write(WORKSPACE / "output" / "metrics.json", """\
{
  "total_runs": 1247,
  "success_rate": 0.987,
  "avg_duration_seconds": 287,
  "p99_duration_seconds": 891
}
""")

write(WORKSPACE / ".env.example", """\
AGENT_NAME=main
AGENT_MODEL=gpt-4o
DATABASE_URL=postgres://localhost:5432/agentdb
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
""")

write(WORKSPACE / "Makefile", """\
.PHONY: health compress rebuild

health:
\tpython scripts/health_check.py

compress:
\tpython scripts/compress_memory.py

rebuild:
\tpython scripts/rebuild_index.py
""")

write(WORKSPACE / "memory" / "snapshots" / "snapshot-2024-01-15.md", """\
# Memory Snapshot — 2024-01-15
Archived state of MEMORY.md as of 2024-01-15.
[content omitted for brevity — 312 lines archived]
""")

write(WORKSPACE / "memory" / "snapshots" / "snapshot-2024-02-01.md", """\
# Memory Snapshot — 2024-02-01
Archived state of MEMORY.md as of 2024-02-01.
[content omitted for brevity — 389 lines archived]
""")

# Summary of what the agent needs to score:
# Completeness:  10+5+10+0 = 25/30  (P0 usage fails: only 2 P0 items)
# Freshness:      0+10+0  = 10/25   (no today log; INDEX 4 days old)
# Structure:     10+0+5   = 15/20   (only 2 open issues)
# Density:       10+0     = 10/15   (log avg ~10 lines < 20)
# Consistency:    0+0     =  0/10   (INDEX↔MEMORY mismatch; issue-099 missing)
# TOTAL: 25+10+15+10+0 = 60  → grade: 警告

print("Workspace generated. Expected total score: 60 / 100 (grade: 警告)")

# Compute actual average log lines for verification
log_dir = WORKSPACE / "memory" / "logs"
log_files = list(log_dir.glob("*.md"))
total_lines = sum(len(f.read_text().splitlines()) for f in log_files)
avg = total_lines / len(log_files) if log_files else 0
print(f"Log files: {len(log_files)}, avg lines: {avg:.1f}")
print(f"MEMORY.md lines: {len((WORKSPACE / 'MEMORY.md').read_text().splitlines())}")