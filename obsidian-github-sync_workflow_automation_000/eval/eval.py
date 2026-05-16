#!/usr/bin/env python3
"""
Evaluation script for the Obsidian GitHub Sync task.
Usage: python3 eval_script.py /workspace
"""
import sys
import os
import json
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
vault_dir = workspace / "my-notes-vault"
bare_remote = workspace / "remote-bare-repo.git"
scripts_dir = workspace / "scripts"

checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── CHECK 1: .gitignore exists and contains all required Obsidian patterns ───
try:
    gitignore_path = vault_dir / ".gitignore"
    if not gitignore_path.exists():
        check("gitignore_exists", False, ".gitignore not found in vault directory")
    else:
        content = gitignore_path.read_text()
        required_patterns = [
            ".obsidian/workspace.json",
            ".obsidian/workspace-mobile.json",
            ".obsidian/plugins/*/data.json",
            ".trash/",
        ]
        missing = [p for p in required_patterns if p not in content]
        if missing:
            check("gitignore_obsidian_patterns", False,
                  f"Missing required Obsidian gitignore patterns: {missing}")
        else:
            check("gitignore_obsidian_patterns", True,
                  "All 4 required Obsidian patterns present in .gitignore")
except Exception as e:
    check("gitignore_obsidian_patterns", False, f"Exception: {e}")

# ── CHECK 2: Vault is a git repo with correct remote ─────────────────────────
try:
    result = subprocess.run(
        ["git", "-C", str(vault_dir), "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    remote_url = result.stdout.strip()
    expected_remote = str(bare_remote)
    if result.returncode == 0 and (expected_remote in remote_url or remote_url.endswith("remote-bare-repo.git")):
        check("git_remote_configured", True, f"Remote origin points to bare repo: {remote_url}")
    else:
        check("git_remote_configured", False,
              f"Remote 'origin' missing or wrong. Got: '{remote_url}', expected path to remote-bare-repo.git")
except Exception as e:
    check("git_remote_configured", False, f"Exception: {e}")

# ── CHECK 3: Conflict flag does NOT exist (conflict was resolved) ─────────────
try:
    default_flag = Path("/tmp/obsidian-sync-conflict.flag")
    # Also check for any custom flag files the agent might have used
    flag_exists = default_flag.exists()
    
    # Check custom CONFLICT_FLAG_FILE env if set (look in common locations)
    custom_flags = list(workspace.rglob("*.flag")) + list(Path("/tmp").glob("*conflict*"))
    active_flags = [f for f in custom_flags if f.exists()]
    
    if flag_exists or (active_flags and not all(str(f) == str(default_flag) for f in active_flags)):
        check("conflict_resolved", False,
              f"Conflict flag still exists: {default_flag}. Active flags: {active_flags}")
    else:
        check("conflict_resolved", True, "No conflict flag found - conflict was resolved")
except Exception as e:
    check("conflict_resolved", False, f"Exception: {e}")

# ── CHECK 4: Vault git log shows commits were pushed to bare remote ───────────
try:
    # Check that bare repo has more than just the initial 2 commits
    result = subprocess.run(
        ["git", "-C", str(bare_remote), "log", "--oneline", "master"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        check("commits_pushed_to_remote", False, f"git log failed: {result.stderr}")
    else:
        log_lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
        # Should have at least 3 commits: initial + remote update + agent's push
        if len(log_lines) >= 3:
            check("commits_pushed_to_remote", True,
                  f"Bare remote has {len(log_lines)} commits (including agent push): {log_lines[:3]}")
        else:
            check("commits_pushed_to_remote", False,
                  f"Expected at least 3 commits in remote, found {len(log_lines)}: {log_lines}")
except Exception as e:
    check("commits_pushed_to_remote", False, f"Exception: {e}")

# ── CHECK 5: Vault working tree is clean (rebase completed successfully) ──────
try:
    result = subprocess.run(
        ["git", "-C", str(vault_dir), "status", "--short"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        check("vault_clean_state", False, f"git status failed: {result.stderr}")
    else:
        # No rebase in progress
        rebase_dir = vault_dir / ".git" / "rebase-merge"
        rebase_apply = vault_dir / ".git" / "rebase-apply"
        if rebase_dir.exists() or rebase_apply.exists():
            check("vault_clean_state", False, "Rebase still in progress - not completed")
        else:
            check("vault_clean_state", True, "Vault git state is clean, no rebase in progress")
except Exception as e:
    check("vault_clean_state", False, f"Exception: {e}")

# ── CHECK 6: Systemd service file exists and has correct content ──────────────
try:
    # Find the service file anywhere in the workspace or home
    search_roots = [workspace, Path.home(), Path("/etc/systemd")]
    service_files = []
    for root in search_roots:
        if root.exists():
            service_files.extend(root.rglob("obsidian-sync.service"))
    
    if not service_files:
        check("systemd_service_file", False, "obsidian-sync.service not found anywhere")
    else:
        svc = service_files[0]
        content = svc.read_text()
        errors = []
        if "Type=oneshot" not in content:
            errors.append("Missing 'Type=oneshot'")
        if "OBSIDIAN_VAULT_DIR" not in content:
            errors.append("Missing 'OBSIDIAN_VAULT_DIR' environment")
        if "GITHUB_REMOTE_URL" not in content:
            errors.append("Missing 'GITHUB_REMOTE_URL' environment")
        if "obsidian-sync.sh" not in content:
            errors.append("Missing ExecStart pointing to obsidian-sync.sh")
        if "[Unit]" not in content or "[Service]" not in content:
            errors.append("Missing [Unit] or [Service] sections")
        if errors:
            check("systemd_service_file", False, f"Service file issues: {errors}. File at: {svc}")
        else:
            check("systemd_service_file", True, f"Service file valid at {svc}")
except Exception as e:
    check("systemd_service_file", False, f"Exception: {e}")

# ── CHECK 7: Systemd timer file exists with correct OnCalendar + Persistent ───
try:
    search_roots = [workspace, Path.home(), Path("/etc/systemd")]
    timer_files = []
    for root in search_roots:
        if root.exists():
            timer_files.extend(root.rglob("obsidian-sync.timer"))
    
    if not timer_files:
        check("systemd_timer_file", False, "obsidian-sync.timer not found anywhere")
    else:
        tmr = timer_files[0]
        content = tmr.read_text()
        errors = []
        if "OnCalendar=*-*-* 03:00:00" not in content:
            errors.append(f"Missing or wrong OnCalendar (need '*-*-* 03:00:00'). Found: {[l for l in content.splitlines() if 'OnCalendar' in l]}")
        if "Persistent=true" not in content:
            errors.append("Missing 'Persistent=true'")
        if "[Timer]" not in content:
            errors.append("Missing [Timer] section")
        if "[Install]" not in content:
            errors.append("Missing [Install] section")
        if "WantedBy=timers.target" not in content:
            errors.append("Missing 'WantedBy=timers.target'")
        if errors:
            check("systemd_timer_file", False, f"Timer file issues: {errors}. File at: {tmr}")
        else:
            check("systemd_timer_file", True, f"Timer file valid at {tmr}")
except Exception as e:
    check("systemd_timer_file", False, f"Exception: {e}")

# ── CHECK 8: Cron schedule file with both sync and conflict-check jobs ────────
try:
    cron_files = list(workspace.rglob("obsidian-cron.txt"))
    if not cron_files:
        check("cron_schedule_file", False, "obsidian-cron.txt not found in workspace")
    else:
        cron = cron_files[0]
        content = cron.read_text()
        errors = []
        # Sync job: 0 3 * * *
        if "0 3 * * *" not in content:
            errors.append("Missing sync cron '0 3 * * *'")
        # Sync script referenced
        if "obsidian-sync.sh" not in content:
            errors.append("Missing obsidian-sync.sh in sync cron line")
        # Conflict check job: 0 9 * * *
        if "0 9 * * *" not in content:
            errors.append("Missing conflict-check cron '0 9 * * *'")
        # Conflict check script referenced
        if "check-conflict.sh" not in content:
            errors.append("Missing check-conflict.sh in conflict-check cron line")
        if errors:
            check("cron_schedule_file", False, f"Cron file issues: {errors}")
        else:
            check("cron_schedule_file", True, f"Cron file valid at {cron}")
except Exception as e:
    check("cron_schedule_file", False, f"Exception: {e}")

# ── CHECK 9: SharedNote.md from remote is present in vault (sync happened) ────
try:
    shared_note = vault_dir / "SharedNote.md"
    if not shared_note.exists():
        check("remote_content_pulled", False,
              "SharedNote.md from remote not found in vault - sync/rebase did not complete")
    else:
        content = shared_note.read_text()
        if "Remote Update" in content or "remote" in content.lower():
            check("remote_content_pulled", True,
                  "SharedNote.md exists with remote content - pull/rebase succeeded")
        else:
            check("remote_content_pulled", False,
                  f"SharedNote.md exists but lacks remote commit content. Content: {content[:200]}")
except Exception as e:
    check("remote_content_pulled", False, f"Exception: {e}")

# ── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
all_passed = passed_count == total

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, indent=2))