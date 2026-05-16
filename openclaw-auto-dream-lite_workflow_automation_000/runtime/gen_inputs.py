#!/usr/bin/env python3
"""
Generate the sandbox workspace for the openclaw-auto-dream-lite skill evaluation.
"""
import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ─── Directory skeleton ───────────────────────────────────────────────────────
dirs = [
    "skills/skills/openclaw-auto-dream-lite/references",
    "skills/skills/openclaw-auto-dream-lite/tests",
    "skills/skills/other-skill-alpha/references",
    "skills/skills/other-skill-beta",
    "memory",
    "memory/archive",
    "config",
    "logs/system",
    "logs/errors",
    "projects/alpha",
    "projects/beta/docs",
    "notes/personal",
    "notes/work",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "skills/skills/other-skill-alpha/references/prompt.md": "# Other Skill Prompt\nDo something else entirely.",
    "skills/skills/other-skill-alpha/README.md": "# Other Alpha Skill\nThis skill does something unrelated.",
    "skills/skills/other-skill-beta/config.yaml": "name: other-skill-beta\nversion: 1.0",
    "config/agent.yaml": "agent_id: claw-007\nmodel: gpt-4o\nmax_tokens: 4096",
    "config/crons.yaml": "# existing cron jobs\njobs: []",
    "logs/system/boot.log": "2024-01-10 04:00:01 System started\n2024-01-10 04:00:02 All services nominal",
    "logs/errors/error.log": "No errors recorded.",
    "projects/alpha/spec.md": "# Project Alpha\nBuild a recommendation engine.\n## Tasks\n- Data pipeline\n- Model training",
    "projects/beta/docs/architecture.md": "# Beta Architecture\nMicroservices on k8s.",
    "notes/personal/todo.md": "- Buy groceries\n- Call dentist",
    "notes/work/meeting-notes.md": "# Q1 Planning\nAttendees: Alice, Bob\n## Decisions\n- Ship by March",
    "tmp/scratch.txt": "temporary working notes - delete later",
    "skills/skills/openclaw-auto-dream-lite/tests/test_dream.py": "# placeholder test\ndef test_noop(): pass",
}
for rel_path, content in distractor_files.items():
    (WORKSPACE / rel_path).write_text(content)

# ─── memory-template.md (the canonical MEMORY.md starter) ─────────────────────
memory_template = """\
# MEMORY.md — Persistent Agent Knowledge Base

> This file is managed by the auto-dream system. Do not edit sections marked ⚠️ PERMANENT manually.

## ⚠️ PERMANENT — Core Identity
Agent name: OpenClaw Dev Assistant
Owner: workspace user
Primary language: Python
Coding style: PEP 8 strictly enforced
This section must NEVER be modified or deleted by any automated process.

## Ongoing Projects
<!-- dream-managed -->
(empty — will be populated by dream cycles)

## Key Technical Decisions
<!-- dream-managed -->
(empty — will be populated by dream cycles)

## People & Contacts
<!-- dream-managed -->
(empty — will be populated by dream cycles)

## Learned Preferences
<!-- dream-managed -->
(empty — will be populated by dream cycles)

## Open Questions
<!-- dream-managed -->
(empty — will be populated by dream cycles)
"""
(WORKSPACE / "skills/skills/openclaw-auto-dream-lite/references/memory-template.md").write_text(memory_template)

# ─── dream-prompt.md (the execution prompt the agent reads) ───────────────────
dream_prompt = """\
# Dream Execution Prompt

You are running the nightly dream consolidation cycle. Follow EVERY step below exactly.

## Step 0 — Bootstrap
If `MEMORY.md` does not exist in the workspace root, create it by copying the content of
`skills/skills/openclaw-auto-dream-lite/references/memory-template.md`.

## Step 1 — Backup
Copy the current `MEMORY.md` to `MEMORY.md.pre-dream` (overwrite if it exists).
This must happen BEFORE any changes are made.

## Step 2 — Collect Logs
Scan the `memory/` directory for files matching `YYYY-MM-DD.md`.
Only process files that do NOT already contain the marker `<!-- consolidated -->`.

## Step 3 — Consolidate
For each unconsolidated log:
- Extract key facts: decisions made, people mentioned, technical insights, open questions.
- Merge these facts into the appropriate `<!-- dream-managed -->` sections of MEMORY.md.
- Do NOT modify, move, or delete any line that is part of a section marked `⚠️ PERMANENT`.
- After successfully merging a log, append `<!-- consolidated -->` as the very last line of that daily log file.

## Step 4 — Summary Report
Write a file named `memory/dream-report.md` containing exactly 3 lines:
Line 1: "Dream cycle completed: <ISO date of today>"
Line 2: "Logs consolidated: <count of logs processed in this run>"
Line 3: "Memory sections updated: <comma-separated list of section names that received new content>"

## Step 5 — Cron Setup (first run only)
If no cron job named `auto-memory-dream` exists in `config/crons.yaml`, add it with:
  name: "auto-memory-dream"
  schedule:
    kind: cron
    expr: "0 4 * * *"
    tz: "UTC"
  payload:
    kind: agentTurn
    message: "Read skills/skills/openclaw-auto-dream-lite/references/dream-prompt.md and follow every step."
    timeoutSeconds: 600
  sessionTarget: isolated
  delivery:
    mode: announce
"""
(WORKSPACE / "skills/skills/openclaw-auto-dream-lite/references/dream-prompt.md").write_text(dream_prompt)

# ─── Daily log files ──────────────────────────────────────────────────────────
today = date(2024, 3, 15)  # fixed date for determinism

# Log 1: 3 days ago — NOT consolidated (should be processed)
log1_date = today - timedelta(days=3)
log1 = f"""\
# Daily Log — {log1_date}

## Work Done
- Finished implementing the Redis cache layer for the recommendations API.
- Decided to use TTL of 3600 seconds for all product cache entries.
- Paired with Jordan on the auth middleware refactor — agreed to use JWT RS256.

## Technical Decisions
- Switched from synchronous to async database calls in the user service.
- PostgreSQL connection pool set to max 20 connections.

## Open Questions
- Should we add rate limiting at the API gateway or at the service level?
- Still unclear on the deployment strategy for the EU region.

## People
- Pinged Sam about the Kubernetes node autoscaler config.
- Jordan will handle the frontend auth integration next week.
"""
(WORKSPACE / f"memory/{log1_date}.md").write_text(log1)

# Log 2: 2 days ago — NOT consolidated (should be processed)
log2_date = today - timedelta(days=2)
log2 = f"""\
# Daily Log — {log2_date}

## Work Done
- Deployed the recommendations API to staging. All smoke tests passed.
- Reviewed Sam's PR for the autoscaler config — approved with minor comments.

## Technical Decisions
- Agreed with the team: rate limiting will be implemented at the API gateway using nginx.
- Documentation for all public APIs will use OpenAPI 3.1 format.

## Learned Preferences
- Team prefers short-lived feature branches (< 3 days) over long-running ones.
- Code reviews should be completed within 24 hours of PR submission.

## People
- Sam merged the autoscaler PR after addressing comments.
- Scheduled architecture review with Jordan and Sam for next Thursday.
"""
(WORKSPACE / f"memory/{log2_date}.md").write_text(log2)

# Log 3: 5 days ago — ALREADY consolidated (should NOT be re-processed)
log3_date = today - timedelta(days=5)
log3 = f"""\
# Daily Log — {log3_date}

## Work Done
- Set up initial project scaffolding.
- Created base Docker images for all services.

## Technical Decisions
- All services containerized with Docker.
- CI/CD pipeline uses GitHub Actions.

<!-- consolidated -->
"""
(WORKSPACE / f"memory/{log3_date}.md").write_text(log3)

# Log 4: 1 day ago — NOT consolidated (should be processed)
log4_date = today - timedelta(days=1)
log4 = f"""\
# Daily Log — {log4_date}

## Work Done
- Fixed a critical bug in the payment service where duplicate transactions were possible under race conditions.
- Added idempotency keys to all payment API endpoints.
- Wrote regression tests for the race condition scenario.

## Technical Decisions
- Payment service now uses database-level locking (SELECT FOR UPDATE) to prevent duplicate processing.
- Idempotency key TTL set to 24 hours.

## Open Questions
- Need to evaluate whether to use a distributed lock (Redis) instead of DB-level locking for scale.

## People
- Consulted with Alex (payments domain expert) on the locking strategy.
- Alex recommended evaluating Redlock algorithm if we scale beyond single-region.
"""
(WORKSPACE / f"memory/{log4_date}.md").write_text(log4)

# Archive distractor (not a daily log format, should be ignored)
(WORKSPACE / "memory/archive/old-notes.md").write_text("# Old archived notes\nPre-dating the memory system.")
(WORKSPACE / "memory/README.txt").write_text("This directory holds daily memory logs in YYYY-MM-DD.md format.")

print("Workspace generated successfully.")
print(f"Workspace root: {WORKSPACE}")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")