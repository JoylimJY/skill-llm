#!/usr/bin/env python3
"""
Evaluation script for the memory-pruner task.
Checks three operations:
  1. wake-state.md pruned to last 150 lines (not first 150)
  2. mission-log.md compacted (entries before 2025-06-01 removed)
  3. rover_alpha/logs has exactly 5 files (the 5 newest by mtime)
"""

import sys
import json
import os
import time
from pathlib import Path
from datetime import datetime

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weight_per_check = 1.0 / 3.0

    # ─── CHECK 1: wake-state.md pruned to last 150 lines ───────────────────────
    check1_name = "wake-state.md pruned to last 150 lines"
    try:
        wake_path = ws / "agents/rover_alpha/memory/wake-state.md"
        if not wake_path.exists():
            checks.append({"name": check1_name, "passed": False, "detail": "File not found: agents/rover_alpha/memory/wake-state.md"})
        else:
            lines = wake_path.read_text().splitlines()
            line_count = len(lines)
            # Must have exactly 150 lines (last 150 of 420)
            if line_count != 150:
                checks.append({
                    "name": check1_name, "passed": False,
                    "detail": f"Expected 150 lines, got {line_count}. File was not pruned to exactly 150 lines."
                })
            else:
                # Verify it's the LAST 150 lines (lines should be from 2026-01-03 onward roughly)
                # The 421st line in 0-indexed is line[270] original → kept are lines[270:420]
                # Each line starts with a timestamp. Line 271 (index 270) = day 270*2 hours from 2025-01-01
                # Let's verify the FIRST kept line is timestamp >= line 271 of original
                # Simpler: check first line date is not 2025-01-01 (that would be the very first original line)
                first_line = lines[0].strip()
                # Original line 1 starts with [2025-01-01 06:00]
                # Last 150 lines start at index 270 → timestamp = 2025-01-01 06:00 + 270*2h = +540h = +22.5 days
                # = ~2025-01-23
                if first_line.startswith("[2025-01-01"):
                    checks.append({
                        "name": check1_name, "passed": False,
                        "detail": f"File has 150 lines but starts with earliest entry — appears to be FIRST 150, not LAST 150. First line: {first_line[:60]}"
                    })
                else:
                    checks.append({
                        "name": check1_name, "passed": True,
                        "detail": f"Correct: 150 lines retained (last 150). First kept line: {first_line[:60]}"
                    })
                    total_score += weight_per_check
    except Exception as e:
        checks.append({"name": check1_name, "passed": False, "detail": f"Exception: {e}"})

    # ─── CHECK 2: mission-log.md compacted (remove entries before 2025-06-01) ──
    check2_name = "mission-log.md entries before 2025-06-01 removed"
    try:
        log_path = ws / "agents/base_station/memory/mission-log.md"
        if not log_path.exists():
            checks.append({"name": check2_name, "passed": False, "detail": "File not found: agents/base_station/memory/mission-log.md"})
        else:
            lines = log_path.read_text().splitlines()
            cutoff = datetime(2025, 6, 1)
            old_entries_remaining = []
            new_entries_present = []
            missing_new = []

            # Expected old entries (should be gone)
            old_dates = ["2025-01-15","2025-02-03","2025-02-28","2025-03-10",
                         "2025-04-05","2025-04-22","2025-05-01","2025-05-17","2025-05-31"]
            # Expected new entries (must remain)
            new_dates = ["2025-06-01","2025-06-15","2025-07-04","2025-07-20",
                         "2025-08-08","2025-09-03","2025-10-12","2025-11-01",
                         "2025-11-28","2025-12-15"]

            file_content = log_path.read_text()

            # Check old entries are gone
            for d in old_dates:
                if f"[{d}]" in file_content:
                    old_entries_remaining.append(d)

            # Check new entries are present
            for d in new_dates:
                if f"[{d}]" not in file_content:
                    missing_new.append(d)

            if old_entries_remaining:
                checks.append({
                    "name": check2_name, "passed": False,
                    "detail": f"Old entries still present (should be removed): {old_entries_remaining}"
                })
            elif missing_new:
                checks.append({
                    "name": check2_name, "passed": False,
                    "detail": f"New entries were incorrectly removed (should be kept): {missing_new}"
                })
            else:
                checks.append({
                    "name": check2_name, "passed": True,
                    "detail": f"Correct: all 9 old entries removed, all 10 new entries retained."
                })
                total_score += weight_per_check
    except Exception as e:
        checks.append({"name": check2_name, "passed": False, "detail": f"Exception: {e}"})

    # ─── CHECK 3: rover_alpha/logs has exactly 5 files (the 5 newest) ──────────
    check3_name = "rover_alpha/logs pruned to 5 newest files"
    try:
        log_dir = ws / "agents/rover_alpha/logs"
        if not log_dir.exists():
            checks.append({"name": check3_name, "passed": False, "detail": "Directory not found: agents/rover_alpha/logs"})
        else:
            remaining = [f for f in log_dir.iterdir() if f.is_file()]
            remaining_names = sorted([f.name for f in remaining])

            if len(remaining) != 5:
                checks.append({
                    "name": check3_name, "passed": False,
                    "detail": f"Expected exactly 5 files remaining, got {len(remaining)}: {remaining_names}"
                })
            else:
                # The 5 newest files should be session_008.log through session_012.log
                # (files were created with mtime = base_time + i*3600, so session_008 has highest 5 mtimes)
                expected_survivors = {f"session_{i:03d}.log" for i in range(8, 13)}
                actual_names = {f.name for f in remaining}
                if actual_names == expected_survivors:
                    checks.append({
                        "name": check3_name, "passed": True,
                        "detail": f"Correct: 5 newest files retained: {sorted(actual_names)}"
                    })
                    total_score += weight_per_check
                else:
                    unexpected = actual_names - expected_survivors
                    missing = expected_survivors - actual_names
                    checks.append({
                        "name": check3_name, "passed": False,
                        "detail": (
                            f"Wrong files kept. Expected {sorted(expected_survivors)}, "
                            f"got {sorted(actual_names)}. "
                            f"Unexpected: {sorted(unexpected)}, Missing: {sorted(missing)}. "
                            "Hint: circular buffer should keep the 5 NEWEST by modification time."
                        )
                    })
    except Exception as e:
        checks.append({"name": check3_name, "passed": False, "detail": f"Exception: {e}"})

    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": round(total_score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)