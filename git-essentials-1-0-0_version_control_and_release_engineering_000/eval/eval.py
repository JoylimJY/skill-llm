import subprocess
import sys
import json
import os

def run_git(cmd, cwd):
    result = subprocess.run(
        f"git {cmd}", shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    repo = os.path.join(workspace, "payflow-lib")
    checks = []
    total_score = 0.0
    weights = {
        "feature_validation_merged_noff": 0.20,
        "feature_ledger_merged_noff": 0.20,
        "validation_squashed": 0.15,
        "ledger_squashed": 0.15,
        "annotated_tag_v1": 0.15,
        "security_cherry_picked_main": 0.15,
    }

    # -------------------------------------------------------
    # CHECK 1: feature/payment-validation was merged into main with --no-ff
    # A no-ff merge creates a merge commit (has 2 parents)
    # -------------------------------------------------------
    try:
        log_out, _, _ = run_git("log --oneline --merges main", repo)
        merge_commits = log_out.strip().splitlines()
        
        # Check if any merge commit message references payment-validation
        found_val_merge = False
        for mc in merge_commits:
            hash_part = mc.split()[0]
            show_out, _, _ = run_git(f"show --format=%P -s {hash_part}", repo)
            parents = show_out.strip().split()
            if len(parents) == 2:
                # Check if this merge brought in payment-validation content
                diff_out, _, _ = run_git(f"show {hash_part} --name-only --format=''", repo)
                msg_out, _, _ = run_git(f"log -1 --format=%s {hash_part}", repo)
                # Also check by looking at what the second parent brought
                parent2 = parents[1]
                files_out, _, _ = run_git(f"diff --name-only {parents[0]}...{parent2}", repo)
                if "transaction.py" in files_out or "payment" in msg_out.lower() or "validation" in msg_out.lower():
                    found_val_merge = True
                    break

        # Fallback: check if transaction.py from feature branch is in main
        if not found_val_merge:
            content_out, _, _ = run_git("show main:src/core/transaction.py", repo)
            if "validate" in content_out and ("USD" in content_out or "currency" in content_out or "to_dict" in content_out):
                # The content is there; check if it came via a merge commit
                if len(merge_commits) > 0:
                    found_val_merge = True

        passed_c1 = found_val_merge
        detail_c1 = f"Found {len(merge_commits)} merge commit(s) on main. payment-validation merge detected: {found_val_merge}"
    except Exception as e:
        passed_c1 = False
        detail_c1 = f"Exception: {e}"

    checks.append({"name": "feature_validation_merged_noff", "passed": passed_c1, "detail": detail_c1})
    if passed_c1:
        total_score += weights["feature_validation_merged_noff"]

    # -------------------------------------------------------
    # CHECK 2: feature/ledger-export was merged into main with --no-ff
    # -------------------------------------------------------
    try:
        log_out, _, _ = run_git("log --oneline --merges main", repo)
        merge_commits = log_out.strip().splitlines()

        found_ledger_merge = False
        for mc in merge_commits:
            hash_part = mc.split()[0]
            show_out, _, _ = run_git(f"show --format=%P -s {hash_part}", repo)
            parents = show_out.strip().split()
            if len(parents) == 2:
                parent2 = parents[1]
                files_out, _, _ = run_git(f"diff --name-only {parents[0]}...{parent2}", repo)
                msg_out, _, _ = run_git(f"log -1 --format=%s {hash_part}", repo)
                if "ledger" in files_out or "ledger" in msg_out.lower() or "export" in msg_out.lower():
                    found_ledger_merge = True
                    break

        if not found_ledger_merge:
            # Fallback: check ledger.py content in main
            content_out, _, _ = run_git("show main:src/core/ledger.py", repo)
            if "export_json" in content_out and len(merge_commits) >= 2:
                found_ledger_merge = True

        passed_c2 = found_ledger_merge
        detail_c2 = f"Found {len(merge_commits)} merge commit(s). ledger-export merge detected: {found_ledger_merge}"
    except Exception as e:
        passed_c2 = False
        detail_c2 = f"Exception: {e}"

    checks.append({"name": "feature_ledger_merged_noff", "passed": passed_c2, "detail": detail_c2})
    if passed_c2:
        total_score += weights["feature_ledger_merged_noff"]

    # -------------------------------------------------------
    # CHECK 3: feature/payment-validation was squashed to fewer commits
    # The original branch had 3 commits (wip, fix typo, add tests).
    # After rebase -i squash, it should have ≤ 2 commits bringing those changes.
    # We measure: the merge commit's second parent should have ≤ 2 commits
    # ahead of main's state before that merge, OR we check the branch directly.
    # -------------------------------------------------------
    try:
        # Check the git log for the payment-validation feature content path
        # Find the merge commit that brought in payment-validation
        log_out, _, _ = run_git("log --oneline --merges main", repo)
        merge_commits_lines = log_out.strip().splitlines()

        squashed_val = False
        for mc in merge_commits_lines:
            hash_part = mc.split()[0]
            show_out, _, _ = run_git(f"show --format=%P -s {hash_part}", repo)
            parents = show_out.strip().split()
            if len(parents) == 2:
                parent1, parent2 = parents[0], parents[1]
                files_out, _, _ = run_git(f"diff --name-only {parent1}...{parent2}", repo)
                if "transaction.py" in files_out:
                    # Count commits from parent1 to parent2 (exclusive of parent1)
                    count_out, _, _ = run_git(f"rev-list --count {parent1}..{parent2}", repo)
                    commit_count = int(count_out.strip()) if count_out.strip().isdigit() else 99
                    # Original had 3 commits; after squash should be 1 or 2
                    if commit_count <= 2:
                        squashed_val = True
                    detail_c3 = f"Commits in payment-validation tip vs merge base: {commit_count} (need ≤2 for squash)"
                    break
        else:
            # Branch may still exist
            branch_exists, _, rc = run_git("rev-parse feature/payment-validation", repo)
            if rc == 0:
                count_out, _, _ = run_git("rev-list --count main..feature/payment-validation", repo)
                commit_count = int(count_out.strip()) if count_out.strip().isdigit() else 99
                squashed_val = commit_count <= 2
                detail_c3 = f"Branch still exists with {commit_count} commits ahead of main"
            else:
                detail_c3 = "Could not find payment-validation merge commit or branch"

        passed_c3 = squashed_val
    except Exception as e:
        passed_c3 = False
        detail_c3 = f"Exception: {e}"

    checks.append({"name": "validation_squashed", "passed": passed_c3, "detail": detail_c3})
    if passed_c3:
        total_score += weights["validation_squashed"]

    # -------------------------------------------------------
    # CHECK 4: feature/ledger-export was squashed to fewer commits
    # Original had 3 commits; after rebase -i should have ≤ 2
    # -------------------------------------------------------
    try:
        log_out, _, _ = run_git("log --oneline --merges main", repo)
        merge_commits_lines = log_out.strip().splitlines()

        squashed_ledger = False
        detail_c4 = "No ledger merge commit found"
        for mc in merge_commits_lines:
            hash_part = mc.split()[0]
            show_out, _, _ = run_git(f"show --format=%P -s {hash_part}", repo)
            parents = show_out.strip().split()
            if len(parents) == 2:
                parent1, parent2 = parents[0], parents[1]
                files_out, _, _ = run_git(f"diff --name-only {parent1}...{parent2}", repo)
                if "ledger.py" in files_out:
                    count_out, _, _ = run_git(f"rev-list --count {parent1}..{parent2}", repo)
                    commit_count = int(count_out.strip()) if count_out.strip().isdigit() else 99
                    if commit_count <= 2:
                        squashed_ledger = True
                    detail_c4 = f"Commits in ledger-export tip vs merge base: {commit_count} (need ≤2)"
                    break
        else:
            branch_exists, _, rc = run_git("rev-parse feature/ledger-export", repo)
            if rc == 0:
                count_out, _, _ = run_git("rev-list --count main..feature/ledger-export", repo)
                commit_count = int(count_out.strip()) if count_out.strip().isdigit() else 99
                squashed_ledger = commit_count <= 2
                detail_c4 = f"Branch still exists with {commit_count} commits ahead of main"

        passed_c4 = squashed_ledger
    except Exception as e:
        passed_c4 = False
        detail_c4 = f"Exception: {e}"

    checks.append({"name": "ledger_squashed", "passed": passed_c4, "detail": detail_c4})
    if passed_c4:
        total_score += weights["ledger_squashed"]

    # -------------------------------------------------------
    # CHECK 5: An ANNOTATED tag v1.0.0 exists on main's HEAD (or recent commit)
    # Must be annotated (has a tag object), not lightweight
    # -------------------------------------------------------
    try:
        # Check tag exists
        tag_out, _, rc = run_git("tag -l v1.0.0", repo)
        tag_exists = rc == 0 and "v1.0.0" in tag_out

        is_annotated = False
        tag_detail = ""
        if tag_exists:
            # Annotated tags have type=tag; lightweight tags have type=commit
            type_out, _, _ = run_git("cat-file -t v1.0.0", repo)
            is_annotated = type_out.strip() == "tag"

            # Verify it points to a commit on main
            tag_commit, _, _ = run_git("rev-list -n 1 v1.0.0", repo)
            main_log, _, _ = run_git("log --oneline main", repo)
            tag_on_main = tag_commit.strip() in [l.split()[0] for l in main_log.splitlines()] or tag_commit.strip()[:7] in main_log

            # Verify it has a message
            tag_msg, _, _ = run_git("tag -v v1.0.0 2>&1 || git show v1.0.0 --format=%s -s", repo)

            tag_detail = f"tag exists={tag_exists}, annotated={is_annotated}, on_main={tag_on_main}, type={type_out.strip()}"
        else:
            tag_detail = "Tag v1.0.0 does not exist"

        passed_c5 = tag_exists and is_annotated
    except Exception as e:
        passed_c5 = False
        tag_detail = f"Exception: {e}"

    checks.append({"name": "annotated_tag_v1", "passed": passed_c5, "detail": tag_detail})
    if passed_c5:
        total_score += weights["annotated_tag_v1"]

    # -------------------------------------------------------
    # CHECK 6: Security fix commit was cherry-picked onto main
    # The security fix added isinstance check for Transaction amount
    # We check if main's transaction.py contains the isinstance guard
    # AND that the commit that introduced it on main is NOT the original
    # hotfix branch commit (i.e., it's a cherry-pick = new commit hash)
    # -------------------------------------------------------
    try:
        security_hash_file = os.path.join(repo, ".security_commit_hash")
        original_security_hash = ""
        if os.path.exists(security_hash_file):
            with open(security_hash_file) as f:
                original_security_hash = f.read().strip()

        # Check main's transaction.py has the isinstance guard
        content_out, _, _ = run_git("show main:src/core/transaction.py", repo)
        has_isinstance = "isinstance" in content_out and "TypeError" in content_out

        # Find the commit on main that introduced isinstance
        blame_out, _, _ = run_git("log --oneline --all --follow -- src/core/transaction.py", repo)
        
        cherry_picked = False
        cherry_detail = f"isinstance guard in main: {has_isinstance}"
        
        if has_isinstance:
            # Find which commit on main introduced isinstance
            log_main, _, _ = run_git("log --oneline main", repo)
            for line in log_main.splitlines():
                h = line.split()[0]
                full_h, _, _ = run_git(f"rev-parse {h}", repo)
                show_out, _, _ = run_git(f"show {h} -- src/core/transaction.py", repo)
                if "isinstance" in show_out and "+isinstance" in show_out:
                    # This is the commit that added isinstance on main
                    # It should NOT be the original hotfix commit hash
                    if original_security_hash and full_h.strip() != original_security_hash.strip():
                        cherry_picked = True
                        cherry_detail = f"isinstance found via cherry-pick commit {h} (original was {original_security_hash[:8]})"
                    elif not original_security_hash:
                        # Can't verify original hash, just check content is there
                        cherry_picked = True
                        cherry_detail = f"isinstance found on main at commit {h} (original hash file missing)"
                    else:
                        cherry_detail = f"isinstance found but commit hash {h} matches original hotfix (not cherry-picked?)"
                    break

        passed_c6 = cherry_picked
    except Exception as e:
        passed_c6 = False
        cherry_detail = f"Exception: {e}"

    checks.append({"name": "security_cherry_picked_main", "passed": passed_c6, "detail": cherry_detail})
    if passed_c6:
        total_score += weights["security_cherry_picked_main"]

    # Final output
    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": round(total_score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()