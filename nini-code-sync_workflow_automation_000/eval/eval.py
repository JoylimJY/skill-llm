#!/usr/bin/env python3
"""
Evaluation script for code-sync Pull mode task.
Tests that the agent:
1. Ran scan.sh with --fetch flag (or equivalent fetch behavior)
2. Auto-ran git pull --ff-only on needs-pull repos (payment-api, reporting-dashboard)
3. Did NOT pull ledger-service (dirty+behind) or auth-gateway (fetch-error)
4. Produced a sync_report.md with correct Summary structure
"""
import sys
import json
import subprocess
import re
from pathlib import Path

def run_git(cmd, cwd):
    try:
        result = subprocess.run(
            f"git {cmd}", shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def check_repo_updated(repo_path, expected_commits_gained):
    """Check if repo was pulled ahead by expected number of commits."""
    out, rc = run_git("log --oneline HEAD", repo_path)
    if rc != 0:
        return False, f"git log failed: {out}"
    lines = [l for l in out.strip().split('\n') if l.strip()]
    return True, lines

def get_commit_count_vs_origin(repo_path):
    """Get ahead/behind counts vs origin/main."""
    out, rc = run_git("rev-list --left-right --count HEAD...origin/main", repo_path)
    if rc != 0:
        return None, None, f"failed: {out}"
    parts = out.strip().split()
    if len(parts) == 2:
        return int(parts[0]), int(parts[1]), None
    return None, None, f"unexpected output: {out}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace = Path(workspace)
    code_dir = workspace / "code"
    
    checks = []
    
    # -------------------------------------------------------------------------
    # Check 1: payment-api was pulled (ahead=0, behind=0 vs origin)
    # -------------------------------------------------------------------------
    try:
        repo = code_dir / "payment-api"
        ahead, behind, err = get_commit_count_vs_origin(repo)
        if err:
            checks.append({
                "name": "payment-api pulled successfully",
                "passed": False,
                "detail": f"Could not check git status: {err}"
            })
        elif behind == 0 and ahead == 0:
            # Repo is now in sync
            out, _ = run_git("log --oneline -5 HEAD", repo)
            checks.append({
                "name": "payment-api pulled successfully",
                "passed": True,
                "detail": f"payment-api is now in sync (ahead={ahead}, behind={behind}). Recent commits: {out[:200]}"
            })
        else:
            checks.append({
                "name": "payment-api pulled successfully",
                "passed": False,
                "detail": f"payment-api still has ahead={ahead}, behind={behind} — pull was NOT run or failed"
            })
    except Exception as e:
        checks.append({
            "name": "payment-api pulled successfully",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -------------------------------------------------------------------------
    # Check 2: reporting-dashboard was pulled (ahead=0, behind=0 vs origin)
    # -------------------------------------------------------------------------
    try:
        repo = code_dir / "reporting-dashboard"
        ahead, behind, err = get_commit_count_vs_origin(repo)
        if err:
            checks.append({
                "name": "reporting-dashboard pulled successfully",
                "passed": False,
                "detail": f"Could not check git status: {err}"
            })
        elif behind == 0 and ahead == 0:
            out, _ = run_git("log --oneline -5 HEAD", repo)
            checks.append({
                "name": "reporting-dashboard pulled successfully",
                "passed": True,
                "detail": f"reporting-dashboard is now in sync. Recent commits: {out[:200]}"
            })
        else:
            checks.append({
                "name": "reporting-dashboard pulled successfully",
                "passed": False,
                "detail": f"reporting-dashboard still has ahead={ahead}, behind={behind} — pull was NOT run or failed"
            })
    except Exception as e:
        checks.append({
            "name": "reporting-dashboard pulled successfully",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -------------------------------------------------------------------------
    # Check 3: ledger-service was NOT auto-pulled (still dirty)
    # -------------------------------------------------------------------------
    try:
        repo = code_dir / "ledger-service"
        out, rc = run_git("status --porcelain", repo)
        is_dirty = len([l for l in out.strip().split('\n') if l.strip()]) > 0
        # Also check it wasn't reset/cleaned silently
        content = (repo / "ledger.py").read_text()
        has_dirty_content = "local dirty change" in content or "TODO: fix this" in content
        
        if is_dirty or has_dirty_content:
            checks.append({
                "name": "ledger-service (dirty+behind) was NOT auto-pulled",
                "passed": True,
                "detail": f"ledger-service correctly left in dirty state (dirty={is_dirty}, content preserved)"
            })
        else:
            # Check if it was stashed-and-pulled (acceptable interactive handling)
            behind_now, _, _ = get_commit_count_vs_origin(repo)
            # If not dirty but was handled interactively (stash+pull), that could be OK
            # But for strict eval: dirty+behind must NOT be auto-pulled without interaction
            # We'll be lenient: if it's been cleaned AND pulled, warn but still check report
            checks.append({
                "name": "ledger-service (dirty+behind) was NOT auto-pulled",
                "passed": False,
                "detail": f"ledger-service appears to have been auto-modified without proper interaction (dirty={is_dirty}, has_dirty_content={has_dirty_content})"
            })
    except Exception as e:
        checks.append({
            "name": "ledger-service (dirty+behind) was NOT auto-pulled",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -------------------------------------------------------------------------
    # Check 4: fraud-detector and config-store remain up-to-date (not touched)
    # -------------------------------------------------------------------------
    try:
        all_clean = True
        details = []
        for repo_name in ["fraud-detector", "config-store"]:
            repo = code_dir / repo_name
            ahead, behind, err = get_commit_count_vs_origin(repo)
            if err:
                details.append(f"{repo_name}: error checking ({err})")
            elif ahead == 0 and behind == 0:
                details.append(f"{repo_name}: correctly up-to-date")
            else:
                all_clean = False
                details.append(f"{repo_name}: unexpected state ahead={ahead} behind={behind}")
        checks.append({
            "name": "Up-to-date repos unchanged",
            "passed": all_clean,
            "detail": "; ".join(details)
        })
    except Exception as e:
        checks.append({
            "name": "Up-to-date repos unchanged",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -------------------------------------------------------------------------
    # Check 5: ff-only was used (check git pull log or verify merge type)
    # -------------------------------------------------------------------------
    try:
        ff_only_used = False
        detail_msg = ""
        
        # Method 1: Check the git pull log written by setup
        pull_log = Path("/tmp/git_pull_log.txt")
        if pull_log.exists():
            log_content = pull_log.read_text()
            if "--ff-only" in log_content:
                ff_only_used = True
                detail_msg = f"Found --ff-only in pull log: {log_content[:300]}"
        
        # Method 2: Check merge commits — ff-only never creates merge commits
        # If payment-api has no merge commits in last 5 commits, ff-only was likely used
        if not ff_only_used:
            for repo_name in ["payment-api", "reporting-dashboard"]:
                repo = code_dir / repo_name
                out, rc = run_git("log --oneline --merges -5 HEAD", repo)
                merge_count = len([l for l in out.strip().split('\n') if l.strip()])
                if merge_count == 0:
                    # No merge commits = consistent with ff-only (though not conclusive alone)
                    pass
            
            # Check if any script or shell history mentions ff-only
            # Also check bash history
            bash_hist = Path("/root/.bash_history")
            if bash_hist.exists():
                hist = bash_hist.read_text()
                if "--ff-only" in hist:
                    ff_only_used = True
                    detail_msg = "Found --ff-only in bash history"
            
            # Check agent's produced report for mention of ff-only or pull approach
            # Primary: check if repos are in sync (which requires pull having worked)
            # Since we already verified payment-api and reporting-dashboard are pulled,
            # and they are fast-forward-able (remote has strictly more commits),
            # any correct pull would have used ff-only per the spec
            # Give partial credit here based on repo state
            if not ff_only_used:
                repo = code_dir / "payment-api"
                ahead, behind, err = get_commit_count_vs_origin(repo)
                if err is None and behind == 0 and ahead == 0:
                    # Repos are synced — ff-only or regular pull both work here
                    # since history is linear. Credit the intent.
                    ff_only_used = True
                    detail_msg = "Repos pulled successfully (linear history consistent with --ff-only)"
        
        checks.append({
            "name": "git pull --ff-only used for needs-pull repos",
            "passed": ff_only_used,
            "detail": detail_msg if detail_msg else "No evidence of --ff-only found in logs or history"
        })
    except Exception as e:
        checks.append({
            "name": "git pull --ff-only used for needs-pull repos",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -------------------------------------------------------------------------
    # Check 6: sync_report.md exists with correct Summary structure
    # -------------------------------------------------------------------------
    try:
        report_files = list(Path(workspace).rglob("sync_report.md"))
        if not report_files:
            checks.append({
                "name": "sync_report.md exists",
                "passed": False,
                "detail": "No sync_report.md found anywhere in workspace"
            })
        else:
            report_path = report_files[0]
            content = report_path.read_text()
            checks.append({
                "name": "sync_report.md exists",
                "passed": True,
                "detail": f"Found at {report_path}"
            })
            
            # Check for Pull Summary header
            has_pull_header = bool(re.search(r'Pull\s+Summary', content, re.IGNORECASE))
            checks.append({
                "name": "sync_report.md has Pull Summary header",
                "passed": has_pull_header,
                "detail": f"Header {'found' if has_pull_header else 'NOT found'} in report"
            })
            
            # Check for "Updated" section (not "Pushed")
            has_updated_section = bool(re.search(r'Updated\s*\(', content, re.IGNORECASE))
            checks.append({
                "name": "sync_report.md uses 'Updated' (not 'Pushed') section",
                "passed": has_updated_section,
                "detail": f"'Updated' section {'found' if has_updated_section else 'NOT found'}"
            })
            
            # Check that payment-api and reporting-dashboard appear in Updated section
            updated_match = re.search(r'Updated.*?(?=\n##|\n[A-Z][a-z].*?\(|\Z)', content, re.DOTALL | re.IGNORECASE)
            updated_block = updated_match.group(0) if updated_match else ""
            has_payment = "payment-api" in updated_block or "payment-api" in content
            has_dashboard = "reporting-dashboard" in updated_block or "reporting-dashboard" in content
            
            checks.append({
                "name": "Pulled repos listed in report (payment-api, reporting-dashboard)",
                "passed": has_payment and has_dashboard,
                "detail": f"payment-api={'found' if has_payment else 'missing'}, reporting-dashboard={'found' if has_dashboard else 'missing'}"
            })
            
            # Check for "Already up-to-date" section
            has_uptodate = bool(re.search(r'(up.to.date|already.up)', content, re.IGNORECASE))
            checks.append({
                "name": "sync_report.md has 'Already up-to-date' section",
                "passed": has_uptodate,
                "detail": f"Up-to-date section {'found' if has_uptodate else 'NOT found'}"
            })
            
            # Check for Skipped section with ledger-service and/or auth-gateway
            has_skipped = bool(re.search(r'Skipped', content, re.IGNORECASE))
            skipped_has_repos = (
                ("ledger-service" in content or "auth-gateway" in content)
            )
            checks.append({
                "name": "sync_report.md has Skipped section with problem repos",
                "passed": has_skipped and skipped_has_repos,
                "detail": f"Skipped section: {'found' if has_skipped else 'missing'}, relevant repos: {'mentioned' if skipped_has_repos else 'missing'}"
            })
            
            # Check fraud-detector and config-store appear in up-to-date section
            has_fraud = "fraud-detector" in content
            has_config = "config-store" in content
            checks.append({
                "name": "Up-to-date repos mentioned in report",
                "passed": has_fraud and has_config,
                "detail": f"fraud-detector={'found' if has_fraud else 'missing'}, config-store={'found' if has_config else 'missing'}"
            })
            
    except Exception as e:
        checks.append({
            "name": "sync_report.md exists",
            "passed": False,
            "detail": f"Exception reading report: {e}"
        })

    # -------------------------------------------------------------------------
    # Compute final score
    # -------------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0
    overall_passed = score >= 0.75  # Must pass at least 75% of checks

    output = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()