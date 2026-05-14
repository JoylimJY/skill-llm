#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw safe-update task.
Usage: python3 eval.py /workspace
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
AGENT_HOME = Path("/home/agent")
PROJECT_DIR = WORKSPACE / "projects" / "my-openclaw"
BACKUP_DIR = AGENT_HOME / ".openclaw" / "backups"


def run(cmd, cwd=None, user="agent"):
    """Run a shell command as agent user."""
    if user == "agent":
        full_cmd = f"su - agent -c {repr(cmd)}"
    else:
        full_cmd = cmd
    result = subprocess.run(
        full_cmd, shell=True, capture_output=True, text=True,
        cwd=str(cwd) if cwd else None
    )
    return result


checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    status = "✅" if passed else "❌"
    print(f"  {status} {name}: {detail}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: dry_run_report.txt exists somewhere in workspace or agent home
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 1: dry_run_report.txt exists ===")
try:
    # Search in workspace and agent home
    report_candidates = list(WORKSPACE.rglob("dry_run_report.txt")) + \
                        list(AGENT_HOME.rglob("dry_run_report.txt"))
    if report_candidates:
        report_path = report_candidates[0]
        report_content = report_path.read_text()
        add_check(
            "dry_run_report.txt exists",
            True,
            f"Found at {report_path} ({len(report_content)} bytes)"
        )
    else:
        add_check(
            "dry_run_report.txt exists",
            False,
            "File not found anywhere in workspace or /home/agent"
        )
        report_content = ""
        report_path = None
except Exception as e:
    add_check("dry_run_report.txt exists", False, f"Error: {e}")
    report_content = ""
    report_path = None


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: dry-run report contains DRY-RUN markers from update.sh
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 2: dry-run report content is valid ===")
try:
    if report_content:
        # Must contain the [DRY-RUN] marker from the script
        has_dry_run_marker = "[DRY-RUN]" in report_content
        # Must mention the key operations that would be skipped
        has_no_changes = (
            "no changes" in report_content.lower() or
            "dry-run complete" in report_content.lower() or
            "no actual changes" in report_content.lower() or
            "dry run complete" in report_content.lower()
        )
        # Must mention npm or build step
        has_build_mention = "npm" in report_content or "build" in report_content.lower()

        all_ok = has_dry_run_marker and (has_no_changes or has_build_mention)
        detail = (
            f"DRY-RUN marker={'✓' if has_dry_run_marker else '✗'}, "
            f"no-changes indicator={'✓' if has_no_changes else '✗'}, "
            f"build mention={'✓' if has_build_mention else '✗'}"
        )
        add_check("dry-run report content valid", all_ok, detail)
    else:
        add_check("dry-run report content valid", False, "No report content to check")
except Exception as e:
    add_check("dry-run report content valid", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: dry-run report was generated with correct --dir and --branch flags
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 3: correct --dir and --branch used in dry-run ===")
try:
    if report_content:
        # The script echoes "Project dir : ..." and "Branch : ..."
        has_custom_dir = (
            "my-openclaw" in report_content or
            str(PROJECT_DIR) in report_content or
            "/workspace/projects" in report_content
        )
        has_custom_branch = "dev/integration" in report_content

        detail = (
            f"Custom dir (my-openclaw) present={'✓' if has_custom_dir else '✗'}, "
            f"Branch (dev/integration) present={'✓' if has_custom_branch else '✗'}"
        )
        add_check(
            "correct --dir and --branch in dry-run",
            has_custom_dir and has_custom_branch,
            detail
        )
    else:
        add_check("correct --dir and --branch in dry-run", False, "No report content")
except Exception as e:
    add_check("correct --dir and --branch in dry-run", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: Actual update was executed (package.json updated to 2.4.0)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 4: Actual update executed (version bumped) ===")
try:
    pkg_path = PROJECT_DIR / "package.json"
    if pkg_path.exists():
        pkg_data = json.loads(pkg_path.read_text())
        version = pkg_data.get("version", "")
        is_updated = version == "2.4.0"
        add_check(
            "package.json version updated to 2.4.0",
            is_updated,
            f"Found version: '{version}' (expected '2.4.0')"
        )
    else:
        add_check("package.json version updated to 2.4.0", False, "package.json not found")
except Exception as e:
    add_check("package.json version updated to 2.4.0", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Git branch is dev/integration and has merged upstream commits
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 5: git branch state after update ===")
try:
    branch_result = run(
        f"cd {PROJECT_DIR} && git rev-parse --abbrev-ref HEAD"
    )
    current_branch = branch_result.stdout.strip()
    is_correct_branch = current_branch == "dev/integration"

    # Check that the upstream commit is in the local history
    log_result = run(
        f"cd {PROJECT_DIR} && git log --oneline -5"
    )
    has_upstream_commit = (
        "v2.4.0" in log_result.stdout or
        "router" in log_result.stdout or
        "new router" in log_result.stdout or
        "2.4.0" in log_result.stdout
    )

    detail = (
        f"Branch='{current_branch}' (expected 'dev/integration'), "
        f"upstream commit merged={'✓' if has_upstream_commit else '✗'}, "
        f"log: {log_result.stdout[:100].strip()}"
    )
    add_check(
        "correct branch and upstream merged",
        is_correct_branch and has_upstream_commit,
        detail
    )
except Exception as e:
    add_check("correct branch and upstream merged", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: --mode merge was used (not rebase) — clean commit history
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 6: merge mode used (appropriate for clean working tree) ===")
try:
    # Check git log for a merge commit (merge produces a merge commit, rebase doesn't)
    log_result = run(
        f"cd {PROJECT_DIR} && git log --oneline --merges -5"
    )
    has_merge_commit = bool(log_result.stdout.strip())

    # Alternative: check if upstream commits are in history via rebase (no merge commit)
    # Either merge or rebase is acceptable per the SKILL.md for clean working tree,
    # but the agent should have used --mode (not omitted it for production safety)
    # We check that the update actually happened regardless of method
    all_commits = run(f"cd {PROJECT_DIR} && git log --oneline -10")
    upstream_in_history = (
        "2.4.0" in all_commits.stdout or
        "router" in all_commits.stdout or
        "feat:" in all_commits.stdout
    )

    detail = (
        f"Merge commit found={'✓' if has_merge_commit else '—(rebase used)'}, "
        f"upstream in history={'✓' if upstream_in_history else '✗'}"
    )
    add_check(
        "update mode applied and upstream integrated",
        upstream_in_history,
        detail
    )
except Exception as e:
    add_check("update mode applied and upstream integrated", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: Config backup files exist in ~/.openclaw/backups/
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 7: Config backup files exist ===")
try:
    backup_files = list(BACKUP_DIR.glob("openclaw.json.bak.*")) if BACKUP_DIR.exists() else []
    backup_suffix_pattern = re.compile(r"openclaw\.json\.bak\.\d{8}-\d{6}$")
    valid_backups = [f for f in backup_files if backup_suffix_pattern.match(f.name)]

    has_valid_backup = len(valid_backups) > 0
    detail = (
        f"Backup dir exists={'✓' if BACKUP_DIR.exists() else '✗'}, "
        f"valid backups found={len(valid_backups)}, "
        f"files: {[f.name for f in valid_backups[:3]]}"
    )
    add_check("openclaw.json backup with correct naming", has_valid_backup, detail)
except Exception as e:
    add_check("openclaw.json backup with correct naming", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: auth-profiles.json was also backed up
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 8: auth-profiles.json backup ===")
try:
    auth_backups = list(BACKUP_DIR.glob("auth-profiles.json.bak.*")) if BACKUP_DIR.exists() else []
    auth_suffix_pattern = re.compile(r"auth-profiles\.json\.bak\.\d{8}-\d{6}$")
    valid_auth_backups = [f for f in auth_backups if auth_suffix_pattern.match(f.name)]

    has_valid_auth_backup = len(valid_auth_backups) > 0
    detail = (
        f"Valid auth-profiles backups found={len(valid_auth_backups)}, "
        f"files: {[f.name for f in valid_auth_backups[:3]]}"
    )
    add_check("auth-profiles.json backup with correct naming", has_valid_auth_backup, detail)
except Exception as e:
    add_check("auth-profiles.json backup with correct naming", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: npm build was executed (dist/ directory exists)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Check 9: npm run build was executed ===")
try:
    dist_dir = PROJECT_DIR / "dist"
    dist_exists = dist_dir.exists()
    dist_files = list(dist_dir.iterdir()) if dist_exists else []

    detail = (
        f"dist/ dir exists={'✓' if dist_exists else '✗'}, "
        f"files in dist/: {[f.name for f in dist_files[:5]]}"
    )
    add_check("npm build artifacts present (dist/)", dist_exists and len(dist_files) > 0, detail)
except Exception as e:
    add_check("npm build artifacts present (dist/)", False, f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)

# Critical checks that must pass for overall pass
critical = [
    "dry_run_report.txt exists",
    "dry-run report content valid",
    "package.json version updated to 2.4.0",
    "openclaw.json backup with correct naming",
]
critical_passed = all(
    c["passed"] for c in checks if c["name"] in critical
)

overall_passed = critical_passed and score >= 0.70

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(f"\n=== RESULT: {'PASSED' if overall_passed else 'FAILED'} ===")
print(f"Score: {passed_count}/{total} = {score}")
print(json.dumps(result, indent=2))