#!/usr/bin/env python3
"""
Evaluation script for openclaw-backup task.

Checks:
  1. Exactly one (or more) backup directory exists at $HOME level named .openclawYYYYMMDDHHMMSS
  2. Backup name matches the exact regex pattern (dot + openclaw + 14 digits)
  3. All key files including hidden files are present in the backup
  4. Nested hidden file (.archived_flag) is present
  5. Restrictive permission on credentials/api_keys.enc is preserved (0o600)
  6. The original .openclaw directory is still intact (not moved/deleted)
"""

import sys
import os
import re
import stat
import json
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/workspace")
    home = workspace  # HOME == workspace in this task

    results = []
    overall = True

    # ── Check 1: At least one backup dir with correct naming convention ──────
    timestamp_pattern = re.compile(r"^\.openclaw(\d{14})$")
    backup_dirs = [
        d for d in home.iterdir()
        if d.is_dir() and timestamp_pattern.match(d.name)
    ]

    if backup_dirs:
        results.append(check(
            "backup_dir_exists_correct_name",
            True,
            f"Found {len(backup_dirs)} backup dir(s): {[d.name for d in backup_dirs]}"
        ))
    else:
        # Look for any openclaw-related dir to give a useful failure message
        candidates = [d.name for d in home.iterdir() if "openclaw" in d.name.lower() and d.name != ".openclaw"]
        results.append(check(
            "backup_dir_exists_correct_name",
            False,
            f"No directory matching .openclawYYYYMMDDHHMMSS found in {home}. "
            f"Candidates found: {candidates}"
        ))
        overall = False
        # Can't proceed with further checks
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": results
        }))
        return

    # Use the most-recently-modified backup dir for content checks
    backup_dir = sorted(backup_dirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]

    # ── Check 2: Timestamp is exactly 14 digits ───────────────────────────────
    m = timestamp_pattern.match(backup_dir.name)
    ts = m.group(1) if m else ""
    ts_valid = bool(re.fullmatch(r"\d{14}", ts))
    results.append(check(
        "timestamp_format_14_digits",
        ts_valid,
        f"Timestamp extracted: '{ts}'"
    ))
    if not ts_valid:
        overall = False

    # ── Check 3: Backup is sibling of .openclaw (same parent = home) ─────────
    correct_location = backup_dir.parent == home
    results.append(check(
        "backup_at_correct_level",
        correct_location,
        f"Backup parent: {backup_dir.parent} | Expected: {home}"
    ))
    if not correct_location:
        overall = False

    # ── Check 4: Core files present ───────────────────────────────────────────
    required_files = [
        "openclaw.json",
        "openclaw.json.bak1",
        "openclaw.json.bak2",
        "workspace/project_alpha.md",
        "workspace/notes.txt",
        "workspace/archive/2025/old_session.json",
        "credentials/api_keys.enc",
        "credentials/oauth_token.dat",
        "extensions/coderunner.json",
        "agents/default_agent.yaml",
        "cron/cleanup.cron",
        "logs/app.log",
    ]
    missing = []
    for rel in required_files:
        if not (backup_dir / rel).exists():
            missing.append(rel)

    files_ok = len(missing) == 0
    results.append(check(
        "core_files_present",
        files_ok,
        f"Missing files: {missing}" if missing else "All core files present."
    ))
    if not files_ok:
        overall = False

    # ── Check 5: Hidden files present in backup ───────────────────────────────
    hidden_files = [
        ".DS_Store",
        ".hidden_token",
        ".session_cache",
    ]
    missing_hidden = [f for f in hidden_files if not (backup_dir / f).exists()]
    hidden_ok = len(missing_hidden) == 0
    results.append(check(
        "hidden_files_included",
        hidden_ok,
        f"Missing hidden files: {missing_hidden}" if missing_hidden else "All hidden files present."
    ))
    if not hidden_ok:
        overall = False

    # ── Check 6: Nested hidden file present ──────────────────────────────────
    nested_hidden = backup_dir / "workspace" / "archive" / "2025" / ".archived_flag"
    nested_ok = nested_hidden.exists()
    results.append(check(
        "nested_hidden_file_included",
        nested_ok,
        f"Path checked: {nested_hidden}"
    ))
    if not nested_ok:
        overall = False

    # ── Check 7: Restrictive permission preserved on credentials/api_keys.enc ─
    try:
        cred_file = backup_dir / "credentials" / "api_keys.enc"
        if cred_file.exists():
            mode = stat.S_IMODE(cred_file.stat().st_mode)
            perm_ok = (mode == 0o600)
            results.append(check(
                "restrictive_permission_preserved",
                perm_ok,
                f"credentials/api_keys.enc mode: {oct(mode)} (expected 0o600)"
            ))
            if not perm_ok:
                overall = False
        else:
            results.append(check(
                "restrictive_permission_preserved",
                False,
                "credentials/api_keys.enc not found in backup."
            ))
            overall = False
    except Exception as e:
        results.append(check("restrictive_permission_preserved", False, str(e)))
        overall = False

    # ── Check 8: Original .openclaw still intact ──────────────────────────────
    original = home / ".openclaw"
    original_intact = original.is_dir() and (original / "openclaw.json").exists()
    results.append(check(
        "original_openclaw_intact",
        original_intact,
        f".openclaw exists: {original.is_dir()}, openclaw.json present: {(original / 'openclaw.json').exists()}"
    ))
    if not original_intact:
        overall = False

    # ── Check 9: Hidden-file content correctness (spot-check) ─────────────────
    try:
        token_content = (backup_dir / ".hidden_token").read_text()
        token_ok = "tok_abc123_secret" in token_content
        results.append(check(
            "hidden_token_content_correct",
            token_ok,
            f"Content: {token_content.strip()[:60]}"
        ))
        if not token_ok:
            overall = False
    except Exception as e:
        results.append(check("hidden_token_content_correct", False, str(e)))
        overall = False

    # ── Score ─────────────────────────────────────────────────────────────────
    passed_count = sum(1 for r in results if r["passed"])
    score = round(passed_count / len(results), 3)

    print(json.dumps({
        "passed": overall,
        "score": score,
        "checks": results
    }, indent=2))

if __name__ == "__main__":
    main()