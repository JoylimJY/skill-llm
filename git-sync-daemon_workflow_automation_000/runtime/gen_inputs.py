import os
import subprocess
import random
import stat

random.seed(42)

workspace = "/workspace"

# ─── Create the scripts directory with realistic git_sync_ctl.sh and git_sync_daemon.sh ───

scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# Write git_sync_daemon.sh — the engine
daemon_sh = r"""#!/usr/bin/env bash
# git_sync_daemon.sh — engine: iterate repos.conf and sync each repo

set -euo pipefail

STATE_DIR="${GIT_SYNC_STATE_DIR:-$HOME/.config/git-sync-daemon}"
REPOS_CONF="$STATE_DIR/repos.conf"
LOG_FILE="$STATE_DIR/git-sync-daemon.log"

log() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

sync_repo() {
    local entry="$1"
    local repo_path remote branch enabled

    repo_path="$(echo "$entry" | cut -d'|' -f1)"
    remote="origin"
    branch=""
    enabled="1"

    while IFS= read -r kv; do
        case "$kv" in
            remote=*) remote="${kv#remote=}" ;;
            branch=*) branch="${kv#branch=}" ;;
            enabled=*) enabled="${kv#enabled=}" ;;
        esac
    done < <(echo "$entry" | cut -d'|' -f2- | tr '|' '\n')

    # Normalize enabled
    case "$enabled" in
        0|false|False|FALSE) log "SKIP (disabled): $repo_path"; return 0 ;;
    esac

    if [[ ! -d "$repo_path/.git" ]]; then
        log "ERROR: Not a git repo: $repo_path"
        return 1
    fi

    local lockfile="$STATE_DIR/$(echo "$repo_path" | tr '/' '_').lock"

    if [[ -f "$lockfile" ]]; then
        log "WARN: Lock exists for $repo_path, skipping"
        return 0
    fi

    touch "$lockfile"
    trap "rm -f '$lockfile'" RETURN

    cd "$repo_path"

    # Determine branch
    if [[ -z "$branch" ]]; then
        branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
    fi

    log "SYNC START: $repo_path (remote=$remote branch=$branch)"

    git add -A 2>>"$LOG_FILE" || { log "ERROR: git add failed for $repo_path"; return 1; }

    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "auto-sync: $(date '+%Y-%m-%dT%H:%M:%S')" 2>>"$LOG_FILE" \
            || { log "ERROR: git commit failed for $repo_path"; return 1; }
        log "COMMITTED: $repo_path"
    else
        log "NO CHANGES: $repo_path"
    fi

    # Pull with rebase (skip if no upstream configured)
    if git remote get-url "$remote" &>/dev/null; then
        git fetch "$remote" "$branch" 2>>"$LOG_FILE" \
            && git rebase "$remote/$branch" 2>>"$LOG_FILE" \
            || log "WARN: rebase conflict or fetch issue for $repo_path"
        git push "$remote" "$branch" 2>>"$LOG_FILE" \
            || log "WARN: push failed for $repo_path (remote may be bare/offline)"
    else
        log "INFO: No remote '$remote' configured for $repo_path, skipping fetch/push"
    fi

    log "SYNC DONE: $repo_path"
}

main() {
    mkdir -p "$STATE_DIR"
    touch "$LOG_FILE"

    if [[ ! -f "$REPOS_CONF" ]]; then
        log "ERROR: repos.conf not found at $REPOS_CONF"
        exit 1
    fi

    log "=== Sync cycle start ==="
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip blank lines and comments
        [[ -z "$line" || "$line" == \#* ]] && continue
        sync_repo "$line" || log "WARN: sync_repo failed for: $line"
    done < "$REPOS_CONF"
    log "=== Sync cycle end ==="
}

main "$@"
"""

# Write git_sync_ctl.sh — the control CLI
ctl_sh = r"""#!/usr/bin/env bash
# git_sync_ctl.sh — control CLI for git-sync-daemon

set -euo pipefail

STATE_DIR="${GIT_SYNC_STATE_DIR:-$HOME/.config/git-sync-daemon}"
REPOS_CONF="$STATE_DIR/repos.conf"
LOG_FILE="$STATE_DIR/git-sync-daemon.log"
DAEMON_SCRIPT="$(cd "$(dirname "$0")" && pwd)/git_sync_daemon.sh"

usage() {
    echo "Usage: $0 <command> [args]"
    echo "Commands:"
    echo "  init                         Initialize state directory"
    echo "  add-repo <path> [branch] [remote]  Register a repo"
    echo "  remove-repo <path>           Unregister a repo"
    echo "  list-repos                   List registered repos"
    echo "  run-once                     Execute one sync cycle"
    echo "  status                       Show status and log tail"
    echo "  install-systemd              Install systemd service (Linux)"
    echo "  uninstall-systemd            Remove systemd service (Linux)"
    echo "  install-launchd              Install launchd plist (macOS)"
    echo "  uninstall-launchd            Remove launchd plist (macOS)"
    exit 1
}

cmd_init() {
    mkdir -p "$STATE_DIR"
    touch "$REPOS_CONF"
    touch "$LOG_FILE"
    echo "[init] State directory ready: $STATE_DIR"
}

cmd_add_repo() {
    local path="$1"
    local branch="${2:-}"
    local remote="${3:-origin}"

    path="$(realpath "$path")"

    if ! [[ -d "$path/.git" ]]; then
        echo "ERROR: $path is not a git repository" >&2
        exit 1
    fi

    if grep -qF "$path|" "$REPOS_CONF" 2>/dev/null; then
        echo "INFO: $path already registered, skipping"
        return 0
    fi

    local entry="$path|remote=$remote"
    if [[ -n "$branch" ]]; then
        entry="$entry|branch=$branch"
    fi
    entry="$entry|enabled=1"

    echo "$entry" >> "$REPOS_CONF"
    echo "[add-repo] Registered: $entry"
}

cmd_remove_repo() {
    local path="$1"
    path="$(realpath "$path")"
    if [[ -f "$REPOS_CONF" ]]; then
        local tmp
        tmp="$(mktemp)"
        grep -vF "$path|" "$REPOS_CONF" > "$tmp" || true
        mv "$tmp" "$REPOS_CONF"
        echo "[remove-repo] Removed: $path"
    fi
}

cmd_list_repos() {
    if [[ ! -f "$REPOS_CONF" ]]; then
        echo "No repos.conf found. Run 'init' first."
        return 0
    fi
    echo "=== Registered Repos ==="
    cat "$REPOS_CONF"
    echo "========================"
}

cmd_run_once() {
    bash "$DAEMON_SCRIPT"
}

cmd_status() {
    echo "=== Git Sync Daemon Status ==="
    echo "State dir : $STATE_DIR"
    echo "Repos conf: $REPOS_CONF"
    echo ""
    echo "--- Log tail (last 20 lines) ---"
    if [[ -f "$LOG_FILE" ]]; then
        tail -n 20 "$LOG_FILE"
    else
        echo "(no log file yet)"
    fi
}

cmd_install_systemd() {
    local user_id
    user_id="$(id -u)"
    local service_name="git-sync-daemon"
    local service_dir="$HOME/.config/systemd/user"
    mkdir -p "$service_dir"

    cat > "$service_dir/${service_name}.service" <<EOF
[Unit]
Description=Git Sync Daemon
After=network.target

[Service]
Type=oneshot
ExecStart=$(realpath "$DAEMON_SCRIPT")
Environment="HOME=$HOME"
Environment="GIT_SYNC_STATE_DIR=$STATE_DIR"

[Install]
WantedBy=default.target
EOF

    cat > "$service_dir/${service_name}.timer" <<EOF
[Unit]
Description=Git Sync Daemon Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=${service_name}.service

[Install]
WantedBy=timers.target
EOF

    echo "[install-systemd] Service files written to $service_dir"
    echo "[install-systemd] Enable with: systemctl --user enable --now ${service_name}.timer"
}

cmd_uninstall_systemd() {
    local service_dir="$HOME/.config/systemd/user"
    rm -f "$service_dir/git-sync-daemon.service" "$service_dir/git-sync-daemon.timer"
    echo "[uninstall-systemd] Removed service files"
}

cmd_install_launchd() {
    local plist_path="$HOME/Library/LaunchAgents/com.git-sync-daemon.plist"
    mkdir -p "$(dirname "$plist_path")"
    cat > "$plist_path" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.git-sync-daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$(realpath "$DAEMON_SCRIPT")</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>$HOME</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>GIT_SYNC_STATE_DIR</key>
        <string>$STATE_DIR</string>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
EOF
    echo "[install-launchd] Plist written to $plist_path"
    echo "[install-launchd] Load with: launchctl load $plist_path"
}

cmd_uninstall_launchd() {
    local plist_path="$HOME/Library/LaunchAgents/com.git-sync-daemon.plist"
    rm -f "$plist_path"
    echo "[uninstall-launchd] Removed plist"
}

CMD="${1:-}"
shift || true

case "$CMD" in
    init)             cmd_init ;;
    add-repo)         cmd_add_repo "$@" ;;
    remove-repo)      cmd_remove_repo "$@" ;;
    list-repos)       cmd_list_repos ;;
    run-once)         cmd_run_once ;;
    status)           cmd_status ;;
    install-systemd)  cmd_install_systemd ;;
    uninstall-systemd) cmd_uninstall_systemd ;;
    install-launchd)  cmd_install_launchd ;;
    uninstall-launchd) cmd_uninstall_launchd ;;
    *)                usage ;;
esac
"""

with open(os.path.join(scripts_dir, "git_sync_daemon.sh"), "w") as f:
    f.write(daemon_sh)

with open(os.path.join(scripts_dir, "git_sync_ctl.sh"), "w") as f:
    f.write(ctl_sh)

# ─── Create 5 local git repositories (the "genomics lab repos") ───

repos_base = "/opt/genomics-repos"
os.makedirs(repos_base, exist_ok=True)

repo_configs = [
    ("pipeline-aligner",    "main",    True),    # active, branch=main
    ("variant-caller",      "develop", True),    # active, branch=develop
    ("qc-dashboard",        "main",    True),    # active, branch=main
    ("legacy-assembler",    "master",  False),   # DISABLED (maintenance)
    ("ref-genome-tools",    "main",    True),    # active, branch=main, but must be REMOVED later
]

created_repos = []

for repo_name, branch, enabled in repo_configs:
    repo_path = os.path.join(repos_base, repo_name)
    os.makedirs(repo_path, exist_ok=True)

    subprocess.run(["git", "init", "-b", branch, repo_path], check=True,
                   capture_output=True)
    subprocess.run(["git", "config", "user.email", "ci@lab.org"],
                   cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "CI Bot"],
                   cwd=repo_path, check=True, capture_output=True)

    # Add some realistic files
    files = {
        "README.md": f"# {repo_name}\nGenomic pipeline component.\n",
        "config.yaml": f"pipeline: {repo_name}\nversion: 1.0\nthreads: 4\n",
        "src/main.py": f"# {repo_name} main\ndef run(): pass\n",
        "src/utils.py": "def load_ref(path): return open(path).read()\n",
        "tests/test_smoke.py": "def test_import(): pass\n",
        "data/.gitkeep": "",
        "logs/.gitkeep": "",
        "docs/architecture.md": f"## {repo_name} Architecture\nSee wiki.\n",
    }

    for rel_path, content in files.items():
        full = os.path.join(repo_path, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)

    subprocess.run(["git", "add", "-A"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial commit"],
                   cwd=repo_path, check=True, capture_output=True)

    created_repos.append((repo_path, branch, enabled))

# ─── Create distractor files in workspace to increase noise ───

distractor_dirs = [
    "infra/terraform/modules/vpc",
    "infra/terraform/modules/ecs",
    "infra/ansible/roles/deploy",
    "docs/runbooks",
    "ci/github-actions",
    "ci/jenkins",
    "monitoring/grafana/dashboards",
    "monitoring/prometheus/rules",
    "tools/linting",
    "tools/formatting",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }\n',
    "infra/terraform/modules/ecs/main.tf": 'resource "aws_ecs_cluster" "main" { name = "genomics" }\n',
    "infra/ansible/roles/deploy/tasks.yml": "- name: deploy\n  shell: echo deployed\n",
    "docs/runbooks/incident-response.md": "# Incident Response\n1. Page on-call.\n2. Check dashboards.\n",
    "ci/github-actions/ci.yml": "on: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
    "ci/jenkins/Jenkinsfile": 'pipeline { agent any; stages { stage("build") { steps { sh "make" } } } }\n',
    "monitoring/grafana/dashboards/pipeline.json": '{"title": "Pipeline Metrics", "panels": []}\n',
    "monitoring/prometheus/rules/alerts.yml": "groups:\n- name: pipeline\n  rules: []\n",
    "tools/linting/.flake8": "[flake8]\nmax-line-length = 120\n",
    "tools/formatting/.editorconfig": "[*]\nindent_style = space\nindent_size = 4\n",
    "deployment_notes.txt": "Deployment notes:\n- Use rolling updates\n- Validate health checks\n",
    "oncall_schedule.csv": "week,engineer\n1,alice\n2,bob\n3,carol\n",
}

for rel_path, content in distractor_files.items():
    full = os.path.join(workspace, rel_path)
    with open(full, "w") as f:
        f.write(content)

# ─── Write a task brief for the agent ───
# (This is intentionally NOT the SKILL.md — just raw business context)
task_brief = """\
GENOMICS LAB — AUTOMATED REPOSITORY SYNC SETUP

Context:
The bioinformatics team maintains 5 git repositories under /opt/genomics-repos/.
We need to set up an automated sync system using the provided scripts in ./scripts/.

Repositories:
  - pipeline-aligner   (branch: main)     → ACTIVE sync
  - variant-caller     (branch: develop)  → ACTIVE sync
  - qc-dashboard       (branch: main)     → ACTIVE sync
  - legacy-assembler   (branch: master)   → TEMPORARILY PAUSED (maintenance mode)
  - ref-genome-tools   (branch: main)     → DO NOT sync (decommissioned, omit entirely)

The sync config file should live in the default location expected by the scripts.
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Repos created in: {repos_base}")
print(f"Scripts in: {scripts_dir}")