#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the Obsidian GitHub Sync task.
"""
import os
import subprocess
import stat
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Directory structure ────────────────────────────────────────────────────
vault_dir = os.path.join(WORKSPACE, "my-notes-vault")
obsidian_dir = os.path.join(vault_dir, ".obsidian")
plugins_dir = os.path.join(obsidian_dir, "plugins", "dataview")
trash_dir = os.path.join(vault_dir, ".trash")
daily_dir = os.path.join(vault_dir, "daily")
projects_dir = os.path.join(vault_dir, "projects", "2024")
resources_dir = os.path.join(vault_dir, "resources", "images")
scripts_dir = os.path.join(WORKSPACE, "scripts")
references_dir = os.path.join(WORKSPACE, "references")

for d in [vault_dir, obsidian_dir, plugins_dir, trash_dir, daily_dir,
          projects_dir, resources_dir, scripts_dir, references_dir]:
    os.makedirs(d, exist_ok=True)

# ── 2. Vault markdown notes (realistic content) ───────────────────────────────
notes = {
    "daily/2024-01-15.md": "# 2024-01-15\n\n- Reviewed PR #42\n- Fixed bug in auth module\n",
    "daily/2024-01-16.md": "# 2024-01-16\n\n- Team standup\n- Deployed hotfix\n",
    "daily/2024-01-17.md": "# 2024-01-17\n\n- Wrote unit tests\n- Code review for Alice\n",
    "projects/2024/ProjectAlpha.md": "# Project Alpha\n\n## Goals\n- Launch by Q2\n\n## Notes\nNeed to finalise API design.\n",
    "projects/2024/ProjectBeta.md": "# Project Beta\n\n## Status\nIn progress\n",
    "resources/images/README.md": "# Images\nStore image attachments here.\n",
    "Meeting Notes.md": "# Meeting Notes\n\n## 2024-01-10\nDiscussed roadmap for Q1.\n",
    "Index.md": "# Index\n\n- [[Meeting Notes]]\n- [[projects/2024/ProjectAlpha]]\n",
    "TODO.md": "# TODO\n\n- [ ] Finish report\n- [ ] Review PR\n",
}
for rel, content in notes.items():
    path = os.path.join(vault_dir, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# Obsidian config files (should be gitignored per SKILL.md)
obsidian_files = {
    ".obsidian/workspace.json": '{"main":{"id":"abc123","type":"split"}}\n',
    ".obsidian/workspace-mobile.json": '{"main":{"id":"def456","type":"split"}}\n',
    ".obsidian/app.json": '{"legacyEditor":false,"livePreview":true}\n',
    ".obsidian/plugins/dataview/data.json": '{"renderNullAs":"-","taskCompletionTracking":true}\n',
    ".trash/deleted-note.md": "# Old note\nThis was deleted.\n",
}
for rel, content in obsidian_files.items():
    path = os.path.join(vault_dir, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# ── 3. Distractor files in workspace root ────────────────────────────────────
distractors = {
    "config.yaml": "sync_interval: 3600\nlog_level: info\n",
    "README.txt": "Personal notes backup project.\n",
    "references/setup-guide.md": "# Setup Guide\n\nSee main README for details.\n",
    "notes.txt": "Remember to configure the remote URL correctly.\n",
    "backup.sh": "#!/bin/bash\n# Old manual backup script - DEPRECATED\ncp -r ~/notes /backup/\n",
    ".env.example": "# Copy to .env and fill in values\nVAULT_DIR=\nREMOTE_URL=\n",
    "requirements.txt": "gitpython==3.1.40\n",
    "Makefile": "sync:\n\t./scripts/obsidian-sync.sh\n\ncheck:\n\t./scripts/check-conflict.sh\n",
    "logs/old-sync.log": "[2024-01-01 03:00:01] Sync started\n[2024-01-01 03:00:05] Sync complete\n",
}
for rel, content in distractors.items():
    path = os.path.join(WORKSPACE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# ── 4. The real obsidian-sync.sh script ──────────────────────────────────────
sync_script = r"""#!/bin/bash
set -e

# Required environment variables
: "${OBSIDIAN_VAULT_DIR:?'OBSIDIAN_VAULT_DIR is required'}"
: "${GITHUB_REMOTE_URL:?'GITHUB_REMOTE_URL is required'}"

# Optional environment variables with defaults
GIT_USER_NAME="${GIT_USER_NAME:-Obsidian Sync Bot}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-sync@obsidian.local}"
SYNC_LOG_FILE="${SYNC_LOG_FILE:-/tmp/obsidian-sync.log}"
CONFLICT_FLAG_FILE="${CONFLICT_FLAG_FILE:-/tmp/obsidian-sync-conflict.flag}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SYNC_LOG_FILE"
}

log "Starting Obsidian sync..."

cd "$OBSIDIAN_VAULT_DIR"

# Configure git user if provided
git config user.name "$GIT_USER_NAME"
git config user.email "$GIT_USER_EMAIL"

# Ensure remote is set
if ! git remote get-url origin &>/dev/null 2>&1; then
    git remote add origin "$GITHUB_REMOTE_URL"
    log "Added remote origin: $GITHUB_REMOTE_URL"
else
    git remote set-url origin "$GITHUB_REMOTE_URL"
    log "Updated remote origin: $GITHUB_REMOTE_URL"
fi

# Stage and commit any local changes
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git status --short)" ]; then
    git add -A
    git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')" || true
    log "Committed local changes"
else
    log "No local changes to commit"
fi

# Pull with rebase
log "Pulling from remote with rebase..."
if ! git pull --rebase origin master; then
    log "ERROR: Rebase failed - conflict detected!"
    echo "Conflict detected at $(date '+%Y-%m-%d %H:%M:%S')" > "$CONFLICT_FLAG_FILE"
    echo "Vault: $OBSIDIAN_VAULT_DIR" >> "$CONFLICT_FLAG_FILE"
    echo "Remote: $GITHUB_REMOTE_URL" >> "$CONFLICT_FLAG_FILE"
    exit 1
fi

# Push to remote
log "Pushing to remote..."
git push origin master

log "Sync complete!"

# Clear conflict flag if it exists
if [ -f "$CONFLICT_FLAG_FILE" ]; then
    rm "$CONFLICT_FLAG_FILE"
    log "Cleared conflict flag"
fi
"""

check_script = r"""#!/bin/bash
CONFLICT_FLAG_FILE="${CONFLICT_FLAG_FILE:-/tmp/obsidian-sync-conflict.flag}"

if [ -f "$CONFLICT_FLAG_FILE" ]; then
    echo "CONFLICT DETECTED!"
    echo "-------------------"
    cat "$CONFLICT_FLAG_FILE"
    echo "-------------------"
    echo "Please resolve conflicts manually and re-run sync."
    exit 1
else
    echo "No conflicts detected. Vault is in sync."
    exit 0
fi
"""

with open(os.path.join(scripts_dir, "obsidian-sync.sh"), "w") as f:
    f.write(sync_script)
with open(os.path.join(scripts_dir, "check-conflict.sh"), "w") as f:
    f.write(check_script)

# ── 5. Bare "remote" repo (simulates GitHub) ─────────────────────────────────
bare_repo = os.path.join(WORKSPACE, "remote-bare-repo.git")
os.makedirs(bare_repo, exist_ok=True)

# Init bare repo
subprocess.run(["git", "init", "--bare", bare_repo], check=True, capture_output=True)

# Create a working clone of the bare repo to push an initial + diverging commit
clone_dir = os.path.join(WORKSPACE, "_remote_setup_clone")
subprocess.run(["git", "clone", bare_repo, clone_dir], check=True, capture_output=True)

env = os.environ.copy()
env["GIT_AUTHOR_NAME"] = "Remote User"
env["GIT_AUTHOR_EMAIL"] = "remote@test.local"
env["GIT_COMMITTER_NAME"] = "Remote User"
env["GIT_COMMITTER_EMAIL"] = "remote@test.local"

# Initial commit on remote (simulates existing repo state)
initial_note = os.path.join(clone_dir, "SharedNote.md")
with open(initial_note, "w") as f:
    f.write("# Shared Note\n\nThis note exists on the remote.\n")
subprocess.run(["git", "-C", clone_dir, "add", "-A"], check=True, capture_output=True, env=env)
subprocess.run(["git", "-C", clone_dir, "commit", "-m", "Initial remote commit"], 
               check=True, capture_output=True, env=env)
subprocess.run(["git", "-C", clone_dir, "push", "origin", "master"], 
               check=True, capture_output=True, env=env)

# Diverging commit on remote (this will cause the rebase conflict)
with open(initial_note, "a") as f:
    f.write("\n## Remote Update\n\nAdded from another device.\n")
subprocess.run(["git", "-C", clone_dir, "add", "-A"], check=True, capture_output=True, env=env)
subprocess.run(["git", "-C", clone_dir, "commit", "-m", "Remote device update"], 
               check=True, capture_output=True, env=env)
subprocess.run(["git", "-C", clone_dir, "push", "origin", "master"], 
               check=True, capture_output=True, env=env)

# Clean up the setup clone
import shutil
shutil.rmtree(clone_dir)

# ── 6. Write task context file ────────────────────────────────────────────────
context = f"""TASK CONTEXT
============
vault_dir: {vault_dir}
bare_remote: {bare_repo}
scripts_dir: {scripts_dir}
"""
with open(os.path.join(WORKSPACE, "task_context.txt"), "w") as f:
    f.write(context)

print("Workspace generated successfully.")
print(f"  Vault:       {vault_dir}")
print(f"  Remote:      {bare_repo}")
print(f"  Scripts:     {scripts_dir}")