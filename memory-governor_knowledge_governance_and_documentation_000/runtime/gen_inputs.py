import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create the skill reference tree ─────────────────────────────────────────
skill_dir = workspace / "skills" / "memory-governor"
skill_dir.mkdir(parents=True, exist_ok=True)
refs_dir = skill_dir / "references"
refs_dir.mkdir(exist_ok=True)

# SKILL.md
(skill_dir / "SKILL.md").write_text("""\
---
name: memory-governor
description: Memory governance core for AI agents. Defines what is worth remembering, where it should go, when it should be promoted, and what should be excluded, while providing a shared memory contract for other skills.
---

# Memory Governor

Reusable memory-governance core for different host environments.

It is a governance kernel, not an execution-first productivity skill.

## What Counts as Memory

Only information that improves future judgment, recovery, execution quality, or coordination consistency counts as memory.

Typical examples:
- stable long-term preferences
- stable long-term facts
- key same-day events
- explicit corrections
- unproven but promising candidate lessons
- reusable lessons
- current progress state
- short-term recovery hints

## Core Rule

Standardize the core, not everything else.

## Target Classes

- `long_term_memory`
- `daily_memory`
- `learning_candidates`
- `reusable_lessons`
- `proactive_state`
- `working_buffer`
- `project_facts`
- `system_rules`
- `tool_rules`

Notes:
- `learning_candidates` is a low-commitment staging layer for corrections and emerging lessons
- it exists to prevent single observations from hardening too early
- `proactive_state` and `working_buffer` are stateful targets
- they should not become infinite append-only logs
- they need freshness, replace or merge, and retention rules by default

## Routing Order

When evaluating a candidate memory, reason in this order:

1. Is it worth remembering at all?
2. What memory type is it?
3. Which target class does that type belong to?
4. Which adapter in the current host should store that target class?
5. Is it still short-term, or is it ready for promotion?
6. Does it match any exclusion rule?

## Promotion Rules

All promotion should extract and refine before it hardens.

Never:
- write raw logs directly into long-term memory
- treat a working buffer as long-term memory
- use system-governance files as temporary capture inboxes

## Never Do

- do not write secrets, raw long logs, or short-lived noise into memory
""")

# references/memory-routing.md
(refs_dir / "memory-routing.md").write_text("""\
# Memory Routing Table

Use the routing order from SKILL.md when evaluating each candidate.

| Memory Type                     | Target Class         |
|---------------------------------|----------------------|
| stable long-term preference     | long_term_memory     |
| stable long-term fact           | long_term_memory     |
| key same-day event              | daily_memory         |
| explicit correction             | learning_candidates  |
| unproven candidate lesson       | learning_candidates  |
| reusable proven lesson          | reusable_lessons     |
| current progress / task state   | proactive_state      |
| short-term recovery hint        | working_buffer       |
| project-specific constant fact  | project_facts        |
| system-level behavioral rule    | system_rules         |
| tool-specific behavioral rule   | tool_rules           |

## Ambiguity Notes

- If an item is a correction observed only once, route to `learning_candidates`, not `reusable_lessons`.
- If an item is a preference but changes daily, route to `daily_memory`, not `long_term_memory`.
- If an item is a lesson that has been validated across multiple sessions, route to `reusable_lessons`.
- Raw logs, ephemeral noise, or secrets must be excluded entirely.
""")

# references/promotion-rules.md
(refs_dir / "promotion-rules.md").write_text("""\
# Promotion Rules

## General Principle

All promotion should extract and refine before it hardens.

## Candidate-to-Lesson Promotion

A `learning_candidates` entry may be promoted to `reusable_lessons` when:
- it has been confirmed correct in more than one independent session
- it generalizes beyond the original context
- it has been explicitly verified by the user or host

A `learning_candidates` entry must NOT be promoted if:
- it is based on a single observation
- it has not been verified

## Working Buffer Promotion

A `working_buffer` entry may be promoted to `proactive_state` when:
- the short-term hint has stabilized into an ongoing state item
- the session has ended and the hint remains relevant

A `working_buffer` entry must NOT be promoted to `long_term_memory` directly.

## Daily Memory Promotion

A `daily_memory` entry may be promoted to `long_term_memory` when:
- the same-day event reveals a stable preference or fact
- the event is not ephemeral noise

A `daily_memory` entry must NOT be promoted if it is just an ephemeral log line.

## Never

- Never write raw logs directly into long-term memory.
- Never treat working_buffer as long-term memory.
- Never use system_rules or tool_rules files as temporary capture inboxes.
""")

# references/exclusions.md
(refs_dir / "exclusions.md").write_text("""\
# Exclusion Rules

The following must never enter any memory layer:

1. **Secrets**: passwords, tokens, API keys, private credentials of any kind.
2. **Raw long logs**: unprocessed console output, stack traces, raw event streams exceeding a single meaningful summary.
3. **Short-lived noise**: transient UI state, momentary errors that resolved themselves, one-off debugging steps with no lasting lesson.
4. **Ephemeral task artifacts**: intermediate build files, temp file paths, session-local variables with no future value.
5. **Redundant duplicates**: if an equivalent item already exists in memory, do not add a near-copy.

If an item matches any exclusion rule, it must be marked `excluded` and must not be routed to any target class.
""")

# references/adapters.md
(refs_dir / "adapters.md").write_text("""\
# Default Adapters

These are the default file-path mappings for each target class.

| Target Class        | Default Adapter Path               |
|---------------------|------------------------------------|
| long_term_memory    | MEMORY.md                          |
| daily_memory        | memory/YYYY-MM-DD.md               |
| learning_candidates | memory/candidates.md               |
| reusable_lessons    | memory/lessons.md                  |
| proactive_state     | memory/proactive_state.md          |
| working_buffer      | memory/working_buffer.md           |
| project_facts       | memory/project_facts.md            |
| system_rules        | memory/system_rules.md             |
| tool_rules          | memory/tool_rules.md               |

Notes:
- `daily_memory` paths use the actual date (e.g., `memory/2024-06-15.md`).
- If the `self-improving` skill is installed, `reusable_lessons` may route there instead.
- For this host profile, assume `self-improving` is NOT installed.
- Adapter paths are relative to the workspace root.
""")

# references/routing-precedence.md
(refs_dir / "routing-precedence.md").write_text("""\
# Routing Precedence

When a candidate could match multiple target classes:

1. Exclusion always wins — if excluded, stop routing.
2. Correction-based items default to `learning_candidates` unless multi-session confirmed.
3. Prefer the more specific class: `tool_rules` over `system_rules` if tool-specific.
4. Prefer `daily_memory` over `long_term_memory` for same-day observations unless clearly stable.
5. `working_buffer` beats `proactive_state` if the item is short-term only.
""")

# references/stateful-targets.md
(refs_dir / "stateful-targets.md").write_text("""\
# Stateful Target Semantics

`proactive_state` and `working_buffer` are stateful, not append-only.

Update semantics:
- On write: replace or merge with existing content, do not blindly append.
- On session end: prune stale items that no longer reflect current state.
- Retention: items in `working_buffer` expire after one session unless promoted.
- Items in `proactive_state` are replaced when new state supersedes them.

These targets must never grow into infinite logs.
""")

# references/retention-rules.md
(refs_dir / "retention-rules.md").write_text("""\
# Retention Rules

| Target Class        | Retention Policy                                  |
|---------------------|---------------------------------------------------|
| long_term_memory    | Permanent until explicitly retracted              |
| daily_memory        | Kept for 30 days, then archived or deleted        |
| learning_candidates | Kept until promoted or discarded (max 14 days)    |
| reusable_lessons    | Permanent until superseded                        |
| proactive_state     | Replace on update; prune stale items each session |
| working_buffer      | Expires after one session                         |
| project_facts       | Permanent for project lifetime                    |
| system_rules        | Permanent until explicitly retracted              |
| tool_rules          | Permanent until explicitly retracted              |
""")

# references/correction-pipeline.md
(refs_dir / "correction-pipeline.md").write_text("""\
# Correction Pipeline

When the host or user issues a correction:

1. Capture the correction as a `learning_candidates` entry immediately.
2. Do NOT promote to `reusable_lessons` on first observation.
3. On second independent confirmation, promote to `reusable_lessons`.
4. On promotion, extract and refine the raw correction into a clean lesson statement.
5. Never write the raw correction text directly into `long_term_memory`.
""")

# references/candidate-review.md
(refs_dir / "candidate-review.md").write_text("""\
# Candidate Review Workflow

For each item in `learning_candidates`:

- keep: item is still unconfirmed but plausible — leave in candidates
- promote: item has been confirmed across sessions — move to reusable_lessons
- discard: item was wrong, noisy, or no longer relevant — remove

Review should happen at session boundaries, not mid-session.
""")

# references/schema-conventions.md
(refs_dir / "schema-conventions.md").write_text("""\
# Schema Conventions

Each memory entry in a governance output file should follow this structure:

```
## [Entry Title]
- type: <memory type>
- target_class: <target class>
- adapter_path: <file path relative to workspace>
- promotion_status: <accepted | excluded | staged>
- note: <optional rationale>
```

For excluded items:
```
## [Entry Title]
- type: <memory type>
- target_class: excluded
- adapter_path: none
- promotion_status: excluded
- note: <reason for exclusion>
```
""")

# references/skill-integration.md
(refs_dir / "skill-integration.md").write_text("""\
# Skill Integration

When another skill integrates with memory-governor:
- the skill may declare which information types it emits
- the skill may declare where those types usually land
- the skill should not invent a new global memory-layer definition
- the skill should not bypass exclusion rules
- the skill should not confuse downstream storage rules with upstream memory rules
""")

# references/host-profiles.md
(refs_dir / "host-profiles.md").write_text("""\
# Host Profiles

This kernel supports multiple host profiles. The current host profile for this workspace is `default`.

For the `default` profile:
- Use all default adapter paths from references/adapters.md
- Assume `self-improving` skill is NOT installed
- Use `memory/lessons.md` for `reusable_lessons`
- Date for daily_memory: use 2024-06-15 as today's date
""")

# references/integration-checklist.md
(refs_dir / "integration-checklist.md").write_text("""\
# Integration Checklist

Before writing any memory:
- [ ] Routing order has been applied (all 6 steps)
- [ ] Exclusion rules have been checked
- [ ] Promotion rules have been applied where relevant
- [ ] Adapter paths are resolved
- [ ] Stateful targets use replace/merge semantics
- [ ] No secrets or raw logs are written
""")

# references/installation-integration.md
(refs_dir / "installation-integration.md").write_text("""\
# Installation and Host Integration

To integrate memory-governor into a host:
1. Copy the skill directory into the host's skills folder.
2. Reference SKILL.md as the governance kernel entry point.
3. Configure adapter paths in references/adapters.md to match host conventions.
4. Ensure all memory-writing skills import exclusion and routing rules.
""")

# references/read-order.md
(refs_dir / "read-order.md").write_text("""\
# Recovery-Time Read Order

At session recovery time, read memory in this order:
1. system_rules
2. tool_rules
3. long_term_memory
4. reusable_lessons
5. proactive_state
6. project_facts
7. daily_memory
8. working_buffer
9. learning_candidates
""")

# ── Create distractor files and directories ──────────────────────────────────

# Agent session logs (distractors)
logs_dir = workspace / "agent_sessions" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
(logs_dir / "session_2024-06-10.log").write_text("""\
[2024-06-10 09:00:01] Agent started.
[2024-06-10 09:00:03] Tool call: web_search("current weather")
[2024-06-10 09:00:04] Result: sunny, 72F
[2024-06-10 09:00:10] Tool call: write_file("report.txt")
[2024-06-10 09:00:12] Session ended.
""")
(logs_dir / "session_2024-06-11.log").write_text("""\
[2024-06-11 10:12:00] Agent started.
[2024-06-11 10:12:05] Task: summarize Q2 financials
[2024-06-11 10:15:00] Task complete.
[2024-06-11 10:15:01] Session ended.
""")
(logs_dir / "session_2024-06-14.log").write_text("""\
[2024-06-14 08:00:00] Agent started.
[2024-06-14 08:00:10] Correction received: user said always use metric units
[2024-06-14 08:00:15] Session ended.
""")

# Old memory drafts (distractors)
drafts_dir = workspace / "memory_drafts"
drafts_dir.mkdir(exist_ok=True)
(drafts_dir / "old_notes.txt").write_text("""\
Random scratch notes:
- buy milk
- check server at 3pm
- password for staging: hunter2
- the API key is sk-1234abcd
""")
(drafts_dir / "unprocessed_dump.txt").write_text("""\
Huge raw log dump from yesterday:
ERROR: NullPointerException at line 42
WARN: Disk space low
INFO: Request received
INFO: Request processed
INFO: Response sent
... (10000 more lines)
""")

# Project config files (distractors)
config_dir = workspace / "project" / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "settings.json").write_text(json.dumps({
    "project": "AgentCore",
    "version": "2.1.0",
    "database": "postgres://localhost/agentdb",
    "feature_flags": {"memory_v2": True, "experimental_routing": False}
}, indent=2))
(config_dir / "agents.yaml").write_text("""\
agents:
  - name: planner
    skills: [memory-governor, task-planner]
  - name: executor
    skills: [memory-governor, code-executor]
""")

# Old MEMORY.md with some pre-existing content (distractor — agent should not blindly overwrite)
(workspace / "MEMORY.md").write_text("""\
# Long-Term Memory

## Preferred output format
- type: stable long-term preference
- target_class: long_term_memory
- adapter_path: MEMORY.md
- promotion_status: accepted
- note: User consistently prefers JSON output over CSV for structured data exports.
""")

# Pre-existing memory dir with some files
memory_dir = workspace / "memory"
memory_dir.mkdir(exist_ok=True)
(memory_dir / "2024-06-14.md").write_text("""\
# Daily Memory — 2024-06-14

## Agent ran Q2 summary task
- type: key same-day event
- target_class: daily_memory
- adapter_path: memory/2024-06-14.md
- promotion_status: accepted
- note: Completed Q2 financial summary without errors.
""")

# ── THE MAIN TASK INPUT: raw candidate backlog ────────────────────────────────
# This is the messy, realistic input the agent must process.
# Each item is described informally — the agent must classify, route, apply
# promotion rules, check exclusions, and output the governance file.

candidates_backlog = workspace / "memory_backlog.md"
candidates_backlog.write_text("""\
# Memory Candidate Backlog — Unprocessed

The following items were collected from recent agent sessions and need to be
processed through the memory governance system. Each item is described as
captured — raw, unfiltered. Do what needs to be done.

---

## Item 1: Metric units preference
Collected: 2024-06-14 session
"User corrected the agent during the 2024-06-14 session: always use metric units,
not imperial. This was the first time this correction appeared."

---

## Item 2: Python f-strings are faster than .format()
Collected: 2024-06-10 and 2024-06-13 sessions (confirmed in both)
"In two independent sessions the agent verified and the user confirmed: Python
f-strings execute faster than .format() for simple string interpolation. This
applies broadly and has been validated multiple times."

---

## Item 3: API key for staging environment
Collected: found in old_notes.txt
"staging API key: sk-1234abcd"

---

## Item 4: Today the agent completed the Q2 financial summary task
Collected: 2024-06-15
"Agent successfully completed the Q2 financial summary task today without errors."

---

## Item 5: Current task in progress — waiting for user approval on budget report
Collected: 2024-06-15 (ongoing)
"Agent is currently mid-task: draft budget report is complete, waiting for user
approval before sending. This is live session state."

---

## Item 6: The project database is PostgreSQL hosted at localhost
Collected: project config
"The AgentCore project uses PostgreSQL at localhost as its primary database.
This is a stable fact about the project."

---

## Item 7: Always call tool X before tool Y in the data pipeline
Collected: 2024-06-11 session
"First observation: the agent noticed that calling tool X before tool Y in the
pipeline avoids a race condition. Not yet confirmed in other sessions."

---

## Item 8: Raw full console output from 2024-06-14 session
Collected: logs/session_2024-06-14.log
"[2024-06-14 08:00:00] Agent started.\\n[2024-06-14 08:00:10] Correction received: user said always use metric units\\n[2024-06-14 08:00:15] Session ended."

---

## Item 9: System rule — never modify files in /etc without explicit user approval
Collected: established policy
"Global system behavioral rule: the agent must never modify files in /etc without
the user giving explicit written approval first. This applies across all sessions
and all tools."

---

## Item 10: Short recovery hint — retry failed HTTP calls up to 3 times before escalating
Collected: 2024-06-15 session start
"At the start of this session, note: retry failed HTTP calls up to 3 times before
escalating. This hint is for the current session only."
""")

print("Workspace generated successfully.")
print(f"Key file: {candidates_backlog}")