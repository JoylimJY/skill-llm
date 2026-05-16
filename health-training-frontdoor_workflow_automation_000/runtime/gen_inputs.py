import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor directory structure ---

dirs = [
    "skills/health-training-frontdoor/scripts",
    "skills/health-training-frontdoor/reference",
    "skills/health-training-frontdoor/memory",
    "fitbit-connector/scripts",
    "fitbit-connector/cache",
    "fitbit-connector/logs",
    "reference/practical-programming",
    "memory",
    "logs/sessions",
    "logs/errors",
    "config/profiles",
    "config/schedules",
    "data/raw/hrv",
    "data/raw/sleep",
    "data/processed",
    "reports/archive",
    "tmp",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# Fake training log
with open(os.path.join(workspace, "logs/sessions/session_2024_03_01.log"), "w") as f:
    f.write("Session: Squat 5x5 @ 100kg\nDeadlift 1x5 @ 140kg\nPress 5x5 @ 60kg\n")

with open(os.path.join(workspace, "logs/sessions/session_2024_03_03.log"), "w") as f:
    f.write("Session: Power Clean 5x3 @ 75kg\nSquat 5x5 @ 102.5kg\n")

with open(os.path.join(workspace, "logs/errors/connector_error_20240301.log"), "w") as f:
    f.write("ERROR: Token refresh failed at 03:14 UTC\nRetrying...\nFailed after 3 attempts.\n")

# Fake old config
with open(os.path.join(workspace, "config/profiles/joao_profile.json"), "w") as f:
    json.dump({
        "name": "Joao",
        "age": 34,
        "weight_kg": 82.5,
        "goal": "intermediate_strength",
        "preferred_source": "fitbit"
    }, f, indent=2)

with open(os.path.join(workspace, "config/schedules/weekly_plan.json"), "w") as f:
    json.dump({
        "monday": "squat_press",
        "wednesday": "squat_deadlift",
        "friday": "squat_press_variant",
        "saturday": "optional_conditioning"
    }, f, indent=2)

# Fake partial cache data (distractor)
with open(os.path.join(workspace, "fitbit-connector/cache/last_sync.json"), "w") as f:
    json.dump({
        "last_sync_utc": "2024-03-04T06:00:00Z",
        "records": 14,
        "status": "stale"
    }, f, indent=2)

with open(os.path.join(workspace, "fitbit-connector/cache/hrv_cache.csv"), "w") as f:
    f.write("date,rmssd\n2024-03-01,42.1\n2024-03-02,38.7\n2024-03-03,45.2\n")

# Fake fitbit_tools.py stub (distractor - not the real one but present)
with open(os.path.join(workspace, "fitbit-connector/scripts/fitbit_tools.py"), "w") as f:
    f.write("""#!/usr/bin/env python3
# fitbit_tools.py - canonical backend (stub distractor)
# This file is the backend; use the front door instead.
import sys
print('ERROR: Do not call this directly. Use the front door.')
sys.exit(1)
""")

# Fake reference files
with open(os.path.join(workspace, "reference/practical-programming/INDEX.md"), "w") as f:
    f.write("# Practical Programming Index\n\nChapter 1: Physiology\nChapter 2: Novice\nChapter 3: Intermediate\n")

with open(os.path.join(workspace, "memory/training-continuity.md"), "w") as f:
    f.write("# Training Continuity\n\nLast squat: 102.5kg x5x5\nLast deadlift: 142.5kg x1x5\nHRV trend: slightly declining\n")

# Old stale report (distractor)
with open(os.path.join(workspace, "reports/archive/health_snapshot_OLD.json"), "w") as f:
    json.dump({
        "generated": "2024-02-15",
        "note": "OUTDATED - do not use",
        "auth": {"status": "expired"},
        "recovery": {}
    }, f, indent=2)

# Fake tmp files
with open(os.path.join(workspace, "tmp/scratch.txt"), "w") as f:
    f.write("scratch notes\ndays=7\nforget this\n")

with open(os.path.join(workspace, "data/raw/hrv/hrv_raw_20240303.json"), "w") as f:
    json.dump({"date": "2024-03-03", "rmssd": 45.2, "source": "fitbit"}, f)

with open(os.path.join(workspace, "data/raw/sleep/sleep_20240303.json"), "w") as f:
    json.dump({"date": "2024-03-03", "sleep_minutes": 437, "sleep_score": 78}, f)

with open(os.path.join(workspace, "data/processed/weekly_averages.csv"), "w") as f:
    f.write("week,avg_hrv,avg_sleep_score\n2024-W08,41.2,76.4\n2024-W09,43.1,79.1\n")

# SKILL.md for the front door
with open(os.path.join(workspace, "skills/health-training-frontdoor/SKILL.md"), "w") as f:
    f.write("""---
name: health-training-frontdoor
description: Narrow first-class front door for live Fitbit/training retrieval via stable JSON actions.
---

# Health/Training Front Door

Use this when OpenClaw needs **live Fitbit/health/training data** in a stable, low-ambiguity way.

This is a thin, typed front door over the canonical Fitbit connector tooling.

## Why this exists

`fitbit_tools.py` is the canonical operational backend, but it still requires low-level CLI composition.
This front door provides a narrow action contract so agents can call one stable interface instead of assembling raw shell commands every time.

## Contract

Run:

- `node skills/health-training-frontdoor/scripts/request.js '{...json...}'`

Input JSON:

```json
{
  "action": "latest_recovery"
}
```

Supported actions:

- `auth_status`
- `latest_recovery`
- `quality_flags`
- `training_status`
- `training_window`
- `unified_latest`

Optional fields:

- `days` (integer)
- `ensureFresh` (boolean)
- `source` (for `unified_latest`, default `best`)

## Default behavior by action

- `latest_recovery`: fetches latest days of `hrv_rmssd,resting_hr,sleep_minutes,sleep_score,data_quality`; defaults `days=3`, `ensureFresh=true`
- `quality_flags`: defaults `days=7`
- `training_status`: defaults `days=14`, `ensureFresh=true`
- `training_window`: defaults `days=14`, `ensureFresh=true`
- `unified_latest`: defaults `days=14`, `source=best`

## Notes

- Output is compact JSON.
- This surface is read-only.
- Interpretation/coaching remains outside this skill.
""")

# request.js SKILL.md reference (so agents can find it)
with open(os.path.join(workspace, "skills/health-training-frontdoor/reference/actions.md"), "w") as f:
    f.write("# Actions Reference\nSee SKILL.md for full contract.\n")

print("Workspace generated successfully.")