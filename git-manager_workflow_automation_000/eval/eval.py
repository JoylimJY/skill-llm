#!/usr/bin/env python3
"""
Evaluation script for the git-manager compliance commit task.
Checks:
1. A feature branch was created (not main/master/production)
2. The two target config files were committed
3. The distractor files were NOT committed
4. The commit SHA is a valid short git SHA
5. The audit_log contains a commit entry
6. The git-manager activity log records the commit
"""

import sys
import json
import subprocess
from pathlib import Path

def run(cmd: list, cwd: str = None) -> tuple:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    repo_dir = ws / "pharma-compliance-system"

    checks = []

    # ── Helper: get all commits on a branch ──────────────────────────────────
    def get_commit_files(sha: str) -> list:
        out, _, _ = run(
            ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", sha],
            cwd=str(repo_dir)
        )
        return [f.strip() for f in out.split("\n") if f.strip()]

    # ── Check 1: A non-protected branch exists (feature branch was created) ──
    branch_check = {"name": "feature_branch_created", "passed": False, "detail": ""}
    try:
        out, _, rc = run(["git", "-C", str(repo_dir), "branch", "-a"])
        protected = {"main", "master", "production"}
        all_branches = [b.strip().lstrip("* ").strip() for b in out.split("\n") if b.strip()]
        feature_branches = [b for b in all_branches if b not in protected and not b.startswith("remotes/")]
        if feature_branches:
            branch_check["passed"] = True
            branch_check["detail"] = f"Feature branch(es) found: {feature_branches}"
        else:
            branch_check["detail"] = f"No non-protected branches found. All branches: {all_branches}"
    except Exception as e:
        branch_check["detail"] = f"Exception: {e}"
    checks.append(branch_check)

    # ── Check 2: Current HEAD is NOT main ─────────────────────────────────────
    not_main_check = {"name": "commit_not_on_main", "passed": False, "detail": ""}
    try:
        # Get the commit SHAs on main
        main_log, _, _ = run(["git", "-C", str(repo_dir), "log", "main", "--oneline"], )
        main_shas = set()
        for line in main_log.split("\n"):
            parts = line.split(" ", 1)
            if parts:
                main_shas.add(parts[0].strip())

        # Look at commits on feature branches
        target_files = {
            "configs/features/dosing_limits.yaml",
            "configs/environments/adverse_events_thresholds.yaml",
        }

        feature_commit_sha = None
        for branch in feature_branches if branch_check["passed"] else []:
            log_out, _, _ = run(
                ["git", "-C", str(repo_dir), "log", branch, "--oneline", "--not", "main"]
            )
            for line in log_out.split("\n"):
                line = line.strip()
                if not line:
                    continue
                sha = line.split(" ", 1)[0]
                committed = set(get_commit_files(sha))
                if target_files & committed:
                    feature_commit_sha = sha
                    break
            if feature_commit_sha:
                break

        if feature_commit_sha:
            not_main_check["passed"] = True
            not_main_check["detail"] = f"Target files committed on feature branch at SHA: {feature_commit_sha}"
        else:
            # Fallback: check if files appear in any non-initial commit
            all_log, _, _ = run(["git", "-C", str(repo_dir), "log", "--all", "--oneline"])
            not_main_check["detail"] = f"Could not find target files committed on a feature branch. All commits: {all_log[:300]}"
    except Exception as e:
        not_main_check["detail"] = f"Exception: {e}"
        feature_commit_sha = None
    checks.append(not_main_check)

    # ── Check 3: Both target config files are in a feature branch commit ─────
    target_files_check = {"name": "target_config_files_committed", "passed": False, "detail": ""}
    try:
        # Find the relevant commit: any non-main commit that includes target files
        target_files = {
            "configs/features/dosing_limits.yaml",
            "configs/environments/adverse_events_thresholds.yaml",
        }

        found_commit_sha = None
        found_files = set()

        # Check all branches except protected
        all_log, _, _ = run(
            ["git", "-C", str(repo_dir), "log", "--all", "--oneline", "--not", "main"]
        )
        for line in all_log.split("\n"):
            line = line.strip()
            if not line:
                continue
            sha = line.split(" ", 1)[0]
            committed = set(get_commit_files(sha))
            overlap = target_files & committed
            if len(overlap) == 2:
                found_commit_sha = sha
                found_files = committed
                break
            elif overlap:
                # partial match - keep searching
                if not found_commit_sha:
                    found_commit_sha = sha
                    found_files = committed

        if found_commit_sha and target_files <= found_files:
            target_files_check["passed"] = True
            target_files_check["detail"] = f"Both target files found in commit {found_commit_sha}. Files: {sorted(found_files)}"
        elif found_commit_sha:
            target_files_check["detail"] = f"Only partial target files in commit {found_commit_sha}: {found_files}. Missing: {target_files - found_files}"
        else:
            target_files_check["detail"] = "Neither target config file found in any non-main commit."
    except Exception as e:
        target_files_check["detail"] = f"Exception: {e}"
    checks.append(target_files_check)

    # ── Check 4: Distractor files NOT committed ────────────────────────────────
    distractor_check = {"name": "distractor_files_not_committed", "passed": False, "detail": ""}
    try:
        distractor_files = {
            "src/api/endpoints/laboratory.py",
            "src/database/migrations/0002_lab_results.sql",
        }
        # Check all non-main commits
        all_log, _, _ = run(
            ["git", "-C", str(repo_dir), "log", "--all", "--oneline", "--not", "main"]
        )
        distractor_in_commits = set()
        for line in all_log.split("\n"):
            line = line.strip()
            if not line:
                continue
            sha = line.split(" ", 1)[0]
            committed = set(get_commit_files(sha))
            distractor_in_commits |= (distractor_files & committed)

        if not distractor_in_commits:
            distractor_check["passed"] = True
            distractor_check["detail"] = "No distractor files were committed. Correct selective staging."
        else:
            distractor_check["detail"] = f"Distractor files incorrectly committed: {distractor_in_commits}"
    except Exception as e:
        distractor_check["detail"] = f"Exception: {e}"
    checks.append(distractor_check)

    # ── Check 5: git-manager activity log records the commit ─────────────────
    log_check = {"name": "git_manager_log_recorded", "passed": False, "detail": ""}
    try:
        log_path = Path.home() / ".openclaw" / "logs" / "git-manager.log"
        # Also check GIT_MANAGER_LOG env variable path if set
        import os
        env_log = os.environ.get("GIT_MANAGER_LOG")
        if env_log:
            log_path = Path(env_log)

        if log_path.exists():
            log_content = log_path.read_text()
            lines = [l.strip() for l in log_content.strip().split("\n") if l.strip()]
            commit_entries = []
            for line in lines:
                try:
                    entry = json.loads(line)
                    if entry.get("action") == "commit" or (
                        isinstance(entry.get("result"), dict) and
                        entry["result"].get("action") == "commit"
                    ):
                        commit_entries.append(entry)
                except Exception:
                    pass
            if commit_entries:
                log_check["passed"] = True
                log_check["detail"] = f"Found {len(commit_entries)} commit entries in git-manager log."
            else:
                log_check["detail"] = f"Log file exists but no commit entries found. Log lines: {len(lines)}"
        else:
            log_check["detail"] = f"Log file not found at {log_path}"
    except Exception as e:
        log_check["detail"] = f"Exception: {e}"
    checks.append(log_check)

    # ── Check 6: Commit SHA is a valid short git SHA ──────────────────────────
    sha_check = {"name": "valid_commit_sha_exists", "passed": False, "detail": ""}
    try:
        all_log, _, _ = run(
            ["git", "-C", str(repo_dir), "log", "--all", "--oneline", "--not", "main",
             "--pretty=format:%h"]
        )
        shas = [s.strip() for s in all_log.split("\n") if s.strip()]
        # A valid short SHA is 7+ hex chars
        import re
        valid_shas = [s for s in shas if re.match(r"^[0-9a-f]{7,}$", s)]
        if valid_shas:
            sha_check["passed"] = True
            sha_check["detail"] = f"Valid commit SHA(s) found on feature branch: {valid_shas}"
        else:
            sha_check["detail"] = f"No valid SHA found in non-main commits. Raw: {shas}"
    except Exception as e:
        sha_check["detail"] = f"Exception: {e}"
    checks.append(sha_check)

    # ── Check 7: Main branch was not directly modified ─────────────────────────
    main_protected_check = {"name": "main_branch_not_modified", "passed": False, "detail": ""}
    try:
        # Count commits on main since initial
        main_log, _, _ = run(
            ["git", "-C", str(repo_dir), "log", "main", "--oneline"]
        )
        main_commits = [l.strip() for l in main_log.split("\n") if l.strip()]
        # Should only have the initial commit
        if len(main_commits) == 1:
            main_protected_check["passed"] = True
            main_protected_check["detail"] = f"Main branch has exactly 1 commit (initial only). Protected correctly."
        else:
            # Check if any of the additional commits include our target files
            target_files = {
                "configs/features/dosing_limits.yaml",
                "configs/environments/adverse_events_thresholds.yaml",
            }
            extra_commits = main_commits[1:]  # skip initial
            contamination = []
            for line in extra_commits:
                sha = line.split(" ", 1)[0]
                committed = set(get_commit_files(sha))
                if target_files & committed:
                    contamination.append(sha)
            if contamination:
                main_protected_check["detail"] = f"Target files were committed directly to main at: {contamination}"
            else:
                # Extra commits on main but not our files — acceptable (e.g. merge)
                main_protected_check["passed"] = True
                main_protected_check["detail"] = f"Main has {len(main_commits)} commits but target files not directly committed to it."
    except Exception as e:
        main_protected_check["detail"] = f"Exception: {e}"
    checks.append(main_protected_check)

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "feature_branch_created": 1.5,
        "commit_not_on_main": 1.5,
        "target_config_files_committed": 2.5,
        "distractor_files_not_committed": 1.5,
        "git_manager_log_recorded": 1.0,
        "valid_commit_sha_exists": 1.0,
        "main_branch_not_modified": 1.0,
    }

    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 3)
    passed = all(c["passed"] for c in checks)

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))