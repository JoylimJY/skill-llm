import os
import json
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── 1. Clone / simulate the codex-quota skill being present in the workspace ──
skill_dir = workspace / "codex-quota"
skill_dir.mkdir(exist_ok=True)

# The actual codex-quota.py script content (faithful to SKILL.md description)
codex_quota_script = r'''#!/usr/bin/env python3
"""codex-quota: Check OpenAI Codex CLI rate limit status from session logs."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_latest_session_file(sessions_dir: Path):
    """Find the most recent .jsonl session file under YYYY/MM/DD/ structure."""
    candidates = sorted(sessions_dir.rglob("*.jsonl"))
    if not candidates:
        return None
    return candidates[-1]


def extract_rate_limits(session_file: Path):
    """Extract the last rate_limits object from token_count events."""
    last_rate_limits = None
    with open(session_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "token_count" and "rate_limits" in event:
                last_rate_limits = event["rate_limits"]
    return last_rate_limits


def format_countdown(reset_ts: float) -> str:
    now = datetime.now(timezone.utc).timestamp()
    delta = reset_ts - now
    if delta <= 0:
        return "already reset"
    h = int(delta // 3600)
    m = int((delta % 3600) // 60)
    return f"{h}h {m}m"


def format_output(rate_limits: dict, session_file: Path, as_json: bool):
    now = datetime.now(timezone.utc)
    file_stat = session_file.stat()
    age_seconds = now.timestamp() - file_stat.st_mtime
    age_minutes = int(age_seconds // 60)

    primary = rate_limits.get("primary", {})
    secondary = rate_limits.get("secondary", {})

    if as_json:
        output = {
            "source_file": str(session_file),
            "file_age_minutes": age_minutes,
            "primary_window": primary,
            "secondary_window": secondary,
        }
        print(json.dumps(output, indent=2))
        return

    print(f"Codex Quota Status")
    print(f"  Source: {session_file} ({age_minutes}m ago)")
    print()
    print(f"  Primary Window (5h):")
    print(f"    Used:  {primary.get('used', '?')} / {primary.get('limit', '?')}")
    print(f"    Reset: {format_countdown(primary.get('reset_at', 0))}")
    print()
    print(f"  Secondary Window (7d):")
    print(f"    Used:  {secondary.get('used', '?')} / {secondary.get('limit', '?')}")
    print(f"    Reset: {format_countdown(secondary.get('reset_at', 0))}")


def main():
    parser = argparse.ArgumentParser(description="Check OpenAI Codex CLI rate limit status")
    parser.add_argument("--fresh", action="store_true", help="Ping Codex first for live data")
    parser.add_argument("--all", action="store_true", help="Check all accounts")
    parser.add_argument("--yes", action="store_true", help="Confirm account switching")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    args = parser.parse_args()

    sessions_dir = Path.home() / ".codex" / "sessions"

    if args.fresh:
        # Trigger a codex invocation to refresh session data
        os.system("codex --version > /dev/null 2>&1 || true")

    if not sessions_dir.exists():
        print("No session directory found at ~/.codex/sessions/", file=sys.stderr)
        sys.exit(1)

    session_file = find_latest_session_file(sessions_dir)
    if session_file is None:
        print("No session files found.", file=sys.stderr)
        sys.exit(1)

    rate_limits = extract_rate_limits(session_file)
    if rate_limits is None:
        print("No rate_limits data found in session files.", file=sys.stderr)
        sys.exit(1)

    format_output(rate_limits, session_file, args.as_json)


if __name__ == "__main__":
    main()
'''

(skill_dir / "codex-quota.py").write_text(codex_quota_script)
(skill_dir / "codex-quota.py").chmod(0o755)

# SKILL.md
skill_md = """---
name: codex-quota
version: 1.2.2
homepage: https://github.com/odrobnik/codex-quota-skill
description: >
  Check OpenAI Codex CLI rate limit status (daily/weekly quotas) using local
  session logs. Portable Python script.

  Reads ~/.codex/sessions/ for quota data.
  When using --all --yes, it temporarily switches accounts by overwriting
  ~/.codex/auth.json (restored afterwards) to query each account.

  Uses the `codex` CLI for --fresh / --all.
metadata:
  openclaw:
    requires:
      bins: ["python3", "codex"]
---

# Skill: codex-quota

Check OpenAI Codex CLI rate limit status.

## Quick Reference

```bash
# Run the included Python script
./codex-quota.py

# Or if installed to PATH
codex-quota
```

## Options

```bash
codex-quota              # Show current quota (cached from latest session)
codex-quota --fresh      # Ping Codex first for live data
codex-quota --all --yes  # Update all accounts, save to /tmp/codex-quota-all.json
codex-quota --json       # Output as JSON
codex-quota --help       # Show help
```

## Setup

See SETUP.md for prerequisites and setup instructions.

## What It Shows

- **Primary Window** (5 hours) — Short-term rate limit
- **Secondary Window** (7 days) — Weekly rate limit
- Reset times in local timezone with countdown
- Source session file and age

## When to Use

- Before starting heavy Codex work (check weekly quota)
- When Codex seems slow (might be rate-limited)
- Monitoring quota across multiple accounts
"""
(skill_dir / "SKILL.md").write_text(skill_md)

setup_md = """# Codex Quota - Setup Instructions

## Prerequisites

### Required Software

- **Python 3** — For running the quota checker script
- **Codex CLI** — OpenAI Codex command-line client (required for `--fresh` and `--all` options)

No additional Python packages required. The skill uses only Python standard library modules.

### File Access

The skill reads from:
- `~/.codex/sessions/` — Codex session logs containing rate limit data
- `~/.codex/auth.json` — Current Codex authentication (for `--fresh` option)

## How It Works

Codex CLI logs rate limit information in every session file (`~/.codex/sessions/YYYY/MM/DD/*.jsonl`) as part of `token_count` events. This tool:

1. Finds the most recent session file
2. Extracts the last `rate_limits` object
3. Formats and displays it with:
   - **Primary Window** (5 hours) — Short-term rate limit
   - **Secondary Window** (7 days) — Weekly rate limit
   - Reset times in local timezone with countdown
   - Source session file and age

### Options

- **Default** — Show cached quota from latest session (instant, no API call)
- **`--fresh`** — Ping Codex API first for live data (requires `codex` CLI)
- **`--all --yes`** — Check quota for all saved accounts by temporarily switching between them
- **`--json`** — Output as JSON for programmatic use
"""
(skill_dir / "SETUP.md").write_text(setup_md)

# ── 2. Distractor files in workspace ──
distractor_dirs = [
    workspace / "projects" / "alpha" / "src",
    workspace / "projects" / "beta" / "config",
    workspace / "tools" / "monitoring" / "scripts",
    workspace / "tools" / "linting",
    workspace / "docs" / "api" / "v2",
    workspace / "logs" / "archived" / "2023",
    workspace / "tmp" / "scratch",
    workspace / "scripts" / "deploy",
    workspace / "config" / "envs",
    workspace / ".cache" / "quota-tool",
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = [
    (workspace / "projects" / "alpha" / "src" / "main.py", "# main app\nprint('hello')\n"),
    (workspace / "projects" / "alpha" / "src" / "utils.py", "def helper(): pass\n"),
    (workspace / "projects" / "beta" / "config" / "settings.json", json.dumps({"env": "prod", "debug": False})),
    (workspace / "tools" / "monitoring" / "scripts" / "check_disk.sh", "#!/bin/bash\ndf -h\n"),
    (workspace / "tools" / "linting" / ".flake8", "[flake8]\nmax-line-length = 120\n"),
    (workspace / "docs" / "api" / "v2" / "openapi.yaml", "openapi: 3.0.0\ninfo:\n  title: API\n  version: v2\n"),
    (workspace / "logs" / "archived" / "2023" / "app.log", "2023-01-01 00:00:00 INFO startup\n"),
    (workspace / "tmp" / "scratch" / "notes.txt", "TODO: fix quota parsing\n"),
    (workspace / "scripts" / "deploy" / "deploy.sh", "#!/bin/bash\necho deploying\n"),
    (workspace / "config" / "envs" / "prod.env", "API_URL=https://example.com\nDEBUG=false\n"),
    (workspace / ".cache" / "quota-tool" / "stale_data.json", json.dumps({"stale": True, "data": None})),
    (workspace / "projects" / "beta" / "config" / "limits.yaml", "max_requests: 1000\nwindow_seconds: 3600\n"),
]

for path, content in distractor_files:
    path.write_text(content)

# ── 3. Create MESSY ~/.codex/sessions/ with multiple session files ──
# The agent must figure out the path structure and create valid data.
# We create OLDER session files with WRONG/incomplete data to test
# that the agent uses the MOST RECENT file with valid rate_limits.

home = Path(os.path.expanduser("~"))
sessions_root = home / ".codex" / "sessions"

# Older session: has token_count but NO rate_limits key (trap!)
old_date = datetime.now() - timedelta(days=5)
old_dir = sessions_root / old_date.strftime("%Y") / old_date.strftime("%m") / old_date.strftime("%d")
old_dir.mkdir(parents=True, exist_ok=True)

old_session_events = [
    {"type": "session_start", "ts": (old_date - timedelta(hours=1)).timestamp(), "session_id": "old-sess-111"},
    {"type": "token_count", "ts": old_date.timestamp(), "tokens_used": 500},  # NO rate_limits!
    {"type": "session_end", "ts": old_date.timestamp(), "duration_s": 120},
]
old_session_file = old_dir / "session_aaa111.jsonl"
with open(old_session_file, "w") as f:
    for event in old_session_events:
        f.write(json.dumps(event) + "\n")

# Medium-age session: has rate_limits but they are OUTDATED values (trap for agents that use first found)
mid_date = datetime.now() - timedelta(days=1)
mid_dir = sessions_root / mid_date.strftime("%Y") / mid_date.strftime("%m") / mid_date.strftime("%d")
mid_dir.mkdir(parents=True, exist_ok=True)

mid_reset_primary = (datetime.now() + timedelta(hours=3)).timestamp()
mid_reset_secondary = (datetime.now() + timedelta(days=4)).timestamp()

mid_session_events = [
    {"type": "session_start", "ts": (mid_date - timedelta(hours=2)).timestamp(), "session_id": "mid-sess-222"},
    {
        "type": "token_count",
        "ts": mid_date.timestamp(),
        "tokens_used": 1200,
        "rate_limits": {
            "primary": {"used": 9999, "limit": 10000, "reset_at": mid_reset_primary},   # OUTDATED: almost maxed
            "secondary": {"used": 49999, "limit": 50000, "reset_at": mid_reset_secondary},
        },
    },
    {"type": "session_end", "ts": mid_date.timestamp()},
]
mid_session_file = mid_dir / "session_bbb222.jsonl"
with open(mid_session_file, "w") as f:
    for event in mid_session_events:
        f.write(json.dumps(event) + "\n")

# NOTE: We do NOT create the most recent session file.
# The agent must create it with the correct structure.
# We place a README-free marker so the agent knows what's expected.

# We leave an auth.json stub (needed by --all --yes path but not tested here)
codex_config_dir = home / ".codex"
auth_json = codex_config_dir / "auth.json"
auth_json.write_text(json.dumps({"account": "test@example.com", "token": "stub-token-do-not-use"}))

# ── 4. Create a task brief file (business context, not instructions) ──
task_brief = workspace / "task_brief.txt"
task_brief.write_text(
    "CONTEXT: Our team uses an AI coding assistant and we need to monitor rate limit consumption.\n"
    "The monitoring utility lives in ./codex-quota/codex-quota.py\n"
    "We have discovered session log files exist but may be incomplete.\n"
    "We need a current JSON quota report for our dashboard.\n"
    "Output file should be named: quota_report.json\n"
)

print("Workspace generation complete.")
print(f"Skill directory: {skill_dir}")
print(f"Sessions root: {sessions_root}")
print(f"Existing session files:")
for f in sorted(sessions_root.rglob("*.jsonl")):
    print(f"  {f}")