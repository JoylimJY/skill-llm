#!/usr/bin/env python3
"""
Evaluation script for the analytics-sdk release task.
Checks:
1. analytics-sdk version bumped to 2.1.0
2. analytics-core version bumped (1.3.1 -> 1.4.0 or any reasonable bump used as shared dep)
3. analytics-cli version NOT changed (must stay 0.5.2)
4. Workflow YAML bug fixed (no @acme/analytics-sdk-v2 reference)
5. Build artifacts exist for both analytics-core and analytics-sdk
6. A commit with a release-prep message exists after the version bump
7. An ANNOTATED tag v2.1.0 exists (not lightweight)
8. The tag v2.1.0 exists in the remote (bare repo)
9. The release-prep commit was pushed to remote before or alongside the tag
"""

import sys
import json
import subprocess
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def check(name, fn):
    try:
        passed, detail = fn()
    except Exception as e:
        passed, detail = False, f"Exception: {e}"
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

def run_git(*args, cwd=None):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd or workspace),
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode

# ── 1. analytics-sdk version ─────────────────────────────────────────────────

def check_sdk_version():
    pkg = json.loads((workspace / "packages" / "analytics-sdk" / "package.json").read_text())
    v = pkg.get("version", "")
    if v == "2.1.0":
        return True, f"analytics-sdk version is {v}"
    return False, f"analytics-sdk version is {v!r}, expected '2.1.0'"

check("analytics-sdk bumped to 2.1.0", check_sdk_version)

# ── 2. analytics-core version bumped ─────────────────────────────────────────

def check_core_version():
    pkg = json.loads((workspace / "packages" / "analytics-core" / "package.json").read_text())
    v = pkg.get("version", "")
    # Must have been changed from 1.3.1
    if v == "1.3.1":
        return False, f"analytics-core version was NOT bumped (still {v})"
    # Must be a valid semver-ish bump
    parts = v.split(".")
    if len(parts) == 3:
        return True, f"analytics-core bumped to {v}"
    return False, f"analytics-core version '{v}' looks malformed"

check("analytics-core (shared dep) version bumped", check_core_version)

# ── 3. analytics-cli NOT bumped ───────────────────────────────────────────────

def check_cli_unchanged():
    pkg = json.loads((workspace / "packages" / "analytics-cli" / "package.json").read_text())
    v = pkg.get("version", "")
    if v == "0.5.2":
        return True, "analytics-cli version correctly unchanged at 0.5.2"
    return False, f"analytics-cli version changed to {v!r}, should remain 0.5.2"

check("analytics-cli NOT bumped (unrelated package)", check_cli_unchanged)

# ── 4. Workflow YAML bug fixed ────────────────────────────────────────────────

def check_workflow_fix():
    wf = (workspace / ".github" / "workflows" / "release.yml").read_text()
    if "@acme/analytics-sdk-v2" in wf:
        return False, "Old package name '@acme/analytics-sdk-v2' still present in release.yml"
    if "@acme/analytics-sdk" not in wf:
        return False, "Expected '@acme/analytics-sdk' not found in release.yml"
    return True, "release.yml no longer references stale '@acme/analytics-sdk-v2'"

check("Workflow YAML bug fixed (stale package name removed)", check_workflow_fix)

# ── 5. Build artifacts exist ──────────────────────────────────────────────────

def check_builds():
    core_dist = workspace / "packages" / "analytics-core" / "dist" / "index.js"
    sdk_dist  = workspace / "packages" / "analytics-sdk"  / "dist" / "index.js"
    missing = []
    if not core_dist.exists():
        missing.append("analytics-core/dist/index.js")
    if not sdk_dist.exists():
        missing.append("analytics-sdk/dist/index.js")
    if missing:
        return False, f"Missing build artifacts: {missing}"
    return True, "Build artifacts found for analytics-core and analytics-sdk"

check("Build artifacts present for both packages", check_builds)

# ── 6. Release-prep commit exists ─────────────────────────────────────────────

def check_commit_message():
    log, _ = run_git("log", "--oneline", "-20")
    lines = log.splitlines()
    # Look for a commit message that references the release (case-insensitive)
    pattern = re.compile(r"(prepare|release|bump|v2\.1\.0)", re.IGNORECASE)
    for line in lines:
        if pattern.search(line):
            return True, f"Found release-prep commit: {line.strip()}"
    return False, f"No release-prep commit found in recent history:\n{log}"

check("Release-prep commit with appropriate message exists", check_commit_message)

# ── 7. Tag v2.1.0 is ANNOTATED ────────────────────────────────────────────────

def check_annotated_tag():
    # git cat-file -t <tag> returns 'tag' for annotated, 'commit' for lightweight
    result = subprocess.run(
        ["git", "cat-file", "-t", "v2.1.0"],
        cwd=str(workspace),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, "Tag v2.1.0 does not exist locally"
    tag_type = result.stdout.strip()
    if tag_type == "tag":
        return True, "v2.1.0 is an annotated tag object"
    return False, f"v2.1.0 is a '{tag_type}' (lightweight), expected annotated 'tag' object"

check("Tag v2.1.0 is ANNOTATED (not lightweight)", check_annotated_tag)

# ── 8. Tag v2.1.0 pushed to remote ────────────────────────────────────────────

def check_tag_in_remote():
    # Check the bare remote repo directly
    bare_repo = workspace.parent / "remote.git"
    result = subprocess.run(
        ["git", "tag", "-l", "v2.1.0"],
        cwd=str(bare_repo),
        capture_output=True, text=True
    )
    if result.returncode == 0 and "v2.1.0" in result.stdout:
        return True, "Tag v2.1.0 found in remote bare repo"
    # Also check via ls-remote from workspace
    ls, rc = run_git("ls-remote", "--tags", "origin", "v2.1.0")
    if rc == 0 and "v2.1.0" in ls:
        return True, "Tag v2.1.0 found via ls-remote"
    return False, "Tag v2.1.0 NOT found in remote"

check("Tag v2.1.0 pushed to remote", check_tag_in_remote)

# ── 9. Branch commit pushed to remote before tag ─────────────────────────────

def check_branch_pushed():
    # The release-prep commit must exist in the remote's main branch
    # Check: what is the remote HEAD on main?
    remote_head, rc = run_git("ls-remote", "origin", "refs/heads/main")
    if rc != 0 or not remote_head:
        return False, "Could not determine remote HEAD for main"
    remote_sha = remote_head.split()[0] if remote_head else ""

    # Get local HEAD
    local_head, _ = run_git("rev-parse", "HEAD")

    if remote_sha == local_head:
        return True, f"Remote main is up-to-date with local HEAD ({local_head[:12]})"

    # Check if local HEAD is reachable from remote_sha (i.e. remote is ahead or equal)
    # More practically: check if remote has the release-prep commit
    result = subprocess.run(
        ["git", "branch", "-r", "--contains", local_head],
        cwd=str(workspace),
        capture_output=True, text=True
    )
    if result.returncode == 0 and "origin/main" in result.stdout:
        return True, f"Release-prep commit {local_head[:12]} is present on remote/main"

    # Final check: compare counts
    ahead, _ = run_git("rev-list", "--count", f"{remote_sha}..HEAD")
    if ahead == "0":
        return True, "Local HEAD is not ahead of remote (branch was pushed)"
    return False, f"Local main is {ahead} commit(s) ahead of remote — branch not fully pushed"

check("Release-prep branch pushed to remote", check_branch_pushed)

# ── summary ───────────────────────────────────────────────────────────────────

passed_checks = [c for c in checks if c["passed"]]
score = len(passed_checks) / len(checks)
all_passed = len(passed_checks) == len(checks)

output = {
    "passed": all_passed,
    "score": round(score, 4),
    "checks": checks
}

print(json.dumps(output, indent=2))