#!/usr/bin/env python3
"""
Generate a realistic fintech workspace with multiple git repos in various states
for testing the code-sync Pull mode workflow.
"""
import os
import subprocess
import json
import stat
from pathlib import Path

# Fixed seed for determinism
WORKSPACE = Path("/workspace")
CODE_DIR = WORKSPACE / "code"
REMOTES_DIR = WORKSPACE / "_remotes"
SCRIPTS_DIR = WORKSPACE / "scripts"

def run(cmd, cwd=None, check=True, capture=False):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=capture, text=True
    )
    if check and result.returncode != 0:
        print(f"WARN: cmd failed: {cmd}\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return result

def create_bare_remote(name):
    remote_path = REMOTES_DIR / f"{name}.git"
    remote_path.mkdir(parents=True, exist_ok=True)
    run(f"git init --bare {remote_path}")
    return remote_path

def create_repo_with_remote(name, remote_path):
    repo_path = CODE_DIR / name
    repo_path.mkdir(parents=True, exist_ok=True)
    run("git init", cwd=repo_path)
    run(f"git remote add origin {remote_path}", cwd=repo_path)
    return repo_path

def make_commit(repo_path, filename, content, message):
    filepath = repo_path / filename
    filepath.write_text(content)
    run(f"git add {filename}", cwd=repo_path)
    run(f'git commit -m "{message}"', cwd=repo_path)

def setup():
    CODE_DIR.mkdir(parents=True, exist_ok=True)
    REMOTES_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Repo 1: payment-api — clean, behind by 2 commits (needs-pull)
    # -----------------------------------------------------------------------
    remote1 = create_bare_remote("payment-api")
    repo1 = create_repo_with_remote("payment-api", remote1)
    make_commit(repo1, "main.py", "# payment api v1\n", "init: payment api")
    run("git push -u origin main", cwd=repo1)
    # Add 2 more commits to remote via a temp clone
    tmp1 = WORKSPACE / "_tmp_payment"
    run(f"git clone {remote1} {tmp1}")
    make_commit(tmp1, "routes.py", "# routes v2\n", "feat: add routes")
    make_commit(tmp1, "models.py", "# models\n", "feat: add models")
    run("git push", cwd=tmp1)
    # Local repo stays 2 behind
    run(f"git fetch origin", cwd=repo1)

    # -----------------------------------------------------------------------
    # Repo 2: fraud-detector — clean, up-to-date
    # -----------------------------------------------------------------------
    remote2 = create_bare_remote("fraud-detector")
    repo2 = create_repo_with_remote("fraud-detector", remote2)
    make_commit(repo2, "detector.py", "# fraud detector\n", "init: fraud detector")
    run("git push -u origin main", cwd=repo2)
    run("git fetch origin", cwd=repo2)

    # -----------------------------------------------------------------------
    # Repo 3: ledger-service — dirty + behind by 1 commit (dirty+behind)
    # -----------------------------------------------------------------------
    remote3 = create_bare_remote("ledger-service")
    repo3 = create_repo_with_remote("ledger-service", remote3)
    make_commit(repo3, "ledger.py", "# ledger v1\n", "init: ledger service")
    run("git push -u origin main", cwd=repo3)
    # Add 1 commit to remote
    tmp3 = WORKSPACE / "_tmp_ledger"
    run(f"git clone {remote3} {tmp3}")
    make_commit(tmp3, "journal.py", "# journal\n", "feat: add journal")
    run("git push", cwd=tmp3)
    # Fetch so local knows it's behind
    run("git fetch origin", cwd=repo3)
    # Make local dirty (uncommitted change)
    (repo3 / "ledger.py").write_text("# ledger v1 - local dirty change\n# TODO: fix this\n")
    # Do NOT stage or commit — leave as dirty working tree

    # -----------------------------------------------------------------------
    # Repo 4: auth-gateway — fetch_error (remote is unreachable/invalid)
    # -----------------------------------------------------------------------
    repo4 = CODE_DIR / "auth-gateway"
    repo4.mkdir(parents=True, exist_ok=True)
    run("git init", cwd=repo4)
    make_commit(repo4, "auth.py", "# auth gateway\n", "init: auth gateway")
    # Point to a non-existent remote to simulate fetch_error
    run("git remote add origin git@192.0.2.1:fintech/auth-gateway.git", cwd=repo4)
    # Set up tracking branch manually by faking it - just leave no upstream actually
    # We'll handle this in scan.sh: no upstream → but we want fetch_error
    # Let's create a local upstream reference that points nowhere reachable
    # We'll simulate this in scan.sh output directly

    # -----------------------------------------------------------------------
    # Repo 5: reporting-dashboard — clean, behind by 3 commits (needs-pull)
    # -----------------------------------------------------------------------
    remote5 = create_bare_remote("reporting-dashboard")
    repo5 = create_repo_with_remote("reporting-dashboard", remote5)
    make_commit(repo5, "dashboard.py", "# dashboard v1\n", "init: reporting dashboard")
    run("git push -u origin main", cwd=repo5)
    tmp5 = WORKSPACE / "_tmp_dashboard"
    run(f"git clone {remote5} {tmp5}")
    make_commit(tmp5, "charts.py", "# charts\n", "feat: add charts")
    make_commit(tmp5, "filters.py", "# filters\n", "feat: add filters")
    make_commit(tmp5, "export.py", "# export\n", "feat: add export")
    run("git push", cwd=tmp5)
    run("git fetch origin", cwd=repo5)

    # -----------------------------------------------------------------------
    # Repo 6: config-store — clean, up-to-date
    # -----------------------------------------------------------------------
    remote6 = create_bare_remote("config-store")
    repo6 = create_repo_with_remote("config-store", remote6)
    make_commit(repo6, "config.yaml", "env: production\n", "init: config store")
    run("git push -u origin main", cwd=repo6)
    run("git fetch origin", cwd=repo6)

    # -----------------------------------------------------------------------
    # Distractor files (realistic fintech project noise)
    # -----------------------------------------------------------------------
    distractors = [
        ("notes/standup-2024-01-15.md", "- Review PR #42\n- Fix auth bug\n"),
        ("notes/architecture-decisions.md", "# ADR-001: Use PostgreSQL\n"),
        ("scratch/perf-test-results.txt", "p99: 145ms\np50: 23ms\n"),
        ("scratch/old-migration.sql", "ALTER TABLE payments ADD COLUMN currency VARCHAR(3);\n"),
        ("tools/db-seed.py", "#!/usr/bin/env python3\n# seed script\n"),
        ("tools/load-test.sh", "#!/bin/bash\n# locust load test\n"),
        ("docs/api-spec.yaml", "openapi: 3.0.0\ninfo:\n  title: Fintech API\n"),
        ("docs/runbook.md", "# On-call Runbook\n## Payment Failures\n"),
        (".local-env", "DB_HOST=localhost\nREDIS_URL=redis://localhost:6379\n"),
        ("Makefile", "test:\n\tpytest tests/\nlint:\n\tflake8 .\n"),
        ("docker-compose.yml", "version: '3.8'\nservices:\n  db:\n    image: postgres:15\n"),
    ]
    for rel_path, content in distractors:
        full_path = WORKSPACE / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    # -----------------------------------------------------------------------
    # Create the scan.sh script
    # This is a realistic implementation that does actual git introspection
    # -----------------------------------------------------------------------
    scan_sh_content = r'''#!/bin/bash
# scripts/scan.sh — Scan git repos under base directory
# Usage: bash scripts/scan.sh [--fetch] [--base-dir /path]

set -euo pipefail

FETCH=false
BASE_DIR="$HOME/code"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fetch)
            FETCH=true
            shift
            ;;
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            shift
            ;;
    esac
done

# Expand tilde
BASE_DIR="${BASE_DIR/#\~/$HOME}"

find_repos() {
    local base="$1"
    # Top-level repos: <base>/*/
    for d in "$base"/*/; do
        [ -d "$d/.git" ] && echo "$d"
    done
    # Monorepo sub-repos: <base>/*/repos/*/
    for d in "$base"/*/repos/*/; do
        [ -d "$d/.git" ] && echo "$d"
    done
}

REPOS=()
while IFS= read -r repo; do
    REPOS+=("$repo")
done < <(find_repos "$BASE_DIR")

if [ ${#REPOS[@]} -eq 0 ]; then
    echo "[]"
    exit 0
fi

output="["
first=true

for repo_path in "${REPOS[@]}"; do
    repo_path="${repo_path%/}"
    name=$(basename "$repo_path")
    
    # Get current branch
    branch=$(git -C "$repo_path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    
    # Get remote
    remote=$(git -C "$repo_path" remote 2>/dev/null | head -1 || echo "")
    remote_url=""
    if [ -n "$remote" ]; then
        remote_url=$(git -C "$repo_path" remote get-url "$remote" 2>/dev/null || echo "")
    fi
    
    # Check upstream
    has_upstream="false"
    upstream=""
    upstream=$(git -C "$repo_path" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
    if [ -n "$upstream" ]; then
        has_upstream="true"
    fi
    
    # Fetch if requested
    fetch_error="false"
    if [ "$FETCH" = "true" ] && [ -n "$remote" ]; then
        timeout 10 git -C "$repo_path" fetch "$remote" 2>/dev/null || fetch_error="true"
    fi
    
    # Dirty count (number of changed files)
    dirty_count=$(git -C "$repo_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    
    # Ahead/behind
    ahead=0
    behind=0
    if [ "$has_upstream" = "true" ]; then
        ab=$(git -C "$repo_path" rev-list --left-right --count HEAD...@{u} 2>/dev/null || echo "0	0")
        ahead=$(echo "$ab" | awk '{print $1}')
        behind=$(echo "$ab" | awk '{print $2}')
    fi
    
    # Build JSON entry
    entry=$(printf '{
  "path": "%s",
  "name": "%s",
  "branch": "%s",
  "remote": "%s",
  "remote_url": "%s",
  "dirty_count": %s,
  "has_upstream": %s,
  "ahead": %s,
  "behind": %s,
  "fetch_error": %s
}' "$repo_path" "$name" "$branch" "$remote" "$remote_url" \
       "$dirty_count" "$has_upstream" "$ahead" "$behind" "$fetch_error")
    
    if [ "$first" = "true" ]; then
        output="$output$entry"
        first=false
    else
        output="$output,$entry"
    fi
done

output="$output]"
echo "$output"
'''

    scan_sh_path = SCRIPTS_DIR / "scan.sh"
    scan_sh_path.write_text(scan_sh_content)
    scan_sh_path.chmod(scan_sh_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # -----------------------------------------------------------------------
    # Create config file (code-sync config)
    # -----------------------------------------------------------------------
    config_dir = Path("/root/.config/nini-skill/code-sync")
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.md").write_text(f"base_dir: {CODE_DIR}\n")

    # -----------------------------------------------------------------------
    # Create git pull hook logger on repos that should be auto-pulled
    # This records whether --ff-only was used
    # -----------------------------------------------------------------------
    hook_script = """#!/bin/bash
# Log git pull arguments for evaluation
echo "$(date -Iseconds) git pull $@" >> /tmp/git_pull_log.txt
"""
    for repo_name in ["payment-api", "reporting-dashboard"]:
        hooks_dir = CODE_DIR / repo_name / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        hook_file = hooks_dir / "pre-receive"
        # Actually, we need to log the pull command from the client side
        # Use a wrapper approach via git config
    
    # Create a git pull command logger via alias or wrapper
    # We'll use a post-merge hook to confirm pulls happened
    for repo_name in ["payment-api", "reporting-dashboard", "ledger-service"]:
        hooks_dir = CODE_DIR / repo_name / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        post_merge = hooks_dir / "post-merge"
        post_merge.write_text(f"#!/bin/bash\necho '{repo_name} merged' >> /tmp/git_merge_log.txt\n")
        post_merge.chmod(post_merge.stat().st_mode | stat.S_IEXEC)

    # -----------------------------------------------------------------------
    # Install git wrapper to capture --ff-only usage
    # -----------------------------------------------------------------------
    git_wrapper = WORKSPACE / "scripts" / "git_wrapper.sh"
    git_wrapper.write_text("""#!/bin/bash
# Transparent git wrapper that logs pull commands
if [[ "$1" == "pull" ]]; then
    echo "$(pwd) git pull $@" >> /tmp/git_pull_log.txt
fi
/usr/bin/git "$@"
""")
    git_wrapper.chmod(git_wrapper.stat().st_mode | stat.S_IEXEC)

    print("Workspace setup complete.")
    print(f"Repos created under: {CODE_DIR}")
    print(f"  payment-api     — needs-pull (behind 2)")
    print(f"  fraud-detector  — up-to-date")
    print(f"  ledger-service  — dirty+behind (1)")
    print(f"  auth-gateway    — fetch-error (bad remote)")
    print(f"  reporting-dashboard — needs-pull (behind 3)")
    print(f"  config-store    — up-to-date")

if __name__ == "__main__":
    setup()