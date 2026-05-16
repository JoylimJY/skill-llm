#!/usr/bin/env python3
"""
Build the sandbox workspace:
  - Create a realistic ~/.openclaw directory tree with hidden files, nested dirs, varied permissions
  - Place the scripts/openclaw-backup.sh script at the correct workspace path
  - Add distractor files/dirs to make the environment feel real and messy
"""

import os
import stat
import random
import hashlib
from pathlib import Path

random.seed(42)

# ── Workspace root (passed in or default) ─────────────────────────────────────
import sys
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Simulate HOME = workspace (agent will run as this user) ───────────────────
home = workspace  # treat workspace as $HOME for this task

# ══════════════════════════════════════════════════════════════════════════════
# 1.  .openclaw  directory (the thing to be backed up)
# ══════════════════════════════════════════════════════════════════════════════
openclaw = home / ".openclaw"
openclaw.mkdir(exist_ok=True)

# Main config
(openclaw / "openclaw.json").write_text(
    '{\n  "version": "3.7.1",\n  "model": "gpt-4o",\n  "theme": "dark"\n}\n'
)

# Config backup files
(openclaw / "openclaw.json.bak1").write_text('{"version":"3.6.0","model":"gpt-4","theme":"light"}\n')
(openclaw / "openclaw.json.bak2").write_text('{"version":"3.5.2","model":"gpt-3.5-turbo","theme":"dark"}\n')

# Hidden files (critical – must survive backup)
(openclaw / ".DS_Store").write_bytes(bytes(range(32)))          # macOS-style hidden
(openclaw / ".hidden_token").write_text("tok_abc123_secret\n")  # sensitive hidden file
(openclaw / ".session_cache").write_text("session=xyz987\nexpiry=9999999999\n")

# workspace/ sub-dir
ws = openclaw / "workspace"
ws.mkdir(exist_ok=True)
(ws / "project_alpha.md").write_text("# Project Alpha\nStatus: In progress\n")
(ws / "notes.txt").write_text("Remember to update credentials after upgrade.\n")
nested = ws / "archive" / "2025"
nested.mkdir(parents=True, exist_ok=True)
(nested / "old_session.json").write_text('{"session":"legacy","ts":1700000000}\n')
(nested / ".archived_flag").write_text("archived=true\n")       # hidden in nested dir

# credentials/
creds = openclaw / "credentials"
creds.mkdir(exist_ok=True)
(creds / "api_keys.enc").write_bytes(hashlib.sha256(b"fake_key").digest())
(creds / "oauth_token.dat").write_text("Bearer fake_oauth_token_abcdef\n")
creds_priv = creds / "api_keys.enc"
os.chmod(creds_priv, 0o600)  # restrictive permission – must be preserved

# extensions/
ext = openclaw / "extensions"
ext.mkdir(exist_ok=True)
(ext / "coderunner.json").write_text('{"enabled":true,"version":"1.2"}\n')
(ext / "translator.json").write_text('{"enabled":false,"version":"0.9"}\n')

# agents/
agents = openclaw / "agents"
agents.mkdir(exist_ok=True)
(agents / "default_agent.yaml").write_text("name: default\nmodel: gpt-4o\ntemp: 0.7\n")
(agents / "research_agent.yaml").write_text("name: research\nmodel: gpt-4o\ntemp: 0.2\n")

# cron/
cron = openclaw / "cron"
cron.mkdir(exist_ok=True)
(cron / "cleanup.cron").write_text("0 3 * * * /usr/local/bin/openclaw clean\n")

# completions/
completions = openclaw / "completions"
completions.mkdir(exist_ok=True)
for i in range(3):
    (completions / f"hist_{i:04d}.jsonl").write_text(
        f'{{"q":"query {i}","a":"answer {i}"}}\n'
    )

# logs/
logs = openclaw / "logs"
logs.mkdir(exist_ok=True)
(logs / "app.log").write_text("2026-03-16 01:00:00 INFO  startup complete\n" * 5)
(logs / "error.log").write_text("2026-03-16 01:02:00 ERROR null pointer\n")

# ══════════════════════════════════════════════════════════════════════════════
# 2.  Distractor files/dirs at HOME level (not related to .openclaw)
# ══════════════════════════════════════════════════════════════════════════════
(home / ".bashrc").write_text("# bash init\nexport PATH=$PATH:/usr/local/bin\n")
(home / ".profile").write_text("# profile\n")
(home / ".gitconfig").write_text("[user]\n  name=Dev User\n  email=dev@example.com\n")

other_app = home / ".other_app_config"
other_app.mkdir(exist_ok=True)
(other_app / "settings.json").write_text('{"theme":"blue"}\n')

projects = home / "projects"
projects.mkdir(exist_ok=True)
(projects / "README.txt").write_text("Various projects live here.\n")
subproj = projects / "backend" / "src"
subproj.mkdir(parents=True, exist_ok=True)
(subproj / "main.py").write_text("print('hello world')\n")

# ══════════════════════════════════════════════════════════════════════════════
# 3.  scripts/  directory with the backup script (already exists per SKILL.md)
# ══════════════════════════════════════════════════════════════════════════════
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

backup_script = scripts_dir / "openclaw-backup.sh"
backup_script.write_text(r"""#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Backup Script
# Creates a timestamped copy of ~/.openclaw at the same directory level.

SOURCE="${HOME}/.openclaw"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
DEST="${HOME}/.openclaw${TIMESTAMP}"

if [ ! -d "${SOURCE}" ]; then
    echo "ERROR: Source directory '${SOURCE}' not found." >&2
    exit 1
fi

echo "Backing up '${SOURCE}' -> '${DEST}' ..."

if command -v rsync &>/dev/null; then
    rsync -a "${SOURCE}/" "${DEST}/"
else
    cp -a "${SOURCE}/." "${DEST}/"
fi

echo "Backup complete: ${DEST}"
""")
os.chmod(backup_script, 0o755)

print(f"[gen_inputs] Workspace built at: {workspace}")
print(f"[gen_inputs] .openclaw tree created with hidden files, nested dirs, and restricted permissions.")
print(f"[gen_inputs] scripts/openclaw-backup.sh written and made executable.")