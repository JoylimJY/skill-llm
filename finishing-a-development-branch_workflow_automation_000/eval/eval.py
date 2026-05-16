#!/usr/bin/env python3
"""
Evaluation script for the finishing-a-development-branch task.

Checks (in order of discriminative power):
1. Worktree for feature/currency-converter has been removed (key proprietary trap).
2. Feature branch feature/currency-converter no longer exists.
3. Feature commits are integrated into main (currency.py present on main).
4. Main branch still has passing tests (post-merge verification implied).
5. Main repo worktree (primary) still exists and is intact.
"""

import sys
import json
import subprocess
from pathlib import Path


def run(cmd, cwd):
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, shell=False
    )
    return result.returncode, result.stdout, result.stderr


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    repo_dir = Path(workspace) / "fintech-pipeline"

    checks = []
    total_score = 0.0
    weights = {
        "worktree_removed":      0.30,
        "feature_branch_deleted": 0.25,
        "feature_code_on_main":   0.20,
        "main_tests_pass":        0.15,
        "main_repo_intact":       0.10,
    }

    # ── Check 0: repo exists ──────────────────────────────────────────────────
    if not repo_dir.exists():
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "repo_exists", "passed": False,
                        "detail": f"Repo directory not found: {repo_dir}"}]
        }))
        return

    # ── Check 1: Worktree removed ─────────────────────────────────────────────
    try:
        rc, stdout, stderr = run(["git", "worktree", "list"], repo_dir)
        worktree_lines = stdout.strip().splitlines()
        # The worktree for feature/currency-converter should NOT appear
        feature_worktree_present = any(
            "currency-converter" in line or "feature/currency-converter" in line
            for line in worktree_lines
        )
        # Also check the physical path
        worktree_path = Path(workspace) / "worktrees" / "currency-converter"
        physical_exists = worktree_path.exists()

        wt_passed = (not feature_worktree_present) and (not physical_exists)
        detail = (
            f"git worktree list output:\n{stdout.strip()}\n"
            f"Physical path exists: {physical_exists}"
        )
        checks.append({
            "name": "worktree_removed",
            "passed": wt_passed,
            "detail": detail
        })
        if wt_passed:
            total_score += weights["worktree_removed"]
    except Exception as e:
        checks.append({
            "name": "worktree_removed",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 2: Feature branch deleted ──────────────────────────────────────
    try:
        rc, stdout, stderr = run(
            ["git", "branch", "--list", "feature/currency-converter"], repo_dir
        )
        branch_exists = "feature/currency-converter" in stdout
        fb_passed = not branch_exists
        checks.append({
            "name": "feature_branch_deleted",
            "passed": fb_passed,
            "detail": f"Branch list output: '{stdout.strip()}'"
        })
        if fb_passed:
            total_score += weights["feature_branch_deleted"]
    except Exception as e:
        checks.append({
            "name": "feature_branch_deleted",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 3: Feature code present on main ─────────────────────────────────
    try:
        # Show the file tree on main branch using git ls-tree
        rc, stdout, stderr = run(
            ["git", "show", "main:src/pipeline/currency.py"], repo_dir
        )
        currency_on_main = rc == 0 and "CurrencyConverter" in stdout

        # Also verify the extended normalizer is on main
        rc2, stdout2, _ = run(
            ["git", "show", "main:src/pipeline/normalizer.py"], repo_dir
        )
        normalizer_updated = rc2 == 0 and "normalize_to_usd" in stdout2

        fc_passed = currency_on_main and normalizer_updated
        checks.append({
            "name": "feature_code_on_main",
            "passed": fc_passed,
            "detail": (
                f"currency.py on main: {currency_on_main}, "
                f"normalizer has normalize_to_usd: {normalizer_updated}"
            )
        })
        if fc_passed:
            total_score += weights["feature_code_on_main"]
    except Exception as e:
        checks.append({
            "name": "feature_code_on_main",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Check 4: Tests pass on main ───────────────────────────────────────────
    try:
        # Run pytest from the main repo directory (main is checked out there)
        rc, stdout, stderr = run(
            ["python", "-m", "pytest", "--tb=short", "-q"], repo_dir
        )
        tests_passed = rc == 0
        # Extract summary line
        summary_lines = [l for l in stdout.splitlines() if "passed" in l or "failed" in l or "error" in l]
        summary = summary_lines[-1] if summary_lines else stdout[-300:]
        checks.append({
            "name": "main_tests_pass",
            "passed": tests_passed,
            "detail": f"pytest exit code: {rc}. Summary: {summary}"
        })
        if tests_passed:
            total_score += weights["main_tests_pass"]
    except Exception as e:
        checks.append({
            "name": "main_tests_pass",
            "passed": False,
            "detail": f"Exception running pytest: {e}"
        })

    # ── Check 5: Main repo (primary worktree) intact ──────────────────────────
    try:
        rc, stdout, stderr = run(["git", "status"], repo_dir)
        # Should be on main branch, clean working tree
        on_main = "On branch main" in stdout or "HEAD detached" not in stdout
        rc2, branch_out, _ = run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_dir
        )
        current_branch = branch_out.strip()
        mr_passed = (rc == 0) and (current_branch == "main")
        checks.append({
            "name": "main_repo_intact",
            "passed": mr_passed,
            "detail": f"Current branch: '{current_branch}', git status rc: {rc}"
        })
        if mr_passed:
            total_score += weights["main_repo_intact"]
    except Exception as e:
        checks.append({
            "name": "main_repo_intact",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── Final result ──────────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    total_score = round(total_score, 4)

    print(json.dumps({
        "passed": all_passed,
        "score": total_score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()