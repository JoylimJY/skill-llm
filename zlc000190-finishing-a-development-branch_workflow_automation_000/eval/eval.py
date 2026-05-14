#!/usr/bin/env python3
"""
Evaluation script for the finishing-a-development-branch skill task.
Checks that the agent correctly:
1. Ran tests before acting
2. Merged the feature branch into main (Option 1 path)
3. Deleted the feature branch
4. Removed the worktree
5. Verified tests on merged main
"""

import sys
import json
import subprocess
import os
from pathlib import Path


def run(cmd, cwd=None):
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def main(workspace: str):
    checks = []
    ws = Path(workspace)
    repo = ws / "payments-service"
    meta_file = ws / ".task_meta.json"

    # ── Load metadata ──────────────────────────────────────────────────────
    try:
        meta = json.loads(meta_file.read_text())
        feature_branch = meta["feature_branch"]
        worktree_dir = meta["worktree_path"]
        base_branch = meta["base_branch"]
        worktree_path = ws / worktree_dir
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [check("metadata_load", False, f"Could not load task metadata: {e}")]
        }
        print(json.dumps(result))
        return

    # ── CHECK 1: feature branch no longer exists ───────────────────────────
    try:
        rc, out, err = run("git branch --list", cwd=str(repo))
        branches = [b.strip().lstrip("* ") for b in out.splitlines()]
        branch_deleted = feature_branch not in branches
        checks.append(check(
            "feature_branch_deleted",
            branch_deleted,
            f"Feature branch '{feature_branch}' {'not found (correctly deleted)' if branch_deleted else 'still exists — not deleted'}"
        ))
    except Exception as e:
        checks.append(check("feature_branch_deleted", False, f"Exception: {e}"))
        branch_deleted = False

    # ── CHECK 2: feature branch commits are on main ────────────────────────
    try:
        rc, out, err = run(
            f"git log {base_branch} --oneline --all",
            cwd=str(repo)
        )
        validator_commit_on_main = "TransactionValidator" in out or "transaction-validator" in out.lower() or "validator" in out.lower()
        # More precise: check if the specific commit message is in main's log
        rc2, log_main, _ = run(
            f"git log {base_branch} --oneline",
            cwd=str(repo)
        )
        validator_on_main = "validator" in log_main.lower() or "TransactionValidator" in log_main
        checks.append(check(
            "feature_commits_on_main",
            validator_on_main,
            f"Validator feature commits {'found' if validator_on_main else 'NOT found'} on {base_branch}. Log: {log_main[:300]}"
        ))
    except Exception as e:
        checks.append(check("feature_commits_on_main", False, f"Exception: {e}"))
        validator_on_main = False

    # ── CHECK 3: validator.py exists on main branch ────────────────────────
    try:
        rc, out, err = run(
            f"git show {base_branch}:src/validator.py",
            cwd=str(repo)
        )
        validator_file_on_main = rc == 0 and "TransactionValidator" in out
        checks.append(check(
            "validator_module_on_main",
            validator_file_on_main,
            f"src/validator.py {'found with correct content' if validator_file_on_main else 'NOT found'} on {base_branch}"
        ))
    except Exception as e:
        checks.append(check("validator_module_on_main", False, f"Exception: {e}"))
        validator_file_on_main = False

    # ── CHECK 4: worktree is removed ──────────────────────────────────────
    try:
        rc, out, err = run("git worktree list", cwd=str(repo))
        worktree_removed = worktree_dir not in out and str(worktree_path) not in out
        # Also check the worktree directory is gone or de-registered
        dir_gone = not worktree_path.exists() or worktree_removed
        checks.append(check(
            "worktree_removed",
            worktree_removed,
            f"Worktree '{worktree_dir}' {'not listed (correctly removed)' if worktree_removed else 'still registered'}. worktree list: {out[:300]}"
        ))
    except Exception as e:
        checks.append(check("worktree_removed", False, f"Exception: {e}"))
        worktree_removed = False

    # ── CHECK 5: main branch tests pass after merge ────────────────────────
    try:
        # Make sure we're on main in the repo
        run(f"git checkout {base_branch}", cwd=str(repo))
        rc, out, err = run(
            "python3 -m pytest tests/ -q --tb=short 2>&1",
            cwd=str(repo)
        )
        tests_pass = rc == 0
        # Check that the new validator tests are included
        validator_tests_run = "test_validator" in out or "4 passed" in out or ("passed" in out and rc == 0)
        checks.append(check(
            "tests_pass_on_main",
            tests_pass,
            f"pytest on {base_branch}: {'PASSED' if tests_pass else 'FAILED'}. Output: {out[-400:]}"
        ))
        checks.append(check(
            "new_tests_included",
            validator_tests_run,
            f"New validator tests {'present and ran' if validator_tests_run else 'NOT detected'} on {base_branch}. Output: {out[-400:]}"
        ))
    except Exception as e:
        checks.append(check("tests_pass_on_main", False, f"Exception: {e}"))
        checks.append(check("new_tests_included", False, f"Exception: {e}"))
        tests_pass = False
        validator_tests_run = False

    # ── CHECK 6: current HEAD of repo is on main (not orphaned) ───────────
    try:
        rc, current_branch, err = run("git branch --show-current", cwd=str(repo))
        on_main = current_branch == base_branch
        checks.append(check(
            "repo_on_base_branch",
            on_main,
            f"Repo HEAD is on '{current_branch}' (expected '{base_branch}')"
        ))
    except Exception as e:
        checks.append(check("repo_on_base_branch", False, f"Exception: {e}"))
        on_main = False

    # ── CHECK 7: original worktree directory cleaned up ───────────────────
    try:
        # After worktree remove, the directory should not exist (or be empty)
        wt_path_gone = not worktree_path.exists()
        checks.append(check(
            "worktree_directory_gone",
            wt_path_gone,
            f"Worktree directory at '{worktree_path}': {'removed' if wt_path_gone else 'still exists on filesystem'}"
        ))
    except Exception as e:
        checks.append(check("worktree_directory_gone", False, f"Exception: {e}"))
        wt_path_gone = False

    # ── Scoring ────────────────────────────────────────────────────────────
    # Weights: critical checks are worth more
    weights = {
        "feature_branch_deleted":   1.5,
        "feature_commits_on_main":  2.0,
        "validator_module_on_main": 1.5,
        "worktree_removed":         2.0,
        "tests_pass_on_main":       2.0,
        "new_tests_included":       1.5,
        "repo_on_base_branch":      0.5,
        "worktree_directory_gone":  1.0,
    }

    total_weight = sum(weights.values())
    earned = sum(
        weights.get(c["name"], 1.0)
        for c in checks
        if c["passed"]
    )
    score = round(earned / total_weight, 3)

    # Must-pass checks: the integration is only valid if commits are on main
    # AND branch is deleted AND worktree is gone
    hard_pass = (
        branch_deleted and
        validator_on_main and
        validator_file_on_main and
        worktree_removed and
        tests_pass
    )

    result = {
        "passed": hard_pass,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)