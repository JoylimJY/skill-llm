#!/usr/bin/env python3
"""
Generates the sandbox workspace for the openclaw-backup-restore task.
Creates:
  - A realistic ~/.openclaw/ directory with agents, sessions, workspace, config, memory, logs, node_modules, tmp, dist, completions
  - The skill structure at ~/.openclaw/skills/openclaw-backup-restore/ with backup.sh, restore.sh, and .gitignore
  - A partially populated openclaw.json (missing the OPENCLAW_BACKUP_REPO key — agent must set it)
  - A local bare git repo to act as the "remote" (file:// URL)
  - Distractor files throughout
"""

import os
import json
import random
import stat
import subprocess
from pathlib import Path

random.seed(42)

HOME = Path("/home/devops")
OPENCLAW_DIR = HOME / ".openclaw"
SKILL_DIR = OPENCLAW_DIR / "skills" / "openclaw-backup-restore"
SCRIPTS_DIR = SKILL_DIR / "scripts"
BACKUP_REMOTE = HOME / "openclaw-backup-remote.git"  # local bare repo acting as "remote"

# ── 1. Create .openclaw runtime structure ──────────────────────────────────────
dirs = [
    OPENCLAW_DIR / "agents" / "code-reviewer",
    OPENCLAW_DIR / "agents" / "doc-writer",
    OPENCLAW_DIR / "agents" / "deployment-bot",
    OPENCLAW_DIR / "sessions" / "session-20240601",
    OPENCLAW_DIR / "sessions" / "session-20240602",
    OPENCLAW_DIR / "workspace" / "projects" / "infra-automation",
    OPENCLAW_DIR / "workspace" / "projects" / "k8s-configs",
    OPENCLAW_DIR / "memory" / "long-term",
    OPENCLAW_DIR / "memory" / "short-term",
    OPENCLAW_DIR / "runtime",
    OPENCLAW_DIR / "logs",                    # should be EXCLUDED
    OPENCLAW_DIR / "node_modules" / "lodash", # should be EXCLUDED
    OPENCLAW_DIR / "tmp",                     # should be EXCLUDED
    OPENCLAW_DIR / "dist",                    # should be EXCLUDED
    OPENCLAW_DIR / "completions",             # should be EXCLUDED
    SKILL_DIR / "scripts",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── 2. Populate files ──────────────────────────────────────────────────────────

# agents
(OPENCLAW_DIR / "agents" / "code-reviewer" / "agent.json").write_text(json.dumps({
    "id": "code-reviewer", "model": "gpt-4o", "temperature": 0.1,
    "system_prompt": "You are an expert code reviewer for infrastructure code."
}, indent=2))
(OPENCLAW_DIR / "agents" / "doc-writer" / "agent.json").write_text(json.dumps({
    "id": "doc-writer", "model": "gpt-4o-mini", "temperature": 0.7,
    "system_prompt": "You write clear technical documentation."
}, indent=2))
(OPENCLAW_DIR / "agents" / "deployment-bot" / "agent.json").write_text(json.dumps({
    "id": "deployment-bot", "model": "claude-3-5-sonnet", "temperature": 0.0,
    "system_prompt": "You handle deployment pipelines."
}, indent=2))
(OPENCLAW_DIR / "agents" / "deployment-bot" / "tools.json").write_text(json.dumps([
    {"name": "run_kubectl", "enabled": True},
    {"name": "send_slack", "enabled": False}
], indent=2))

# sessions
(OPENCLAW_DIR / "sessions" / "session-20240601" / "history.jsonl").write_text(
    '{"role":"user","content":"Review my Terraform plan"}\n'
    '{"role":"assistant","content":"The plan looks correct but watch for state drift."}\n'
)
(OPENCLAW_DIR / "sessions" / "session-20240602" / "history.jsonl").write_text(
    '{"role":"user","content":"Deploy to staging"}\n'
    '{"role":"assistant","content":"Deployment initiated successfully."}\n'
)

# workspace
(OPENCLAW_DIR / "workspace" / "projects" / "infra-automation" / "main.tf").write_text(
    'resource "aws_s3_bucket" "backup" {\n  bucket = "my-backup-bucket"\n}\n'
)
(OPENCLAW_DIR / "workspace" / "projects" / "k8s-configs" / "deployment.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-server\n"
)

# memory
(OPENCLAW_DIR / "memory" / "long-term" / "facts.json").write_text(json.dumps({
    "org": "PlatformTeam", "environment": "production", "region": "us-east-1"
}, indent=2))
(OPENCLAW_DIR / "memory" / "short-term" / "context.json").write_text(json.dumps({
    "last_task": "k8s upgrade", "pending": ["rotate-certs", "update-dns"]
}, indent=2))

# runtime
(OPENCLAW_DIR / "runtime" / "pid.txt").write_text("12345\n")
(OPENCLAW_DIR / "runtime" / "gateway.sock").write_text("socket-placeholder\n")

# excluded dirs (should NOT appear in backup)
(OPENCLAW_DIR / "logs" / "gateway.log").write_text("2024-06-01 INFO Gateway started\n" * 50)
(OPENCLAW_DIR / "logs" / "error.log").write_text("2024-06-02 ERROR timeout\n" * 10)
(OPENCLAW_DIR / "node_modules" / "lodash" / "index.js").write_text("// lodash stub\nmodule.exports = {};\n")
(OPENCLAW_DIR / "tmp" / "scratch.txt").write_text("temp data\n")
(OPENCLAW_DIR / "dist" / "bundle.js").write_text("// compiled bundle\n")
(OPENCLAW_DIR / "completions" / "bash_completions.sh").write_text("# bash completions\n")

# ── 3. openclaw.json — missing OPENCLAW_BACKUP_REPO ───────────────────────────
openclaw_config = {
    "version": "2.1.0",
    "gateway": {
        "port": 3000,
        "host": "localhost",
        "autostart": True
    },
    "skills": {
        "entries": {
            "openclaw-backup-restore": {
                "enabled": True,
                "env": {
                    "OPENCLAW_LOG_LEVEL": "info"
                    # OPENCLAW_BACKUP_REPO is intentionally missing — agent must set it
                }
            },
            "code-search": {
                "enabled": True,
                "env": {}
            }
        }
    },
    "ui": {
        "theme": "dark",
        "language": "en"
    }
}
(OPENCLAW_DIR / "openclaw.json").write_text(json.dumps(openclaw_config, indent=2))

# ── 4. Skill .gitignore ────────────────────────────────────────────────────────
gitignore_content = """node_modules/
logs/
completions/
tmp/
dist/
*.sock
*.pid
"""
(SKILL_DIR / ".gitignore").write_text(gitignore_content)

# ── 5. backup.sh ──────────────────────────────────────────────────────────────
backup_sh = r"""#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${HOME}/.openclaw/openclaw.json"
SOURCE_DIR="${HOME}/.openclaw"
BACKUP_DIR="${HOME}/openclaw-backup"

# Read OPENCLAW_BACKUP_REPO from openclaw.json
REPO_URL=$(python3 -c "
import json, sys
with open('${CONFIG_FILE}') as f:
    cfg = json.load(f)
url = cfg.get('skills', {}).get('entries', {}).get('openclaw-backup-restore', {}).get('env', {}).get('OPENCLAW_BACKUP_REPO', '')
if not url:
    sys.exit('ERROR: OPENCLAW_BACKUP_REPO is not set in openclaw.json')
print(url)
")

echo "Backup repo: ${REPO_URL}"

# Initialize or update backup dir
if [ ! -d "${BACKUP_DIR}/.git" ]; then
    git init "${BACKUP_DIR}"
    cd "${BACKUP_DIR}"
    git remote add origin "${REPO_URL}"
    # Copy .gitignore from skill
    cp "${SKILL_DIR}/.gitignore" "${BACKUP_DIR}/.gitignore"
    git fetch origin main 2>/dev/null || true
    git checkout -b main 2>/dev/null || git checkout main 2>/dev/null || true
else
    cd "${BACKUP_DIR}"
    # Ensure remote is correct
    git remote set-url origin "${REPO_URL}"
    # Copy .gitignore from skill (refresh it)
    cp "${SKILL_DIR}/.gitignore" "${BACKUP_DIR}/.gitignore"
    git pull origin main 2>/dev/null || true
fi

# Rsync source to backup, respecting .gitignore
rsync -av --delete \
    --exclude='.git' \
    --filter=':- .gitignore' \
    "${SOURCE_DIR}/" "${BACKUP_DIR}/"

cd "${BACKUP_DIR}"

# Build categorized commit summary
CHANGED_PATHS=$(git diff --name-only HEAD 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)

CATEGORIES=""
for path in ${CHANGED_PATHS}; do
    if echo "${path}" | grep -q '^workspace/'; then
        CATEGORIES="${CATEGORIES} workspace"
    elif echo "${path}" | grep -q '^agents/\|^sessions/'; then
        CATEGORIES="${CATEGORIES} config"
    elif echo "${path}" | grep -q '^runtime/'; then
        CATEGORIES="${CATEGORIES} runtime"
    elif echo "${path}" | grep -q '^memory/'; then
        CATEGORIES="${CATEGORIES} memory"
    else
        CATEGORIES="${CATEGORIES} config"
    fi
done

# Deduplicate categories
UNIQUE_CATS=$(echo "${CATEGORIES}" | tr ' ' '\n' | sort -u | tr '\n' '/' | sed 's|/$||')

if [ -z "${UNIQUE_CATS}" ]; then
    COMMIT_MSG="chore: backup (no changes)"
else
    COMMIT_MSG="chore: backup ${UNIQUE_CATS}"
fi

git add -A
git diff --cached --quiet && echo "Nothing to commit." && exit 0

git commit -m "${COMMIT_MSG}"
git push origin main

echo "Backup complete: ${COMMIT_MSG}"
"""
(SCRIPTS_DIR / "backup.sh").write_text(backup_sh)
(SCRIPTS_DIR / "backup.sh").chmod(
    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
)

# ── 6. restore.sh ─────────────────────────────────────────────────────────────
restore_sh = r"""#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${HOME}/.openclaw/openclaw.json"
BACKUP_DIR="${HOME}/openclaw-backup"
TARGET_DIR="${HOME}/.openclaw"

REPO_URL=$(python3 -c "
import json, sys
with open('${CONFIG_FILE}') as f:
    cfg = json.load(f)
url = cfg.get('skills', {}).get('entries', {}).get('openclaw-backup-restore', {}).get('env', {}).get('OPENCLAW_BACKUP_REPO', '')
if not url:
    sys.exit('ERROR: OPENCLAW_BACKUP_REPO is not set in openclaw.json')
print(url)
")

echo "Restoring from: ${REPO_URL}"

if [ ! -d "${BACKUP_DIR}/.git" ]; then
    git clone "${REPO_URL}" "${BACKUP_DIR}"
else
    cd "${BACKUP_DIR}" && git pull origin main
fi

rsync -av --exclude='.git' "${BACKUP_DIR}/" "${TARGET_DIR}/"

echo "Restore complete. Run: openclaw doctor --yes && openclaw gateway restart"
"""
(SCRIPTS_DIR / "restore.sh").write_text(restore_sh)
(SCRIPTS_DIR / "restore.sh").chmod(
    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
)

# ── 7. Mock `openclaw` CLI ─────────────────────────────────────────────────────
openclaw_cli = r"""#!/usr/bin/env python3
"""
openclaw_cli += '''
import sys
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("HOME", "/home/devops"))
CONFIG_PATH = HOME / ".openclaw" / "openclaw.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def set_nested(d, key_path, value):
    keys = key_path.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value

def main():
    args = sys.argv[1:]
    if not args:
        print("openclaw CLI mock")
        return
    if args[0] == "config" and args[1] == "set":
        key = args[2]
        value = args[3]
        cfg = load_config()
        set_nested(cfg, key, value)
        save_config(cfg)
        print(f"Set {key} = {value}")
    elif args[0] == "gateway" and args[1] == "restart":
        print("Gateway restarted (mock).")
    elif args[0] == "doctor":
        print("openclaw doctor: all checks passed (mock).")
    elif args[0] == "onboard":
        print("openclaw onboard: daemon installed (mock).")
    else:
        print(f"openclaw: unknown command {args}")

main()
'''
CLI_PATH = Path("/usr/local/bin/openclaw")
CLI_PATH.write_text(openclaw_cli)
CLI_PATH.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── 8. Create local bare git repo (simulating private remote) ─────────────────
BACKUP_REMOTE.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "init", "--bare", str(BACKUP_REMOTE)], check=True)

# seed it with an initial commit so we can push to main
SEED_DIR = HOME / "_seed_repo"
SEED_DIR.mkdir(exist_ok=True)
subprocess.run(["git", "init", str(SEED_DIR)], check=True)
subprocess.run(["git", "-C", str(SEED_DIR), "checkout", "-b", "main"], check=True)
(SEED_DIR / "README.md").write_text("# OpenClaw Backup\n")
subprocess.run(["git", "-C", str(SEED_DIR), "add", "."], check=True)
subprocess.run(["git", "-C", str(SEED_DIR), "commit", "-m", "init"], check=True)
subprocess.run(["git", "-C", str(SEED_DIR), "remote", "add", "origin", str(BACKUP_REMOTE)], check=True)
subprocess.run(["git", "-C", str(SEED_DIR), "push", "origin", "main"], check=True)
# cleanup seed dir
import shutil
shutil.rmtree(str(SEED_DIR))

# ── 9. Distractor files ───────────────────────────────────────────────────────
distractor_dir = HOME / "other-projects"
distractor_dir.mkdir(exist_ok=True)
for i in range(8):
    (distractor_dir / f"project_{i}.json").write_text(json.dumps({"id": i, "active": bool(i % 2)}))
(distractor_dir / "README.txt").write_text("These are unrelated project files. Do not back these up.\n")

# Write the backup repo URL to a hint-free location so eval can verify it
# (This is for eval script use only, not visible to the agent as a hint)
(HOME / ".test_meta" / "backup_repo_url.txt").parent.mkdir(exist_ok=True)
(HOME / ".test_meta" / "backup_repo_url.txt").write_text(str(BACKUP_REMOTE) + "\n")

print("Workspace generation complete.")
print(f"  ~/.openclaw/ populated with agents, sessions, workspace, memory, runtime")
print(f"  Skill scripts at: {SCRIPTS_DIR}")
print(f"  Local bare repo (simulated remote): {BACKUP_REMOTE}")
print(f"  openclaw.json is missing OPENCLAW_BACKUP_REPO — agent must set it")