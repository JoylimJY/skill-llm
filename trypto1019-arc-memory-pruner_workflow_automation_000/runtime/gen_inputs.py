#!/usr/bin/env python3
"""
Generate the sandbox workspace for the memory-pruner evaluation task.
Simulates a robotics lab agent memory directory with bloated files and a messy log directory.
"""

import os
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ─── Directory Structure ───────────────────────────────────────────────────────
dirs = [
    "agents/rover_alpha/logs",
    "agents/rover_alpha/memory",
    "agents/rover_beta/logs",
    "agents/rover_beta/memory",
    "agents/base_station/logs",
    "agents/base_station/memory",
    "config",
    "missions/q1_2025",
    "missions/q2_2025",
    "reports",
    "scripts",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files (non-target) ─────────────────────────────────────────────
distractor_contents = {
    "config/robot_params.yaml": "max_speed: 1.2\narm_reach: 0.8\nbattery_warn: 20\n",
    "config/network.conf": "[wifi]\nssid=lab_net\nchannel=6\n",
    "missions/q1_2025/mission_brief.txt": "Objective: Terrain mapping sector 7.\nDuration: 14 days.\nStatus: COMPLETE\n",
    "missions/q2_2025/mission_brief.txt": "Objective: Sample collection grid B.\nDuration: 21 days.\nStatus: IN PROGRESS\n",
    "reports/quarterly_summary.md": "# Q1 Summary\nAll rovers performed within spec.\n",
    "agents/rover_beta/memory/calibration.dat": "imu_offset=0.003\nlidar_bias=0.12\n",
    "agents/base_station/memory/antenna_log.txt": "Bearing: 273.4\nSignal: -67dBm\n",
    "tmp/scratch.txt": "delete me\ntemp data\n",
    "agents/rover_beta/logs/placeholder.txt": "no logs yet\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'deploying...'\n",
}
for rel_path, content in distractor_contents.items():
    (WORKSPACE / rel_path).write_text(content)

# ─── TARGET FILE 1: rover_alpha wake-state.md (bloated, needs pruning) ─────────
# Must be pruned to last 150 lines. Generate 420 lines.
state_lines = []
base_date = datetime(2025, 1, 1, 6, 0, 0)
for i in range(420):
    ts = base_date + timedelta(hours=i * 2)
    state_lines.append(f"[{ts.strftime('%Y-%m-%d %H:%M')}] STATUS: battery={random.randint(20,100)}% | loc=({random.uniform(-10,10):.2f},{random.uniform(-10,10):.2f}) | task=patrol_sector_{random.randint(1,9)}\n")

wake_state_path = WORKSPACE / "agents/rover_alpha/memory/wake-state.md"
wake_state_path.write_text("".join(state_lines))
print(f"[gen] wake-state.md: {len(state_lines)} lines written")

# ─── TARGET FILE 2: base_station mission-log.md (needs date compaction) ────────
# Remove entries BEFORE 2025-06-01. Mix of old and new entries.
log_entries = []
# Old entries (before cutoff 2025-06-01) — should be removed
old_dates = [
    datetime(2025, 1, 15), datetime(2025, 2, 3), datetime(2025, 2, 28),
    datetime(2025, 3, 10), datetime(2025, 4, 5), datetime(2025, 4, 22),
    datetime(2025, 5, 1), datetime(2025, 5, 17), datetime(2025, 5, 31),
]
for d in old_dates:
    log_entries.append((d, f"[{d.strftime('%Y-%m-%d')}] MISSION: routine_check | result=nominal | agent=base_station\n"))

# New entries (on or after 2025-06-01) — must be KEPT
new_dates = [
    datetime(2025, 6, 1), datetime(2025, 6, 15), datetime(2025, 7, 4),
    datetime(2025, 7, 20), datetime(2025, 8, 8), datetime(2025, 9, 3),
    datetime(2025, 10, 12), datetime(2025, 11, 1), datetime(2025, 11, 28),
    datetime(2025, 12, 15),
]
for d in new_dates:
    log_entries.append((d, f"[{d.strftime('%Y-%m-%d')}] MISSION: active_ops | result=success | agent=base_station\n"))

log_entries.sort(key=lambda x: x[0])
mission_log_path = WORKSPACE / "agents/base_station/memory/mission-log.md"
mission_log_path.write_text("".join(e[1] for e in log_entries))
print(f"[gen] mission-log.md: {len(log_entries)} entries written ({len(old_dates)} old, {len(new_dates)} new)")

# ─── TARGET DIR: rover_alpha/logs (needs circular buffer, keep last 5) ─────────
# Create 12 log files with different timestamps (oldest should be deleted)
log_dir = WORKSPACE / "agents/rover_alpha/logs"
log_files = []
base_time = time.time() - (12 * 3600)  # 12 hours ago
for i in range(12):
    fname = f"session_{i+1:03d}.log"
    fpath = log_dir / fname
    fpath.write_text(
        f"# Session {i+1}\n"
        f"start_time: {datetime.fromtimestamp(base_time + i*3600).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"events: {random.randint(50,500)}\n"
        f"errors: {random.randint(0,5)}\n"
    )
    # Set mtime explicitly so ordering is deterministic
    mtime = base_time + i * 3600
    os.utime(fpath, (mtime, mtime))
    log_files.append((fname, mtime))
    print(f"[gen] log file: {fname} mtime={datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')}")

# Record which files should survive (last 5 by mtime = sessions 8..12)
surviving = sorted(log_files, key=lambda x: x[1])[-5:]
print(f"[gen] Expected survivors after prune-logs --keep 5: {[f[0] for f in surviving]}")

print("\n[gen] Workspace generation complete.")
print(f"[gen] Targets:")
print(f"  1. Prune {wake_state_path} to last 150 lines")
print(f"  2. Compact {mission_log_path} removing entries before 2025-06-01")
print(f"  3. Prune-logs {log_dir} keeping last 5 files")