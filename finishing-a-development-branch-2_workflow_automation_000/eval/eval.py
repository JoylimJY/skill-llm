#!/usr/bin/env python3
"""
Evaluation script for finishing-a-development-branch skill task.
Checks:
1. Tests were run (pytest) and the merged main branch has passing tests
2. Feature branch commits are now on main
3. Feature branch 'feature/dose-calculation' is deleted
4. Worktree at /workspace/worktrees/dose-calculation-wt is removed
5. No broken state on main (dose_calculator.py exists in main)
"""

import sys
import json
import subprocess
import os
from pathlib import Path

def run(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=60
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    repo = os.path.join(workspace, "infusion-firmware")
    worktree_path = os.path.join(workspace, "worktrees", "dose-calculation-wt")
    
    checks = []
    
    # ── Check 1: Repo exists and main branch is checked out ──────────────────
    try:
        rc, branch, err = run("git rev-parse --abbrev-ref HEAD", cwd=repo)
        on_main = rc == 0 and branch == "main"
        checks.append(check(
            "repo_on_main_branch",
            on_main,
            f"Current branch: '{branch}' (expected 'main')" if not on_main else "Main branch is active"
        ))
    except Exception as e:
        checks.append(check("repo_on_main_branch", False, f"Exception: {e}"))

    # ── Check 2: Feature branch commits are merged into main ─────────────────
    try:
        rc, log, err = run(
            "git log --oneline main",
            cwd=repo
        )
        has_dose_commit = "dose" in log.lower() or "ic-2024-07" in log.lower()
        checks.append(check(
            "feature_commits_on_main",
            has_dose_commit,
            f"Main log contains dose commit: {has_dose_commit}. Log snippet: {log[:300]}"
        ))
    except Exception as e:
        checks.append(check("feature_commits_on_main", False, f"Exception: {e}"))

    # ── Check 3: dose_calculator.py exists on main ───────────────────────────
    try:
        dose_file = Path(repo) / "src" / "dose_calculator.py"
        exists = dose_file.exists()
        content_ok = False
        if exists:
            content = dose_file.read_text()
            content_ok = "DoseCalculator" in content and "to_ml_hr" in content
        checks.append(check(
            "dose_calculator_merged_to_main",
            exists and content_ok,
            f"dose_calculator.py exists: {exists}, content valid: {content_ok}"
        ))
    except Exception as e:
        checks.append(check("dose_calculator_merged_to_main", False, f"Exception: {e}"))

    # ── Check 4: Feature branch is deleted ───────────────────────────────────
    try:
        rc, branch_list, err = run("git branch", cwd=repo)
        branch_deleted = "feature/dose-calculation" not in branch_list
        checks.append(check(
            "feature_branch_deleted",
            branch_deleted,
            f"feature/dose-calculation still present: {not branch_deleted}. Branches: {branch_list}"
        ))
    except Exception as e:
        checks.append(check("feature_branch_deleted", False, f"Exception: {e}"))

    # ── Check 5: Worktree is removed ─────────────────────────────────────────
    try:
        rc, worktree_list, err = run("git worktree list", cwd=repo)
        worktree_removed = worktree_path not in worktree_list and "dose-calculation-wt" not in worktree_list
        # Also check the directory no longer exists as a registered worktree
        wt_dir_gone = not Path(worktree_path).exists() or True  # dir may linger, registration matters
        # Primary check: worktree list should not contain the path
        checks.append(check(
            "worktree_removed",
            worktree_removed,
            f"Worktree list: {worktree_list}. dose-calculation-wt removed: {worktree_removed}"
        ))
    except Exception as e:
        checks.append(check("worktree_removed", False, f"Exception: {e}"))

    # ── Check 6: Tests pass on main after merge ───────────────────────────────
    try:
        rc, stdout, stderr = run("python3 -m pytest tests/ -v --tb=short", cwd=repo)
        tests_pass = rc == 0
        # Count passed tests - should include dose calculator tests
        passed_count = stdout.count(" PASSED")
        has_dose_tests = "test_dose_calculator" in stdout
        checks.append(check(
            "tests_pass_on_merged_main",
            tests_pass and has_dose_tests,
            f"pytest exit code: {rc}, passed: {passed_count}, dose tests present: {has_dose_tests}. "
            f"Output snippet: {stdout[-400:] if stdout else stderr[-200:]}"
        ))
    except Exception as e:
        checks.append(check("tests_pass_on_merged_main", False, f"Exception: {e}"))

    # ── Check 7: No remote push was made (Option 1 = local merge only) ───────
    try:
        rc, remote_list, err = run("git remote", cwd=repo)
        # If no remotes exist or no push happened, we're good
        # Check if there's evidence of push (remote tracking branch on main)
        rc2, tracking, err2 = run(
            "git log --oneline origin/main 2>/dev/null || echo 'no-remote'",
            cwd=repo
        )
        no_push = "no-remote" in tracking or rc != 0 or not remote_list.strip()
        checks.append(check(
            "no_remote_push_option1",
            True,  # This is informational; local merge path doesn't require remote
            f"Remote state: '{remote_list}', tracking: '{tracking[:100]}'"
        ))
    except Exception as e:
        checks.append(check("no_remote_push_option1", True, f"Informational check, exception: {e}"))

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Critical checks (must pass): 1,2,3,4,5,6
    critical = checks[:6]
    critical_passed = sum(1 for c in critical if c["passed"])
    total_critical = len(critical)
    
    score = critical_passed / total_critical
    passed = critical_passed == total_critical

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()