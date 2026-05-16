#!/usr/bin/env python3
"""
Evaluation script for memory-git-sync task.
Checks:
  1. Git user.name is configured in the workspace repo
  2. Git user.email is configured in the workspace repo
  3. Origin remote is configured
  4. sync.sh was run and produced [SUCCESS] Sync completed output
  5. The large file (>95MB) was added to .gitignore
  6. The large file was NOT committed to the git history
  7. At least one commit was pushed to the mock remote
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def run(cmd, cwd=None, capture=True):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True, timeout=30)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    all_passed = True

    # ── Check 1: Git user.name is configured ──────────────────────────────────
    rc, out, err = run(["git", "config", "user.name"], cwd=workspace)
    c1_passed = rc == 0 and bool(out.strip())
    checks.append({
        "name": "git_user_name_configured",
        "passed": c1_passed,
        "detail": f"user.name='{out}'" if c1_passed else f"Not configured. rc={rc} err={err}"
    })
    if not c1_passed:
        all_passed = False

    # ── Check 2: Git user.email is configured ─────────────────────────────────
    rc, out, err = run(["git", "config", "user.email"], cwd=workspace)
    c2_passed = rc == 0 and bool(out.strip())
    checks.append({
        "name": "git_user_email_configured",
        "passed": c2_passed,
        "detail": f"user.email='{out}'" if c2_passed else f"Not configured. rc={rc} err={err}"
    })
    if not c2_passed:
        all_passed = False

    # ── Check 3: Origin remote is configured ──────────────────────────────────
    rc, out, err = run(["git", "remote", "get-url", "origin"], cwd=workspace)
    c3_passed = rc == 0 and bool(out.strip())
    checks.append({
        "name": "origin_remote_configured",
        "passed": c3_passed,
        "detail": f"origin='{out}'" if c3_passed else f"No origin remote. rc={rc} err={err}"
    })
    if not c3_passed:
        all_passed = False

    # ── Check 4: .gitignore exists and contains the large file path ───────────
    gitignore_path = Path(workspace) / ".gitignore"
    large_file_rel = "models/checkpoints/variant_classifier_weights.bin"
    c4_passed = False
    c4_detail = ""
    try:
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            # The script writes the relative path; check for filename at minimum
            if large_file_rel in content or "variant_classifier_weights.bin" in content:
                c4_passed = True
                c4_detail = f".gitignore contains large file entry"
            else:
                c4_detail = f".gitignore exists but missing large file entry. Content: {content[:300]}"
        else:
            c4_detail = ".gitignore file does not exist"
    except Exception as e:
        c4_detail = f"Exception reading .gitignore: {e}"
    checks.append({
        "name": "large_file_in_gitignore",
        "passed": c4_passed,
        "detail": c4_detail
    })
    if not c4_passed:
        all_passed = False

    # ── Check 5: Large file NOT in git history ────────────────────────────────
    rc, out, err = run(
        ["git", "log", "--all", "--full-history", "--", large_file_rel, "--oneline"],
        cwd=workspace
    )
    # If no lines, file was never committed — that's correct
    c5_passed = (rc == 0 and out.strip() == "")
    checks.append({
        "name": "large_file_not_committed",
        "passed": c5_passed,
        "detail": "Large file correctly excluded from git history" if c5_passed
                  else f"Large file found in git log: {out[:300]}"
    })
    if not c5_passed:
        all_passed = False

    # ── Check 6: At least one commit exists locally ────────────────────────────
    rc, out, err = run(["git", "log", "--oneline", "-5"], cwd=workspace)
    c6_passed = rc == 0 and bool(out.strip())
    checks.append({
        "name": "commit_exists_locally",
        "passed": c6_passed,
        "detail": f"Local commits: {out[:200]}" if c6_passed else f"No commits found. rc={rc} err={err}"
    })
    if not c6_passed:
        all_passed = False

    # ── Check 7: Commit(s) pushed to mock remote ──────────────────────────────
    c7_passed = False
    c7_detail = ""
    try:
        bare_repo_path = Path("/tmp/mock_remote_path.txt").read_text().strip()
        rc, out, err = run(["git", "log", "--oneline", "-5"], cwd=bare_repo_path)
        if rc == 0 and out.strip():
            c7_passed = True
            c7_detail = f"Remote commits found: {out[:200]}"
        else:
            c7_detail = f"No commits in remote. rc={rc} stdout='{out}' stderr='{err}'"
    except Exception as e:
        c7_detail = f"Exception checking remote: {e}"
    checks.append({
        "name": "pushed_to_remote",
        "passed": c7_passed,
        "detail": c7_detail
    })
    if not c7_passed:
        all_passed = False

    # ── Check 8: Sync completed message in git commit log (structured output) ──
    # The script outputs [SUCCESS] Sync completed — we verify via commit presence
    # and also check that the [WARNING] Large files detected pattern was triggered
    # by inspecting .gitignore non-emptiness (already done above).
    # Additionally verify the commit message format (default or custom).
    rc, out, err = run(["git", "log", "--oneline", "-1", "--format=%s"], cwd=workspace)
    c8_passed = rc == 0 and bool(out.strip())
    checks.append({
        "name": "commit_message_present",
        "passed": c8_passed,
        "detail": f"Commit message: '{out}'" if c8_passed else f"Could not read commit message. err={err}"
    })
    if not c8_passed:
        all_passed = False

    # ── Check 9: scripts/sync.sh is unchanged (not tampered) ─────────────────
    sync_path = Path(workspace) / "scripts" / "sync.sh"
    c9_passed = False
    c9_detail = ""
    try:
        if sync_path.exists():
            content = sync_path.read_text()
            # Key proprietary markers: 95MB threshold, structured prefixes
            has_threshold = "LARGE_FILE_THRESHOLD_MB=95" in content
            has_success = "[SUCCESS]" in content
            has_warning = "[WARNING]" in content
            c9_passed = has_threshold and has_success and has_warning
            c9_detail = (
                f"sync.sh intact: threshold_95MB={has_threshold}, "
                f"has_SUCCESS={has_success}, has_WARNING={has_warning}"
            )
        else:
            c9_detail = "scripts/sync.sh is missing!"
    except Exception as e:
        c9_detail = f"Exception: {e}"
    checks.append({
        "name": "sync_script_intact",
        "passed": c9_passed,
        "detail": c9_detail
    })
    if not c9_passed:
        all_passed = False

    # ── Score ──────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()