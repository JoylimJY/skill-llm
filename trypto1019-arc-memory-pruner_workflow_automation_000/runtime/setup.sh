#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"
SKILL_BASE="${WORKSPACE}/skill"

# Create the skill scripts directory
mkdir -p "${SKILL_BASE}/scripts"

# Write the memory_pruner.py script
cat > "${SKILL_BASE}/scripts/memory_pruner.py" << 'PYEOF'
#!/usr/bin/env python3
"""
memory_pruner.py — Keep agent memory lean.
Supports: prune, prune-logs, compact, stats
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime


def cmd_prune(args):
    fpath = Path(args.file).expanduser()
    if not fpath.exists():
        print(f"ERROR: File not found: {fpath}", file=sys.stderr)
        sys.exit(1)

    lines = fpath.read_text().splitlines(keepends=True)
    total = len(lines)
    keep = lines[-args.max_lines:] if total > args.max_lines else lines
    removed = total - len(keep)

    if args.dry_run:
        print(f"[dry-run] Would remove {removed} lines from {fpath} (keeping last {args.max_lines} of {total})")
        return

    fpath.write_text("".join(keep))
    print(f"Pruned {fpath}: removed {removed} lines, kept {len(keep)} (last {args.max_lines} of {total})")


def cmd_prune_logs(args):
    dpath = Path(args.dir).expanduser()
    if not dpath.is_dir():
        print(f"ERROR: Directory not found: {dpath}", file=sys.stderr)
        sys.exit(1)

    # Gather all files (not subdirs), sort by mtime ascending (oldest first)
    files = [(f, f.stat().st_mtime) for f in dpath.iterdir() if f.is_file()]
    files.sort(key=lambda x: x[1])  # oldest first

    if len(files) <= args.keep:
        print(f"No pruning needed: {len(files)} files <= keep={args.keep}")
        return

    to_delete = files[:-args.keep]  # everything except last N

    if args.dry_run:
        print(f"[dry-run] Would delete {len(to_delete)} files from {dpath}:")
        for f, _ in to_delete:
            print(f"  - {f.name}")
        return

    for f, _ in to_delete:
        f.unlink()
        print(f"Deleted: {f.name}")
    print(f"prune-logs: kept last {args.keep} files, deleted {len(to_delete)}")


def cmd_compact(args):
    fpath = Path(args.file).expanduser()
    if not fpath.exists():
        print(f"ERROR: File not found: {fpath}", file=sys.stderr)
        sys.exit(1)

    try:
        cutoff = datetime.strptime(args.remove_before, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Invalid date format for --remove-before: {args.remove_before}. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    lines = fpath.read_text().splitlines(keepends=True)
    kept = []
    removed = 0

    for line in lines:
        # Try to parse a leading date [YYYY-MM-DD]
        stripped = line.strip()
        if stripped.startswith("[") and len(stripped) >= 12:
            date_str = stripped[1:11]
            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                if entry_date < cutoff:
                    removed += 1
                    continue
            except ValueError:
                pass  # Not a date-prefixed line; keep it
        kept.append(line)

    if args.dry_run:
        print(f"[dry-run] Would remove {removed} entries from {fpath} (before {args.remove_before})")
        return

    fpath.write_text("".join(kept))
    print(f"Compacted {fpath}: removed {removed} entries before {args.remove_before}, kept {len(kept)}")


def cmd_stats(args):
    dpath = Path(args.dir).expanduser()
    if not dpath.is_dir():
        print(f"ERROR: Directory not found: {dpath}", file=sys.stderr)
        sys.exit(1)

    total_bytes = 0
    print(f"Memory stats for: {dpath}")
    for fpath in sorted(dpath.rglob("*")):
        if fpath.is_file():
            size = fpath.stat().st_size
            total_bytes += size
            print(f"  {fpath.relative_to(dpath)}: {size} bytes")
    print(f"Total: {total_bytes} bytes ({total_bytes/1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Memory Pruner — keep agent memory lean.")
    sub = parser.add_subparsers(dest="command", required=True)

    # prune
    p_prune = sub.add_parser("prune", help="Keep last N lines of a file")
    p_prune.add_argument("--file", required=True)
    p_prune.add_argument("--max-lines", type=int, required=True)
    p_prune.add_argument("--dry-run", action="store_true")

    # prune-logs
    p_pl = sub.add_parser("prune-logs", help="Circular buffer for log directories")
    p_pl.add_argument("--dir", required=True)
    p_pl.add_argument("--keep", type=int, required=True)
    p_pl.add_argument("--dry-run", action="store_true")

    # compact
    p_compact = sub.add_parser("compact", help="Remove date-prefixed entries older than cutoff")
    p_compact.add_argument("--file", required=True)
    p_compact.add_argument("--remove-before", required=True)
    p_compact.add_argument("--dry-run", action="store_true")

    # stats
    p_stats = sub.add_parser("stats", help="Overview of memory file sizes")
    p_stats.add_argument("--dir", required=True)

    args = parser.parse_args()

    if args.command == "prune":
        cmd_prune(args)
    elif args.command == "prune-logs":
        cmd_prune_logs(args)
    elif args.command == "compact":
        cmd_compact(args)
    elif args.command == "stats":
        cmd_stats(args)


if __name__ == "__main__":
    main()
PYEOF

chmod +x "${SKILL_BASE}/scripts/memory_pruner.py"
echo "[setup] memory_pruner.py installed at ${SKILL_BASE}/scripts/memory_pruner.py"
echo "[setup] SKILL_BASE=${SKILL_BASE}"
echo "[setup] Setup complete."