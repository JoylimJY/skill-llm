import os
import json
import random
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

HOME = Path("/root")

# ── Directory structure for OpenClaw workspace ──────────────────────────────
SKILLS_DIR = HOME / ".openclaw" / "workspace" / "skills"
SKILL_MGR_DIR = SKILLS_DIR / "dynamic-skill-manager"
SCRIPTS_DIR = SKILL_MGR_DIR / "scripts"
SKILL_DATA_DIR = HOME / ".openclaw" / "workspace" / ".skill-manager"
ARCHIVE_DIR = SKILL_DATA_DIR / "archive"

for d in [SCRIPTS_DIR, SKILL_DATA_DIR, ARCHIVE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Write the actual skill_manager.py ────────────────────────────────────────
skill_manager_code = r'''#!/usr/bin/env python3
"""Dynamic Skill Manager - skill_manager.py"""

import sys
import json
import re
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta

HOME = Path.home()
SKILLS_DIR = HOME / ".openclaw" / "workspace" / "skills"
DATA_DIR = HOME / ".openclaw" / "workspace" / ".skill-manager"
REGISTRY_FILE = DATA_DIR / "registry.json"
USAGE_LOG_FILE = DATA_DIR / "usage-log.jsonl"
ARCHIVE_DIR = DATA_DIR / "archive"

PINNED_SKILLS = {
    "self-improving-agent",
    "pahf",
    "error-log-selfcheck",
    "dynamic-skill-manager",
}

VALID_NAME_RE = re.compile(r'^[A-Za-z0-9_-]+$')


def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {"skills": {}}


def save_registry(reg):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(reg, f, indent=2)


def cmd_sync():
    """Sync installed skills from disk into registry."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    reg = load_registry()
    now = datetime.now(timezone.utc).isoformat()
    added = []
    for skill_path in SKILLS_DIR.iterdir():
        if not skill_path.is_dir() or skill_path.is_symlink():
            continue
        name = skill_path.name
        if not VALID_NAME_RE.match(name):
            continue
        if name not in reg["skills"]:
            reg["skills"][name] = {
                "installed_at": now,
                "source": "local",
                "usage_count": 0,
                "last_used": None,
                "context_keywords": [],
                "pinned": name in PINNED_SKILLS,
            }
            added.append(name)
    save_registry(reg)
    if added:
        print(f"Synced {len(added)} new skill(s): {', '.join(added)}")
    else:
        print("Registry already up to date.")


def cmd_list():
    """List all skills."""
    reg = load_registry()
    skills = reg.get("skills", {})
    if not skills:
        print("No skills registered. Run `sync` first.")
        return
    for name, meta in sorted(skills.items()):
        pin_marker = "📌" if meta.get("pinned") else "  "
        last = meta.get("last_used") or "never"
        count = meta.get("usage_count", 0)
        print(f"{pin_marker} {name:<40} uses={count:<4} last_used={last}")


def cmd_pinned():
    """Show pinned/system skills."""
    reg = load_registry()
    pinned = [(n, m) for n, m in reg.get("skills", {}).items() if m.get("pinned")]
    if not pinned:
        print("No pinned skills found.")
        return
    for name, meta in sorted(pinned):
        print(f"📌 {name}")


def cmd_idle(days_str):
    """Find skills idle for N days."""
    try:
        days = int(days_str)
    except ValueError:
        print(f"Error: days must be an integer, got '{days_str}'")
        sys.exit(1)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    reg = load_registry()
    idle = []
    for name, meta in reg.get("skills", {}).items():
        if meta.get("pinned"):
            continue
        last_used = meta.get("last_used")
        if last_used is None:
            idle.append((name, "never"))
        else:
            lu_dt = datetime.fromisoformat(last_used)
            if lu_dt < cutoff:
                idle.append((name, last_used))
    if not idle:
        print(f"No idle skills found (threshold: {days} days).")
        return
    print(f"Idle skills (>{days} days):")
    for name, last in idle:
        print(f"  {name}  (last_used={last})")


def cmd_track(skill_name, context):
    """Record skill usage."""
    if not VALID_NAME_RE.match(skill_name):
        print(f"Error: invalid skill name '{skill_name}'")
        sys.exit(1)
    reg = load_registry()
    now = datetime.now(timezone.utc).isoformat()
    if skill_name not in reg["skills"]:
        print(f"Warning: skill '{skill_name}' not in registry. Adding it.")
        reg["skills"][skill_name] = {
            "installed_at": now,
            "source": "local",
            "usage_count": 0,
            "last_used": None,
            "context_keywords": [],
            "pinned": skill_name in PINNED_SKILLS,
        }
    entry = reg["skills"][skill_name]
    entry["usage_count"] = entry.get("usage_count", 0) + 1
    entry["last_used"] = now
    keywords = [w.strip().lower() for w in context.split() if len(w.strip()) > 3]
    existing = entry.get("context_keywords", [])
    entry["context_keywords"] = list(set(existing + keywords))[:20]
    save_registry(reg)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USAGE_LOG_FILE, "a") as f:
        f.write(json.dumps({
            "timestamp": now,
            "skill": skill_name,
            "context": context,
        }) + "\n")
    print(f"Tracked usage of '{skill_name}' (total uses: {entry['usage_count']})")


def cmd_uninstall(skill_name):
    """Safely uninstall a skill."""
    # 1. Input validation
    if not VALID_NAME_RE.match(skill_name):
        print(f"Error: invalid skill name '{skill_name}' (only alphanumeric, dash, underscore allowed)")
        sys.exit(1)

    # 2. System skill protection
    if skill_name in PINNED_SKILLS:
        print(f"Error: '{skill_name}' is a system skill and cannot be uninstalled.")
        sys.exit(1)

    # 3. Path traversal prevention
    resolved = (SKILLS_DIR / skill_name).resolve()
    try:
        resolved.relative_to(SKILLS_DIR.resolve())
    except ValueError:
        print(f"Error: path traversal detected for '{skill_name}'")
        sys.exit(1)

    # 4. Symlink detection
    skill_path = SKILLS_DIR / skill_name
    if skill_path.is_symlink():
        print(f"Error: '{skill_name}' is a symlink; refusing to uninstall.")
        sys.exit(1)

    # 5. Check registry
    reg = load_registry()
    if skill_name not in reg["skills"]:
        print(f"Error: '{skill_name}' not found in registry.")
        sys.exit(1)

    # 6. Archive metadata
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_file = ARCHIVE_DIR / f"{skill_name}.json"
    with open(archive_file, "w") as f:
        json.dump({
            "skill": skill_name,
            "uninstalled_at": datetime.now(timezone.utc).isoformat(),
            "metadata": reg["skills"][skill_name],
        }, f, indent=2)

    # 7. Remove from registry
    del reg["skills"][skill_name]
    save_registry(reg)

    # 8. Remove from disk (if exists)
    if skill_path.exists():
        shutil.rmtree(skill_path)
        print(f"Uninstalled '{skill_name}' and removed files.")
    else:
        print(f"Uninstalled '{skill_name}' from registry (no files on disk).")


def main():
    if len(sys.argv) < 2:
        print("Usage: skill_manager.py <command> [args]")
        print("Commands: sync, list, pinned, idle <days>, track <skill> <context>, uninstall <skill>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "sync":
        cmd_sync()
    elif cmd == "list":
        cmd_list()
    elif cmd == "pinned":
        cmd_pinned()
    elif cmd == "idle":
        if len(sys.argv) < 3:
            print("Usage: skill_manager.py idle <days>")
            sys.exit(1)
        cmd_idle(sys.argv[2])
    elif cmd == "track":
        if len(sys.argv) < 4:
            print("Usage: skill_manager.py track <skill-name> \"<context>\"")
            sys.exit(1)
        cmd_track(sys.argv[2], sys.argv[3])
    elif cmd == "uninstall":
        if len(sys.argv) < 3:
            print("Usage: skill_manager.py uninstall <skill-name>")
            sys.exit(1)
        cmd_uninstall(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(SCRIPTS_DIR / "skill_manager.py").write_text(skill_manager_code)

# ── Create installed skill directories on disk ──────────────────────────────
now_utc = datetime.now(timezone.utc)

# Skills that SHOULD be uninstalled (idle > 45 days, not pinned)
idle_skills = [
    "data-formatter",
    "log-analyzer",
    "pdf-converter",
    "image-resizer",
    "csv-merger",
]

# Skills that should NOT be uninstalled: active (used recently)
active_skills = [
    "report-generator",
    "api-tester",
]

# System/pinned skills — must NEVER be uninstalled
system_skills = [
    "self-improving-agent",
    "pahf",
    "error-log-selfcheck",
    "dynamic-skill-manager",  # already exists (the skill manager itself)
]

# Create directories for idle skills
for skill in idle_skills:
    skill_dir = SKILLS_DIR / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    # Add some distractor files
    (skill_dir / "README.md").write_text(f"# {skill}\nA skill for {skill.replace('-', ' ')}.")
    (skill_dir / "config.yaml").write_text(f"name: {skill}\nversion: 1.0.0\n")
    scripts = skill_dir / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "main.py").write_text(f'print("Running {skill}")\n')

# Create directories for active skills
for skill in active_skills:
    skill_dir = SKILLS_DIR / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "README.md").write_text(f"# {skill}\nActive skill.")
    (skill_dir / "config.yaml").write_text(f"name: {skill}\nversion: 2.1.0\n")
    scripts = skill_dir / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "main.py").write_text(f'print("Running {skill}")\n')

# Create directories for system skills (except dynamic-skill-manager which already exists)
for skill in system_skills[:-1]:  # dynamic-skill-manager already set up
    skill_dir = SKILLS_DIR / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "config.yaml").write_text(f"name: {skill}\npinned: true\n")

# ── Pre-populate registry with STALE data (the messy input) ─────────────────
# The registry is deliberately OUT OF SYNC:
#   - idle skills are present but with old last_used dates (80 days ago)
#   - active skills are present but with last_used 5 days ago
#   - system skills are present and marked pinned
#   - one ghost skill entry that is NOT on disk anymore
#   - one skill on disk that is NOT yet in registry (needs sync)

old_date = (now_utc - timedelta(days=80)).isoformat()
recent_date = (now_utc - timedelta(days=5)).isoformat()
medium_date = (now_utc - timedelta(days=46)).isoformat()

# "csv-merger" will be the skill that needs to be discovered by sync (not pre-registered)
# We'll pre-register all EXCEPT csv-merger to force sync usage

stale_registry = {
    "skills": {
        "data-formatter": {
            "installed_at": (now_utc - timedelta(days=120)).isoformat(),
            "source": "clawhub",
            "usage_count": 3,
            "last_used": old_date,
            "context_keywords": ["format", "data", "convert"],
            "pinned": False,
        },
        "log-analyzer": {
            "installed_at": (now_utc - timedelta(days=90)).isoformat(),
            "source": "clawhub",
            "usage_count": 7,
            "last_used": old_date,
            "context_keywords": ["logs", "errors", "analyze"],
            "pinned": False,
        },
        "pdf-converter": {
            "installed_at": (now_utc - timedelta(days=200)).isoformat(),
            "source": "clawhub",
            "usage_count": 1,
            "last_used": None,   # never used
            "context_keywords": [],
            "pinned": False,
        },
        "image-resizer": {
            "installed_at": (now_utc - timedelta(days=150)).isoformat(),
            "source": "clawhub",
            "usage_count": 2,
            "last_used": medium_date,
            "context_keywords": ["image", "resize"],
            "pinned": False,
        },
        "report-generator": {
            "installed_at": (now_utc - timedelta(days=30)).isoformat(),
            "source": "clawhub",
            "usage_count": 15,
            "last_used": recent_date,
            "context_keywords": ["report", "generate"],
            "pinned": False,
        },
        "api-tester": {
            "installed_at": (now_utc - timedelta(days=10)).isoformat(),
            "source": "clawhub",
            "usage_count": 22,
            "last_used": recent_date,
            "context_keywords": ["api", "test", "endpoint"],
            "pinned": False,
        },
        # Ghost: on registry but NOT on disk
        "old-webhook-sender": {
            "installed_at": (now_utc - timedelta(days=300)).isoformat(),
            "source": "clawhub",
            "usage_count": 0,
            "last_used": None,
            "context_keywords": [],
            "pinned": False,
        },
        # System skills
        "self-improving-agent": {
            "installed_at": (now_utc - timedelta(days=365)).isoformat(),
            "source": "system",
            "usage_count": 100,
            "last_used": old_date,  # Trap: old date but pinned -> must NOT be uninstalled
            "context_keywords": ["system", "agent"],
            "pinned": True,
        },
        "pahf": {
            "installed_at": (now_utc - timedelta(days=365)).isoformat(),
            "source": "system",
            "usage_count": 50,
            "last_used": old_date,
            "context_keywords": ["system"],
            "pinned": True,
        },
        "error-log-selfcheck": {
            "installed_at": (now_utc - timedelta(days=365)).isoformat(),
            "source": "system",
            "usage_count": 200,
            "last_used": old_date,
            "context_keywords": ["error", "system"],
            "pinned": True,
        },
        "dynamic-skill-manager": {
            "installed_at": (now_utc - timedelta(days=365)).isoformat(),
            "source": "system",
            "usage_count": 300,
            "last_used": recent_date,
            "context_keywords": ["manage", "skill"],
            "pinned": True,
        },
        # csv-merger is intentionally MISSING from registry (exists on disk) -> sync required
    }
}

save_path = SKILL_DATA_DIR / "registry.json"
with open(save_path, "w") as f:
    json.dump(stale_registry, f, indent=2)

# ── Pre-existing usage log (distractor) ─────────────────────────────────────
usage_log_entries = []
for i in range(8):
    ts = (now_utc - timedelta(days=random.randint(60, 200))).isoformat()
    skill = random.choice(["data-formatter", "log-analyzer", "pdf-converter"])
    usage_log_entries.append(json.dumps({
        "timestamp": ts,
        "skill": skill,
        "context": f"Used for batch operation {i}",
    }))

with open(SKILL_DATA_DIR / "usage-log.jsonl", "w") as f:
    f.write("\n".join(usage_log_entries) + "\n")

# ── Distractor files throughout the workspace ─────────────────────────────────
distractor_dir = HOME / ".openclaw" / "workspace" / "logs"
distractor_dir.mkdir(parents=True, exist_ok=True)
for i in range(5):
    (distractor_dir / f"run_{i}.log").write_text(f"[INFO] Run {i} completed\n[WARN] Some warning\n")

config_dir = HOME / ".openclaw" / "workspace" / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "agent.yaml").write_text("agent:\n  name: ClawdBot\n  version: 2.0\n")
(config_dir / "skills.yaml").write_text("auto_sync: true\nidle_threshold_days: 45\n")
(config_dir / "deprecated_registry.json").write_text('{"version": 1, "skills": []}')

notes_dir = HOME / ".openclaw" / "workspace" / "notes"
notes_dir.mkdir(parents=True, exist_ok=True)
(notes_dir / "todo.txt").write_text("- Review skill usage quarterly\n- Check for idle skills\n")
(notes_dir / "audit_2025.txt").write_text("Audit completed. 3 skills removed.\n")

# Temp files
tmp_dir = HOME / ".openclaw" / "workspace" / ".tmp"
tmp_dir.mkdir(parents=True, exist_ok=True)
for i in range(3):
    (tmp_dir / f"cache_{i}.bin").write_bytes(bytes(random.getrandbits(8) for _ in range(64)))

print("Workspace initialized successfully.")
print(f"Skills on disk: {idle_skills + active_skills + system_skills}")
print(f"Skills missing from registry (need sync): ['csv-merger']")
print(f"Skills that are idle (>45 days): data-formatter, log-analyzer, pdf-converter, image-resizer, csv-merger (after sync)")
print(f"System skills (pinned, must not be uninstalled): {system_skills}")