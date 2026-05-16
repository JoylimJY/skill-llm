#!/usr/bin/env python3
"""
Evaluation script for git-auto task.
Usage: python3 eval_script.py /workspace
"""

import sys
import os
import json
import subprocess
import re
from pathlib import Path

def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # ── Check 1: commit_report.txt exists ────────────────────────────────────
    report_candidates = list(Path(workspace).rglob("commit_report.txt"))
    if not report_candidates:
        checks.append(check("commit_report.txt exists", False,
                            "File 'commit_report.txt' was not found anywhere in the workspace."))
    else:
        checks.append(check("commit_report.txt exists", True,
                            f"Found at: {report_candidates[0]}"))
        report_path = report_candidates[0]

        # ── Check 2: commit_report.txt contains log output ────────────────────
        try:
            content = report_path.read_text()
            # Must contain at least 2 commit lines (initial + security fix)
            # git-auto log outputs lines like: abc1234 (HEAD...) fix(auth): ...
            commit_lines = [l for l in content.splitlines()
                            if re.match(r'^[0-9a-f]{7,}', l.strip())]
            if len(commit_lines) >= 2:
                checks.append(check("commit_report.txt contains >=2 log entries", True,
                                    f"Found {len(commit_lines)} commit entries in log."))
                total_score += 0.10
            else:
                checks.append(check("commit_report.txt contains >=2 log entries", False,
                                    f"Expected >=2 commit hash lines, found {len(commit_lines)}. Content snippet: {content[:300]}"))

            # Must contain git-auto log header markers
            has_header = "git-auto log" in content or "=== git-auto log" in content
            checks.append(check("commit_report.txt contains git-auto log output", has_header,
                                f"Header marker {'found' if has_header else 'NOT found'} in commit_report.txt"))
            if has_header:
                total_score += 0.05
        except Exception as e:
            checks.append(check("commit_report.txt readable", False, str(e)))

    # ── Check 3: The security-fix commit exists in git log ───────────────────
    try:
        log_out, _, rc = run(["git", "log", "--oneline", "--all"], workspace)
        if rc != 0:
            checks.append(check("git log accessible", False, "git log failed"))
        else:
            # Look for a commit with conventional prefix fix/feat/refactor
            # that relates to auth/security/token/session
            SECURITY_PATTERN = re.compile(
                r'^[0-9a-f]{7,}\s+(fix|feat|refactor|chore|docs|test)(\([^)]*\))?:\s+.+',
                re.IGNORECASE
            )
            security_commits = [l for l in log_out.splitlines()
                                 if SECURITY_PATTERN.match(l.strip())]
            # Exclude the initial "chore: initial project scaffold"
            non_initial = [c for c in security_commits
                           if "initial project scaffold" not in c]

            if non_initial:
                checks.append(check("Security-fix commit exists with conventional format", True,
                                    f"Found commit(s): {non_initial}"))
                total_score += 0.20
            else:
                checks.append(check("Security-fix commit exists with conventional format", False,
                                    f"No new conventional commit found. Log:\n{log_out}"))
    except Exception as e:
        checks.append(check("git log accessible", False, str(e)))

    # ── Check 4: Commit message uses a valid conventional prefix ─────────────
    try:
        log_out, _, _ = run(["git", "log", "--oneline"], workspace)
        lines = log_out.splitlines()
        # Second commit (most recent non-initial)
        latest_commits = [l for l in lines if "initial project scaffold" not in l]
        if latest_commits:
            latest = latest_commits[0]
            # Extract message portion (after hash)
            msg_part = " ".join(latest.split()[1:])
            CONV_RE = re.compile(r'^(feat|fix|refactor|docs|chore|test)(\([^)]*\))?:\s+\S+')
            if CONV_RE.match(msg_part):
                checks.append(check("Commit message follows Conventional Commits format", True,
                                    f"Message: '{msg_part}'"))
                total_score += 0.20
            else:
                checks.append(check("Commit message follows Conventional Commits format", False,
                                    f"Message '{msg_part}' does not match <type>[scope]: <desc>"))
        else:
            checks.append(check("Commit message follows Conventional Commits format", False,
                                "No commit beyond the initial scaffold found."))
    except Exception as e:
        checks.append(check("Commit message follows Conventional Commits format", False, str(e)))

    # ── Check 5: ONLY auth files were committed (not config/tests/etc.) ──────
    try:
        # Find the commit hash of the most recent non-initial commit
        log_out, _, _ = run(["git", "log", "--oneline"], workspace)
        commits = [l for l in log_out.splitlines() if "initial project scaffold" not in l]
        if commits:
            commit_hash = commits[0].split()[0]
            # Get the files changed in that commit
            files_out, _, _ = run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", commit_hash],
                workspace
            )
            changed_files = set(files_out.strip().splitlines())

            auth_files = {
                "src/payments/auth/token_validator.py",
                "src/payments/auth/session_manager.py",
            }
            forbidden_files = {
                "config/app.yaml",
                "tests/unit/payments/test_charge.py",
                "docs/api/openapi.yaml",
                "src/payments/processing/fraud_detector.py",
                "infra/terraform/main.tf",
            }

            # Auth files must be present
            auth_committed = auth_files.issubset(changed_files)
            # No forbidden files should be present
            forbidden_committed = forbidden_files.intersection(changed_files)

            if auth_committed:
                checks.append(check("Both auth security files committed", True,
                                    f"Committed files: {sorted(changed_files)}"))
                total_score += 0.25
            else:
                missing = auth_files - changed_files
                checks.append(check("Both auth security files committed", False,
                                    f"Missing auth files in commit: {missing}. Committed: {sorted(changed_files)}"))

            if not forbidden_committed:
                checks.append(check("Non-auth files excluded from commit", True,
                                    "No forbidden files were included in the commit."))
                total_score += 0.20
            else:
                checks.append(check("Non-auth files excluded from commit", False,
                                    f"Forbidden files incorrectly committed: {sorted(forbidden_committed)}"))
        else:
            checks.append(check("Both auth security files committed", False,
                                "No new commit found to inspect."))
            checks.append(check("Non-auth files excluded from commit", False,
                                "No new commit found to inspect."))
    except Exception as e:
        checks.append(check("Commit file inspection", False, str(e)))

    # ── Final scoring ─────────────────────────────────────────────────────────
    # All checks passed bonus
    all_passed = all(c["passed"] for c in checks)
    if all_passed:
        total_score = 1.0
    else:
        # Clamp
        total_score = min(total_score, 0.99)

    result = {
        "passed": all_passed,
        "score": round(total_score, 2),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())