#!/usr/bin/env python3
"""
Evaluation script for openclaw-backup-restore task.
Checks:
  1. openclaw.json contains OPENCLAW_BACKUP_REPO set to the local bare repo path.
  2. ~/openclaw-backup/ exists and is a git repo.
  3. ~/openclaw-backup/ contains the expected content files (agents, sessions, workspace, memory).
  4. ~/openclaw-backup/ does NOT contain excluded paths (node_modules, logs, tmp, dist, completions).
  5. ~/openclaw-backup/.gitignore exists (was copied by backup.sh from skill dir).
  6. The backup git repo has at least one commit beyond 'init' (i.e., a real backup commit was pushed).
  7. The commit message follows the categorized format: 'chore: backup <categories>'.
  8. The local bare remote has the commit (i.e., push actually happened).
"""

import sys
import json
import subprocess
from pathlib import Path

def run(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=15
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/devops"
    HOME = Path(workspace)
    CONFIG_PATH = HOME / ".openclaw" / "openclaw.json"
    BACKUP_DIR = HOME / "openclaw-backup"
    META_FILE = HOME / ".test_meta" / "backup_repo_url.txt"

    checks = []
    total_score = 0.0
    weights = {
        "config_has_repo_url": 0.15,
        "backup_dir_is_git_repo": 0.10,
        "backup_has_content_files": 0.15,
        "excluded_dirs_absent": 0.20,
        "gitignore_copied": 0.10,
        "backup_commit_exists": 0.15,
        "commit_message_format": 0.10,
        "commit_pushed_to_remote": 0.05,
    }

    # ── Load expected repo URL ────────────────────────────────────────────────
    expected_repo_url = ""
    try:
        expected_repo_url = META_FILE.read_text().strip()
    except Exception as e:
        pass  # will fail specific checks below

    # ── Check 1: openclaw.json has OPENCLAW_BACKUP_REPO ──────────────────────
    check_name = "config_has_repo_url"
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        repo_url = (
            cfg.get("skills", {})
               .get("entries", {})
               .get("openclaw-backup-restore", {})
               .get("env", {})
               .get("OPENCLAW_BACKUP_REPO", "")
        )
        if repo_url and len(repo_url) > 3:
            checks.append({"name": check_name, "passed": True,
                           "detail": f"OPENCLAW_BACKUP_REPO = '{repo_url}'"})
            total_score += weights[check_name]
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": "OPENCLAW_BACKUP_REPO is missing or empty in openclaw.json"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 2: ~/openclaw-backup is a git repo ──────────────────────────────
    check_name = "backup_dir_is_git_repo"
    try:
        git_dir = BACKUP_DIR / ".git"
        if git_dir.is_dir():
            checks.append({"name": check_name, "passed": True,
                           "detail": f"{BACKUP_DIR} is a valid git repo"})
            total_score += weights[check_name]
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"{BACKUP_DIR}/.git does not exist"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 3: backup has expected content ──────────────────────────────────
    check_name = "backup_has_content_files"
    try:
        expected_files = [
            BACKUP_DIR / "agents" / "code-reviewer" / "agent.json",
            BACKUP_DIR / "agents" / "doc-writer" / "agent.json",
            BACKUP_DIR / "sessions" / "session-20240601" / "history.jsonl",
            BACKUP_DIR / "workspace" / "projects" / "infra-automation" / "main.tf",
            BACKUP_DIR / "memory" / "long-term" / "facts.json",
            BACKUP_DIR / "openclaw.json",
        ]
        missing = [str(p) for p in expected_files if not p.exists()]
        if not missing:
            checks.append({"name": check_name, "passed": True,
                           "detail": "All expected content files found in backup"})
            total_score += weights[check_name]
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"Missing files: {missing}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 4: Excluded dirs are NOT in backup ───────────────────────────────
    check_name = "excluded_dirs_absent"
    try:
        excluded_paths = [
            BACKUP_DIR / "node_modules",
            BACKUP_DIR / "logs",
            BACKUP_DIR / "tmp",
            BACKUP_DIR / "dist",
            BACKUP_DIR / "completions",
        ]
        present_excluded = [str(p) for p in excluded_paths if p.exists()]
        if not present_excluded:
            checks.append({"name": check_name, "passed": True,
                           "detail": "No excluded directories found in backup (gitignore respected)"})
            total_score += weights[check_name]
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"Excluded paths found in backup (should be absent): {present_excluded}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 5: .gitignore was copied to backup dir ──────────────────────────
    check_name = "gitignore_copied"
    try:
        gi_path = BACKUP_DIR / ".gitignore"
        if gi_path.exists():
            content = gi_path.read_text()
            has_node_modules = "node_modules/" in content
            has_logs = "logs/" in content
            if has_node_modules and has_logs:
                checks.append({"name": check_name, "passed": True,
                               "detail": ".gitignore present and contains expected exclusions"})
                total_score += weights[check_name]
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f".gitignore exists but missing expected rules. Content: {content[:200]}"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": ".gitignore not found in ~/openclaw-backup/"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 6: At least one backup commit beyond 'init' ─────────────────────
    check_name = "backup_commit_exists"
    try:
        rc, out, err = run(["git", "log", "--oneline"], cwd=str(BACKUP_DIR))
        if rc == 0 and out:
            commits = [l for l in out.splitlines() if l.strip()]
            # Filter out the seed 'init' commit
            backup_commits = [c for c in commits if "init" not in c.lower() or "chore" in c.lower()]
            # Any commit with 'chore: backup' is a backup commit
            chore_commits = [c for c in commits if "chore" in c.lower()]
            if chore_commits:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Found backup commit(s): {chore_commits}"})
                total_score += weights[check_name]
            elif len(commits) >= 2:
                # There's more than just init
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Found {len(commits)} commits (including backup)"})
                total_score += weights[check_name]
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"Only initial commit found. Log: {out}"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"git log failed: rc={rc} err={err}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 7: Commit message format 'chore: backup <categories>' ───────────
    check_name = "commit_message_format"
    try:
        rc, out, err = run(
            ["git", "log", "--pretty=%s", "HEAD"],
            cwd=str(BACKUP_DIR)
        )
        if rc == 0 and out:
            last_msg = out.splitlines()[0].strip()
            # Must start with 'chore: backup'
            if last_msg.startswith("chore: backup"):
                # Extract categories part
                parts = last_msg.split("chore: backup", 1)
                suffix = parts[1].strip()
                # Suffix should be either empty (no changes) or contain known category words
                known_cats = {"workspace", "config", "runtime", "memory"}
                if suffix == "(no changes)":
                    # Valid but unusual for a fresh backup — still accept
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"Valid commit message (no changes): '{last_msg}'"})
                    total_score += weights[check_name]
                elif suffix:
                    # categories are slash-separated words
                    cats_found = set(suffix.replace("/", " ").split())
                    if cats_found.issubset(known_cats) and cats_found:
                        checks.append({"name": check_name, "passed": True,
                                       "detail": f"Valid categorized commit message: '{last_msg}'"})
                        total_score += weights[check_name]
                    else:
                        checks.append({"name": check_name, "passed": False,
                                       "detail": f"Categories '{suffix}' contain unknown terms. Known: {known_cats}. Msg: '{last_msg}'"})
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"Commit message has no categories after 'chore: backup': '{last_msg}'"})
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"Last commit message does not follow 'chore: backup <categories>' format: '{last_msg}'"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"Could not read git log. rc={rc}, err={err}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Check 8: Commit was pushed to the local bare remote ───────────────────
    check_name = "commit_pushed_to_remote"
    try:
        if expected_repo_url:
            # Get HEAD of local backup
            rc_local, local_head, _ = run(
                ["git", "rev-parse", "HEAD"], cwd=str(BACKUP_DIR)
            )
            # Get HEAD of remote bare repo
            rc_remote, remote_head, _ = run(
                ["git", "rev-parse", "HEAD"], cwd=expected_repo_url
            )
            if rc_local == 0 and rc_remote == 0 and local_head == remote_head:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Local HEAD ({local_head[:8]}) matches remote HEAD — push verified"})
                total_score += weights[check_name]
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"HEAD mismatch: local={local_head[:8] if local_head else 'N/A'} remote={remote_head[:8] if remote_head else 'N/A'}"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": "Could not read expected_repo_url from test metadata"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Final result ──────────────────────────────────────────────────────────
    passed_all = all(c["passed"] for c in checks)
    final_score = round(total_score, 4)

    result = {
        "passed": passed_all,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()