#!/usr/bin/env python3
"""
Generate a realistic OpenClaw workspace with session JSONL files and distractor files.
The agent must read SKILL.md to understand the credit formula and file layout.
"""
import os
import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")
HOME = Path("/root")

# ─── 1. Distractor files (deeply nested, realistic) ───────────────────────────
distractor_dirs = [
    WORKSPACE / "projects" / "backend" / "api" / "routes",
    WORKSPACE / "projects" / "backend" / "models",
    WORKSPACE / "projects" / "frontend" / "src" / "components",
    WORKSPACE / "projects" / "frontend" / "src" / "hooks",
    WORKSPACE / "projects" / "infra" / "terraform" / "modules" / "vpc",
    WORKSPACE / "logs" / "2024" / "december",
    WORKSPACE / "logs" / "2025" / "january",
    WORKSPACE / "configs" / "nginx",
    WORKSPACE / "configs" / "postgres",
    WORKSPACE / ".cache" / "pip" / "wheels",
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    WORKSPACE / "projects" / "backend" / "api" / "routes" / "users.py": "# User routes\nfrom flask import Blueprint\nusers_bp = Blueprint('users', __name__)\n",
    WORKSPACE / "projects" / "backend" / "api" / "routes" / "billing.py": "# Billing routes\n# TODO: integrate with Stripe\n",
    WORKSPACE / "projects" / "backend" / "models" / "user.py": "class User:\n    id: str\n    email: str\n    plan: str\n",
    WORKSPACE / "projects" / "frontend" / "src" / "components" / "Dashboard.tsx": "export const Dashboard = () => <div>Loading...</div>;\n",
    WORKSPACE / "projects" / "frontend" / "src" / "hooks" / "useCredits.ts": "// Hook to fetch credit usage\nexport const useCredits = () => { return { used: 0, total: 0 }; };\n",
    WORKSPACE / "projects" / "infra" / "terraform" / "modules" / "vpc" / "main.tf": 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n',
    WORKSPACE / "projects" / "infra" / "terraform" / "modules" / "vpc" / "variables.tf": 'variable "region" {\n  default = "us-east-1"\n}\n',
    WORKSPACE / "logs" / "2024" / "december" / "app.log": "[2024-12-01] INFO: Server started\n[2024-12-01] INFO: Connected to DB\n",
    WORKSPACE / "logs" / "2025" / "january" / "app.log": "[2025-01-15] ERROR: Connection timeout\n[2025-01-15] INFO: Retry succeeded\n",
    WORKSPACE / "configs" / "nginx" / "nginx.conf": "worker_processes auto;\nevents { worker_connections 1024; }\n",
    WORKSPACE / "configs" / "postgres" / "pg_hba.conf": "# TYPE  DATABASE  USER  ADDRESS  METHOD\nlocal   all       all            md5\n",
    WORKSPACE / ".cache" / "pip" / "wheels" / "placeholder.txt": "wheel cache placeholder\n",
}

for path, content in distractor_files.items():
    path.write_text(content)

# A misleading "credits.json" to confuse naive agents
fake_credits = {
    "note": "This is NOT the usage report. This is a stale cache from a previous tool.",
    "sessions": [],
    "total_credits": 99999999,
}
(WORKSPACE / "configs" / "credits.json").write_text(json.dumps(fake_credits, indent=2))

# A misleading config file that looks like claude config but is wrong
(WORKSPACE / "configs" / "claude_config_OLD.json").write_text(json.dumps({
    "plan": "pro",
    "reset_time": "2024-01-01 00:00",
    "note": "DEPRECATED - do not use"
}, indent=2))

# ─── 2. OpenClaw session JSONL files ──────────────────────────────────────────
# Weekly reset: Monday 2026-02-09 14:00 UTC (this is what the agent must --save)
# Sessions are within the current week (after that reset)

RESET_TIME = datetime(2026, 2, 9, 14, 0, 0, tzinfo=timezone.utc)

# We define sessions with known token counts so eval can verify math precisely.
# Credits formula:
#   credits = (input_tokens + cache_write_tokens) * input_rate + output_tokens * output_rate
#
# Rates (per 15 tokens):
#   Haiku:  input=2/15,  output=10/15
#   Sonnet: input=6/15,  output=30/15
#   Opus:   input=10/15, output=50/15
#   Gemini: 0 (non-Claude)

def make_session_id():
    return uuid.uuid4().hex[:16]

# Session definitions: list of (session_key, list of message records)
# Each record: model, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens, timestamp_offset_hours

SESSIONS = [
    # Session A: "main-project" — heavy Sonnet + some Haiku usage (HIGHEST cost)
    {
        "key": "main-project",
        "id": "9aadee4f1b2c3d4e",
        "records": [
            # Sonnet: 50000 input, 8000 output, 20000 cache_write, 15000 cache_read
            # credits = (50000+20000)*6/15 + 8000*30/15 = 70000*0.4 + 8000*2 = 28000 + 16000 = 44000
            {"model": "claude-sonnet-4-5", "input_tokens": 50000, "output_tokens": 8000,
             "cache_write_tokens": 20000, "cache_read_tokens": 15000, "offset_hours": 1},
            # Sonnet: 30000 input, 5000 output, 0 cache_write, 10000 cache_read
            # credits = 30000*6/15 + 5000*30/15 = 12000 + 10000 = 22000
            {"model": "claude-sonnet-4-5", "input_tokens": 30000, "output_tokens": 5000,
             "cache_write_tokens": 0, "cache_read_tokens": 10000, "offset_hours": 2},
            # Haiku: 10000 input, 2000 output, 5000 cache_write, 0 cache_read
            # credits = (10000+5000)*2/15 + 2000*10/15 = 15000*2/15 + 2000*10/15 = 2000 + 1333.33
            {"model": "claude-haiku-4-5", "input_tokens": 10000, "output_tokens": 2000,
             "cache_write_tokens": 5000, "cache_read_tokens": 0, "offset_hours": 3},
        ]
    },
    # Session B: "opus-research" — Opus heavy (SECOND highest)
    {
        "key": "opus-research",
        "id": "b3c4d5e6f7a8b9c0",
        "records": [
            # Opus: 20000 input, 4000 output, 10000 cache_write, 5000 cache_read
            # credits = (20000+10000)*10/15 + 4000*50/15 = 30000*10/15 + 4000*50/15
            #         = 20000 + 13333.33
            {"model": "claude-opus-4-5", "input_tokens": 20000, "output_tokens": 4000,
             "cache_write_tokens": 10000, "cache_read_tokens": 5000, "offset_hours": 4},
            # Opus: 15000 input, 3000 output, 0, 8000 cache_read
            # credits = 15000*10/15 + 3000*50/15 = 10000 + 10000 = 20000
            {"model": "claude-opus-4-5", "input_tokens": 15000, "output_tokens": 3000,
             "cache_write_tokens": 0, "cache_read_tokens": 8000, "offset_hours": 5},
        ]
    },
    # Session C: "gemini-experiments" — ALL Gemini (ZERO Claude credits)
    {
        "key": "gemini-experiments",
        "id": "c4d5e6f7a8b9c0d1",
        "records": [
            {"model": "gemini-2.0-flash", "input_tokens": 100000, "output_tokens": 20000,
             "cache_write_tokens": 0, "cache_read_tokens": 0, "offset_hours": 2},
            {"model": "gemini-2.0-flash", "input_tokens": 80000, "output_tokens": 15000,
             "cache_write_tokens": 0, "cache_read_tokens": 0, "offset_hours": 3},
        ]
    },
    # Session D: "haiku-quicktasks" — light Haiku (THIRD highest Claude cost)
    {
        "key": "haiku-quicktasks",
        "id": "d5e6f7a8b9c0d1e2",
        "records": [
            # Haiku: 8000 input, 1500 output, 3000 cache_write, 2000 cache_read
            # credits = (8000+3000)*2/15 + 1500*10/15 = 11000*2/15 + 1500*10/15
            #         = 1466.67 + 1000 = 2466.67
            {"model": "claude-haiku-4-5", "input_tokens": 8000, "output_tokens": 1500,
             "cache_write_tokens": 3000, "cache_read_tokens": 2000, "offset_hours": 6},
            # Haiku: 5000 input, 1000 output, 0, 3000 cache_read
            # credits = 5000*2/15 + 1000*10/15 = 666.67 + 666.67 = 1333.33
            {"model": "claude-haiku-4-5", "input_tokens": 5000, "output_tokens": 1000,
             "cache_write_tokens": 0, "cache_read_tokens": 3000, "offset_hours": 7},
        ]
    },
    # Session E: "mixed-codex" — Codex (non-Claude) + Haiku mix
    {
        "key": "mixed-codex",
        "id": "e6f7a8b9c0d1e2f3",
        "records": [
            # Codex = non-Claude, 0 credits
            {"model": "codex-mini", "input_tokens": 50000, "output_tokens": 10000,
             "cache_write_tokens": 0, "cache_read_tokens": 0, "offset_hours": 8},
            # Haiku: 2000 input, 500 output, 1000 cache_write, 0 cache_read
            # credits = (2000+1000)*2/15 + 500*10/15 = 3000*2/15 + 500*10/15
            #         = 400 + 333.33 = 733.33
            {"model": "claude-haiku-4-5", "input_tokens": 2000, "output_tokens": 500,
             "cache_write_tokens": 1000, "cache_read_tokens": 0, "offset_hours": 8},
        ]
    },
]

# Build JSONL files
sessions_dir = HOME / ".openclaw" / "agents" / "main" / "sessions"
sessions_dir.mkdir(parents=True, exist_ok=True)

def model_to_filename(key):
    return f"session_{key}.jsonl"

for sess in SESSIONS:
    lines = []
    for i, rec in enumerate(sess["records"]):
        ts = RESET_TIME + timedelta(hours=rec["offset_hours"])
        entry = {
            "session_id": sess["id"],
            "session_key": sess["key"],
            "message_id": uuid.UUID(int=random.getrandbits(128), version=4).hex,
            "timestamp": ts.isoformat(),
            "model": rec["model"],
            "usage": {
                "input_tokens": rec["input_tokens"],
                "output_tokens": rec["output_tokens"],
                "cache_creation_input_tokens": rec["cache_write_tokens"],
                "cache_read_input_tokens": rec["cache_read_tokens"],
            }
        }
        lines.append(json.dumps(entry))
    
    fpath = sessions_dir / model_to_filename(sess["key"])
    fpath.write_text("\n".join(lines) + "\n")

# Also write a corrupted/partial session file as a distractor
(sessions_dir / "session_corrupted.jsonl").write_text(
    '{"session_id": "deadbeef", "timestamp": "NOT_A_DATE", "model": "claude-sonnet-4-5"\n'
    '{"broken json line\n'
)

# Write a reference file for the eval script (hidden from agent)
# This encodes the ground-truth credit calculations
ground_truth = {
    "sessions": {
        "main-project": {
            "id": "9aadee4f1b2c3d4e",
            # Record 1 Sonnet: (50000+20000)*6/15 + 8000*30/15 = 28000+16000=44000
            # Record 2 Sonnet: 30000*6/15 + 5000*30/15 = 12000+10000=22000
            # Record 3 Haiku:  (10000+5000)*2/15 + 2000*10/15 = 2000+1333.33=3333.33
            "expected_credits": 44000 + 22000 + (15000*2/15 + 2000*10/15),
        },
        "opus-research": {
            "id": "b3c4d5e6f7a8b9c0",
            # Record 1 Opus: (20000+10000)*10/15 + 4000*50/15 = 20000+13333.33=33333.33
            # Record 2 Opus: 15000*10/15 + 3000*50/15 = 10000+10000=20000
            "expected_credits": (30000*10/15 + 4000*50/15) + (15000*10/15 + 3000*50/15),
        },
        "gemini-experiments": {
            "id": "c4d5e6f7a8b9c0d1",
            "expected_credits": 0,
        },
        "haiku-quicktasks": {
            "id": "d5e6f7a8b9c0d1e2",
            # Record 1: (8000+3000)*2/15 + 1500*10/15 = 11000*2/15 + 1500*10/15
            # Record 2: 5000*2/15 + 1000*10/15
            "expected_credits": (11000*2/15 + 1500*10/15) + (5000*2/15 + 1000*10/15),
        },
        "mixed-codex": {
            "id": "e6f7a8b9c0d1e2f3",
            # Codex = 0; Haiku: (2000+1000)*2/15 + 500*10/15 = 400+333.33=733.33
            "expected_credits": 3000*2/15 + 500*10/15,
        },
    },
    "weekly_reset": "2026-02-09 14:00",
    "plan": "5x",
}

# Compute top 3 by credits
ranked = sorted(
    ground_truth["sessions"].items(),
    key=lambda x: x[1]["expected_credits"],
    reverse=True
)
ground_truth["top3_keys"] = [r[0] for r in ranked[:3]]
ground_truth["top3_credits"] = [r[1]["expected_credits"] for r in ranked[:3]]

(WORKSPACE / ".eval_ground_truth.json").write_text(json.dumps(ground_truth, indent=2))

print("Workspace generated successfully.")
print(f"Sessions dir: {sessions_dir}")
print(f"Sessions created: {[s['key'] for s in SESSIONS]}")
print(f"Expected top 3: {ground_truth['top3_keys']}")
print(f"Expected top 3 credits: {ground_truth['top3_credits']}")