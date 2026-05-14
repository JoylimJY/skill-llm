#!/usr/bin/env python3
"""
Generates the MindCore sandbox workspace with realistic distractor files
and the raw, messy inputs the agent must process.
"""
import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Clone the real MindCore repository ──────────────────────────────────
import subprocess
result = subprocess.run(
    ["git", "clone", "https://github.com/MineLiu19/mindcore.git", str(WORKSPACE / "mindcore")],
    capture_output=True, text=True
)
print(result.stdout)
print(result.stderr)

MINDCORE = WORKSPACE / "mindcore"

# ── 2. Create distractor files (deeply nested, realistic noise) ────────────
dirs = [
    WORKSPACE / "user_profiles" / "beta_testers",
    WORKSPACE / "user_profiles" / "vip",
    WORKSPACE / "logs" / "2024-11" / "sessions",
    WORKSPACE / "logs" / "2024-12" / "errors",
    WORKSPACE / "integration" / "openclaw" / "hooks",
    WORKSPACE / "integration" / "slack" / "webhooks",
    WORKSPACE / "deployment" / "docker" / "configs",
    WORKSPACE / "deployment" / "k8s",
    WORKSPACE / "analytics" / "dashboards",
    WORKSPACE / "analytics" / "exports",
    WORKSPACE / "scratch" / "experiments",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor: old broken config attempt (wrong parameter names)
broken_config = {
    "NOISE_LEVEL": 0.5,
    "ACTIVITY_MULTIPLIER": 3,
    "DAILY_THOUGHTS": 150,
    "burst_offset": 999,  # wrong key name
    "memory_slots": 5
}
(WORKSPACE / "deployment" / "docker" / "configs" / "mindcore_config_BROKEN.json").write_text(
    json.dumps(broken_config, indent=2)
)

# Distractor: old integration notes
(WORKSPACE / "integration" / "openclaw" / "hooks" / "legacy_notes.txt").write_text(
    "Old notes: tried setting noise_multiplier=2 but it didn't work. Need to check main.py params.\n"
    "TODO: figure out how to pre-load topics into memory before cold start.\n"
    "TODO: the burst frequency control is somewhere in the engine config.\n"
)

# Distractor: fake session logs
for i in range(4):
    session = {
        "session_id": f"sess_{1000+i}",
        "user": f"beta_user_{i}",
        "impulses_fired": random.randint(10, 50),
        "categories": random.sample(["food", "social", "entertainment", "rest", "curiosity"], 3)
    }
    (WORKSPACE / "logs" / "2024-11" / "sessions" / f"session_{1000+i}.json").write_text(
        json.dumps(session, indent=2)
    )

# Distractor: analytics export
(WORKSPACE / "analytics" / "exports" / "impulse_stats_nov2024.csv").write_text(
    "category,count,avg_prob\nfood,312,0.67\nsocial,289,0.54\nentertainment,401,0.71\nrest,198,0.43\n"
)

# Distractor: fake user profiles
users = ["alice", "bob", "carol", "dave"]
interests_pool = [
    "coffee", "jazz music", "hiking", "machine learning", "cooking ramen",
    "vintage films", "yoga", "competitive gaming", "reading sci-fi", "bonsai gardening"
]
for user in users:
    profile = {
        "username": user,
        "interests": random.sample(interests_pool, 4),
        "active_hours": random.randint(6, 22),
        "mood_baseline": round(random.uniform(-0.3, 0.8), 2)
    }
    (WORKSPACE / "user_profiles" / "beta_testers" / f"{user}_profile.json").write_text(
        json.dumps(profile, indent=2)
    )

# Distractor: deployment yaml (wrong structure)
(WORKSPACE / "deployment" / "k8s" / "mindcore-deploy.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: mindcore\nspec:\n  replicas: 1\n"
    "  template:\n    spec:\n      containers:\n      - name: mindcore\n        env:\n"
    "        - name: BURST_LEVEL\n          value: '5'\n"  # wrong env var name
)

# Distractor: scratch experiment
(WORKSPACE / "scratch" / "experiments" / "noise_test.py").write_text(
    "# Experiment: tried directly patching noise amplitude\n"
    "# Result: doesn't affect firing rate, need the proper offset param\n"
    "import random\nprint(random.gauss(0, 1))\n"
)

# ── 3. Create the TASK INPUT: a messy user activity file ──────────────────
# The agent must read this to know what topics to seed into short-term memory
user_activity = {
    "user_id": "vip_user_zara",
    "export_timestamp": "2024-12-01T09:15:00Z",
    "recent_topics": [
        {"topic": "matcha latte recipes", "last_accessed": "2024-12-01T08:00:00Z", "engagement_score": 0.91},
        {"topic": "lo-fi study music", "last_accessed": "2024-12-01T07:30:00Z", "engagement_score": 0.85},
        {"topic": "weekend hiking trails", "last_accessed": "2024-11-30T20:00:00Z", "engagement_score": 0.78},
    ],
    "desired_engine_mode": "high_activity",
    "notes": "User wants the AI companion to feel very spontaneous and chatty. Pre-seed with her top interests."
}
(WORKSPACE / "user_profiles" / "vip" / "zara_activity_export.json").write_text(
    json.dumps(user_activity, indent=2)
)

# ── 4. Create the TASK OUTPUT placeholder directory ────────────────────────
(WORKSPACE / "output").mkdir(exist_ok=True)
(WORKSPACE / "output" / ".gitkeep").write_text("")

print("\n✓ Workspace generated.")
print(f"  MindCore cloned to: {MINDCORE}")
print(f"  Distractor files: {len(list(WORKSPACE.rglob('*')))} total items")
print(f"  Task input: {WORKSPACE / 'user_profiles' / 'vip' / 'zara_activity_export.json'}")