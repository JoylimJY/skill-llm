#!/usr/bin/env python3
"""
Generate the sandbox workspace for the git-manager evaluation task.
Simulates a pharmaceutical compliance software repository with messy,
realistic project structure. The agent must use git-manager to:
1. Create a feature branch from main
2. Commit only two specific config files (not all changed files)
3. Capture the commit SHA for audit
"""

import os
import subprocess
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create a realistic git repository ──────────────────────────────────────
repo_dir = WORKSPACE / "pharma-compliance-system"
repo_dir.mkdir(parents=True, exist_ok=True)

# Initialize git repo
subprocess.run(["git", "init", str(repo_dir)], check=True, capture_output=True)
subprocess.run(["git", "-C", str(repo_dir), "config", "user.email", "agent@testenv.local"], check=True)
subprocess.run(["git", "-C", str(repo_dir), "config", "user.name", "Test Agent"], check=True)

# ── 2. Create deeply nested project structure (distractor files) ──────────────
dirs = [
    "src/core/validation",
    "src/core/reporting",
    "src/api/endpoints",
    "src/api/middleware",
    "src/database/migrations",
    "src/database/models",
    "tests/unit/core",
    "tests/integration",
    "docs/compliance",
    "scripts/deploy",
    "configs/environments",
    "configs/features",
]

for d in dirs:
    (repo_dir / d).mkdir(parents=True, exist_ok=True)

# ── 3. Create distractor source files ─────────────────────────────────────────
files = {
    "src/core/validation/drug_validator.py": '''\
"""Drug compound validation module."""
import re

VALID_COMPOUND_PATTERN = re.compile(r"^[A-Z]{2,4}-\\d{4,6}$")

def validate_compound_id(compound_id: str) -> bool:
    return bool(VALID_COMPOUND_PATTERN.match(compound_id))

def validate_batch(batch_data: list) -> dict:
    results = {}
    for item in batch_data:
        results[item["id"]] = validate_compound_id(item["compound_id"])
    return results
''',
    "src/core/reporting/audit_report.py": '''\
"""Audit report generation for regulatory submissions."""
from datetime import datetime

class AuditReport:
    def __init__(self, trial_id: str):
        self.trial_id = trial_id
        self.generated_at = datetime.utcnow().isoformat()
        self.entries = []

    def add_entry(self, action: str, user: str, data: dict):
        self.entries.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": user,
            "data": data
        })

    def to_dict(self):
        return {
            "trial_id": self.trial_id,
            "generated_at": self.generated_at,
            "entries": self.entries
        }
''',
    "src/api/endpoints/trials.py": '''\
"""Clinical trials API endpoints."""
from typing import Optional

def get_trial(trial_id: str) -> Optional[dict]:
    # TODO: integrate with database
    return None

def create_trial(data: dict) -> dict:
    # Placeholder
    return {"status": "created", "trial_id": data.get("id")}
''',
    "src/api/middleware/auth.py": '''\
"""Authentication middleware."""

def require_gmp_role(role: str):
    VALID_ROLES = ["qa_manager", "data_analyst", "sys_admin", "auditor"]
    def decorator(fn):
        def wrapper(*args, **kwargs):
            # Role check placeholder
            return fn(*args, **kwargs)
        return wrapper
    return decorator
''',
    "src/database/models/compound.py": '''\
"""Compound data model."""

class Compound:
    def __init__(self, compound_id: str, name: str, cas_number: str):
        self.compound_id = compound_id
        self.name = name
        self.cas_number = cas_number
        self.status = "pending"

    def approve(self):
        self.status = "approved"

    def reject(self, reason: str):
        self.status = "rejected"
        self.rejection_reason = reason
''',
    "src/database/migrations/0001_initial.sql": '''\
-- Initial schema for pharma compliance system
CREATE TABLE compounds (
    id SERIAL PRIMARY KEY,
    compound_id VARCHAR(20) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    cas_number VARCHAR(30),
    status VARCHAR(20) DEFAULT \'pending\',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    user_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
''',
    "tests/unit/core/test_validator.py": '''\
"""Unit tests for drug validator."""
import pytest

def test_valid_compound_id():
    # Placeholder test
    assert True

def test_invalid_compound_id():
    assert True
''',
    "tests/integration/test_api.py": '''\
"""Integration tests for API endpoints."""
import pytest

class TestTrialsEndpoint:
    def test_create_trial(self):
        assert True

    def test_get_trial_not_found(self):
        assert True
''',
    "scripts/deploy/rollout.sh": '''\
#!/bin/bash
# Production rollout script
set -euo pipefail
echo "Starting GMP-compliant deployment..."
echo "Version: ${DEPLOY_VERSION:-unknown}"
echo "Environment: ${DEPLOY_ENV:-staging}"
''',
    "docs/compliance/21CFR11_checklist.md": '''\
# 21 CFR Part 11 Compliance Checklist

## Electronic Records
- [ ] Audit trail enabled
- [ ] Time-stamped records
- [ ] Unique user IDs

## Electronic Signatures  
- [ ] Signature manifestations
- [ ] Non-repudiation controls
''',
    "docs/compliance/gmp_guidelines.md": '''\
# GMP Software Development Guidelines

## Change Control
All changes to validated systems must follow the change control SOP.
Branch protection on `main` is mandatory.

## Version Control Requirements
- Feature branches required for all changes
- Commit messages must follow conventional commits format
- SHA signatures logged for all production commits
''',
    ".gitignore": '''\
__pycache__/
*.pyc
*.pyo
.env
*.egg-info/
dist/
build/
.pytest_cache/
*.log
''',
    "pyproject.toml": '''\
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.black]
line-length = 100
''',
}

for rel_path, content in files.items():
    full_path = repo_dir / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ── 4. Make the initial commit on main ────────────────────────────────────────
subprocess.run(["git", "-C", str(repo_dir), "add", "."], check=True, capture_output=True)
subprocess.run(
    ["git", "-C", str(repo_dir), "commit", "-m", "chore: initial project scaffold"],
    check=True, capture_output=True
)

# ── 5. Create the TWO TARGET CONFIG FILES that need committing ─────────────────
# These files simulate updated compliance configurations that QA approved.
# They are UNSTAGED and represent the files the agent must selectively commit.

dosing_config = repo_dir / "configs/features/dosing_limits.yaml"
dosing_config.write_text("""\
# Dosing limits configuration - QA approved 2024-Q4
# Change ticket: CHG-20241105-0047
version: "2.1.0"
approved_by: "dr.chen@pharma.local"
approval_date: "2024-11-05"

compounds:
  ATORV-004521:
    max_daily_dose_mg: 80
    warning_threshold_mg: 60
    pediatric_max_mg: 10
    renal_adjustment: true

  METFO-009934:
    max_daily_dose_mg: 2000
    warning_threshold_mg: 1500
    pediatric_max_mg: 500
    renal_adjustment: false

  OMEP-001128:
    max_daily_dose_mg: 40
    warning_threshold_mg: 20
    pediatric_max_mg: 10
    renal_adjustment: false

monitoring:
  alert_on_exceed: true
  notify_email: "safety-alerts@pharma.local"
  log_all_dispensing: true
""")

adverse_events_config = repo_dir / "configs/environments/adverse_events_thresholds.yaml"
adverse_events_config.write_text("""\
# Adverse event reporting thresholds - Regulatory update
# Aligned with EMA/CHMP/ICH E2A guidelines
# Change ticket: CHG-20241105-0048
version: "1.4.2"
approved_by: "regulatory.affairs@pharma.local"
approval_date: "2024-11-05"

severity_levels:
  mild:
    auto_report: false
    review_window_days: 30
  moderate:
    auto_report: false
    review_window_days: 7
    requires_investigator_sign: true
  severe:
    auto_report: true
    report_within_hours: 72
    requires_investigator_sign: true
    notify_authorities: ["EMA", "FDA"]
  life_threatening:
    auto_report: true
    report_within_hours: 24
    requires_investigator_sign: true
    notify_authorities: ["EMA", "FDA", "MHRA"]
    escalate_to_cmo: true

expedited_reporting:
  enabled: true
  icsrs_format: "E2B(R3)"
  gateway: "eudravigilance"
""")

# ── 6. Create DISTRACTOR MODIFIED files that should NOT be committed ───────────
# These simulate work-in-progress that must be excluded from the compliance commit.

wip_endpoint = repo_dir / "src/api/endpoints/laboratory.py"
wip_endpoint.write_text("""\
\"\"\"Laboratory results API - WORK IN PROGRESS - DO NOT COMMIT\"\"\"
# TODO: This module is incomplete and not yet validated
# QA has not approved this for commit

def get_lab_results(sample_id: str):
    # STUB - not implemented
    raise NotImplementedError("Lab results API not yet implemented")

def submit_lab_result(data: dict):
    # STUB - validation pending
    pass
""")

wip_migration = repo_dir / "src/database/migrations/0002_lab_results.sql"
wip_migration.write_text("""\
-- DRAFT - Pending DBA review - DO NOT COMMIT TO MAIN
-- Laboratory results table
CREATE TABLE lab_results (
    id SERIAL PRIMARY KEY,
    sample_id VARCHAR(50) NOT NULL,
    compound_id VARCHAR(20) REFERENCES compounds(compound_id),
    result_value DECIMAL(10,4),
    unit VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    analyst_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

# ── 7. Install the git-manager mock script ────────────────────────────────────
bin_dir = WORKSPACE / "bin"
bin_dir.mkdir(exist_ok=True)

git_manager_script = bin_dir / "git-manager"
git_manager_script.write_text('''\
#!/usr/bin/env python3
"""
git-manager CLI mock implementation.
Implements the git-manager SKILL.md specification.
"""
import argparse
import json
import os
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path


def get_log_path():
    log_env = os.environ.get("GIT_MANAGER_LOG")
    if log_env:
        return Path(log_env)
    return Path.home() / ".openclaw" / "logs" / "git-manager.log"


def write_log(entry: dict):
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\\n")


def get_protected_branches():
    env_val = os.environ.get("GIT_MANAGER_PROTECTED_BRANCHES", "main,master,production")
    return [b.strip() for b in env_val.split(",")]


def is_dry_run(args):
    if hasattr(args, "dry_run") and args.dry_run:
        return True
    return os.environ.get("GIT_MANAGER_DRY_RUN", "0") == "1"


def run_git(cmd: list, repo: str) -> tuple:
    """Run a git command and return (stdout, stderr, returncode)."""
    full_cmd = ["git", "-C", repo] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_current_branch(repo: str) -> str:
    stdout, _, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    return stdout.strip()


def parse_files_arg(files_str: str) -> list:
    """Parse [file1,file2] format."""
    s = files_str.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    if not s:
        return []
    return [f.strip() for f in s.split(",") if f.strip()]


def action_status(args, repo: str) -> dict:
    stdout, stderr, rc = run_git(["status", "--porcelain"], repo)
    branch = get_current_branch(repo)
    result = {
        "success": rc == 0,
        "action": "status",
        "branch": branch,
        "output": stdout if rc == 0 else stderr,
    }
    if rc != 0:
        result["error"] = stderr
    return result


def action_commit(args, repo: str) -> dict:
    protected = get_protected_branches()
    branch = get_current_branch(repo)

    if branch in protected:
        result = {
            "success": False,
            "action": "commit",
            "branch": branch,
            "error": f"Branch \\"{branch}\\" is protected. Cannot commit directly. Create a feature branch first.",
            "output": "",
        }
        write_log({"timestamp": datetime.utcnow().isoformat(), "action": "commit", "repo": repo, "result": result})
        return result

    message = getattr(args, "message", None) or "chore: update"
    files_arg = getattr(args, "files", None)

    if is_dry_run(args):
        result = {
            "success": True,
            "action": "commit",
            "dry_run": True,
            "branch": branch,
            "output": f"[DRY RUN] Would commit to branch {branch} with message: {message}",
            "changed_files": [],
            "commit_sha": None,
        }
        write_log({"timestamp": datetime.utcnow().isoformat(), "action": "commit", "repo": repo, "dry_run": True})
        return result

    # Stage files
    if files_arg:
        files_list = parse_files_arg(files_arg)
        for f in files_list:
            _, stderr, rc = run_git(["add", f], repo)
            if rc != 0:
                return {"success": False, "action": "commit", "branch": branch, "error": f"Failed to stage {f}: {stderr}", "output": ""}
    else:
        run_git(["add", "."], repo)

    # Commit
    stdout, stderr, rc = run_git(["commit", "-m", message], repo)
    if rc != 0:
        return {"success": False, "action": "commit", "branch": branch, "error": stderr, "output": stdout}

    # Get SHA
    sha_out, _, _ = run_git(["rev-parse", "--short", "HEAD"], repo)

    # Get changed files
    diff_out, _, _ = run_git(["diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"], repo)
    changed = [f for f in diff_out.split("\\n") if f.strip()]

    result = {
        "success": True,
        "action": "commit",
        "branch": branch,
        "commit_sha": sha_out.strip(),
        "changed_files": changed,
        "output": stdout,
    }
    write_log({"timestamp": datetime.utcnow().isoformat(), "action": "commit", "repo": repo, "sha": sha_out.strip(), "result": result})
    return result


def action_branch(args, repo: str) -> dict:
    protected = get_protected_branches()
    create = getattr(args, "create", None)
    from_branch = getattr(args, "from_branch", None)
    delete = getattr(args, "delete", None)
    list_branches = getattr(args, "list", False)

    if delete:
        if delete in protected:
            result = {"success": False, "action": "branch", "error": f"Cannot delete protected branch: {delete}", "output": ""}
            write_log({"timestamp": datetime.utcnow().isoformat(), "action": "branch_delete_blocked", "repo": repo})
            return result
        stdout, stderr, rc = run_git(["branch", "-d", delete], repo)
        return {"success": rc == 0, "action": "branch", "output": stdout, "error": stderr if rc != 0 else ""}

    if create:
        cmd = ["checkout", "-b", create]
        if from_branch:
            cmd += [from_branch]
        stdout, stderr, rc = run_git(cmd, repo)
        branch = get_current_branch(repo)
        result = {"success": rc == 0, "action": "branch", "branch": branch, "output": stdout or stderr, "error": stderr if rc != 0 else ""}
        write_log({"timestamp": datetime.utcnow().isoformat(), "action": "branch_create", "repo": repo, "new_branch": create, "from": from_branch})
        return result

    # List
    stdout, stderr, rc = run_git(["branch", "-a"], repo)
    return {"success": rc == 0, "action": "branch", "output": stdout, "branch": get_current_branch(repo)}


def action_checkout(args, repo: str) -> dict:
    branch = getattr(args, "branch", None)
    if not branch:
        return {"success": False, "action": "checkout", "error": "No branch specified", "output": ""}
    stdout, stderr, rc = run_git(["checkout", branch], repo)
    current = get_current_branch(repo)
    return {"success": rc == 0, "action": "checkout", "branch": current, "output": stdout or stderr, "error": stderr if rc != 0 else ""}


def action_log(args, repo: str) -> dict:
    n = getattr(args, "n", 5) or 5
    stdout, stderr, rc = run_git(["log", f"-{n}", "--oneline", "--pretty=format:%H|%h|%s|%an|%ai"], repo)
    branch = get_current_branch(repo)
    commits = []
    for line in stdout.split("\\n"):
        if "|" in line:
            parts = line.split("|", 4)
            if len(parts) >= 5:
                commits.append({"sha": parts[1], "full_sha": parts[0], "message": parts[2], "author": parts[3], "date": parts[4]})
    result = {"success": rc == 0, "action": "log", "branch": branch, "output": stdout, "commits": commits}
    if rc != 0:
        result["error"] = stderr
    return result


def action_diff(args, repo: str) -> dict:
    files_arg = getattr(args, "files", None)
    cmd = ["diff"]
    if files_arg:
        files_list = parse_files_arg(files_arg)
        cmd += files_list
    stdout, stderr, rc = run_git(cmd, repo)
    branch = get_current_branch(repo)
    return {"success": rc == 0, "action": "diff", "branch": branch, "output": stdout, "error": stderr if rc != 0 else ""}


def action_push(args, repo: str) -> dict:
    branch = getattr(args, "branch", None) or get_current_branch(repo)
    force = getattr(args, "force", False)
    if is_dry_run(args):
        return {"success": True, "action": "push", "dry_run": True, "branch": branch, "output": f"[DRY RUN] Would push branch {branch}"}
    cmd = ["push", "origin", branch]
    if force:
        cmd.insert(2, "--force")
    stdout, stderr, rc = run_git(cmd, repo)
    result = {"success": rc == 0, "action": "push", "branch": branch, "output": stdout or stderr, "error": stderr if rc != 0 else ""}
    write_log({"timestamp": datetime.utcnow().isoformat(), "action": "push", "repo": repo, "branch": branch, "result": result})
    return result


def action_pull(args, repo: str) -> dict:
    branch = getattr(args, "branch", None) or get_current_branch(repo)
    rebase = getattr(args, "rebase", False)
    if is_dry_run(args):
        return {"success": True, "action": "pull", "dry_run": True, "branch": branch, "output": f"[DRY RUN] Would pull branch {branch}"}
    cmd = ["pull", "origin", branch]
    if rebase:
        cmd.insert(2, "--rebase")
    stdout, stderr, rc = run_git(cmd, repo)
    return {"success": rc == 0, "action": "pull", "branch": branch, "output": stdout or stderr, "error": stderr if rc != 0 else ""}


def action_stash(args, repo: str) -> dict:
    apply = getattr(args, "apply", False)
    if apply:
        stdout, stderr, rc = run_git(["stash", "apply"], repo)
    else:
        stdout, stderr, rc = run_git(["stash"], repo)
    return {"success": rc == 0, "action": "stash", "branch": get_current_branch(repo), "output": stdout or stderr, "error": stderr if rc != 0 else ""}


def action_merge(args, repo: str) -> dict:
    branch = getattr(args, "branch", None)
    if not branch:
        return {"success": False, "action": "merge", "error": "No branch specified to merge", "output": ""}
    stdout, stderr, rc = run_git(["merge", branch], repo)
    current = get_current_branch(repo)
    return {"success": rc == 0, "action": "merge", "branch": current, "output": stdout or stderr, "error": stderr if rc != 0 else ""}


ACTIONS = {
    "status": action_status,
    "commit": action_commit,
    "push": action_push,
    "pull": action_pull,
    "branch": action_branch,
    "checkout": action_checkout,
    "merge": action_merge,
    "stash": action_stash,
    "log": action_log,
    "diff": action_diff,
}


def main():
    parser = argparse.ArgumentParser(description="git-manager: Safe git operations wrapper")
    parser.add_argument("--action", required=True, choices=list(ACTIONS.keys()))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--message", "-m", default=None)
    parser.add_argument("--files", default=None, help="Comma-separated file list in [file1,file2] format")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--create", default=None)
    parser.add_argument("--from", dest="from_branch", default=None)
    parser.add_argument("--delete", default=None)
    parser.add_argument("--list", action="store_true", default=False)
    parser.add_argument("--force", action="store_true", default=False)
    parser.add_argument("--rebase", action="store_true", default=False)
    parser.add_argument("--apply", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--n", type=int, default=5)

    args = parser.parse_args()
    repo = args.repo

    if not Path(repo).exists():
        result = {"success": False, "action": args.action, "error": f"Repository path does not exist: {repo}", "output": ""}
        print(json.dumps(result, indent=2))
        sys.exit(1)

    handler = ACTIONS[args.action]
    result = handler(args, repo)
    print(json.dumps(result, indent=2))
    write_log({"timestamp": datetime.utcnow().isoformat(), "invocation": " ".join(sys.argv), "result_success": result.get("success")})
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
''')

git_manager_script.chmod(git_manager_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 8. Create an audit record template for the agent to fill ──────────────────
audit_template = WORKSPACE / "audit_record_template.txt"
audit_template.write_text("""\
=== COMPLIANCE CHANGE AUDIT RECORD ===
Change Tickets: CHG-20241105-0047, CHG-20241105-0048
Description: Q4 2024 dosing limits and adverse event threshold updates
Committed Files:
  - configs/features/dosing_limits.yaml
  - configs/environments/adverse_events_thresholds.yaml

COMMIT SHA: [TO BE FILLED BY RELEASE ENGINEER]
FEATURE BRANCH: [TO BE FILLED BY RELEASE ENGINEER]
TIMESTAMP: [TO BE FILLED BY RELEASE ENGINEER]

Approved by QA: dr.chen@pharma.local
Approved by Regulatory: regulatory.affairs@pharma.local
""")

# ── 9. Save metadata for eval script ──────────────────────────────────────────
import json as _json

meta = {
    "repo_dir": str(repo_dir),
    "target_files": [
        "configs/features/dosing_limits.yaml",
        "configs/environments/adverse_events_thresholds.yaml",
    ],
    "distractor_files": [
        "src/api/endpoints/laboratory.py",
        "src/database/migrations/0002_lab_results.sql",
    ],
    "protected_branches": ["main", "master", "production"],
    "expected_branch_prefix": "feature",
}

(WORKSPACE / "eval_meta.json").write_text(_json.dumps(meta, indent=2))

print("[gen_inputs] Workspace generated successfully.")
print(f"[gen_inputs] Repo: {repo_dir}")
print(f"[gen_inputs] Target files: dosing_limits.yaml, adverse_events_thresholds.yaml")
print(f"[gen_inputs] Distractor files: laboratory.py, 0002_lab_results.sql (should NOT be committed)")