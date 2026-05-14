import os
import json
import random
import shutil
from pathlib import Path
from datetime import datetime, timezone

random.seed(42)

# Base workspace directory
workspace = Path("/root/.openclaw/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Create the skill scripts directory and populate with real script logic ──
scripts_dir = workspace / "skills" / "personality-switcher" / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# utils.py
utils_py = '''
import json
import shutil
import os
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path.home() / ".openclaw" / "workspace"
PERSONALITIES_DIR = WORKSPACE / "personalities"
BACKUPS_DIR = PERSONALITIES_DIR / "backups"
STATE_FILE = WORKSPACE / "_personality_state.json"

def get_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"active_personality": "default", "timestamp": None, "previous_personality": None}

def save_state(active, previous):
    state = {
        "active_personality": active,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_personality": previous
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state

def validate_name(name):
    import re
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", name):
        return False, "Name must be lowercase alphanumeric with hyphens only"
    if len(name) > 40:
        return False, "Name too long (max 40 chars)"
    return True, ""

def personality_exists(name):
    return (PERSONALITIES_DIR / name).is_dir()

def create_backup(name):
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat().replace(":", "-").replace("+", "").replace("00", "")
    backup_name = f"current_{ts}"
    backup_path = BACKUPS_DIR / backup_name
    backup_path.mkdir(parents=True, exist_ok=True)
    soul = WORKSPACE / "SOUL.md"
    identity = WORKSPACE / "IDENTITY.md"
    if soul.exists():
        shutil.copy2(soul, backup_path / "SOUL.md")
    if identity.exists():
        shutil.copy2(identity, backup_path / "IDENTITY.md")
    return backup_name

def cleanup_backups(keep=10, days=None):
    if not BACKUPS_DIR.exists():
        return 0
    backups = sorted(
        [d for d in BACKUPS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )
    removed = 0
    if days is not None:
        import time
        cutoff = time.time() - days * 86400
        for b in backups[keep:]:
            if b.stat().st_mtime < cutoff:
                shutil.rmtree(b)
                removed += 1
        backups = [b for b in backups if b.exists()]
    for b in backups[keep:]:
        if b.exists():
            shutil.rmtree(b)
            removed += 1
    return removed
'''

(scripts_dir / "utils.py").write_text(utils_py)

# list_personalities.py
list_py = '''#!/usr/bin/env python3
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import PERSONALITIES_DIR, get_state

def main():
    state = get_state()
    active = state.get("active_personality", "default")
    if not PERSONALITIES_DIR.exists():
        print(json.dumps({"status": "success", "personalities": [], "active": active}))
        return
    personalities = sorted([
        d.name for d in PERSONALITIES_DIR.iterdir()
        if d.is_dir() and d.name != "backups"
    ])
    result = {
        "status": "success",
        "personalities": personalities,
        "active": active
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "list_personalities.py").write_text(list_py)

# create_personality.py
create_py = '''#!/usr/bin/env python3
"""Create a personality from a name and description.
Usage: python3 create_personality.py <name> <soul_content> <identity_content>
  or:  python3 create_personality.py --name <name> --soul <soul_file> --identity <identity_file>
"""
import json, sys, shutil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import PERSONALITIES_DIR, validate_name, personality_exists
from pathlib import Path

def main():
    args = sys.argv[1:]
    if len(args) < 1:
        print(json.dumps({"status": "error", "message": "Usage: create_personality.py <name> [soul_content] [identity_content]", "code": "usage_error"}))
        sys.exit(1)

    if args[0] == "--name":
        # --name <name> --soul <soul_file> --identity <identity_file>
        try:
            name_idx = args.index("--name") + 1
            soul_idx = args.index("--soul") + 1
            identity_idx = args.index("--identity") + 1
            name = args[name_idx]
            soul_content = Path(args[soul_idx]).read_text()
            identity_content = Path(args[identity_idx]).read_text()
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e), "code": "usage_error"}))
            sys.exit(1)
    else:
        name = args[0]
        soul_content = args[1] if len(args) > 1 else f"# SOUL.md - {name}\\n\\n## Core Identity\\n{name} personality.\\n"
        identity_content = args[2] if len(args) > 2 else f"# IDENTITY.md - {name}\\n\\n- **Name:** {name}\\n- **Type:** Custom\\n- **Emoji:** 🤖\\n- **Vibe:** A custom personality.\\n"

    valid, err = validate_name(name)
    if not valid:
        print(json.dumps({"status": "error", "message": err, "code": "invalid_name"}))
        sys.exit(1)

    if personality_exists(name):
        print(json.dumps({"status": "error", "message": f"Personality \\'{name}\\' already exists.", "code": "already_exists"}))
        sys.exit(1)

    PERSONALITIES_DIR.mkdir(parents=True, exist_ok=True)
    pdir = PERSONALITIES_DIR / name
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "SOUL.md").write_text(soul_content)
    (pdir / "IDENTITY.md").write_text(identity_content)

    print(json.dumps({
        "status": "success",
        "message": f"Personality \\'{name}\\' created.",
        "personality": name,
        "folder": str(pdir)
    }, indent=2))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "create_personality.py").write_text(create_py)

# switch_personality.py
switch_py = '''#!/usr/bin/env python3
"""Switch to a named personality with atomic backup/rollback.
Usage: python3 switch_personality.py <name>
"""
import json, sys, shutil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import (WORKSPACE, PERSONALITIES_DIR, get_state, save_state,
                   create_backup, personality_exists, cleanup_backups)
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: switch_personality.py <name>", "code": "usage_error"}))
        sys.exit(1)

    target = sys.argv[1]
    if not personality_exists(target):
        print(json.dumps({"status": "error", "message": f"Personality \\'{target}\\' not found.", "code": "personality_not_found"}))
        sys.exit(1)

    state = get_state()
    current = state.get("active_personality", "default")

    if current == target:
        print(json.dumps({"status": "success", "message": f"Already using \\'{target}\\'.", "personality": target}))
        return

    # Step 1: Create backup of current state
    try:
        backup_name = create_backup(current)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Backup failed: {e}", "code": "switch_failed"}))
        sys.exit(1)

    # Step 2: Persist current personality changes back to its folder
    try:
        current_dir = PERSONALITIES_DIR / current
        current_dir.mkdir(parents=True, exist_ok=True)
        soul = WORKSPACE / "SOUL.md"
        identity = WORKSPACE / "IDENTITY.md"
        if soul.exists():
            shutil.copy2(soul, current_dir / "SOUL.md")
        if identity.exists():
            shutil.copy2(identity, current_dir / "IDENTITY.md")
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Persist failed: {e}", "code": "switch_failed"}))
        sys.exit(1)

    # Step 3: Load new personality
    try:
        target_dir = PERSONALITIES_DIR / target
        shutil.copy2(target_dir / "SOUL.md", WORKSPACE / "SOUL.md")
        shutil.copy2(target_dir / "IDENTITY.md", WORKSPACE / "IDENTITY.md")
    except Exception as e:
        # Rollback
        bdir = PERSONALITIES_DIR / "backups" / backup_name
        if (bdir / "SOUL.md").exists():
            shutil.copy2(bdir / "SOUL.md", WORKSPACE / "SOUL.md")
        if (bdir / "IDENTITY.md").exists():
            shutil.copy2(bdir / "IDENTITY.md", WORKSPACE / "IDENTITY.md")
        print(json.dumps({"status": "error", "message": f"Load failed, rolled back: {e}", "code": "switch_failed"}))
        sys.exit(1)

    # Step 4: Update state
    try:
        save_state(target, current)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"State update failed: {e}", "code": "switch_failed"}))
        sys.exit(1)

    # Step 5: Verify integrity
    try:
        assert (WORKSPACE / "SOUL.md").exists(), "SOUL.md missing"
        assert (WORKSPACE / "IDENTITY.md").exists(), "IDENTITY.md missing"
        new_state = json.loads((WORKSPACE.parent / ".openclaw" / "workspace" / "_personality_state.json").read_text()) if False else json.loads((__import__("pathlib").Path.home() / ".openclaw" / "workspace" / "_personality_state.json").read_text())
        assert new_state.get("active_personality") == target
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Integrity check failed: {e}", "code": "integrity_check_failed"}))
        sys.exit(1)

    # Auto-cleanup backups (keep 10 most recent)
    cleanup_backups(keep=10)

    print(json.dumps({
        "status": "success",
        "message": f"Switched to personality \\'{target}\\'.",
        "personality": target,
        "previous": current,
        "backup": backup_name
    }, indent=2))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "switch_personality.py").write_text(switch_py)

# rename_personality.py
rename_py = '''#!/usr/bin/env python3
import json, sys, shutil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import PERSONALITIES_DIR, get_state, save_state, validate_name, personality_exists

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"status": "error", "message": "Usage: rename_personality.py <old-name> <new-name>", "code": "usage_error"}))
        sys.exit(1)

    old_name, new_name = sys.argv[1], sys.argv[2]

    if old_name == "default":
        print(json.dumps({"status": "error", "message": "Cannot rename \\'default\\'.", "code": "cannot_rename_default"}))
        sys.exit(1)

    valid, err = validate_name(new_name)
    if not valid:
        print(json.dumps({"status": "error", "message": err, "code": "invalid_name"}))
        sys.exit(1)

    if not personality_exists(old_name):
        print(json.dumps({"status": "error", "message": f"Personality \\'{old_name}\\' not found.", "code": "personality_not_found"}))
        sys.exit(1)

    if personality_exists(new_name):
        print(json.dumps({"status": "error", "message": f"Personality \\'{new_name}\\' already exists.", "code": "already_exists"}))
        sys.exit(1)

    (PERSONALITIES_DIR / old_name).rename(PERSONALITIES_DIR / new_name)

    state = get_state()
    if state.get("active_personality") == old_name:
        save_state(new_name, state.get("previous_personality"))

    print(json.dumps({"status": "success", "message": f"Renamed \\'{old_name}\\' to \\'{new_name}\\'.", "personality": new_name}))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "rename_personality.py").write_text(rename_py)

# delete_personality.py
delete_py = '''#!/usr/bin/env python3
import json, sys, shutil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import PERSONALITIES_DIR, WORKSPACE, get_state, save_state, personality_exists
import os

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: delete_personality.py <name>", "code": "usage_error"}))
        sys.exit(1)

    name = sys.argv[1]

    if name == "default":
        print(json.dumps({"status": "error", "message": "Cannot delete \\'default\\'.", "code": "cannot_delete_default"}))
        sys.exit(1)

    if not personality_exists(name):
        print(json.dumps({"status": "error", "message": f"Personality \\'{name}\\' not found.", "code": "personality_not_found"}))
        sys.exit(1)

    state = get_state()
    if state.get("active_personality") == name:
        # Auto-switch to default first
        import subprocess, sys as _sys
        scripts_dir = __import__("pathlib").Path(__file__).parent
        result = subprocess.run([_sys.executable, str(scripts_dir / "switch_personality.py"), "default"], capture_output=True, text=True)

    shutil.rmtree(PERSONALITIES_DIR / name)
    print(json.dumps({"status": "success", "message": f"Deleted personality \\'{name}\\'.", "personality": name}))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "delete_personality.py").write_text(delete_py)

# restore_personality.py
restore_py = '''#!/usr/bin/env python3
import json, sys, shutil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import WORKSPACE, PERSONALITIES_DIR, get_state

def main():
    state = get_state()
    active = state.get("active_personality", "default")
    target_dir = PERSONALITIES_DIR / active
    if not target_dir.exists():
        active = "default"
        target_dir = PERSONALITIES_DIR / "default"
    if not target_dir.exists():
        print(json.dumps({"status": "error", "message": "No personality to restore.", "code": "personality_not_found"}))
        return
    soul_src = target_dir / "SOUL.md"
    identity_src = target_dir / "IDENTITY.md"
    if soul_src.exists():
        shutil.copy2(soul_src, WORKSPACE / "SOUL.md")
    if identity_src.exists():
        shutil.copy2(identity_src, WORKSPACE / "IDENTITY.md")
    print(json.dumps({"status": "success", "message": f"Restored personality \\'{active}\\'.", "personality": active}))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "restore_personality.py").write_text(restore_py)

# cleanup_backups.py
cleanup_py = '''#!/usr/bin/env python3
"""Clean up old personality backups.
Usage: python3 cleanup_backups.py --keep N [--days D]
"""
import json, sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from utils import cleanup_backups, BACKUPS_DIR

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", type=int, default=10, help="Keep N most recent backups")
    parser.add_argument("--days", type=int, default=None, help="Also delete backups older than D days")
    args = parser.parse_args()

    if not BACKUPS_DIR.exists():
        print(json.dumps({"status": "success", "message": "No backups directory found.", "removed": 0}))
        return

    before = len([d for d in BACKUPS_DIR.iterdir() if d.is_dir()])
    removed = cleanup_backups(keep=args.keep, days=args.days)
    after = len([d for d in BACKUPS_DIR.iterdir() if d.is_dir()])

    print(json.dumps({
        "status": "success",
        "message": f"Cleanup complete. Removed {removed} backups.",
        "removed": removed,
        "kept": after,
        "before": before
    }, indent=2))

if __name__ == "__main__":
    main()
'''
(scripts_dir / "cleanup_backups.py").write_text(cleanup_py)

# ── 2. Initialize the workspace with a "default" personality ──
personalities_dir = workspace / "personalities"
personalities_dir.mkdir(parents=True, exist_ok=True)
backups_dir = personalities_dir / "backups"
backups_dir.mkdir(parents=True, exist_ok=True)

default_dir = personalities_dir / "default"
default_dir.mkdir(parents=True, exist_ok=True)

(default_dir / "SOUL.md").write_text("""# SOUL.md - Default

## Core Identity
A helpful, neutral AI assistant. Professional and direct.

## Voice & Mannerisms
Clear, concise communication. No-nonsense approach.

## Philosophy
Accuracy and helpfulness above all else.

## Signature Behaviors
- Answers questions directly
- Admits uncertainty honestly
""")

(default_dir / "IDENTITY.md").write_text("""# IDENTITY.md - Default

- **Name:** Assistant
- **Type:** AI Assistant
- **Emoji:** 🤖
- **Vibe:** Neutral, helpful, and professional.
- **Catchphrase:** How can I help?

## Quick Traits
- Professional
- Accurate
- Concise
""")

# Copy defaults to workspace root (active personality)
import shutil
shutil.copy2(default_dir / "SOUL.md", workspace / "SOUL.md")
shutil.copy2(default_dir / "IDENTITY.md", workspace / "IDENTITY.md")

# Initialize state file
state = {
    "active_personality": "default",
    "timestamp": "2025-01-15T09:00:00.000000Z",
    "previous_personality": None
}
(workspace / "_personality_state.json").write_text(json.dumps(state, indent=2))

# ── 3. Create USER.md (shared, must never be modified) ──
(workspace / "USER.md").write_text("""# USER.md - Shared User Context

- **Timezone:** UTC+0
- **Location:** London, UK
- **Platform:** Gaming Support Portal
- **Preferred Language:** English
- **Communication Style:** Casual but professional
- **Active Project:** GamingBot v3 multi-persona chatbot

## Preferences
- Direct answers
- Minimal jargon
- Short bullet points preferred
""")

# ── 4. Create MEMORY.md (shared, must never be modified) ──
(workspace / "MEMORY.md").write_text("""# MEMORY.md

## Session Notes
- User is building a customer support chatbot for a gaming platform
- Needs multiple themed personas for different support contexts
- Testing personality switching for Q3 release
""")

# ── 5. Create HEARTBEAT.md ──
(workspace / "HEARTBEAT.md").write_text("""# HEARTBEAT.md

## Scheduled Tasks

# Run on every heartbeat cycle
echo "Heartbeat tick at $(date)"
""")

# ── 6. Create distractor files to test contextual awareness ──
# Distractor directories and files
distractor_dirs = [
    workspace / "logs",
    workspace / "config",
    workspace / "data" / "exports",
    workspace / "data" / "imports",
    workspace / "tmp" / "sessions",
    workspace / "skills" / "other-skill" / "scripts",
    workspace / "docs" / "api",
    workspace / "docs" / "internal",
    workspace / "cache" / "responses",
    workspace / "cache" / "embeddings",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "logs" / "system.log": "2025-01-15 09:00:00 INFO System started\n2025-01-15 09:01:00 INFO Bot connected\n",
    workspace / "logs" / "errors.log": "2025-01-15 09:05:00 ERROR Timeout on request #4421\n",
    workspace / "config" / "bot_config.json": json.dumps({"version": "3.0", "max_sessions": 100, "timeout": 30}, indent=2),
    workspace / "config" / "personas_config.yaml": "# Personas config\ndefault_persona: assistant\nfallback: true\n",
    workspace / "data" / "exports" / "session_data_2025_01.csv": "session_id,user_id,timestamp,persona\n1001,u42,2025-01-10T10:00:00,default\n1002,u43,2025-01-11T11:00:00,default\n",
    workspace / "data" / "imports" / "user_profiles.json": json.dumps([{"id": "u42", "tier": "gold"}, {"id": "u43", "tier": "silver"}], indent=2),
    workspace / "tmp" / "sessions" / "sess_abc123.tmp": "session_token=abc123\nexpiry=2025-01-16T00:00:00Z\n",
    workspace / "tmp" / "sessions" / "sess_def456.tmp": "session_token=def456\nexpiry=2025-01-16T00:00:00Z\n",
    workspace / "skills" / "other-skill" / "scripts" / "run.py": "# This is a different skill entirely\nprint('other skill')\n",
    workspace / "docs" / "api" / "openapi.yaml": "openapi: 3.0.0\ninfo:\n  title: GamingBot API\n  version: 3.0\n",
    workspace / "docs" / "internal" / "architecture.md": "# Architecture\nGamingBot uses a microservices approach...\n",
    workspace / "cache" / "responses" / "resp_cache.db": "BINARY_PLACEHOLDER_CACHE_DATA\n",
    workspace / "cache" / "embeddings" / "embed_v2.bin": "EMBEDDING_VECTOR_DATA\n",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── 7. Create a "leftover" broken personality folder (distractor / edge case) ──
broken_dir = personalities_dir / "old-bot"
broken_dir.mkdir(parents=True, exist_ok=True)
# Intentionally incomplete: only has SOUL.md, missing IDENTITY.md
(broken_dir / "SOUL.md").write_text("# SOUL.md - Old Bot\n\n## Core Identity\nAn old, deprecated bot personality.\n")
# No IDENTITY.md - this is intentionally broken for distractor purposes

# ── 8. Pre-create some old backup dirs to test cleanup ──
import time
old_backup_timestamps = [
    "current_2025-01-10T08-00-00.000000",
    "current_2025-01-11T09-00-00.000000",
    "current_2025-01-12T10-00-00.000000",
    "current_2025-01-13T11-00-00.000000",
    "current_2025-01-14T12-00-00.000000",
]
for ts in old_backup_timestamps:
    b = backups_dir / ts
    b.mkdir(parents=True, exist_ok=True)
    (b / "SOUL.md").write_text(f"# SOUL.md backup from {ts}\n")
    (b / "IDENTITY.md").write_text(f"# IDENTITY.md backup from {ts}\n")

print("Workspace initialized successfully.")
print(f"Workspace root: {workspace}")
print(f"Personalities dir: {personalities_dir}")
print(f"Scripts dir: {scripts_dir}")
print(f"Pre-existing backups: {len(old_backup_timestamps)}")