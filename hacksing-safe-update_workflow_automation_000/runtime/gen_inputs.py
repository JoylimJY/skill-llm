#!/usr/bin/env python3
"""
Generate the sandbox workspace for the OpenClaw safe-update task.
Creates a realistic project structure with a fake OpenClaw repo,
upstream bare repo, openclaw config files, and distractor files.
"""

import os
import subprocess
import textwrap
import random
import stat
from pathlib import Path
from datetime import datetime

random.seed(42)

WORKSPACE = Path("/workspace")
AGENT_HOME = Path("/home/agent")
PROJECT_DIR = WORKSPACE / "projects" / "my-openclaw"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
UPSTREAM_BARE = WORKSPACE / "_upstream_bare.git"
OPENCLAW_CONFIG_DIR = AGENT_HOME / ".openclaw"
AGENTS_DIR = OPENCLAW_CONFIG_DIR / "agents" / "main" / "agent"

def run(cmd, cwd=None, env=None, user=None):
    """Run a shell command."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    if user:
        cmd = f"su - agent -c {repr('cd ' + str(cwd) + ' && ' + cmd if cwd else cmd)}"
        cwd = None
    result = subprocess.run(cmd, shell=True, cwd=str(cwd) if cwd else None,
                           env=full_env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"WARNING: Command failed: {cmd}")
        print(f"  stdout: {result.stdout[:200]}")
        print(f"  stderr: {result.stderr[:200]}")
    return result

def run_agent(cmd, cwd=None):
    """Run a shell command as the agent user."""
    return run(cmd, cwd=cwd, user="agent")

def write_file(path, content, executable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content))
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path

# ─────────────────────────────────────────────────────────────────────────────
# 1. Create upstream bare repo (simulates github.com/openclaw/openclaw.git)
# ─────────────────────────────────────────────────────────────────────────────
UPSTREAM_BARE.mkdir(parents=True, exist_ok=True)
run(f"git init --bare {UPSTREAM_BARE}")
run(f"chown -R agent:agent {UPSTREAM_BARE}")

# Create a temp clone to populate upstream
TEMP_UPSTREAM = WORKSPACE / "_temp_upstream"
run(f"git clone {UPSTREAM_BARE} {TEMP_UPSTREAM}")
run(f"chown -R agent:agent {TEMP_UPSTREAM}")

# Populate temp upstream with package.json and source files
pkg_json = '''{
  "name": "openclaw",
  "version": "2.3.1",
  "description": "OpenClaw Gateway",
  "bin": {
    "openclaw": "./dist/cli.js"
  },
  "scripts": {
    "build": "echo Building OpenClaw... && mkdir -p dist && echo '#!/usr/bin/env node\\nconsole.log(\"openclaw 2.3.1\")' > dist/cli.js"
  }
}'''

write_file(TEMP_UPSTREAM / "package.json", pkg_json)
write_file(TEMP_UPSTREAM / "README.md", "# OpenClaw Gateway\nVersion 2.3.1\n")
write_file(TEMP_UPSTREAM / "src" / "index.js", "// OpenClaw main entry\nconsole.log('OpenClaw started');\n")
write_file(TEMP_UPSTREAM / "src" / "gateway.js", "// Gateway logic\nmodule.exports = {};\n")
write_file(TEMP_UPSTREAM / "src" / "auth.js", "// Auth module\nmodule.exports = {};\n")

run_agent("git add -A", cwd=TEMP_UPSTREAM)
run_agent("git commit -m 'chore: release v2.3.1'", cwd=TEMP_UPSTREAM)
# Create a tag for version
run_agent("git tag v2.3.0", cwd=TEMP_UPSTREAM)
# Create the dev/integration branch in upstream with a new commit
run_agent("git checkout -b dev/integration", cwd=TEMP_UPSTREAM)

# Add a new commit to upstream dev/integration (simulates upstream progress)
upstream_pkg = '''{
  "name": "openclaw",
  "version": "2.4.0",
  "description": "OpenClaw Gateway - Latest",
  "bin": {
    "openclaw": "./dist/cli.js"
  },
  "scripts": {
    "build": "echo Building OpenClaw 2.4.0... && mkdir -p dist && echo '#!/usr/bin/env node\\nconsole.log(\\"openclaw 2.4.0\\")' > dist/cli.js"
  }
}'''
write_file(TEMP_UPSTREAM / "package.json", upstream_pkg)
write_file(TEMP_UPSTREAM / "CHANGELOG.md", "## v2.4.0\n- New gateway features\n- Bug fixes\n")
write_file(TEMP_UPSTREAM / "src" / "router.js", "// New router module\nmodule.exports = {};\n")
run_agent("git add -A", cwd=TEMP_UPSTREAM)
run_agent("git commit -m 'feat: v2.4.0 - new router and gateway features'", cwd=TEMP_UPSTREAM)
run_agent("git tag v2.4.0", cwd=TEMP_UPSTREAM)

# Push both branches to bare upstream
run_agent("git push origin main", cwd=TEMP_UPSTREAM)
run_agent("git push origin dev/integration", cwd=TEMP_UPSTREAM)
run_agent("git push origin --tags", cwd=TEMP_UPSTREAM)

# Clean up temp upstream
run(f"rm -rf {TEMP_UPSTREAM}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Create local project at non-default path
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
run(f"chown -R agent:agent {PROJECT_DIR}")

# Init local repo on dev/integration (one commit BEHIND upstream)
run_agent("git init", cwd=PROJECT_DIR)
run_agent(f"git remote add upstream {UPSTREAM_BARE}", cwd=PROJECT_DIR)

# Create initial local state: old version, clean working tree
old_pkg = '''{
  "name": "openclaw",
  "version": "2.3.1",
  "description": "OpenClaw Gateway",
  "bin": {
    "openclaw": "./dist/cli.js"
  },
  "scripts": {
    "build": "echo Building OpenClaw... && mkdir -p dist && echo '#!/usr/bin/env node\\nconsole.log(\\"openclaw 2.3.1\\")' > dist/cli.js"
  }
}'''

write_file(PROJECT_DIR / "package.json", old_pkg)
write_file(PROJECT_DIR / "README.md", "# OpenClaw Gateway\nVersion 2.3.1 (local)\n")
write_file(PROJECT_DIR / "src" / "index.js", "// OpenClaw main entry\nconsole.log('OpenClaw started');\n")
write_file(PROJECT_DIR / "src" / "gateway.js", "// Gateway logic\nmodule.exports = {};\n")
write_file(PROJECT_DIR / "src" / "auth.js", "// Auth module\nmodule.exports = {};\n")
write_file(PROJECT_DIR / ".gitignore", "node_modules/\ndist/\n*.log\n")

run(f"chown -R agent:agent {PROJECT_DIR}")

run_agent("git checkout -b dev/integration", cwd=PROJECT_DIR)
run_agent("git add -A", cwd=PROJECT_DIR)
run_agent("git commit -m 'chore: initial local state v2.3.1'", cwd=PROJECT_DIR)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create the update.sh script (pre-existing skill script)
# ─────────────────────────────────────────────────────────────────────────────
update_sh_content = r'''#!/usr/bin/env bash
# OpenClaw Safe Update Script
# Usage: ./update.sh [OPTIONS]
# Options:
#   --dir PATH       OpenClaw project directory (default: $HOME/projects/openclaw)
#   --branch NAME    Git branch to update (default: main)
#   --mode MODE      Update mode: merge or rebase
#   --dry-run       Show what would be done without executing
#   --help          Show this help message

set -euo pipefail

# ─── Defaults ─────────────────────────────────────────────────────────────────
DIR="${OPENCLAW_PROJECT_DIR:-$HOME/projects/openclaw}"
BRANCH="${OPENCLAW_BRANCH:-main}"
MODE=""
DRY_RUN="${DRY_RUN:-false}"
HELP=false

# ─── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)
      DIR="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      if [[ "$MODE" != "merge" && "$MODE" != "rebase" ]]; then
        echo "ERROR: --mode must be 'merge' or 'rebase'" >&2
        exit 1
      fi
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --help)
      HELP=true
      shift
      ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$HELP" == "true" ]]; then
  grep '^#' "$0" | sed 's/^# \?//'
  exit 0
fi

# ─── Validate project directory ───────────────────────────────────────────────
if [[ ! -d "$DIR" ]]; then
  echo "ERROR: Project directory does not exist: $DIR" >&2
  exit 1
fi

echo "=== OpenClaw Safe Update ==="
echo "Project dir : $DIR"
echo "Branch      : $BRANCH"
echo "Mode        : ${MODE:-auto}"
echo "Dry run     : $DRY_RUN"
echo ""

# ─── Step 1: Analyze current state ───────────────────────────────────────────
echo "=== Step 1: Analyzing current state ==="
cd "$DIR"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

UNCOMMITTED=$(git status --porcelain)
if [[ -n "$UNCOMMITTED" ]]; then
  echo "⚠️  Uncommitted changes detected:"
  echo "$UNCOMMITTED"
  RECOMMENDED_MODE="merge"
  echo "Recommended mode: merge (uncommitted changes present)"
else
  echo "✅ Working tree is clean"
  if [[ -z "$MODE" ]]; then
    RECOMMENDED_MODE="merge"
    echo "Recommended mode: merge (routine dev update)"
  fi
fi

# Fetch upstream to check for new commits
echo ""
echo "=== Fetching upstream ==="
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] Would run: git fetch upstream"
  echo "[DRY-RUN] Would check for new commits on upstream/$BRANCH"
else
  git fetch upstream
  LOCAL_HASH=$(git rev-parse HEAD)
  UPSTREAM_HASH=$(git rev-parse "upstream/$BRANCH" 2>/dev/null || echo "")
  if [[ -n "$UPSTREAM_HASH" && "$LOCAL_HASH" != "$UPSTREAM_HASH" ]]; then
    echo "📦 New commits available from upstream/$BRANCH"
    AHEAD_BEHIND=$(git rev-list --left-right --count HEAD...upstream/$BRANCH 2>/dev/null || echo "? ?")
    echo "   Local/Upstream delta: $AHEAD_BEHIND"
  else
    echo "✅ Already up to date with upstream/$BRANCH"
  fi
fi

echo ""

# ─── Dry-run exit point ───────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "=== DRY-RUN PREVIEW (no changes made) ==="
  echo "[DRY-RUN] Would checkout branch: $BRANCH"
  echo "[DRY-RUN] Would run: git ${MODE:-$RECOMMENDED_MODE} upstream/$BRANCH"
  echo "[DRY-RUN] Would backup config files to ~/.openclaw/backups/"
  echo "[DRY-RUN] Would run: npm run build"
  echo "[DRY-RUN] Would run: npm i -g ."
  echo "[DRY-RUN] Would run: openclaw daemon install --force"
  echo "[DRY-RUN] Would run: systemctl --user restart openclaw-gateway"
  echo ""
  echo "✅ Dry-run complete. No changes were made."
  exit 0
fi

# ─── Step 2: Execute update ───────────────────────────────────────────────────
echo "=== Step 2: Backing up config files ==="
mkdir -p ~/.openclaw/backups
BACKUP_SUFFIX=$(date +%Y%m%d-%H%M%S)

if [[ -f ~/.openclaw/openclaw.json ]]; then
  cp ~/.openclaw/openclaw.json \
     ~/.openclaw/backups/openclaw.json.bak.$BACKUP_SUFFIX
  echo "✅ Backed up: openclaw.json"
else
  echo "⚠️  ~/.openclaw/openclaw.json not found, skipping backup"
fi

if [[ -f ~/.openclaw/agents/main/agent/auth-profiles.json ]]; then
  cp ~/.openclaw/agents/main/agent/auth-profiles.json \
     ~/.openclaw/backups/auth-profiles.json.bak.$BACKUP_SUFFIX
  echo "✅ Backed up: auth-profiles.json"
fi

echo "💡 Backups saved to: ~/.openclaw/backups/"
echo ""

# ─── Step 3: Git update ───────────────────────────────────────────────────────
echo "=== Step 3: Updating branch ==="
git checkout "$BRANCH"

FINAL_MODE="${MODE:-${RECOMMENDED_MODE:-merge}}"
echo "Using mode: $FINAL_MODE"

if [[ "$FINAL_MODE" == "merge" ]]; then
  git merge "upstream/$BRANCH" --no-edit
elif [[ "$FINAL_MODE" == "rebase" ]]; then
  git rebase "upstream/$BRANCH"
fi

echo ""

# ─── Step 4: View changelog ───────────────────────────────────────────────────
echo "=== Full Changelog ==="
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || node -e 'console.log("v"+require("./package.json").version)' 2>/dev/null || echo "unknown")
echo "Current version: $CURRENT_TAG"
echo ""

# ─── Step 5: Build and install ───────────────────────────────────────────────
echo "=== Step 5: Building ==="
npm run build

echo ""
echo "=== Installing globally ==="
npm i -g .

echo ""

# ─── Step 6: Reinstall systemd service ───────────────────────────────────────
echo "=== Reinstalling Gateway service ==="
# Mock: openclaw daemon install --force (openclaw may not be in PATH yet)
echo "[INFO] openclaw daemon install --force"
echo "✅ Gateway service definition updated"

echo ""

# ─── Step 7: Check version ───────────────────────────────────────────────────
NEW_VERSION=$(node -e 'console.log("v"+require("./package.json").version)' 2>/dev/null || echo "unknown")
echo "✅ Update complete! New version: $NEW_VERSION"
echo ""

# ─── Step 8: Restart prompt ──────────────────────────────────────────────────
echo "=== Gateway needs restart to apply updates ==="
echo "Confirm restart? (y/N)"
echo "[INFO] To restart manually: systemctl --user restart openclaw-gateway"
'''

write_file(SCRIPTS_DIR / "update.sh", update_sh_content, executable=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Create OpenClaw config files (to be backed up)
# ─────────────────────────────────────────────────────────────────────────────
OPENCLAW_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
AGENTS_DIR.mkdir(parents=True, exist_ok=True)

write_file(OPENCLAW_CONFIG_DIR / "openclaw.json", '''{
  "version": "2.3.1",
  "gateway": {
    "port": 8080,
    "host": "localhost"
  },
  "logging": {
    "level": "info",
    "file": "~/.openclaw/logs/gateway.log"
  }
}
''')

write_file(AGENTS_DIR / "auth-profiles.json", '''{
  "profiles": [
    {
      "name": "default",
      "type": "token",
      "token": "local-dev-token-abc123"
    }
  ]
}
''')

# ─────────────────────────────────────────────────────────────────────────────
# 5. Create distractor files (realistic project noise)
# ─────────────────────────────────────────────────────────────────────────────
distractors = {
    PROJECT_DIR / "src" / "plugins" / "auth-plugin.js": "// Auth plugin\nmodule.exports = require('./base');\n",
    PROJECT_DIR / "src" / "plugins" / "logger-plugin.js": "// Logger plugin\nmodule.exports = {};\n",
    PROJECT_DIR / "src" / "utils" / "retry.js": "// Retry utility\nfunction retry(fn, n) { return fn(); }\nmodule.exports = { retry };\n",
    PROJECT_DIR / "src" / "utils" / "config-loader.js": "// Config loader\nconst fs = require('fs');\nmodule.exports = JSON.parse(fs.readFileSync('./config.json'));\n",
    PROJECT_DIR / "tests" / "unit" / "gateway.test.js": "// Unit tests\ndescribe('gateway', () => { it('should start', () => {}); });\n",
    PROJECT_DIR / "tests" / "integration" / "auth.test.js": "// Integration tests\ndescribe('auth', () => { it('should validate', () => {}); });\n",
    PROJECT_DIR / "config" / "default.json": '{"env": "development", "debug": true}\n',
    PROJECT_DIR / "config" / "production.json": '{"env": "production", "debug": false}\n',
    PROJECT_DIR / "scripts" / "deploy.sh": "#!/usr/bin/env bash\necho 'Deploying OpenClaw...'\n",
    PROJECT_DIR / "scripts" / "rollback.sh": "#!/usr/bin/env bash\necho 'Rolling back...'\n",
    PROJECT_DIR / "scripts" / "health-check.sh": "#!/usr/bin/env bash\ncurl -s http://localhost:8080/health\n",
    PROJECT_DIR / "docs" / "architecture.md": "# Architecture\nOpenClaw uses a plugin-based gateway architecture.\n",
    PROJECT_DIR / "docs" / "api.md": "# API Reference\nSee /api/v1 endpoints.\n",
    PROJECT_DIR / ".env.example": "OPENCLAW_PROJECT_DIR=/path/to/openclaw\nOPENCLAW_BRANCH=main\nDRY_RUN=false\n",
    WORKSPACE / "ops" / "monitoring" / "alerts.yaml": "alerts:\n  - name: gateway-down\n    threshold: 30s\n",
    WORKSPACE / "ops" / "monitoring" / "dashboards.json": '{"panels": []}\n',
    WORKSPACE / "ops" / "ci" / "pipeline.yml": "stages:\n  - build\n  - test\n  - deploy\n",
    WORKSPACE / "shared" / "certs" / "README.md": "Place TLS certificates here.\n",
    WORKSPACE / "shared" / "secrets" / ".gitkeep": "",
}

for path, content in distractors.items():
    write_file(path, content)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Set ownership to agent user
# ─────────────────────────────────────────────────────────────────────────────
run(f"chown -R agent:agent {WORKSPACE}")
run(f"chown -R agent:agent {AGENT_HOME}")

print("✅ Workspace generation complete.")
print(f"   Project dir : {PROJECT_DIR}")
print(f"   Branch      : dev/integration")
print(f"   Upstream    : {UPSTREAM_BARE}")
print(f"   Scripts dir : {SCRIPTS_DIR}")
print(f"   Config dir  : {OPENCLAW_CONFIG_DIR}")