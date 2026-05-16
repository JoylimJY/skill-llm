import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── helpers ──────────────────────────────────────────────────────────────────
def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# ── 1. Messy / legacy agent topology ─────────────────────────────────────────

# Bad AGENTS.md: has lab, multiple business agents, rescue shares memory with main
write(WORKSPACE / "AGENTS.md", """\
# Agents

## main
- model: gpt-4o
- memory: memory/
- skills: skills/

## lab
- model: gpt-4-turbo
- memory: memory/
- purpose: experiments and research drafts

## bizdev
- model: gpt-4o
- memory: memory/
- purpose: business development conversations

## ops
- model: gpt-4o
- memory: memory/
- purpose: operational tasks

## rescue
- model: gpt-3.5-turbo
- memory: memory/
- purpose: fallback when main is unavailable

## analytics-sidecar
- model: local/mistral
- memory: memory/
- purpose: data analysis using local Ollama inference
""")

# Bad AUTOMATION.md: vague, no file references, wrong cadence
write(WORKSPACE / "AUTOMATION.md", """\
# Automation

## Cron
- every hour: do things
- every day: summarize stuff

## Notes
The system will learn automatically over time as the model improves.
Side effects happen instantly without gates.
""")

# No HEARTBEAT.md at all (missing)

# ── 2. Memory layer – broken / incomplete ────────────────────────────────────

# Bloated MEMORY.md (dump of everything, not curated)
write(WORKSPACE / "MEMORY.md", """\
# Memory

## Random facts
- Client A likes email
- Meeting on Thursday
- Password hint: use the usual one
- TODO: fix the invoice template
- The weather was nice yesterday
- Bought coffee
- Need to call vendor
- Project Phoenix started in March
- Deadline is Q3
- Team offsite was cancelled
- Preferred font: Inter
- Laptop battery drains fast
- Use Notion for notes sometimes
- Slack channel #general has 200 members
- git commit message convention: feat/fix/chore
""")

# No memory/topics/ directory at all
# No daily memory logs

# ── 3. Project directory – partial, missing required files ───────────────────

# Project "phoenix" exists but is missing EXECUTION_PLAN.md and PROGRESS.md
write(WORKSPACE / "projects" / "phoenix" / "PRD.md", """\
# Project Phoenix PRD

## Goal
Redesign client onboarding flow to reduce time-to-value from 3 weeks to 5 days.

## Stakeholders
- CEO: strategic sponsor
- Ops Lead: delivery owner
- Client Success: primary users

## Success Criteria
- Onboarding checklist automated
- Welcome kit delivered in 24h
- NPS >50 at day-7
""")

# projects/INDEX.md missing entirely

# ── 4. Skills directory – missing reflect-mode ───────────────────────────────

write(WORKSPACE / "skills" / "scout-mode" / "skill.md", """\
# Scout Mode
Purpose: research and opportunity identification
Trigger: user says 'scout' or 'research'
""")

write(WORKSPACE / "skills" / "closer-mode" / "skill.md", """\
# Closer Mode
Purpose: proposal writing and deal closing
Trigger: user says 'close' or 'proposal'
""")

# reflect-mode missing entirely
# ops-mode missing

# ── 5. Distractor / legacy files ─────────────────────────────────────────────

write(WORKSPACE / "lab" / "experiment_001.md", """\
# Experiment 001
Testing a chain-of-thought approach for pricing.
Status: abandoned
""")

write(WORKSPACE / "lab" / "experiment_002.md", """\
# Experiment 002
Prototype for a multi-agent debate on strategy.
Status: never finished
""")

write(WORKSPACE / "lab" / "notes.txt", "random scratch notes\ndo not use\n")

write(WORKSPACE / "archive" / "old_agents.md", """\
# Old Agents (deprecated 2024-01)
- research-bot
- summarizer-v1
- email-drafter
All removed.
""")

write(WORKSPACE / "archive" / "legacy_cron.sh", """\
#!/bin/bash
# Legacy cron – DO NOT USE
echo "running old cron"
python old_summarizer.py
""")

write(WORKSPACE / "archive" / "migration_notes.md", """\
Notes from migration in Jan 2024.
Moved from v1 to v2 agent framework.
Some memory files were lost.
""")

write(WORKSPACE / "tmp" / "scratch.md", "temporary ideas\n- idea 1\n- idea 2\n")
write(WORKSPACE / "tmp" / "debug.log", "2024-01-15 ERROR: agent timeout\n2024-01-15 INFO: retry ok\n")

write(WORKSPACE / "config" / "gateway.yaml", """\
mode: router
port: 3000
agents:
  - main
  - lab
  - bizdev
  - ops
  - rescue
  - analytics-sidecar
""")

write(WORKSPACE / "config" / "ollama.yaml", """\
# Ollama config
host: localhost:11434
models:
  - mistral
  - llama3
purpose: general inference for analytics-sidecar and any agent needing local model
""")

# ── 6. A partially seeded memory/topics with wrong content ───────────────────
write(WORKSPACE / "memory" / "topics" / "random-dump.md", """\
# Random Dump
This file contains everything that seemed important at some point.
- client names
- random passwords
- old project ideas
- todo items
- grocery list
""")

# One old daily log with wrong format name
write(WORKSPACE / "memory" / "daily-notes.md", """\
# Daily Notes (not date-stamped, just accumulated)
2024-03-01: talked to client A
2024-03-02: wrote proposal
2024-03-05: reviewed contract
""")

print("Workspace seeded successfully.")
print("\nCurrent structure:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")