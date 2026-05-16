import json
import os
import random
from pathlib import Path
from datetime import datetime, date, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "memory/user",
    "memory/self",
    "memory/relationship",
    "memory/world",
    "skills/hippocampus/scripts",
    "skills/hippocampus/config",
    "logs",
    "config",
    "sessions",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
(workspace / "config" / "openclaw.json").write_text(json.dumps({
    "agents": {"defaults": {"memorySearch": {"extraPaths": []}}},
    "version": "3.8.6"
}, indent=2))

(workspace / "logs" / "encoding-2025-01-10.log").write_text(
    "INFO  [encode] processed 12 signals\nINFO  [encode] 3 reinforced, 9 created\n"
)
(workspace / "logs" / "decay-2025-01-10.log").write_text(
    "INFO  [decay] applied to 14 memories\n"
)

(workspace / "sessions" / "session-001.jsonl").write_text(
    '{"role":"user","content":"I prefer dark mode always"}\n'
    '{"role":"assistant","content":"Noted!"}\n'
)

(workspace / "tmp" / "pending-signals.jsonl").write_text(
    '{"signal":"user likes Python over JavaScript","score":0.8}\n'
)

(workspace / "skills" / "hippocampus" / "config" / "settings.json").write_text(json.dumps({
    "signalLimit": 100,
    "decayFactor": 0.99,
    "reinforcementBump": 0.10
}, indent=2))

(workspace / "skills" / "hippocampus" / "scripts" / "README.txt").write_text(
    "Scripts live here. Do not edit manually.\n"
)

(workspace / "memory" / "signals.jsonl").write_text(
    '{"id":"sig_001","content":"user hates Comic Sans","ts":"2025-01-18T10:00:00Z"}\n'
    '{"id":"sig_002","content":"user is a morning person","ts":"2025-01-19T08:00:00Z"}\n'
)

(workspace / "memory" / "user" / "notes.txt").write_text(
    "Informal user notes – NOT part of the memory index.\n"
)
(workspace / "memory" / "self" / "identity.txt").write_text(
    "Agent name: Aria\n"
)
(workspace / "memory" / "relationship" / "trust-log.txt").write_text(
    "Trust level established: high\n"
)
(workspace / "memory" / "world" / "projects.txt").write_text(
    "Project Alpha – deadline Q2 2025\n"
)

# ── THE PROBLEM: a stale, partially broken index.json ───────────────────────
# Reference date for the audit is 2025-02-15.
# lastAccessed dates are set so decay calculations are non-trivial.
# Some memories have timesReinforced > 0 (importance already bumped in past, no extra bump needed now).
# The schema is missing required fields on some entries (agent must fix).
# One entry has importance > 1.0 (schema violation, must be clamped to 1.0 before decay).
# "decayLastRun" is stale (2025-01-01) — decay must be applied up to 2025-02-15.
# days = (2025-02-15) - lastAccessed

stale_index = {
    "version": 1,
    "lastUpdated": "2025-01-20T08:00:00Z",   # will be updated by agent
    "decayLastRun": "2025-01-01",              # STALE — agent must update to 2025-02-15
    "lastProcessedMessageId": "msg_042",
    "memories": [
        {
            # Core user preference – lastAccessed 2025-02-10 → 5 days before ref
            # importance 0.85, timesReinforced=3
            # decay: 0.85 * 0.99^5 = 0.85 * 0.95099... ≈ 0.8083
            # Post-decay: 0.8083 → Core (≥0.7)
            "id": "mem_001",
            "domain": "user",
            "category": "preferences",
            "content": "User prefers dark mode in all applications",
            "importance": 0.85,
            "created": "2025-01-05",
            "lastAccessed": "2025-02-10",
            "timesReinforced": 3,
            "keywords": ["dark mode", "preference", "ui"]
        },
        {
            # Emotional memory – lastAccessed 2025-01-15 → 31 days before ref
            # importance 0.85, timesReinforced=1
            # decay: 0.85 * 0.99^31 ≈ 0.85 * 0.7327 ≈ 0.6228
            # Post-decay: ~0.6228 → Active (0.4-0.7), NOT core
            "id": "mem_002",
            "domain": "relationship",
            "category": "trust",
            "content": "User shared a personal struggle about work-life balance",
            "importance": 0.85,
            "created": "2025-01-10",
            "lastAccessed": "2025-01-15",
            "timesReinforced": 1,
            "keywords": ["struggle", "work-life", "emotional"]
        },
        {
            # Decision memory – lastAccessed 2025-02-14 → 1 day before ref
            # importance 0.75, timesReinforced=0
            # decay: 0.75 * 0.99^1 = 0.75 * 0.99 = 0.7425
            # Post-decay: 0.7425 → Core (≥0.7)
            "id": "mem_003",
            "domain": "world",
            "category": "decisions",
            "content": "Team decided to migrate backend to FastAPI by Q2 2025",
            "importance": 0.75,
            "created": "2025-01-20",
            "lastAccessed": "2025-02-14",
            "timesReinforced": 0,
            "keywords": ["fastapi", "migration", "decision"]
        },
        {
            # General knowledge – lastAccessed 2025-01-01 → 45 days before ref
            # importance 0.5, timesReinforced=0
            # decay: 0.5 * 0.99^45 ≈ 0.5 * 0.6378 ≈ 0.3189
            # Post-decay: ~0.3189 → Background (0.2-0.4)
            "id": "mem_004",
            "domain": "world",
            "category": "knowledge",
            "content": "Python 3.12 released with significant performance improvements",
            "importance": 0.5,
            "created": "2024-12-15",
            "lastAccessed": "2025-01-01",
            "timesReinforced": 0,
            "keywords": ["python", "release", "performance"]
        },
        {
            # Self memory – lastAccessed 2025-01-20 → 26 days before ref
            # importance INVALID: 1.05 (>1.0) → must clamp to 1.0 first
            # decay: 1.0 * 0.99^26 ≈ 0.7697
            # Post-decay: ~0.7697 → Core (≥0.7)
            "id": "mem_005",
            "domain": "self",
            "category": "identity",
            "content": "Agent identity: analytical, concise, and empathetic communicator",
            "importance": 1.05,   # SCHEMA VIOLATION – must be clamped to 1.0
            "created": "2025-01-01",
            "lastAccessed": "2025-01-20",
            "timesReinforced": 5,
            "keywords": ["identity", "personality", "self"]
        },
        {
            # Old/neglected memory – lastAccessed 2024-12-01 → 76 days before ref
            # importance 0.4, timesReinforced=0
            # decay: 0.4 * 0.99^76 ≈ 0.4 * 0.4633 ≈ 0.1853
            # Post-decay: ~0.1853 → Archive candidate (<0.2)
            "id": "mem_006",
            "domain": "user",
            "category": "context",
            "content": "User mentioned they once lived in Berlin for a year",
            "importance": 0.4,
            "created": "2024-11-01",
            "lastAccessed": "2024-12-01",
            "timesReinforced": 0,
            "keywords": ["berlin", "travel", "history"]
        },
        {
            # MISSING REQUIRED FIELDS: no 'timesReinforced', no 'keywords'
            # lastAccessed 2025-02-01 → 14 days before ref
            # importance 0.7, no timesReinforced (treat as 0)
            # decay: 0.7 * 0.99^14 ≈ 0.7 * 0.8687 ≈ 0.6081
            # Post-decay: ~0.6081 → Active (NOT core, just misses 0.7 threshold)
            "id": "mem_007",
            "domain": "user",
            "category": "preferences",
            "content": "User prefers Python over JavaScript for scripting tasks",
            # missing timesReinforced
            # missing keywords
            "importance": 0.7,
            "created": "2025-01-08",
            "lastAccessed": "2025-02-01"
        },
        {
            # Background memory – lastAccessed 2025-01-25 → 21 days before ref
            # importance 0.35, timesReinforced=2
            # decay: 0.35 * 0.99^21 ≈ 0.35 * 0.8080 ≈ 0.2828
            # Post-decay: ~0.2828 → Background (0.2-0.4)
            "id": "mem_008",
            "domain": "world",
            "category": "knowledge",
            "content": "Docker Compose v2 is now the default in Docker Desktop",
            "importance": 0.35,
            "created": "2025-01-10",
            "lastAccessed": "2025-01-25",
            "timesReinforced": 2,
            "keywords": ["docker", "compose", "tooling"]
        }
    ]
}

(workspace / "memory" / "index.json").write_text(json.dumps(stale_index, indent=2))

# ── audit instructions file (business context only, no hints) ───────────────
(workspace / "AUDIT_REQUEST.txt").write_text(
    "Memory Audit Request\n"
    "====================\n"
    "Reference date: 2025-02-15\n"
    "Please update the memory system to reflect current memory health as of this date.\n"
    "Produce a snapshot of the most important active memories for session loading.\n"
    "Output file requested: core-memories.json\n"
)

print("Workspace generated successfully.")