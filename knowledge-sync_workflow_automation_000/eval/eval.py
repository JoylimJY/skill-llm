#!/usr/bin/env python3
"""
Evaluation script for knowledge-sync configuration task.
Usage: python3 eval_script.py /workspace
"""

import sys
import os
import re
import json

def evaluate(workspace: str) -> dict:
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    # ─── 1. sync-realtime.sh ─────────────────────────────────────────────────
    realtime_path = os.path.join(workspace, "knowledge-sync/scripts/sync-realtime.sh")
    try:
        with open(realtime_path, "r") as f:
            realtime = f.read()

        # 1a. All 6 required directories must appear
        required_dirs = ["articles", "memory", "projects", "docs", "scripts", "learnings"]
        missing = [d for d in required_dirs if d not in realtime]
        check(
            "sync-realtime: all 6 watch directories present",
            len(missing) == 0,
            f"Missing dirs: {missing}" if missing else "All 6 directories found."
        )

        # 1b. Exclude pattern must cover the 3 required patterns: node_modules, __pycache__, .git
        # AND the file extension pattern .(log|tmp|swp|pyc)
        exclude_covers_node_modules = "node_modules" in realtime
        exclude_covers_pycache = "__pycache__" in realtime
        exclude_covers_git = r"\.git" in realtime or "\\.git" in realtime
        exclude_covers_extensions = bool(
            re.search(r'\\\..*log.*tmp.*swp.*pyc|\\\..*pyc.*swp.*tmp.*log|log\|tmp\|swp\|pyc|pyc\|swp\|tmp\|log', realtime)
            or re.search(r'\\\.\(log\|tmp\|swp\|pyc\)', realtime)
            or re.search(r'\\\..*\(.*log.*\|.*tmp.*\|.*swp.*\|.*pyc.*\)', realtime)
            or (re.search(r'log', realtime) and re.search(r'tmp', realtime) and re.search(r'swp', realtime) and re.search(r'pyc', realtime) and "EXCLUDE" in realtime)
        )

        check(
            "sync-realtime: exclude pattern covers node_modules",
            exclude_covers_node_modules,
            "node_modules found in EXCLUDE_PATTERN" if exclude_covers_node_modules else "node_modules missing from EXCLUDE_PATTERN"
        )
        check(
            "sync-realtime: exclude pattern covers __pycache__",
            exclude_covers_pycache,
            "__pycache__ found in EXCLUDE_PATTERN" if exclude_covers_pycache else "__pycache__ missing from EXCLUDE_PATTERN"
        )
        check(
            "sync-realtime: exclude pattern covers .git",
            exclude_covers_git,
            ".git found in EXCLUDE_PATTERN" if exclude_covers_git else ".git missing from EXCLUDE_PATTERN"
        )
        check(
            "sync-realtime: exclude pattern covers file extensions (log/tmp/swp/pyc)",
            exclude_covers_extensions,
            "File extension exclusions (log/tmp/swp/pyc) found" if exclude_covers_extensions else "File extension exclusions missing from EXCLUDE_PATTERN"
        )

        # 1c. DELAY must be in 3–10 second range
        delay_matches = re.findall(r'DELAY\s*=\s*(\d+)', realtime)
        sleep_matches = re.findall(r'sleep\s+["\']?(\d+)["\']?', realtime)
        all_delays = [int(x) for x in delay_matches + sleep_matches]
        # Filter to find the sync delay (should be 3-10)
        valid_delay = any(3 <= d <= 10 for d in all_delays)
        check(
            "sync-realtime: sync delay is in 3-10 second range",
            valid_delay,
            f"Delay values found: {all_delays}. At least one must be 3-10." if all_delays else "No DELAY or sleep value found."
        )

    except FileNotFoundError:
        check("sync-realtime: file exists", False, f"File not found: {realtime_path}")
        check("sync-realtime: all 6 watch directories present", False, "File missing")
        check("sync-realtime: exclude pattern covers node_modules", False, "File missing")
        check("sync-realtime: exclude pattern covers __pycache__", False, "File missing")
        check("sync-realtime: exclude pattern covers .git", False, "File missing")
        check("sync-realtime: exclude pattern covers file extensions (log/tmp/swp/pyc)", False, "File missing")
        check("sync-realtime: sync delay is in 3-10 second range", False, "File missing")
    except Exception as e:
        check("sync-realtime: parse error", False, str(e))

    # ─── 2. git-auto-push.sh ─────────────────────────────────────────────────
    push_path = os.path.join(workspace, "knowledge-sync/scripts/git-auto-push.sh")
    try:
        with open(push_path, "r") as f:
            push = f.read()

        # 2a. Must do git pull before git push (pull-before-push pattern)
        pull_pos = [m.start() for m in re.finditer(r'git\s+pull', push)]
        push_pos = [m.start() for m in re.finditer(r'git\s+push', push)]
        pull_before_push = (
            len(pull_pos) > 0 and
            len(push_pos) > 0 and
            min(pull_pos) < min(push_pos)
        )
        check(
            "git-auto-push: pull before push",
            pull_before_push,
            "git pull found before git push." if pull_before_push else
            f"pull positions: {pull_pos}, push positions: {push_pos}. Pull must come before push."
        )

        # 2b. Must push to 'main' branch (not master)
        push_main = bool(re.search(r'git\s+push\s+\S+\s+main', push))
        check(
            "git-auto-push: pushes to 'main' branch",
            push_main,
            "push to 'main' found." if push_main else "push to 'main' not found (check branch name)."
        )

        # 2c. Must have git add -A or similar staging
        has_add = bool(re.search(r'git\s+add', push))
        check(
            "git-auto-push: stages changes with git add",
            has_add,
            "git add found." if has_add else "git add not found."
        )

        # 2d. Must have a git commit
        has_commit = bool(re.search(r'git\s+commit', push))
        check(
            "git-auto-push: commits changes",
            has_commit,
            "git commit found." if has_commit else "git commit not found."
        )

    except FileNotFoundError:
        check("git-auto-push: file exists", False, f"File not found: {push_path}")
        check("git-auto-push: pull before push", False, "File missing")
        check("git-auto-push: pushes to 'main' branch", False, "File missing")
        check("git-auto-push: stages changes with git add", False, "File missing")
        check("git-auto-push: commits changes", False, "File missing")
    except Exception as e:
        check("git-auto-push: parse error", False, str(e))

    # ─── 3. git-auto-pull.sh ─────────────────────────────────────────────────
    pull_path = os.path.join(workspace, "knowledge-sync/scripts/git-auto-pull.sh")
    try:
        with open(pull_path, "r") as f:
            pull_script = f.read()

        # 3a. Must use --rebase flag
        has_rebase = "--rebase" in pull_script
        check(
            "git-auto-pull: uses --rebase flag",
            has_rebase,
            "--rebase flag found." if has_rebase else "--rebase flag missing from git pull command."
        )

        # 3b. Must pull from 'main' (not master)
        pull_main = bool(re.search(r'git\s+pull\s+\S+\s+main', pull_script))
        check(
            "git-auto-pull: pulls from 'main' branch",
            pull_main,
            "pull from 'main' found." if pull_main else "pull from 'main' not found (check branch name, should not be 'master')."
        )

    except FileNotFoundError:
        check("git-auto-pull: file exists", False, f"File not found: {pull_path}")
        check("git-auto-pull: uses --rebase flag", False, "File missing")
        check("git-auto-pull: pulls from 'main' branch", False, "File missing")
    except Exception as e:
        check("git-auto-pull: parse error", False, str(e))

    # ─── 4. sync-crontab.txt ─────────────────────────────────────────────────
    # Search for this file anywhere in workspace
    from pathlib import Path
    crontab_files = list(Path(workspace).rglob("sync-crontab.txt"))

    if not crontab_files:
        check("sync-crontab.txt: file exists", False, "sync-crontab.txt not found anywhere in workspace.")
        check("sync-crontab.txt: git-auto-push every 5 minutes (*/5 * * * *)", False, "File missing")
        check("sync-crontab.txt: git-auto-pull every hour (0 * * * *)", False, "File missing")
        check("sync-crontab.txt: push entry references git-auto-push.sh", False, "File missing")
        check("sync-crontab.txt: pull entry uses --rebase", False, "File missing")
    else:
        crontab_path = crontab_files[0]
        check("sync-crontab.txt: file exists", True, f"Found at {crontab_path}")
        try:
            with open(crontab_path, "r") as f:
                crontab = f.read()

            # 4a. Git push schedule: */5 * * * *
            push_schedule = bool(re.search(r'\*/5\s+\*\s+\*\s+\*\s+\*', crontab))
            check(
                "sync-crontab.txt: git-auto-push every 5 minutes (*/5 * * * *)",
                push_schedule,
                "*/5 * * * * schedule found." if push_schedule else "*/5 * * * * schedule not found for git push."
            )

            # 4b. Git pull schedule: 0 * * * *
            pull_schedule = bool(re.search(r'^0\s+\*\s+\*\s+\*\s+\*', crontab, re.MULTILINE))
            check(
                "sync-crontab.txt: git-auto-pull every hour (0 * * * *)",
                pull_schedule,
                "0 * * * * schedule found." if pull_schedule else "0 * * * * schedule not found for git pull."
            )

            # 4c. Push crontab line must reference git-auto-push.sh
            push_ref = bool(re.search(r'\*/5.*git.?auto.?push\.sh', crontab) or
                          re.search(r'git.?auto.?push\.sh.*\*/5', crontab) or
                          re.search(r'\*/5\s+\*\s+\*\s+\*\s+\*.*push', crontab, re.IGNORECASE))
            check(
                "sync-crontab.txt: push entry references git-auto-push.sh",
                push_ref,
                "git-auto-push.sh referenced in push crontab entry." if push_ref else "git-auto-push.sh not referenced in */5 crontab line."
            )

            # 4d. Pull crontab line must use --rebase
            pull_rebase_in_cron = bool(re.search(r'0\s+\*\s+\*\s+\*\s+\*.*--rebase', crontab) or
                                        re.search(r'git.?auto.?pull\.sh', crontab) or
                                        "--rebase" in crontab)
            check(
                "sync-crontab.txt: pull entry uses --rebase or references git-auto-pull.sh",
                pull_rebase_in_cron,
                "--rebase or git-auto-pull.sh found in crontab." if pull_rebase_in_cron else "--rebase missing from pull crontab line."
            )

        except Exception as e:
            check("sync-crontab.txt: parse error", False, str(e))

    # ─── Scoring ─────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.80  # 80% threshold

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))