#!/usr/bin/env python3
"""
Evaluation script for fork-manager full-sync task.
Checks: config mutations, production branch content, history.md format.
"""

import sys
import json
import subprocess
import os
from pathlib import Path

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace = Path(workspace)

    skill_dir = workspace / "skills" / "fork-manager"
    config_path = skill_dir / "repos" / "numcore" / "config.json"
    history_path = skill_dir / "repos" / "numcore" / "history.md"
    work_dir = workspace / "repos" / "numcore-local"

    checks = []
    total_score = 0.0
    total_weight = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, total_weight
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            total_score += weight

    # ─── Load config.json ───
    config = None
    try:
        config = json.loads(config_path.read_text())
        add_check(
            "config_json_readable",
            True,
            f"config.json loaded successfully from {config_path}",
            weight=0.5
        )
    except Exception as e:
        add_check("config_json_readable", False, f"Could not read/parse config.json: {e}", weight=0.5)

    # ─── CHECK 1: PR #103 restored to openPRs ───
    if config is not None:
        pr103_restored = 103 in config.get("openPRs", [])
        add_check(
            "pr103_restored_to_openPRs",
            pr103_restored,
            f"PR #103 should be in openPRs (restored from droppedPatches). "
            f"Found openPRs={config.get('openPRs')}",
            weight=2.0
        )

    # ─── CHECK 2: PR #103 has branch entry in prBranches ───
    if config is not None:
        pr103_branch = config.get("prBranches", {}).get("103")
        add_check(
            "pr103_branch_in_prBranches",
            pr103_branch is not None,
            f"PR #103 must have an entry in prBranches. Found: {pr103_branch}",
            weight=1.5
        )

    # ─── CHECK 3: PR #103 removed from notes.droppedPatches ───
    if config is not None:
        dropped = config.get("notes", {}).get("droppedPatches", {})
        pr103_not_dropped = "103" not in dropped
        add_check(
            "pr103_removed_from_droppedPatches",
            pr103_not_dropped,
            f"PR #103 must NOT be in notes.droppedPatches after restoration. "
            f"droppedPatches keys: {list(dropped.keys())}",
            weight=1.5
        )

    # ─── CHECK 4: PR #102 NOT in openPRs ───
    if config is not None:
        pr102_not_open = 102 not in config.get("openPRs", [])
        add_check(
            "pr102_removed_from_openPRs",
            pr102_not_open,
            f"PR #102 (closed by upstream) must NOT be in openPRs. "
            f"Found openPRs={config.get('openPRs')}",
            weight=2.0
        )

    # ─── CHECK 5: PR #102 moved to localPatches (kept as local patch) ───
    if config is not None:
        local_patches = config.get("localPatches", {})
        # Look for any entry with local/ prefix that references feat/gpu-backend or PR 102
        pr102_as_patch = False
        pr102_patch_branch = None
        for branch_key, patch_info in local_patches.items():
            is_local_prefix = branch_key.startswith("local/")
            original_pr_match = patch_info.get("originalPR") == 102
            branch_content_match = "gpu" in branch_key.lower() or "gpu" in str(patch_info.get("description", "")).lower()
            if is_local_prefix and (original_pr_match or branch_content_match):
                pr102_as_patch = True
                pr102_patch_branch = branch_key
                break

        add_check(
            "pr102_in_localPatches_with_local_prefix",
            pr102_as_patch,
            f"Closed PR #102 must be in localPatches with a 'local/' prefix branch key. "
            f"Current localPatches keys: {list(local_patches.keys())}. "
            f"Found match: {pr102_patch_branch}",
            weight=2.5
        )

    # ─── CHECK 6: main branch synced with upstream ───
    try:
        origin_main_sha, _, rc1 = run("git rev-parse origin/main", cwd=work_dir)
        upstream_main_sha, _, rc2 = run("git rev-parse upstream/main", cwd=work_dir)
        run("git fetch upstream", cwd=work_dir)
        run("git fetch origin", cwd=work_dir)
        origin_main_sha2, _, _ = run("git rev-parse origin/main", cwd=work_dir)
        upstream_main_sha2, _, _ = run("git rev-parse upstream/main", cwd=work_dir)

        main_synced = (origin_main_sha2 == upstream_main_sha2)
        behind_count, _, _ = run(
            "git rev-list --count origin/main..upstream/main", cwd=work_dir
        )
        add_check(
            "main_branch_synced_with_upstream",
            main_synced,
            f"origin/main should equal upstream/main after sync. "
            f"origin/main={origin_main_sha2[:8]}, upstream/main={upstream_main_sha2[:8]}, "
            f"behind={behind_count}",
            weight=2.0
        )
    except Exception as e:
        add_check("main_branch_synced_with_upstream", False, f"Error checking main sync: {e}", weight=2.0)

    # ─── CHECK 7: Production branch exists ───
    try:
        prod_branch = "main-with-all-prs"
        stdout, _, rc = run(f"git ls-remote origin {prod_branch}", cwd=work_dir)
        prod_exists = rc == 0 and len(stdout.strip()) > 0

        # Also check locally
        if not prod_exists:
            stdout2, _, rc2 = run(f"git rev-parse --verify {prod_branch}", cwd=work_dir)
            prod_exists = rc2 == 0

        add_check(
            "production_branch_exists",
            prod_exists,
            f"Production branch '{prod_branch}' must exist (locally or on origin). "
            f"ls-remote output: '{stdout[:100]}'",
            weight=2.0
        )
    except Exception as e:
        add_check("production_branch_exists", False, f"Error checking production branch: {e}", weight=2.0)

    # ─── CHECK 8: Production branch contains PR #101 commit ───
    try:
        prod_branch = "main-with-all-prs"
        # Switch to production branch and check log
        run(f"git fetch origin", cwd=work_dir)

        # Check that the production branch has a commit touching solver/sparse.py (PR #101)
        log_output, _, rc = run(
            f"git log origin/{prod_branch} --oneline --all 2>/dev/null || git log {prod_branch} --oneline",
            cwd=work_dir
        )

        # Check files in production branch
        files_sparse, _, _ = run(
            f"git show origin/{prod_branch}:solver/sparse.py 2>/dev/null || git show {prod_branch}:solver/sparse.py 2>/dev/null",
            cwd=work_dir
        )
        pr101_in_prod = "convergence" in files_sparse or "rs_old" in files_sparse or "conjugate" in files_sparse.lower()

        add_check(
            "production_contains_pr101",
            pr101_in_prod,
            f"Production branch must contain PR #101 changes (improved CG in sparse.py). "
            f"sparse.py preview: '{files_sparse[:200]}'",
            weight=2.0
        )
    except Exception as e:
        add_check("production_contains_pr101", False, f"Error checking PR #101 in production: {e}", weight=2.0)

    # ─── CHECK 9: Production branch contains local/precision-fix ───
    try:
        prod_branch = "main-with-all-prs"
        files_precision, _, _ = run(
            f"git show origin/{prod_branch}:utils/precision.py 2>/dev/null || git show {prod_branch}:utils/precision.py 2>/dev/null",
            cwd=work_dir
        )
        # local/precision-fix sets EPSILON = 1e-12
        precision_in_prod = "1e-12" in files_precision

        add_check(
            "production_contains_local_precision_fix",
            precision_in_prod,
            f"Production branch must include local/precision-fix (EPSILON=1e-12). "
            f"precision.py preview: '{files_precision[:300]}'",
            weight=2.0
        )
    except Exception as e:
        add_check(
            "production_contains_local_precision_fix", False,
            f"Error checking local patch in production: {e}", weight=2.0
        )

    # ─── CHECK 10: Production branch contains PR #103 changes (restored PR) ───
    try:
        prod_branch = "main-with-all-prs"
        files_prec_103, _, _ = run(
            f"git show origin/{prod_branch}:utils/precision.py 2>/dev/null || git show {prod_branch}:utils/precision.py 2>/dev/null",
            cwd=work_dir
        )
        # PR #103 adds cleanup_buffers function OR local/precision-fix is applied on top
        # Either the cleanup_buffers function exists OR the precision fix covers it
        # Since both touch precision.py, check if the production branch has meaningful content
        # The key check: production branch should have EITHER cleanup_buffers OR the 1e-12 EPSILON
        # (the local patch may override the PR #103 changes per merge order)
        pr103_or_patch = "cleanup_buffers" in files_prec_103 or "1e-12" in files_prec_103

        add_check(
            "production_contains_pr103_or_patch",
            pr103_or_patch,
            f"Production branch should contain PR #103 or local/precision-fix changes to precision.py. "
            f"Found: cleanup_buffers={'cleanup_buffers' in files_prec_103}, 1e-12={'1e-12' in files_prec_103}",
            weight=1.5
        )
    except Exception as e:
        add_check(
            "production_contains_pr103_or_patch", False,
            f"Error checking PR #103 in production: {e}", weight=1.5
        )

    # ─── CHECK 11: history.md exists with proper format ───
    try:
        history_exists = history_path.exists()
        if history_exists:
            history_content = history_path.read_text()
            has_separator = "---" in history_content
            has_date_header = any(
                line.startswith("## 20") and "UTC" in line
                for line in history_content.splitlines()
            )
            has_summary = "Summary" in history_content or "summary" in history_content
            has_actions = "Action" in history_content or "action" in history_content

            history_ok = has_separator and (has_date_header or has_summary)
            add_check(
                "history_md_correct_format",
                history_ok,
                f"history.md must exist with '---' separator and date header. "
                f"has_sep={has_separator}, has_date_hdr={has_date_header}, "
                f"has_summary={has_summary}, content_len={len(history_content)}",
                weight=1.5
            )
        else:
            add_check(
                "history_md_correct_format",
                False,
                f"history.md does not exist at {history_path}",
                weight=1.5
            )
    except Exception as e:
        add_check("history_md_correct_format", False, f"Error reading history.md: {e}", weight=1.5)

    # ─── CHECK 12: PR #101 still in openPRs ───
    if config is not None:
        pr101_still_open = 101 in config.get("openPRs", [])
        add_check(
            "pr101_still_in_openPRs",
            pr101_still_open,
            f"PR #101 (still open) must remain in openPRs. "
            f"Found openPRs={config.get('openPRs')}",
            weight=1.0
        )

    # ─── CHECK 13: config.json lastSync updated ───
    if config is not None:
        old_sync = "2026-01-20T10:00:00Z"
        new_sync = config.get("lastSync", "")
        sync_updated = new_sync != old_sync and new_sync != ""
        add_check(
            "config_lastSync_updated",
            sync_updated,
            f"config.json lastSync must be updated from '{old_sync}'. "
            f"Current: '{new_sync}'",
            weight=1.0
        )

    # ─── CHECK 14: PR #102 prBranches entry removed ───
    if config is not None:
        pr102_branch_removed = "102" not in config.get("prBranches", {})
        add_check(
            "pr102_removed_from_prBranches",
            pr102_branch_removed,
            f"PR #102 must NOT be in prBranches after being moved to localPatches. "
            f"prBranches keys: {list(config.get('prBranches', {}).keys())}",
            weight=1.5
        )

    # ─── Compute final score ───
    if total_weight > 0:
        score = round(total_score / total_weight, 4)
    else:
        score = 0.0

    overall_passed = all(c["passed"] for c in checks) or score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()