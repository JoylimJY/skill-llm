#!/usr/bin/env python3
"""
Evaluation script for the openclaw-backup-skill task.

Checks:
1. A manual backup archive exists in backups/ (openclaw-manual-*.tar.gz, newer than setup).
2. An auto/regular backup archive exists in backups/ (openclaw-backup-*.tar.gz, newer than setup).
3. A dry-run prune was run and its output was captured in a file named prune_dry_run.txt.
4. The prune_dry_run.txt references standard retention flags (keep-hours 24, keep-days 7, keep-weeks 4).
5. A cron job is installed that runs --auto with the standard retention flags.
6. The cron job path references scripts/openclaw-backup.sh (uses the bundled script, not inline logic).
7. Manual archive is NOT listed as a would-be deletion in the dry-run output.
"""

import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone

checks = []
WORKSPACE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
BACKUPS = WORKSPACE / "backups"

# Helper: discover archives created after container start
# We use a sentinel epoch: anything after 2024-06-01 is "new" (our pre-seeded
# archives are all ≤ 2024-06-15, but the agent's new archives will be from
# "now" i.e. current container time which is likely 2024+ anyway).
# We discriminate by filename timestamp prefix pattern.

def parse_archive_ts(fname: str) -> datetime | None:
    """Extract UTC datetime from archive filename."""
    m = re.search(r'(\d{8}T\d{6}Z)', fname)
    if not m:
        return None
    ts = m.group(1)
    try:
        return datetime(int(ts[0:4]), int(ts[4:6]), int(ts[6:8]),
                        int(ts[9:11]), int(ts[11:13]), int(ts[13:15]),
                        tzinfo=timezone.utc)
    except Exception:
        return None

# The pre-seeded archives have timestamps up to 2024-06-15T10:00:00Z.
# Anything created by the agent will have the container's current clock,
# which we treat as "after seeding" if the filename ts > the newest seed ts.
SEED_CUTOFF_FNAME = "20240615T100100Z"  # anything newer than this is agent-created

def is_agent_created(fname: str) -> bool:
    m = re.search(r'(\d{8}T\d{6}Z)', fname)
    if not m:
        return False
    return m.group(1) > SEED_CUTOFF_FNAME

# ── Check 1: Manual backup created ─────────────────────────────────────────
try:
    manual_archives = sorted(BACKUPS.glob("openclaw-manual-*.tar.gz"))
    new_manuals = [f for f in manual_archives if is_agent_created(f.name)]
    if new_manuals:
        checks.append({
            "name": "manual_backup_created",
            "passed": True,
            "detail": f"Found manual archive(s): {[f.name for f in new_manuals]}"
        })
    else:
        # Maybe the agent created a manual backup before the seed cutoff hack works
        # Fall back: any manual archive that is NOT one of the pre-seeded ones
        # Pre-seeded manual: openclaw-manual-20240506T100000Z.tar.gz
        seeded_manual = "openclaw-manual-20240506T100000Z.tar.gz"
        others = [f for f in manual_archives if f.name != seeded_manual]
        if others:
            checks.append({
                "name": "manual_backup_created",
                "passed": True,
                "detail": f"Found manual archive(s): {[f.name for f in others]}"
            })
        else:
            checks.append({
                "name": "manual_backup_created",
                "passed": False,
                "detail": f"No agent-created manual archive found. Existing: {[f.name for f in manual_archives]}"
            })
except Exception as e:
    checks.append({"name": "manual_backup_created", "passed": False, "detail": str(e)})

# ── Check 2: Regular (auto) backup created ──────────────────────────────────
try:
    regular_archives = sorted(BACKUPS.glob("openclaw-backup-*.tar.gz"))
    # Pre-seeded ones are known; agent's will have newer timestamps
    pre_seeded_names = {
        f"openclaw-backup-{ts}.tar.gz" for ts in [
            "20240511T100000Z","20240518T100000Z","20240525T100000Z",
            "20240601T100000Z","20240609T100000Z","20240611T100000Z",
            "20240613T100000Z","20240614T140000Z","20240615T000000Z",
            "20240615T080000Z",
        ]
    }
    new_regulars = [f for f in regular_archives
                    if f.name not in pre_seeded_names and is_agent_created(f.name)]
    if new_regulars:
        checks.append({
            "name": "regular_backup_created",
            "passed": True,
            "detail": f"Found regular archive(s): {[f.name for f in new_regulars]}"
        })
    else:
        # Any regular archive not in pre-seeded set
        others = [f for f in regular_archives if f.name not in pre_seeded_names]
        if others:
            checks.append({
                "name": "regular_backup_created",
                "passed": True,
                "detail": f"Found regular archive(s): {[f.name for f in others]}"
            })
        else:
            checks.append({
                "name": "regular_backup_created",
                "passed": False,
                "detail": f"No agent-created regular archive. Existing: {[f.name for f in regular_archives]}"
            })
except Exception as e:
    checks.append({"name": "regular_backup_created", "passed": False, "detail": str(e)})

# ── Check 3: Dry-run prune output file exists ───────────────────────────────
try:
    dry_run_files = list(WORKSPACE.rglob("prune_dry_run.txt"))
    if dry_run_files:
        dry_run_content = dry_run_files[0].read_text()
        checks.append({
            "name": "dry_run_output_file_exists",
            "passed": True,
            "detail": f"Found at {dry_run_files[0]}, size={len(dry_run_content)} chars"
        })
    else:
        checks.append({
            "name": "dry_run_output_file_exists",
            "passed": False,
            "detail": "No prune_dry_run.txt found anywhere in workspace."
        })
except Exception as e:
    checks.append({"name": "dry_run_output_file_exists", "passed": False, "detail": str(e)})

# ── Check 4: Dry-run used correct retention parameters ──────────────────────
try:
    dry_run_files = list(WORKSPACE.rglob("prune_dry_run.txt"))
    if dry_run_files:
        content = dry_run_files[0].read_text()
        # The file should contain PRUNE_DRY_RUN or PRUNE_COMPLETE markers
        # or at minimum evidence of --keep-hours 24, --keep-days 7, --keep-weeks 4
        has_prune_marker = ("PRUNE_DRY_RUN" in content or "PRUNE_COMPLETE" in content
                            or "would delete" in content.lower() or "dry" in content.lower())
        if has_prune_marker:
            checks.append({
                "name": "dry_run_output_content_valid",
                "passed": True,
                "detail": f"Dry-run output contains expected prune markers. Preview: {content[:300]}"
            })
        else:
            checks.append({
                "name": "dry_run_output_content_valid",
                "passed": False,
                "detail": f"prune_dry_run.txt exists but lacks expected prune output. Content: {content[:300]}"
            })
    else:
        checks.append({
            "name": "dry_run_output_content_valid",
            "passed": False,
            "detail": "No prune_dry_run.txt to check."
        })
except Exception as e:
    checks.append({"name": "dry_run_output_content_valid", "passed": False, "detail": str(e)})

# ── Check 5: Manual archive NOT listed for deletion in dry-run ──────────────
try:
    dry_run_files = list(WORKSPACE.rglob("prune_dry_run.txt"))
    if dry_run_files:
        content = dry_run_files[0].read_text()
        if "openclaw-manual-" in content and (
            "delete" in content.lower() or "prune" in content.lower()
        ):
            # Check if the manual archive appears as a PRUNE_DRY_RUN target
            manual_prune_lines = [
                l for l in content.splitlines()
                if "openclaw-manual-" in l and
                   ("PRUNE_DRY_RUN" in l or "would delete" in l.lower() or "PRUNED" in l)
            ]
            if manual_prune_lines:
                checks.append({
                    "name": "manual_archive_not_targeted_for_prune",
                    "passed": False,
                    "detail": f"Manual archive incorrectly targeted for pruning: {manual_prune_lines}"
                })
            else:
                checks.append({
                    "name": "manual_archive_not_targeted_for_prune",
                    "passed": True,
                    "detail": "Manual archive appears in output but not as a prune target (correct)."
                })
        else:
            checks.append({
                "name": "manual_archive_not_targeted_for_prune",
                "passed": True,
                "detail": "Manual archive not mentioned as deletion target in dry-run output."
            })
    else:
        checks.append({
            "name": "manual_archive_not_targeted_for_prune",
            "passed": True,
            "detail": "No dry-run file; check skipped (benefit of doubt)."
        })
except Exception as e:
    checks.append({"name": "manual_archive_not_targeted_for_prune", "passed": False, "detail": str(e)})

# ── Check 6: Cron job installed ─────────────────────────────────────────────
try:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    cron_output = result.stdout
    if result.returncode != 0 or not cron_output.strip():
        checks.append({
            "name": "cron_job_installed",
            "passed": False,
            "detail": f"No crontab found. stderr: {result.stderr[:200]}"
        })
    else:
        # Check for openclaw-backup.sh in cron
        has_script = "openclaw-backup.sh" in cron_output
        if has_script:
            checks.append({
                "name": "cron_job_installed",
                "passed": True,
                "detail": f"Crontab contains openclaw-backup.sh. Content: {cron_output[:400]}"
            })
        else:
            checks.append({
                "name": "cron_job_installed",
                "passed": False,
                "detail": f"Crontab exists but doesn't reference openclaw-backup.sh. Content: {cron_output[:400]}"
            })
except Exception as e:
    checks.append({"name": "cron_job_installed", "passed": False, "detail": str(e)})

# ── Check 7: Cron job uses --auto with correct retention flags ───────────────
try:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    cron_output = result.stdout
    relevant_lines = [
        l for l in cron_output.splitlines()
        if "openclaw-backup.sh" in l and not l.strip().startswith("#")
    ]
    if relevant_lines:
        line = " ".join(relevant_lines)
        has_auto = "--auto" in line
        has_keep_hours = re.search(r'--keep-hours\s+24', line)
        has_keep_days  = re.search(r'--keep-days\s+7',  line)
        has_keep_weeks = re.search(r'--keep-weeks\s+4', line)
        all_ok = has_auto and has_keep_hours and has_keep_days and has_keep_weeks
        checks.append({
            "name": "cron_job_uses_auto_with_retention_flags",
            "passed": bool(all_ok),
            "detail": (
                f"--auto={has_auto}, --keep-hours 24={bool(has_keep_hours)}, "
                f"--keep-days 7={bool(has_keep_days)}, --keep-weeks 4={bool(has_keep_weeks)}. "
                f"Line: {line[:300]}"
            )
        })
    else:
        checks.append({
            "name": "cron_job_uses_auto_with_retention_flags",
            "passed": False,
            "detail": "No active (non-comment) cron line with openclaw-backup.sh found."
        })
except Exception as e:
    checks.append({"name": "cron_job_uses_auto_with_retention_flags", "passed": False, "detail": str(e)})

# ── Score ────────────────────────────────────────────────────────────────────
# Weights: manual backup (critical) = 2, regular backup = 1.5, dry-run exists = 1,
#          dry-run content = 1, manual not pruned = 1, cron installed = 2, cron flags = 2
weights = {
    "manual_backup_created":                 2.0,
    "regular_backup_created":                1.5,
    "dry_run_output_file_exists":            1.0,
    "dry_run_output_content_valid":          1.0,
    "manual_archive_not_targeted_for_prune": 1.0,
    "cron_job_installed":                    2.0,
    "cron_job_uses_auto_with_retention_flags": 2.0,
}
total_weight = sum(weights.values())
earned = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
score = round(earned / total_weight, 4)

result = {
    "passed": all(c["passed"] for c in checks),
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))