#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the open-memory-system task.
Creates the skill scripts, distractor files, and a partial messy environment.
"""
import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create the skill directory structure (simulating unzipped skill) ────────
skill_dir = WORKSPACE / ".openclaw" / "workspace" / "skills" / "open-memory-system"
scripts_dir = skill_dir / "scripts"
crons_dir = skill_dir / "crons"
hooks_dir = skill_dir / "scripts" / "auto-save-memory"

for d in [scripts_dir, crons_dir, hooks_dir,
          skill_dir / "hooks"]:
    d.mkdir(parents=True, exist_ok=True)

# ── memory.py ──────────────────────────────────────────────────────────────────
memory_py = '''#!/usr/bin/env python3
"""Open Memory System - memory.py CLI"""
import sys, os, json, glob
from pathlib import Path
from datetime import datetime, timedelta

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/root/.openclaw/workspace/memory"))
DEFAULT_EXPIRE_DAYS = 90

def ensure_dirs():
    for sub in ["user/preferences", "user/entities", "user/events",
                "agent/persona", "agent/episodic", "short-term"]:
        (MEMORY_DIR / sub).mkdir(parents=True, exist_ok=True)

def working():
    p = MEMORY_DIR / "working.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"items": [], "updated_at": None}

def save_working(data):
    p = MEMORY_DIR / "working.json"
    data["updated_at"] = datetime.now().isoformat()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_pref(key, value, category):
    ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    fname = MEMORY_DIR / "user" / "preferences" / f"{ts}_{key.replace(' ','_')}.json"
    record = {"key": key, "value": value, "category": category,
              "created_at": datetime.now().isoformat()}
    fname.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    # also update working memory
    w = working()
    w["items"].append({"type": "pref", "key": key, "value": value})
    save_working(w)
    print(f"[pref] saved: {key} = {value} ({category})")

def cmd_event(title, description):
    ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    fname = MEMORY_DIR / "user" / "events" / f"{ts}_{title.replace(' ','_')}.json"
    record = {"title": title, "description": description,
              "created_at": datetime.now().isoformat(), "source": "manual"}
    fname.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    w = working()
    w["items"].append({"type": "event", "title": title})
    save_working(w)
    print(f"[event] saved: {title}")

def cmd_episode(title, sentiment, lesson):
    ensure_dirs()
    if sentiment not in ("positive", "negative", "neutral"):
        print(f"[episode] ERROR: sentiment must be positive/negative/neutral, got: {sentiment}", file=sys.stderr)
        sys.exit(1)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    fname = MEMORY_DIR / "agent" / "episodic" / f"{ts}_{title.replace(' ','_')}.json"
    record = {"title": title, "sentiment": sentiment, "lesson": lesson,
              "created_at": datetime.now().isoformat()}
    fname.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    w = working()
    w["items"].append({"type": "episode", "title": title, "sentiment": sentiment})
    save_working(w)
    print(f"[episode] saved: {title} ({sentiment})")

def cmd_summary():
    ensure_dirs()
    prefs = list((MEMORY_DIR / "user" / "preferences").glob("*.json"))
    events = list((MEMORY_DIR / "user" / "events").glob("*.json"))
    episodes = list((MEMORY_DIR / "agent" / "episodic").glob("*.json"))
    short = list((MEMORY_DIR / "short-term").glob("*.md"))
    print(f"=== Memory Summary ===")
    print(f"Preferences : {len(prefs)}")
    print(f"Events      : {len(events)}")
    print(f"Episodes    : {len(episodes)}")
    print(f"Short-term  : {len(short)}")
    return {"preferences": len(prefs), "events": len(events),
            "episodes": len(episodes), "short_term": len(short)}

def cmd_cleanup():
    ensure_dirs()
    cutoff = datetime.now() - timedelta(days=DEFAULT_EXPIRE_DAYS)
    removed = 0
    for f in (MEMORY_DIR / "short-term").glob("*.md"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                removed += 1
        except Exception:
            pass
    print(f"[cleanup] removed {removed} expired short-term files")

def cmd_read():
    ensure_dirs()
    w = working()
    items = w.get("items", [])
    print(f"=== Working Memory ({len(items)} items) ===")
    for it in items[-10:]:
        print(f"  - {it}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        cmd_read()
    elif args[0] == "summary":
        cmd_summary()
    elif args[0] == "cleanup":
        cmd_cleanup()
    elif args[0] == "read":
        cmd_read()
    elif args[0] == "pref" and len(args) == 4:
        cmd_pref(args[1], args[2], args[3])
    elif args[0] == "event" and len(args) == 3:
        cmd_event(args[1], args[2])
    elif args[0] == "episode" and len(args) == 4:
        cmd_episode(args[1], args[2], args[3])
    else:
        print(f"Unknown command or wrong args: {args}", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  memory.py pref <key> <value> <category>", file=sys.stderr)
        print("  memory.py event <title> <description>", file=sys.stderr)
        print("  memory.py episode <title> <sentiment> <lesson>", file=sys.stderr)
        print("  memory.py summary|cleanup|read", file=sys.stderr)
        sys.exit(1)
'''
(scripts_dir / "memory.py").write_text(memory_py)

# ── distill_l2.py ──────────────────────────────────────────────────────────────
distill_py = '''#!/usr/bin/env python3
"""L2 Distillation: short-term/*.md -> user/events/"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/root/.openclaw/workspace/memory"))
PATTERN = re.compile(r"^(\\d{4}-\\d{2}-\\d{2}-\\d{4})\\.md$")

def distill():
    src = MEMORY_DIR / "short-term"
    dst = MEMORY_DIR / "user" / "events"
    dst.mkdir(parents=True, exist_ok=True)
    
    distilled = 0
    skipped = 0
    for f in sorted(src.glob("*.md")):
        if not PATTERN.match(f.name):
            print(f"[distill] SKIP (bad name format): {f.name}")
            skipped += 1
            continue
        content = f.read_text(encoding="utf-8")
        # Extract title from first # heading
        title = "session-summary"
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        ts = f.stem.replace("-", "").replace(" ", "")[:12]
        out_name = f"{ts}_{title.replace(' ','_')[:40]}.json"
        record = {
            "title": title,
            "description": content[:500],
            "source": "distill_l2",
            "source_file": f.name,
            "created_at": datetime.now().isoformat()
        }
        (dst / out_name).write_text(json.dumps(record, ensure_ascii=False, indent=2))
        print(f"[distill] {f.name} -> {out_name}")
        distilled += 1
    
    print(f"[distill] done: {distilled} distilled, {skipped} skipped")
    return distilled

if __name__ == "__main__":
    count = distill()
    if count == 0:
        print("[distill] WARNING: no short-term files were distilled", file=sys.stderr)
'''
(scripts_dir / "distill_l2.py").write_text(distill_py)

# ── auto-save-memory hook stub ─────────────────────────────────────────────────
hook_sh = '''#!/bin/bash
# auto-save-memory hook - triggered on session:end
MEMORY_DIR="${MEMORY_DIR:-/root/.openclaw/workspace/memory}"
LEARNINGS_DIR=".learnings"
if [ -d "$LEARNINGS_DIR" ]; then
    for f in "$LEARNINGS_DIR"/*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        cp "$f" "$MEMORY_DIR/user/events/${fname%.md}_auto.json" 2>/dev/null || true
    done
fi
echo "[hook] auto-save-memory complete"
'''
(hooks_dir / "run.sh").write_text(hook_sh)
(hooks_dir / "run.sh").chmod(0o755)

# ── crons/memory-crons.txt ─────────────────────────────────────────────────────
crons_txt = """# memory-crons.txt
# Add these to crontab: crontab -e
#
# Daily cleanup at 02:00
0 2 * * * MEMORY_DIR=$HOME/.openclaw/workspace/memory python3 ~/.openclaw/workspace/skills/open-memory-system/scripts/memory.py cleanup
#
# L2 distillation at 20:00
0 20 * * * MEMORY_DIR=$HOME/.openclaw/workspace/memory python3 ~/.openclaw/workspace/skills/open-memory-system/scripts/distill_l2.py
#
# Summary at 09:00
0 9 * * * MEMORY_DIR=$HOME/.openclaw/workspace/memory python3 ~/.openclaw/workspace/skills/open-memory-system/scripts/memory.py summary
"""
(crons_dir / "memory-crons.txt").write_text(crons_txt)

# ── 2. Create hooks directory (pre-installed hook stub) ────────────────────────
hooks_base = WORKSPACE / ".openclaw" / "hooks"
load_mem_hook = hooks_base / "load-memory-on-start"
load_mem_hook.mkdir(parents=True, exist_ok=True)
(load_mem_hook / "run.sh").write_text('''#!/bin/bash
# load-memory-on-start - pre-installed hook
MEMORY_DIR="${MEMORY_DIR:-/root/.openclaw/workspace/memory}"
python3 ~/.openclaw/workspace/skills/open-memory-system/scripts/memory.py read
''')
(load_mem_hook / "run.sh").chmod(0o755)

# ── 3. Create distractor files to test contextual awareness ───────────────────
distractor_root = WORKSPACE / "biotech_lab"
distractor_root.mkdir(parents=True, exist_ok=True)

# Researcher profiles (messy, unstructured)
researchers = [
    {
        "name": "Dr. Elena Marsh",
        "role": "Principal Investigator",
        "preferences": {"reports": "concise bullet-point format", "meeting_time": "mornings only"},
        "projects": ["CRISPR-X1", "ProteinFold-V3"],
        "notes": "Prefers data-driven arguments. Allergic to jargon."
    },
    {
        "name": "Dr. Raj Patel",
        "role": "Computational Biologist",
        "preferences": {"code_review": "asynchronous Slack", "data_format": "parquet over CSV"},
        "projects": ["ProteinFold-V3", "GeneExpr-Atlas"],
        "notes": "Night owl. Responds faster after 9pm."
    },
    {
        "name": "Sophia Chen",
        "role": "Lab Manager",
        "preferences": {"communication": "direct and brief", "scheduling": "Google Calendar only"},
        "projects": ["all"],
        "notes": "Key contact for equipment reservations."
    }
]
for r in researchers:
    fname = r["name"].replace(" ", "_").replace(".", "") + ".json"
    (distractor_root / fname).write_text(json.dumps(r, indent=2))

# Project status files
projects_dir = distractor_root / "projects"
projects_dir.mkdir(exist_ok=True)
project_data = {
    "CRISPR-X1": {"status": "phase2", "start": "2024-01-15", "milestone": "First animal trial"},
    "ProteinFold-V3": {"status": "active", "start": "2024-03-01", "milestone": "Paper submission Q3"},
    "GeneExpr-Atlas": {"status": "planning", "start": "2024-06-01", "milestone": "Data collection"},
}
for pname, pdata in project_data.items():
    (projects_dir / f"{pname}.json").write_text(json.dumps(pdata, indent=2))

# Old meeting notes (distractor)
notes_dir = distractor_root / "meeting_notes"
notes_dir.mkdir(exist_ok=True)
for i, date in enumerate(["2024-03-05", "2024-04-12", "2024-05-20"]):
    (notes_dir / f"meeting_{date}.txt").write_text(
        f"Meeting {date}: Discussed project progress. Action items assigned.\n"
        f"Dr. Marsh emphasized timeline adherence. Budget reviewed.\n"
    )

# Malformed short-term memory files (wrong format - distractors for distill_l2)
bad_stm_dir = WORKSPACE / ".openclaw" / "workspace" / "memory" / "short-term"
bad_stm_dir.mkdir(parents=True, exist_ok=True)

# Wrong-format file (should be skipped by distill_l2)
(bad_stm_dir / "session_old_backup.md").write_text(
    "# Old Session Backup\nThis file has wrong naming format and should be skipped.\n"
)
# Another wrong-format file
(bad_stm_dir / "20240601-notes.md").write_text(
    "# Notes\nAlso wrong format.\n"
)

# ── 4. Create the valid short-term session files the agent must create ─────────
# (These are the RAW INPUTS provided to show what needs distilling — but they are
# intentionally placed at the wrong path to force the agent to create proper ones)
raw_sessions_dir = distractor_root / "raw_session_logs"
raw_sessions_dir.mkdir(exist_ok=True)

session_logs = [
    {
        "filename": "2024-06-10-1430.md",
        "content": """# CRISPR-X1 Phase 2 Kickoff
Session with Dr. Elena Marsh on CRISPR-X1 Phase 2 planning.
Key outcomes: animal trial protocols approved, budget confirmed at $2.1M.
Next milestone: first trial results by 2024-08-15.
"""
    },
    {
        "filename": "2024-06-11-0900.md",
        "content": """# ProteinFold Model Review
Raj Patel presented ProteinFold-V3 intermediate results.
Model accuracy: 94.2% on benchmark set.
Decision: proceed to paper drafting phase.
"""
    }
]
for s in session_logs:
    (raw_sessions_dir / s["filename"]).write_text(s["content"])

# ── 5. Create an outdated/partial working.json (messy input) ──────────────────
mem_root = WORKSPACE / ".openclaw" / "workspace" / "memory"
mem_root.mkdir(parents=True, exist_ok=True)
for sub in ["user/preferences", "user/entities", "user/events",
            "agent/persona", "agent/episodic"]:
    (mem_root / sub).mkdir(parents=True, exist_ok=True)

(mem_root / "working.json").write_text(json.dumps({
    "items": [
        {"type": "stale", "note": "leftover from previous session - ignore"},
    ],
    "updated_at": "2024-01-01T00:00:00",
    "version": "0.1-legacy"
}, indent=2))

# ── 6. More distractor files ───────────────────────────────────────────────────
config_dir = WORKSPACE / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "lab_settings.yaml").write_text(
    "lab_name: BioNovaTech\nregion: EU\ndata_retention_days: 180\n"
)
(config_dir / "agent_config.json").write_text(json.dumps({
    "agent_id": "bionova-assist-v2",
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000
}, indent=2))

logs_dir = WORKSPACE / "logs"
logs_dir.mkdir(exist_ok=True)
for i in range(5):
    (logs_dir / f"run_{i:03d}.log").write_text(
        f"[2024-06-{10+i:02d}] INFO: Agent session started\n"
        f"[2024-06-{10+i:02d}] INFO: Processed {random.randint(10,100)} queries\n"
        f"[2024-06-{10+i:02d}] INFO: Session ended normally\n"
    )

print("Workspace generation complete.")
print(f"Skill scripts: {scripts_dir}")
print(f"Raw session logs: {raw_sessions_dir}")
print(f"Memory root: {mem_root}")