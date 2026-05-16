import os
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ─────────────────────────────────────────────────────
dirs = [
    ".triage/journals",
    ".triage/reports",
    "references",
    "projects/contract_review/briefs",
    "projects/contract_review/exhibits",
    "projects/due_diligence/docs",
    "projects/litigation/motions",
    "projects/litigation/evidence",
    "ops/runbooks",
    "ops/configs",
    "archive/2024/q1",
    "archive/2024/q2",
    "logs/system",
    "logs/errors",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "projects/contract_review/briefs/nda_summary.txt": "NDA between Verilex Corp and Hensley Partners dated 2024-03-15. Clause 7 governs IP.",
    "projects/contract_review/exhibits/exhibit_a_redlined.txt": "REDLINE VERSION - Track changes from counterparty counsel re: indemnification scope.",
    "projects/contract_review/briefs/engagement_letter.txt": "Engagement letter scope: document review, privilege log, deposition prep.",
    "projects/due_diligence/docs/target_company_financials.txt": "FY2024 EBITDA: $4.2M. Pending audit qualification for Q3.",
    "projects/litigation/motions/motion_to_dismiss_draft.txt": "Plaintiff moves to dismiss Count III on grounds of res judicata.",
    "projects/litigation/evidence/deposition_log.txt": "Deposition of J. Mortimer scheduled 2025-08-10. Court reporter confirmed.",
    "ops/runbooks/incident_response.txt": "Severity 1: page on-call. Severity 2: Slack #ops-alerts. Severity 3: ticket.",
    "ops/configs/system_config_old.json": json.dumps({"environment": "production", "version": "1.0.9", "deprecated": True}, indent=2),
    "archive/2024/q1/closed_tasks_q1.txt": "Q1 closed tasks: 47 document review, 12 privilege log, 3 depositions.",
    "archive/2024/q2/closed_tasks_q2.txt": "Q2 closed tasks: 63 review, 8 motions, 5 client advisories.",
    "logs/system/system.log": "\n".join([f"2025-07-{str(i).zfill(2)}T09:00:00Z [INFO] scheduler heartbeat OK" for i in range(1, 15)]),
    "logs/errors/crash_2025_07_14.log": "2025-07-14T03:17:42Z [FATAL] scheduler process terminated unexpectedly. Signal 9. Queue state may be inconsistent.",
    "references/boundary_contracts.md": "# Boundary Contracts\n\n## Consumer pickup protocol\n\nConsumers poll `.triage/signals.jsonl`. On reading a `task_ready` signal, the consumer writes back a `task_acknowledged` signal with the same `task_id` to prevent double-pickup. Mentor reads `heartbeat_interval_seconds` from the signal and configures its internal heartbeat loop. Dispatch handles inbox/message routing only. Base agent handles direct skill execution.",
    "references/schemas.md": """# Schemas

## Task record
```json
{
  "task_id": "string",
  "state": "queued|active|completed|cancelled|blocked|waiting_external",
  "priority_score": 0,
  "estimated_completion_seconds": 0,
  "routing_hint": "self|mentor|dispatch",
  "description": "string",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "blocking_reason": null
}
```

## Signal formats

### task_ready
```json
{
  "signal": "task_ready",
  "task_id": "string",
  "routing_hint": "mentor",
  "priority_score": 75,
  "heartbeat_interval_seconds": 60,
  "heartbeat_rationale": "high priority — stall detection required within 60s",
  "emitted_at": "ISO8601"
}
```

### task_completed
```json
{
  "signal": "task_completed",
  "task_id": "string",
  "outcome": "completed|cancelled",
  "emitted_at": "ISO8601"
}
```

### task_acknowledged
```json
{
  "signal": "task_acknowledged",
  "task_id": "string",
  "acknowledged_at": "ISO8601"
}
```

## DecisionRecord
```json
{
  "record_type": "DecisionRecord",
  "decision": "preemption|scoring|tie_break",
  "task_id": "string",
  "displaced_task_id": "string",
  "reason": "string",
  "priority_score_incoming": 0,
  "priority_score_displaced": 0,
  "decided_at": "ISO8601"
}
```
""",
    "references/scoring_model.md": """# Scoring Model

## Priority score formula

```
priority_score = urgency + deadline_proximity + consequence_weight +
                 interruption_intent + quick_completion_bonus + queue_aging
Clamp: 0–100
```

### Signal definitions

| Signal | Max points | Description |
|---|---|---|
| urgency | 30 | Explicit urgency markers: "urgent", "ASAP", "blocking", "emergency" |
| deadline_proximity | 25 | Hours until deadline: <2h=25, <6h=20, <24h=15, <72h=10, none=0 |
| consequence_weight | 20 | Legal/financial/client-facing consequence: high=20, medium=10, low=5, none=0 |
| interruption_intent | 15 | Explicit "stop everything", "drop what you're doing", "preempt" markers: 15 |
| quick_completion_bonus | 5 | Estimated <5 min: +5 |
| queue_aging | 5 | Task waiting >24h: +5 |

### Task selection formula

```
task_score = priority_score / max(estimated_completion_seconds / 60, 1)
```

Use task_score to select the best task when multiple queued tasks are available. Higher is better.

### Preemption rule

If an incoming task's priority_score exceeds the active task's priority_score by more than 25 points:
1. Checkpoint the active task (state → queued, record checkpoint in journal)
2. Promote incoming task to active
3. Record a DecisionRecord with decision="preemption"
4. Emit task_ready for the new active task

Preemption threshold is strictly greater than 25 (not ≥ 25).

### Tie-breaking

When task_scores are equal: prefer lower task_id lexicographically.

### Routing hint assignment

| Priority score | Routing hint |
|---|---|
| 70–100 | mentor |
| 40–69 | self or mentor depending on complexity |
| 0–39 | self |
""",
}

for rel_path, content in distractors.items():
    target = workspace / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)

# ── .triage/config.json ─────────────────────────────────────────────────────
config = {
    "version": "1.2.0",
    "max_queue_size": 50,
    "max_history_size": 100,
    "stall_threshold_seconds": 120,
    "retry_limit": 3,
    "created_at": "2025-07-01T08:00:00Z"
}
(workspace / ".triage/config.json").write_text(json.dumps(config, indent=2))

# ── .triage/queue.jsonl — messy post-crash state ────────────────────────────
# Task A: was active before crash — marked active, Mentor routed, high-ish priority
# Task B: queued, medium priority
# Task C: queued, low priority
# NOTE: Task A has a CRASH INCONSISTENCY: it's active but has no task_ready signal
#       in signals.jsonl, and its heartbeat_interval_seconds was never injected.
#       The queue also has a stale duplicate record for task A (pre-crash partial write).

now = datetime.now(timezone.utc)

task_a_created = (now - timedelta(hours=3)).isoformat()
task_a_updated = (now - timedelta(minutes=47)).isoformat()
task_b_created = (now - timedelta(hours=1, minutes=30)).isoformat()
task_b_updated = (now - timedelta(hours=1, minutes=30)).isoformat()
task_c_created = (now - timedelta(hours=5)).isoformat()
task_c_updated = (now - timedelta(hours=5)).isoformat()

queue_records = [
    # Task C first entry
    {
        "task_id": "task-c-001",
        "state": "queued",
        "priority_score": 22,
        "estimated_completion_seconds": 900,
        "routing_hint": "self",
        "description": "Update internal matter numbering spreadsheet with new client codes from Q2 intake.",
        "created_at": task_c_created,
        "updated_at": task_c_created,
        "blocking_reason": None
    },
    # Task B
    {
        "task_id": "task-b-002",
        "state": "queued",
        "priority_score": 48,
        "estimated_completion_seconds": 3600,
        "routing_hint": "self",
        "description": "Prepare privilege log index for Hensley Partners matter — production deadline next week.",
        "created_at": task_b_created,
        "updated_at": task_b_updated,
        "blocking_reason": None
    },
    # Task A — initial queued record
    {
        "task_id": "task-a-003",
        "state": "queued",
        "priority_score": 62,
        "estimated_completion_seconds": 7200,
        "routing_hint": "mentor",
        "description": "Comprehensive document review for Verilex Corp acquisition: 400+ documents, privilege assessment, redaction recommendations.",
        "created_at": task_a_created,
        "updated_at": task_a_created,
        "blocking_reason": None
    },
    # Task A — state transition to active (pre-crash)
    {
        "task_id": "task-a-003",
        "state": "active",
        "priority_score": 62,
        "estimated_completion_seconds": 7200,
        "routing_hint": "mentor",
        "description": "Comprehensive document review for Verilex Corp acquisition: 400+ documents, privilege assessment, redaction recommendations.",
        "created_at": task_a_created,
        "updated_at": task_a_updated,
        "blocking_reason": None
    },
    # Stale duplicate/partial write from crash (same task, orphaned active record)
    {
        "task_id": "task-a-003",
        "state": "active",
        "priority_score": 62,
        "estimated_completion_seconds": 7200,
        "routing_hint": "mentor",
        "description": "Comprehensive document review for Verilex Corp acquisition: 400+ documents, privilege assessment, redaction recommendations.",
        "created_at": task_a_created,
        "updated_at": task_a_updated,
        "blocking_reason": None,
        "_crash_artifact": True
    },
]

queue_lines = "\n".join(json.dumps(r) for r in queue_records)
(workspace / ".triage/queue.jsonl").write_text(queue_lines + "\n")

# ── .triage/signals.jsonl — empty (crash wiped it) ───────────────────────────
(workspace / ".triage/signals.jsonl").write_text("")

# ── .triage/decisions.jsonl — empty ─────────────────────────────────────────
(workspace / ".triage/decisions.jsonl").write_text("")

# ── .triage/history.jsonl — some completed tasks ────────────────────────────
history_records = []
for i in range(1, 8):
    completed_at = (now - timedelta(days=i)).isoformat()
    history_records.append({
        "task_id": f"hist-task-{i:03d}",
        "state": "completed",
        "priority_score": random.randint(20, 80),
        "description": f"Historical task {i}: closed.",
        "completed_at": completed_at
    })
history_lines = "\n".join(json.dumps(r) for r in history_records)
(workspace / ".triage/history.jsonl").write_text(history_lines + "\n")

# ── NEW TASK INTAKE — the urgent contract breach request ─────────────────────
# This is the raw incoming request that the agent must process.
# It is NOT yet in the queue — the agent must create it, score it, and process it.
incoming_request = {
    "request_id": "incoming-2025-07-14-urgent",
    "received_at": now.isoformat(),
    "source": "partner_escalation",
    "raw_text": (
        "URGENT — Stop everything. Opposing counsel just filed an emergency motion in the "
        "Carrington v. Nexaline breach-of-contract case. We need a comprehensive analysis of "
        "all contract clauses, damages calculations, and a recommended response strategy. "
        "Court deadline is in under 2 hours. This is client-facing, high financial consequence. "
        "Drop whatever is active and handle this immediately. This will require deep multi-step "
        "analysis — route to Mentor."
    ),
    "matter": "Carrington v. Nexaline",
    "deadline_hours": 1.5,
    "flagged_priority": "emergency"
}
(workspace / ".triage/incoming_request.json").write_text(json.dumps(incoming_request, indent=2))

# ── SKILL.md placement ──────────────────────────────────────────────────────
skill_md = """---
name: ocas-triage
description: System scheduler and priority queue manager. Determines what gets attention next across all pending work. Use when prioritizing competing tasks, checking queue state, preempting active work, auditing execution order, or passing a complex long-running task to Mentor. Assigns heartbeat cadence based on task priority before handoff.
metadata: {"openclaw":{"emoji":"🔀","version":"1.2.0"}}
---

# Triage

Triage is the system scheduler. Its only job is to determine what gets attention next. It maintains a durable priority queue, scores work deterministically, emits pickup signals, injects heartbeat cadence into Mentor handoffs, and handles interrupts.

## When to use

- Prioritize competing tasks
- Check queue state: "what are you working on", "what's pending"
- Interrupt active work: "stop and do this first"
- Add work to the queue
- Any complex multi-step task that requires Mentor

## When not to use

- Project orchestration internals — Mentor owns that
- Message drafting or inbox triage — use Dispatch
- Skill execution requests — route directly to the target skill
- Pattern analysis — use Corvus

## Core promise

One active task at a time. Deterministic scoring. Durable queue. Priority-linked heartbeat on every Mentor handoff. Every task logged.

---

## Meta commands (bypass queue, execute immediately)

```
status / what are you working on
stop / cancel that
pause / resume
```

Meta commands never appear in `queue.jsonl`.

---

## Task model

A task is created for every actionable input. Not created for: thanks, casual conversation, clarification, meta queries.

**States:** `queued` → `active` → `completed` or `cancelled`
Lateral: `blocked` (retries exceeded), `waiting_external` (awaiting response)

Read `references/schemas.md` for full schema and signal formats.

---

## Priority scoring

```
priority_score = urgency + deadline_proximity + consequence_weight +
                 interruption_intent + quick_completion_bonus + queue_aging
Clamp: 0–100
```

Read `references/scoring_model.md` for signal definitions, points, and examples.

---

## Mentor handoff with heartbeat injection

When Triage scores a task and determines it requires Mentor (`routing_hint: mentor`), it **must** inject a `heartbeat_interval` into the `task_ready` signal before emission. This is not optional.

### Heartbeat assignment rules

| Priority score | Heartbeat interval | Rationale |
|---|---|---|
| 70–100 (high) | 60 seconds | High-stakes work must surface stalls within 1 minute |
| 40–69 (medium) | 10 minutes | Sustained work; surface stalls before significant time is lost |
| 0–39 (low) | 1–6 hours | Background work; check-in at natural rest points |

For low-priority tasks, use 1 hour as the default. Scale toward 6 hours only if the task is explicitly flagged as non-urgent background work with no deadline.

### Extended task_ready signal (Mentor handoff)

```json
{
  "signal": "task_ready",
  "task_id": "string",
  "routing_hint": "mentor",
  "priority_score": 75,
  "heartbeat_interval_seconds": 60,
  "heartbeat_rationale": "high priority — stall detection required within 60s",
  "emitted_at": "ISO8601"
}
```

Mentor reads `heartbeat_interval_seconds` from the signal and configures its internal heartbeat loop before beginning work. If this field is absent from a Mentor-routed signal, Mentor defaults to 600 seconds (10 min) and logs a missing-heartbeat warning.

---

## Task selection and preemption

**Selection formula:** `task_score = priority_score / max(estimated_completion_seconds / 60, 1)`

**Preemption:** if new task priority exceeds active task by > 25 points, checkpoint active task and run higher-priority task first.

Read `references/scoring_model.md` for full preemption and tie-breaking rules.

---

## Stall detection

Stall threshold: 120 seconds of no progress on a non-Mentor task.
Retry limit: 3, exponential backoff.
On limit exceeded: `state → blocked`, `blocking_reason` logged.

For Mentor tasks, stall detection is delegated to Mentor's heartbeat loop (interval set at handoff). Triage does not independently poll Mentor-owned tasks.

---

## Queue pickup

Triage writes to `.triage/signals.jsonl`. Consumers poll this file.

`task_ready` — emitted when a task becomes active
`task_completed` — emitted on completion or cancellation
`task_acknowledged` — written by consumer to prevent double-pickup

Read `references/boundary_contracts.md` for consumer pickup protocol.

---

## Storage layout

```
.triage/
  config.json
  queue.jsonl        append-only; state transitions are new records per task_id
  signals.jsonl      task_ready, task_completed, task_acknowledged
  decisions.jsonl    DecisionRecord entries for preemption and scoring
  history.jsonl      completed/cancelled tasks, last 100
  journals/
  reports/
```

---

## Validation rules

- No two tasks simultaneously in `active` state
- Every Mentor-routed `task_ready` signal must include `heartbeat_interval_seconds`
- Meta commands never appear in `queue.jsonl`
- Preemption always produces a journal entry and DecisionRecord
- `waiting_external` tasks have non-null `blocking_reason`
- `history.jsonl` does not exceed 100 records
- Queue does not exceed 50 tasks

---

## Reference files

| File | When to read |
|---|---|
| `references/schemas.md` | Task, signal, DecisionRecord schemas; heartbeat signal extension |
| `references/scoring_model.md` | Full scoring formula, preemption rules, estimation heuristics |
| `references/boundary_contracts.md` | Consumer pickup protocol; Mentor, Dispatch, base agent boundaries |
"""
(workspace / "SKILL.md").write_text(skill_md)

print("Workspace initialized successfully.")
print(f"Queue records: {len(queue_records)}")
print(f"History records: {len(history_records)}")
print(f"Incoming request: {incoming_request['request_id']}")