#!/usr/bin/env python3
"""
Generate the sandbox workspace for the memory-shrink task.
"""
import os
import json
import random

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

def makedirs(*parts):
    path = os.path.join(WORKSPACE, *parts)
    os.makedirs(path, exist_ok=True)
    return path

def writefile(path, content):
    with open(path, "w") as f:
        f.write(content)

# ── directory structure ────────────────────────────────────────────────────────
makedirs("scripts")
makedirs("memory")
makedirs("memory", "archive")
makedirs("logs")
makedirs("config")
makedirs("team")
makedirs("tasks", "sprint_12")
makedirs("tasks", "sprint_13")
makedirs("tasks", "backlog")
makedirs("docs", "meetings")
makedirs("docs", "decisions")

# ── distractor files ──────────────────────────────────────────────────────────
writefile(os.path.join(WORKSPACE, "config", "agent.conf"),
"""[agent]
name=project-assistant
version=2.1
log_level=INFO
""")

writefile(os.path.join(WORKSPACE, "config", "thresholds.conf"),
"""# DO NOT EDIT - managed by platform
max_context_kb=8192
warning_level=0.70
""")

writefile(os.path.join(WORKSPACE, "logs", "agent_2024-01-10.log"),
"2024-01-10 09:00:01 INFO  Agent started\n"
"2024-01-10 09:00:05 INFO  Loaded 42 memory entries\n"
"2024-01-10 11:30:22 WARN  Context at 68%\n"
)

writefile(os.path.join(WORKSPACE, "logs", "agent_2024-01-11.log"),
"2024-01-11 08:55:10 INFO  Agent started\n"
"2024-01-11 14:10:33 WARN  Context at 79%\n"
"2024-01-11 14:10:34 INFO  Shrink triggered\n"
)

writefile(os.path.join(WORKSPACE, "docs", "meetings", "2024-01-08-standup.md"),
"# Standup 2024-01-08\nAttendees: Alice, Bob, Carol\nDiscussed sprint 12 velocity.\n"
)

writefile(os.path.join(WORKSPACE, "docs", "meetings", "2024-01-09-retro.md"),
"# Sprint 12 Retro\nWhat went well: CI pipeline\nWhat to improve: code review latency\n"
)

writefile(os.path.join(WORKSPACE, "docs", "decisions", "adr-001-db-choice.md"),
"# ADR-001: Database Selection\nStatus: Accepted\nDecision: Use PostgreSQL\n"
)

writefile(os.path.join(WORKSPACE, "tasks", "sprint_12", "completed.json"),
json.dumps([
    {"id": "T-101", "title": "Setup CI pipeline", "status": "done", "detail": "Configured GitHub Actions with 47 steps, caching, matrix builds for Python 3.9/3.10/3.11, coverage reporting integrated with Codecov, slack notifications on failure, deployment gating on main branch only"},
    {"id": "T-102", "title": "Database migration v2", "status": "done", "detail": "Wrote 12 migration scripts, added rollback procedures, tested on staging with 2M rows, performance benchmarked at 340ms p95, coordinated 3-hour maintenance window with ops team"},
    {"id": "T-103", "title": "API rate limiting", "status": "done", "detail": "Implemented token bucket algorithm, Redis-backed, 1000 req/min per user, sliding window, bypass list for internal services, monitoring dashboard created"},
], indent=2))

writefile(os.path.join(WORKSPACE, "tasks", "sprint_13", "active.json"),
json.dumps([
    {"id": "T-201", "title": "Implement OAuth2 login", "status": "in_progress", "progress": "60%", "assignee": "Alice", "notes": "PKCE flow done, token refresh pending, blocked on security review"},
    {"id": "T-202", "title": "Performance profiling", "status": "in_progress", "progress": "30%", "assignee": "Bob", "notes": "Profiled auth endpoints, found N+1 query in user lookup, fix in review"},
], indent=2))

writefile(os.path.join(WORKSPACE, "tasks", "backlog", "cancelled.json"),
json.dumps([
    {"id": "T-055", "title": "Migrate to GraphQL", "status": "cancelled", "reason": "Scope too large, deferred indefinitely", "created": "2023-09-01"},
    {"id": "T-067", "title": "Redis cluster upgrade", "status": "cancelled", "reason": "Vendor contract not renewed", "created": "2023-11-15"},
    {"id": "T-078", "title": "Mobile push notifications", "status": "expired", "reason": "Stakeholder left company", "created": "2023-12-01"},
], indent=2))

writefile(os.path.join(WORKSPACE, "team", "status.json"),
json.dumps({
    "Alice": {"role": "Backend Lead", "current_task": "T-201", "availability": "75%", "OOO": None},
    "Bob": {"role": "Senior Engineer", "current_task": "T-202", "availability": "100%", "OOO": None},
    "Carol": {"role": "DevOps", "current_task": None, "availability": "50%", "OOO": "2024-01-15 to 2024-01-19"},
}, indent=2))

# ── memory files (the core data for the skill) ────────────────────────────────

# memory/session_history.json — stale session history (deletable)
writefile(os.path.join(WORKSPACE, "memory", "session_history.json"),
json.dumps([
    {"session_id": "s-001", "date": "2023-10-01", "summary": "Discussed Q3 OKRs", "stale": True},
    {"session_id": "s-002", "date": "2023-10-15", "summary": "Sprint 10 planning", "stale": True},
    {"session_id": "s-003", "date": "2023-11-01", "summary": "Sprint 11 kickoff", "stale": True},
    {"session_id": "s-004", "date": "2023-12-01", "summary": "Year-end review prep", "stale": True},
    {"session_id": "s-005", "date": "2024-01-08", "summary": "Sprint 13 planning - active", "stale": False},
], indent=2))

# memory/completed_tasks_detail.json — verbose completed task records (deletable detail, keep summary)
writefile(os.path.join(WORKSPACE, "memory", "completed_tasks_detail.json"),
json.dumps([
    {"id": "T-101", "title": "Setup CI pipeline", "full_log": "Day 1: researched Jenkins vs GHA... Day 2: wrote initial workflow... Day 3: fixed caching bug... Day 4: matrix build added... Day 5: Codecov integration... total: 5 days, 847 lines changed"},
    {"id": "T-102", "title": "Database migration v2", "full_log": "Week 1: schema analysis... Week 2: migration scripts... Week 3: staging tests... Week 4: production rollout... total: 4 weeks, 12 scripts"},
    {"id": "T-103", "title": "API rate limiting", "full_log": "Research: 3 days on algorithms... Implementation: 5 days... Testing: 2 days... Monitoring: 1 day... total: 11 days"},
], indent=2))

# memory/active_discussions.json — ongoing (must keep)
writefile(os.path.join(WORKSPACE, "memory", "active_discussions.json"),
json.dumps([
    {"topic": "OAuth2 security review process", "status": "open", "participants": ["Alice", "Security Team"], "last_update": "2024-01-11"},
    {"topic": "Performance SLA targets for Q1 2024", "status": "open", "participants": ["Bob", "Product"], "last_update": "2024-01-10"},
    {"topic": "Carol's DevOps backfill during OOO", "status": "open", "participants": ["Carol", "Manager"], "last_update": "2024-01-11"},
], indent=2))

# memory/expired_tasks.json — expired/cancelled (deletable)
writefile(os.path.join(WORKSPACE, "memory", "expired_tasks.json"),
json.dumps([
    {"id": "T-055", "title": "Migrate to GraphQL", "status": "cancelled", "memory_detail": "Evaluated Apollo, Hasura, custom impl. Estimated 6 months. Cancelled after stakeholder alignment meeting on 2023-09-20."},
    {"id": "T-067", "title": "Redis cluster upgrade", "memory_detail": "Vendor EOL notice received. 3 options evaluated. Contract not renewed. All research notes archived externally."},
    {"id": "T-078", "title": "Mobile push notifications", "memory_detail": "Initial design complete. Firebase vs SNS comparison done. Stakeholder departure halted all work."},
], indent=2))

# memory/team_current_status.json — team status (must keep)
writefile(os.path.join(WORKSPACE, "memory", "team_current_status.json"),
json.dumps({
    "last_updated": "2024-01-11",
    "members": {
        "Alice": {"focus": "OAuth2 login implementation", "blocker": "security review pending"},
        "Bob": {"focus": "fixing N+1 query in user lookup", "blocker": None},
        "Carol": {"focus": "infra maintenance", "upcoming_ooo": "2024-01-15 to 2024-01-19"},
    }
}, indent=2))

# memory/old_sprint_notes.json — stale (deletable)
writefile(os.path.join(WORKSPACE, "memory", "old_sprint_notes.json"),
json.dumps([
    {"sprint": 10, "notes": "velocity=34, burndown ok, retro action: improve PR review SLA"},
    {"sprint": 11, "notes": "velocity=29, CI issues in week 2, resolved by Bob, retro action: add flaky test detection"},
    {"sprint": 12, "notes": "velocity=38, all goals met, CI pipeline shipped, DB migration done, rate limiting done"},
], indent=2))

print(f"Workspace generated at {WORKSPACE}")
print("Files created:")
for root, dirs, files in os.walk(WORKSPACE):
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, WORKSPACE)
        print(f"  {rel}")