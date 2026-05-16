#!/usr/bin/env python3
"""
Generate the messy, realistic memory workspace that the agent must clean up.
All timestamps are deterministic based on a fixed reference date.
Reference "now" = 2026-04-20T12:00:00 (hardcoded for determinism)
"""

import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
MEMORY_BASE = WORKSPACE / "memory"
TIERS_DIR = MEMORY_BASE / "tiers"
WORKING_DIR = TIERS_DIR / "working"
SHORT_TERM_DIR = TIERS_DIR / "short-term"
LONG_TERM_DIR = TIERS_DIR / "long-term"
SKILLS_DIR = WORKSPACE / "skills"

# Create directory structure
for d in [MEMORY_BASE, TIERS_DIR, WORKING_DIR, SHORT_TERM_DIR, LONG_TERM_DIR, SKILLS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Reference "now"
NOW = datetime(2026, 4, 20, 12, 0, 0)

# ── MEMORY.md (main memory file, must always be preserved) ──────────────────
(MEMORY_BASE / "MEMORY.md").write_text("""# OpenClaw Memory Index
**Last Updated**: 2026-04-20
**Status**: Active

## Core Identity
- Name: OpenClaw AI Assistant
- Version: 2.3.1
- Primary Role: Autonomous coding and system management

## Key Learnings
- Python async patterns mastered (Round 47)
- Docker orchestration workflows (Round 52)
- Memory management protocols (Round 61)

## Active Projects
- Project Alpha: Code refactoring pipeline
- Project Beta: Knowledge graph optimization
""")

# ── capabilities.json ────────────────────────────────────────────────────────
(MEMORY_BASE / "capabilities.json").write_text(json.dumps({
    "version": "2.3.1",
    "lastUpdated": NOW.isoformat(),
    "capabilities": {
        "coding": {"level": 9, "languages": ["Python", "JavaScript", "Rust"]},
        "systemDesign": {"level": 8},
        "memoryManagement": {"level": 7},
        "debugging": {"level": 9}
    },
    "totalLearningRounds": 78,
    "totalConversations": 23
}, indent=2))

# ── knowledge-graph.json ─────────────────────────────────────────────────────
(MEMORY_BASE / "knowledge-graph.json").write_text(json.dumps({
    "nodes": [
        {"id": "python", "weight": 0.95, "connections": ["async", "testing"]},
        {"id": "docker", "weight": 0.88, "connections": ["kubernetes", "compose"]},
        {"id": "memory", "weight": 0.72, "connections": ["compression", "retrieval"]}
    ],
    "edges": 47,
    "lastOptimized": (NOW - timedelta(days=3)).isoformat()
}, indent=2))

# ── tiers/config.json ────────────────────────────────────────────────────────
# Intentionally WRONG/incomplete config - agent must fix it per SKILL.md specs
(TIERS_DIR / "config.json").write_text(json.dumps({
    "memoryManager": {
        "enabled": True,
        "workingMemoryDays": 3,        # WRONG - should be 7
        "shortTermMemoryDays": 14,     # WRONG - should be 30
        "maxLearningRounds": 100,      # WRONG - should be 50
        "maxConversations": 20,        # WRONG - should be 10
        "autoCompact": False,          # WRONG - should be true
        "compactThreshold": 0.5,       # WRONG - should be 0.7
        "mergeStrategy": "replace"     # WRONG - should be "summarize"
    }
}, indent=2))

# ── learning-round-*.json files ──────────────────────────────────────────────
# Create rounds 1-78 (way more than the 50-round limit)
# Rounds 1-28 are old (>50 rounds ago from current max 78), must be deleted
# We distribute them across different ages for realism

def make_learning_round(n, created_at):
    return {
        "round": n,
        "timestamp": created_at.isoformat(),
        "topic": random.choice(["Python async", "Docker networking", "Memory optimization",
                                 "Code refactoring", "API design", "Testing strategies",
                                 "Performance tuning", "Security hardening"]),
        "keyInsights": [
            f"Insight {n}-A: learned pattern for topic",
            f"Insight {n}-B: optimization discovered"
        ],
        "qualityScore": round(random.uniform(0.6, 0.99), 2),
        "importance": random.choice(["high", "medium", "low"])
    }

# Rounds 1-28 should be DELETED (exceed maxLearningRounds=50, keeping newest 50 means rounds 29-78)
for i in range(1, 29):
    age_days = 70 + (29 - i)  # Very old
    created = NOW - timedelta(days=age_days)
    fpath = MEMORY_BASE / f"learning-round-{i}.json"
    fpath.write_text(json.dumps(make_learning_round(i, created), indent=2))

# Rounds 29-78 should be KEPT (newest 50)
for i in range(29, 79):
    age_days = max(0, 78 - i)  # Newer rounds are more recent
    created = NOW - timedelta(days=age_days)
    fpath = MEMORY_BASE / f"learning-round-{i}.json"
    fpath.write_text(json.dumps(make_learning_round(i, created), indent=2))

# ── conversation-*.json files ─────────────────────────────────────────────────
# Create 23 conversations (way more than the 10-conversation limit)
# Conversations 1-13 should be DELETED (keeping newest 10: conv 14-23)

def make_conversation(n, created_at):
    return {
        "conversationId": f"conv-{n:04d}",
        "timestamp": created_at.isoformat(),
        "turns": random.randint(4, 20),
        "summary": f"Discussion about topic {n}: resolved {random.randint(1,5)} issues",
        "tags": random.sample(["coding", "debugging", "planning", "review", "learning"], 2),
        "archived": False
    }

for i in range(1, 24):
    age_days = 25 - i  # Conv 1 is oldest (24 days), conv 23 is newest (2 days)
    created = NOW - timedelta(days=age_days)
    fpath = MEMORY_BASE / f"conversation-{i:04d}.json"
    fpath.write_text(json.dumps(make_conversation(i, created), indent=2))

# ── working/ tier files ───────────────────────────────────────────────────────
# Mix of fresh files (<=7 days) and stale files (>7 days, must migrate to short-term)

working_files = [
    # Fresh files (<=7 days) - STAY in working
    ("session-20260419-alpha.json", 1,  {"sessionId": "alpha", "data": "recent work on Python module"}),
    ("session-20260418-beta.json",  2,  {"sessionId": "beta",  "data": "Docker compose debugging"}),
    ("session-20260415-gamma.json", 5,  {"sessionId": "gamma", "data": "API endpoint design"}),
    ("session-20260414-delta.json", 6,  {"sessionId": "delta", "data": "unit test refactoring"}),
    ("session-20260413-epsilon.json",7, {"sessionId": "epsilon","data": "performance profiling"}),
    # Stale files (>7 days) - MUST MIGRATE to short-term
    ("session-20260412-zeta.json",  8,  {"sessionId": "zeta",  "data": "code review session"}),
    ("session-20260410-eta.json",   10, {"sessionId": "eta",   "data": "architecture planning"}),
    ("session-20260405-theta.json", 15, {"sessionId": "theta", "data": "database optimization"}),
    ("session-20260401-iota.json",  19, {"sessionId": "iota",  "data": "security audit prep"}),
    ("session-20260322-kappa.json", 29, {"sessionId": "kappa", "data": "async pattern study"}),
]

for fname, age_days, payload in working_files:
    created = NOW - timedelta(days=age_days)
    data = {**payload, "createdAt": created.isoformat(), "tier": "working"}
    (WORKING_DIR / fname).write_text(json.dumps(data, indent=2))

# ── short-term/ tier files ────────────────────────────────────────────────────
# Mix of recent short-term (<=30 days) and old ones (>30 days, must migrate to long-term)

short_term_files = [
    # Recent (<=30 days from now) - STAY in short-term
    ("memo-20260325-001.json", 26, {"memoId": "001", "topic": "Rust ownership patterns"}),
    ("memo-20260320-002.json", 31, {"memoId": "002", "topic": "async/await deep dive"}),  # exactly >30
    ("memo-20260315-003.json", 36, {"memoId": "003", "topic": "microservices patterns"}),
    # Old (>30 days) - MUST MIGRATE to long-term
    ("memo-20260310-004.json", 41, {"memoId": "004", "topic": "CI/CD pipeline design"}),
    ("memo-20260301-005.json", 50, {"memoId": "005", "topic": "database indexing"}),
    ("memo-20260220-006.json", 59, {"memoId": "006", "topic": "memory compression algorithms"}),
    ("memo-20260210-007.json", 69, {"memoId": "007", "topic": "knowledge graph traversal"}),
]

for fname, age_days, payload in short_term_files:
    created = NOW - timedelta(days=age_days)
    data = {**payload, "createdAt": created.isoformat(), "tier": "short-term"}
    (SHORT_TERM_DIR / fname).write_text(json.dumps(data, indent=2))

# ── long-term/ tier files (already there, should be untouched) ────────────────
long_term_files = [
    ("permanent-python-mastery.json", 180, {"topic": "Python mastery", "importance": "critical"}),
    ("permanent-system-design.json",  200, {"topic": "System design fundamentals", "importance": "critical"}),
    ("permanent-core-identity.json",  365, {"topic": "Core identity and values", "importance": "critical"}),
]

for fname, age_days, payload in long_term_files:
    created = NOW - timedelta(days=age_days)
    data = {**payload, "createdAt": created.isoformat(), "tier": "long-term"}
    (LONG_TERM_DIR / fname).write_text(json.dumps(data, indent=2))

# ── Distractor files to test contextual awareness ─────────────────────────────
# These should NOT be touched by the agent

(WORKSPACE / "agent-config.yaml").write_text("""
agent:
  name: OpenClaw
  version: 2.3.1
  skills:
    - memory-manager
    - code-analyzer
    - task-planner
""")

(WORKSPACE / "runtime.log").write_text("""
2026-04-20 11:45:00 [INFO] Agent started
2026-04-20 11:50:00 [INFO] Learning round 78 completed
2026-04-20 11:55:00 [INFO] Memory manager triggered
2026-04-20 12:00:00 [INFO] Awaiting cleanup
""")

(WORKSPACE / "skills" / "memory-manager.js").write_text("""
// Memory Manager Skill - OpenClaw
// This file intentionally left as stub - logic must be implemented per SKILL.md
module.exports = {
  run: async () => { throw new Error("Not implemented - see SKILL.md"); },
  cleanup: async () => { throw new Error("Not implemented - see SKILL.md"); },
  merge: async () => { throw new Error("Not implemented - see SKILL.md"); }
};
""")

(WORKSPACE / "skills" / "code-analyzer.js").write_text("module.exports = {};")
(WORKSPACE / "skills" / "task-planner.js").write_text("module.exports = {};")

(WORKSPACE / ".openclaw-state").write_text(json.dumps({
    "lastRun": (NOW - timedelta(hours=12)).isoformat(),
    "pendingTasks": ["memory-cleanup", "tier-migration"],
    "status": "needs_maintenance"
}, indent=2))

# Create a misleading "old_backup" directory as distractor
old_backup = WORKSPACE / "old_backup" / "memory_snapshot_20260101"
old_backup.mkdir(parents=True, exist_ok=True)
(old_backup / "snapshot.json").write_text(json.dumps({"note": "old backup, do not modify", "date": "2026-01-01"}))
(old_backup / "MEMORY.md.bak").write_text("# Old backup - ignore")

# Another distractor: temp directory
temp_dir = WORKSPACE / "tmp" / "processing"
temp_dir.mkdir(parents=True, exist_ok=True)
(temp_dir / "scratch.json").write_text('{"status": "temporary", "delete_me": true}')
(temp_dir / "partial-merge.json").write_text('{"status": "incomplete", "data": null}')

print("✅ Workspace generated successfully")
print(f"   Memory base: {MEMORY_BASE}")
print(f"   Learning rounds created: 1-78 (28 should be deleted, 50 kept)")
print(f"   Conversations created: 1-23 (13 should be deleted, 10 kept)")
print(f"   Working files: 10 (5 fresh, 5 stale→short-term)")
print(f"   Short-term files: 7 (3 stay, 4 stale→long-term)")
print(f"   Long-term files: 3 (permanent)")