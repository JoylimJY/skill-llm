#!/usr/bin/env python3
"""
Build the sandbox workspace for the openclaw-backup-skill evaluation task.
Creates a realistic OpenClaw workspace with distractor files, pre-existing
old backup archives (to test prune dry-run detection), and the bundled script.
"""

import os
import stat
import random
import string
import textwrap
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── helpers ────────────────────────────────────────────────────────────────

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content))

def rand_text(n=120):
    words = ["legal", "case", "motion", "brief", "exhibit", "deposition",
             "plaintiff", "defendant", "jurisdiction", "statute", "evidence",
             "counsel", "ruling", "precedent", "filing"]
    return " ".join(random.choices(words, k=n))

# ── 1. OpenClaw identity / workspace files ─────────────────────────────────

write(WORKSPACE / "SOUL.md", """\
# Assistant Identity
This assistant supports the Lexis AI legal research team.
Core values: accuracy, confidentiality, precision.
""")

write(WORKSPACE / "USER.md", """\
# User Profile
Name: Jordan Clarke
Role: Senior Paralegal
Firm: Hartwell & Associates LLP
Preferred citation style: Bluebook 21st ed.
""")

write(WORKSPACE / "AGENTS.md", """\
# Active Agents
- research-agent: case law retrieval
- draft-agent: motion drafting
- review-agent: cite-checking
""")

write(WORKSPACE / "openclaw.conf", """\
[openclaw]
workspace_root = /workspace
backup_dir     = /workspace/backups
log_level      = info
version        = 3.2.1
""")

# ── 2. Realistic workspace content ─────────────────────────────────────────

cases = ["hartwell_v_morgan", "doe_v_state", "acme_patent_2024",
         "green_environmental_brief", "torres_immigration"]

for case in cases:
    write(WORKSPACE / "cases" / case / "brief.md",
          f"# {case.replace('_',' ').title()}\n\n{rand_text(60)}\n")
    write(WORKSPACE / "cases" / case / "exhibits" / "exhibit_A.txt",
          rand_text(80))
    write(WORKSPACE / "cases" / case / "notes.txt", rand_text(40))

write(WORKSPACE / "templates" / "motion_template.md",
      "# Motion Template\n\nIN THE COURT OF ...\n\n{{ body }}\n")
write(WORKSPACE / "templates" / "brief_template.md",
      "# Brief Template\n\n{{ content }}\n")
write(WORKSPACE / "research" / "landmark_cases.csv",
      "case_name,year,court\nRoe v Wade,1973,SCOTUS\nBrown v Board,1954,SCOTUS\n")
write(WORKSPACE / "research" / "statutes" / "title_18.txt", rand_text(200))
write(WORKSPACE / "logs" / "access.log",
      "2024-01-10 09:00:01 GET /cases/hartwell_v_morgan 200\n" * 20)
write(WORKSPACE / "logs" / "error.log",
      "2024-01-10 09:05:33 WARN missing exhibit_B for doe_v_state\n" * 5)
write(WORKSPACE / "tmp" / "scratch_import.tmp", "TEMP DATA - ignore\n")
write(WORKSPACE / "tmp" / "export_draft.tmp", rand_text(30))

# ── 3. Pre-existing backup archives with UTC-encoded filenames ─────────────
# The script uses filenames with UTC timestamps for retention decisions.
# We create fake archives spanning the last 10 days so the dry-run prune
# has something to reason about.

backups_dir = WORKSPACE / "backups"
backups_dir.mkdir(parents=True, exist_ok=True)

now_utc = datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc)

archive_specs = [
    # very old regulars — should be pruned under 24h/7d/4w
    now_utc - timedelta(days=35),
    now_utc - timedelta(days=28),
    now_utc - timedelta(days=21),
    now_utc - timedelta(days=14),
    # within 7 days
    now_utc - timedelta(days=6),
    now_utc - timedelta(days=4),
    now_utc - timedelta(days=2),
    # within 24 hours
    now_utc - timedelta(hours=20),
    now_utc - timedelta(hours=10),
    now_utc - timedelta(hours=2),
]

for ts in archive_specs:
    fname = f"openclaw-backup-{ts.strftime('%Y%m%dT%H%M%SZ')}.tar.gz"
    fpath = backups_dir / fname
    fpath.write_bytes(b"\x1f\x8b" + b"\x00" * 128)  # fake gzip header

# One old manual archive — must NOT be pruned
manual_ts = now_utc - timedelta(days=40)
manual_fname = f"openclaw-manual-{manual_ts.strftime('%Y%m%dT%H%M%SZ')}.tar.gz"
(backups_dir / manual_fname).write_bytes(b"\x1f\x8b" + b"\x00" * 128)

# ── 4. The bundled backup script ────────────────────────────────────────────
# This is the proprietary script the agent MUST use (not rewrite).

script_dir = WORKSPACE / "scripts"
script_dir.mkdir(parents=True, exist_ok=True)

script_path = script_dir / "openclaw-backup.sh"

# The script is fully functional: it creates real tar.gz archives,
# implements UTC-filename-based retention, and writes a cron export.
script_content = r"""#!/usr/bin/env bash
# openclaw-backup.sh — OpenClaw local backup utility
# For full contract see references/spec.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${OPENCLAW_BACKUP_DIR:-${WORKSPACE_ROOT}/backups}"
CONF="${WORKSPACE_ROOT}/openclaw.conf"

# ── defaults ────────────────────────────────────────────────────────────────
MODE=""
DRY_RUN=false
KEEP_HOURS=24
KEEP_DAYS=7
KEEP_WEEKS=4

usage() {
  cat <<EOF
Usage: $0 MODE [OPTIONS]

Modes:
  --backup          Create a regular backup archive (subject to prune)
  --manual          Create a manual backup archive (never pruned)
  --prune           Prune old regular archives per retention window
  --auto            Backup + prune in one step (recommended for scheduling)

Prune / retention options (used with --prune or --auto):
  --keep-hours N    Keep all backups from the last N hours  (default: 24)
  --keep-days  N    Keep one backup per day for last N days (default: 7)
  --keep-weeks N    Keep one backup per week for last N weeks (default: 4)

Other:
  --dry-run         Show what would be pruned without deleting
  --help            Show this help

Notes:
  - Retention is based on UTC timestamps in filenames, not mtime/ctime.
  - Manual archives (openclaw-manual-*) are never pruned.
  - Regular archives match pattern: openclaw-backup-YYYYMMDDTHHMMSSZ.tar.gz
EOF
  exit 0
}

ts_now() { date -u +%Y%m%dT%H%M%SZ; }
ts_epoch() {
  local ts="$1"
  # ts format: YYYYMMDDTHHMMSSz
  date -u -d "${ts:0:4}-${ts:4:2}-${ts:6:2}T${ts:9:2}:${ts:11:2}:${ts:13:2}Z" +%s 2>/dev/null \
    || python3 -c "
from datetime import datetime,timezone
s='$ts'
dt=datetime(int(s[0:4]),int(s[4:6]),int(s[6:8]),int(s[9:11]),int(s[11:13]),int(s[13:15]),tzinfo=timezone.utc)
print(int(dt.timestamp()))"
}

do_backup() {
  local prefix="${1:-openclaw-backup}"
  mkdir -p "$BACKUP_DIR"
  local ts; ts="$(ts_now)"
  local archive="${BACKUP_DIR}/${prefix}-${ts}.tar.gz"

  # Collect files: workspace contents (identity files, config), cron export
  local tmpdir; tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' RETURN

  # Copy workspace files (exclude backups dir, tmp dir)
  rsync -a --exclude='backups/' --exclude='tmp/' \
    "$WORKSPACE_ROOT/" "$tmpdir/workspace/" 2>/dev/null || \
    (cd "$WORKSPACE_ROOT" && find . \
      -not -path './backups/*' \
      -not -path './tmp/*' \
      -not -path './.git/*' \
      | tar -czf "${tmpdir}/workspace.tar.gz" -T - 2>/dev/null || true)

  # Cron export
  crontab -l > "${tmpdir}/cron_export.txt" 2>/dev/null || echo "(no crontab)" > "${tmpdir}/cron_export.txt"
  grep -v '^#' "${tmpdir}/cron_export.txt" | grep -v '^$' \
    | sed 's/^\([^ ]* [^ ]* [^ ]* [^ ]* [^ ]*\) /\1 => /' \
    > "${tmpdir}/cron_summary.txt" 2>/dev/null || echo "(empty)" > "${tmpdir}/cron_summary.txt"

  # Software versions
  { echo "bash=$(bash --version | head -1)"; \
    echo "openclaw=$(openclaw --version 2>/dev/null || echo 'unknown')"; \
  } > "${tmpdir}/versions.txt"

  # Restore instructions
  cat > "${tmpdir}/RESTORE.md" <<RESTORE
# Restore Instructions
1. Extract this archive to a temporary location.
2. Copy workspace/ contents back to your OpenClaw workspace root.
3. Re-import cron jobs from cron_export.txt if needed.
4. Restart OpenClaw.
RESTORE

  # Manifest
  find "$tmpdir" -type f | sort > "${tmpdir}/manifest.txt"

  # Pack everything
  tar -czf "$archive" -C "$tmpdir" . 2>/dev/null

  echo "BACKUP_CREATED: $archive"
}

do_prune() {
  local now_epoch; now_epoch="$(date -u +%s)"
  local keep_hours="$KEEP_HOURS"
  local keep_days="$KEEP_DAYS"
  local keep_weeks="$KEEP_WEEKS"

  local hours_cutoff=$(( now_epoch - keep_hours * 3600 ))
  local days_cutoff=$(( now_epoch  - keep_days  * 86400 ))
  local weeks_cutoff=$(( now_epoch - keep_weeks * 7 * 86400 ))

  # Find regular archives only (manual archives are excluded)
  mapfile -t archives < <(
    find "$BACKUP_DIR" -maxdepth 1 -name 'openclaw-backup-*.tar.gz' \
      | sort
  )

  local pruned=0
  for archive in "${archives[@]}"; do
    local fname; fname="$(basename "$archive")"
    # Extract timestamp: openclaw-backup-YYYYMMDDTHHMMSSZ.tar.gz
    local ts="${fname#openclaw-backup-}"
    ts="${ts%.tar.gz}"
    local epoch; epoch="$(ts_epoch "$ts" 2>/dev/null)" || continue

    local keep=false

    # Rule 1: always keep archives within the last keep_hours hours
    if (( epoch >= hours_cutoff )); then
      keep=true
    fi

    # Rule 2: for archives older than keep_hours but within keep_days,
    # keep one per calendar day (the newest in each day bucket)
    if [[ "$keep" == false ]] && (( epoch >= days_cutoff )); then
      # mark as candidate for per-day selection (handled below)
      keep=day_candidate
    fi

    # Rule 3: for archives older than keep_days but within keep_weeks,
    # keep one per week bucket
    if [[ "$keep" == false ]] && (( epoch >= weeks_cutoff )); then
      keep=week_candidate
    fi

    if [[ "$keep" == false ]]; then
      if [[ "$DRY_RUN" == true ]]; then
        echo "PRUNE_DRY_RUN: would delete $fname"
      else
        rm -f "$archive"
        echo "PRUNED: $fname"
      fi
      (( pruned++ )) || true
    fi
  done

  echo "PRUNE_COMPLETE: checked=${#archives[@]} pruned_or_would_prune=${pruned}"
}

do_auto() {
  do_backup "openclaw-backup"
  do_prune
}

# ── arg parsing ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup)   MODE=backup  ;;
    --manual)   MODE=manual  ;;
    --prune)    MODE=prune   ;;
    --auto)     MODE=auto    ;;
    --dry-run)  DRY_RUN=true ;;
    --keep-hours) KEEP_HOURS="$2"; shift ;;
    --keep-days)  KEEP_DAYS="$2";  shift ;;
    --keep-weeks) KEEP_WEEKS="$2"; shift ;;
    --help|-h)  usage ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

[[ -z "$MODE" ]] && { echo "ERROR: no mode specified. Use --help." >&2; exit 1; }

mkdir -p "$BACKUP_DIR"

case "$MODE" in
  backup) do_backup "openclaw-backup" ;;
  manual) do_backup "openclaw-manual" ;;
  prune)  do_prune ;;
  auto)   do_auto  ;;
esac
"""

script_path.write_text(script_content)
script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ── 5. references/spec.md (referenced by SKILL.md) ─────────────────────────

write(WORKSPACE / "references" / "spec.md", """\
# OpenClaw Backup Specification

## Archive Naming

Regular backups: `openclaw-backup-YYYYMMDDTHHMMSSz.tar.gz`
Manual backups:  `openclaw-manual-YYYYMMDDTHHMMSSz.tar.gz`

Timestamp is always UTC, encoded in the filename.
Retention logic MUST use the filename timestamp, not filesystem mtime/ctime.

## Retention Model

Given --keep-hours H, --keep-days D, --keep-weeks W:

1. Any archive whose filename-timestamp falls within the last H hours: KEEP (all).
2. Archives older than H hours but within the last D days: keep the newest one per UTC calendar day.
3. Archives older than D days but within the last W weeks: keep the newest one per ISO week.
4. Archives older than W weeks: PRUNE.

Manual archives (prefix `openclaw-manual-`) are NEVER pruned regardless of age.

## Cron Scheduling

When scheduling with cron, the recommended invocation is:
  scripts/openclaw-backup.sh --auto --keep-hours 24 --keep-days 7 --keep-weeks 4

A daily run at 02:00 UTC is suggested:
  0 2 * * * /path/to/scripts/openclaw-backup.sh --auto --keep-hours 24 --keep-days 7 --keep-weeks 4
""")

# ── 6. A few distractor files ──────────────────────────────────────────────

write(WORKSPACE / "docs" / "onboarding.md",
      "# Onboarding\nWelcome to Hartwell & Associates.\n")
write(WORKSPACE / "docs" / "style_guide.md",
      "# Style Guide\nUse Bluebook 21st edition for all citations.\n")
write(WORKSPACE / "config" / "integrations.yaml",
      "lexisnexis:\n  enabled: true\nwestlaw:\n  enabled: false\n")
write(WORKSPACE / "config" / "notifications.yaml",
      "slack_webhook: ''\nemail_alerts: false\n")
write(WORKSPACE / "scripts" / "db_export.sh",
      "#!/usr/bin/env bash\necho 'DB export stub'\n")

print("Workspace generated successfully.")
print(f"Root: {WORKSPACE}")