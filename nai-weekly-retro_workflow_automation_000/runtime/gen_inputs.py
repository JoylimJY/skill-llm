#!/usr/bin/env python3
"""
Generate a realistic indie game dev workspace with memory logs and distractor files.
All random operations use fixed seeds for determinism.
"""

import os
import json
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create the weekly-retro scripts (simulate pre-existing skill scripts) ──
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# gather_week.py
(scripts_dir / "gather_week.py").write_text(r'''#!/usr/bin/env python3
"""Gather memory logs for the past N days and output structured JSON."""
import argparse, json, os, re, sys
from datetime import date, timedelta
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--memory-dir", default=os.path.expanduser("~/.openclaw/workspace/memory"))
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--end-date", default=str(date.today()))
    p.add_argument("--config", default=None)
    return p.parse_args()

def extract_entries(text):
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            entries.append(line[2:])
        elif re.match(r"^\d+\.", line):
            entries.append(re.sub(r"^\d+\.\s*", "", line))
    return entries

def main():
    args = parse_args()
    end = date.fromisoformat(args.end_date)
    memory_dir = Path(args.memory_dir)
    days_data = []
    all_entries = []
    for i in range(args.days):
        d = end - timedelta(days=args.days - 1 - i)
        fname = memory_dir / f"{d}.md"
        entries = []
        raw = ""
        if fname.exists():
            raw = fname.read_text()
            entries = extract_entries(raw)
        days_data.append({"date": str(d), "file": str(fname), "exists": fname.exists(), "entries": entries, "raw": raw})
        all_entries.extend(entries)
    result = {
        "period": {"start": str(end - timedelta(days=args.days-1)), "end": str(end), "days": args.days},
        "days": days_data,
        "all_entries": all_entries,
        "total_entries": len(all_entries),
        "active_days": sum(1 for d in days_data if d["exists"])
    }
    print(json.dumps(result))

main()
''')

# analyze.py
(scripts_dir / "analyze.py").write_text(r'''#!/usr/bin/env python3
"""Analyze gathered JSON for patterns, accomplishments, friction, etc."""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

ACCOMPLISHMENT_KEYWORDS = ["shipped", "published", "fixed", "built", "completed", "launched", "released", "deployed", "merged", "delivered"]
FRICTION_KEYWORDS = ["blocked", "failed", "broken", "stuck", "issue", "bug", "error", "problem", "struggle", "difficult", "couldn't", "delayed"]

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--history-file", default=None)
    return p.parse_args()

def extract_topics(entries):
    stop = {"a","an","the","and","or","but","in","on","at","to","for","of","with","by","from","is","was","are","were","be","been","being","have","has","had","do","did","does","it","its","i","my","we","our","this","that","as","up","out","not","so","than","then","into","also","just","about","after","all","no","can","could","would","should","will","been","which","what","when","how","who","their","they","them","there","some"}
    words = []
    for e in entries:
        words.extend(re.findall(r"[a-z][a-z\-]+", e.lower()))
    return [w for w in words if w not in stop and len(w) > 3]

def main():
    args = parse_args()
    data = json.load(sys.stdin)
    all_entries = data.get("all_entries", [])
    days = data.get("days", [])

    # Accomplishments
    accomplishments = [e for e in all_entries if any(k in e.lower() for k in ACCOMPLISHMENT_KEYWORDS)]

    # Friction points
    friction = [e for e in all_entries if any(k in e.lower() for k in FRICTION_KEYWORDS)]

    # Topics per day
    topics_by_day = {}
    for d in days:
        if d["exists"]:
            topics_by_day[d["date"]] = extract_topics(d["entries"])

    # Recurring themes (topics appearing 3+ days)
    all_topics = []
    for topics in topics_by_day.values():
        all_topics.extend(set(topics))
    topic_day_count = Counter(all_topics)
    recurring = [t for t, c in topic_day_count.most_common(20) if c >= 3]

    # Time sinks (most mentioned topics)
    flat_topics = []
    for topics in topics_by_day.values():
        flat_topics.extend(topics)
    time_sinks = [t for t, _ in Counter(flat_topics).most_common(5)]

    # Unfinished threads
    unfinished = [e for e in all_entries if any(k in e.lower() for k in ["working on", "wip", "in progress", "todo", "need to", "will", "next"])]

    # Work schedule (by day)
    active_days = [d["date"] for d in days if d["exists"]]

    # History comparison
    history_note = None
    if args.history_file:
        hp = Path(args.history_file)
        if hp.exists():
            try:
                hist = json.loads(hp.read_text())
                prev_scores = [e.get("score", 0) for e in hist.get("entries", [])]
                if prev_scores:
                    history_note = f"Previous week scores: {prev_scores}"
            except Exception:
                history_note = "History file found but could not be parsed."

    result = {
        "period": data.get("period", {}),
        "accomplishments": accomplishments,
        "recurring_themes": recurring,
        "friction_points": friction,
        "time_sinks": time_sinks,
        "unfinished_threads": unfinished,
        "active_days": active_days,
        "total_entries": data.get("total_entries", 0),
        "history_note": history_note,
        "raw_stats": {
            "total_days": data.get("period", {}).get("days", 7),
            "active_days_count": len(active_days),
        }
    }
    print(json.dumps(result))

main()
''')

# retrospective.py
(scripts_dir / "retrospective.py").write_text(r'''#!/usr/bin/env python3
"""Generate a markdown retrospective from analysis JSON."""
import argparse, json, sys
from datetime import date
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=None)
    p.add_argument("--no-frontmatter", action="store_true")
    return p.parse_args()

def score_week(data):
    base = 5.0
    base += min(len(data.get("accomplishments", [])) * 0.4, 2.0)
    base -= min(len(data.get("friction_points", [])) * 0.3, 2.0)
    base += min(data.get("raw_stats", {}).get("active_days_count", 0) * 0.2, 1.5)
    base += min(len(data.get("recurring_themes", [])) * 0.1, 0.5)
    return round(min(max(base, 1.0), 10.0), 1)

def generate_tags(data):
    tags = ["weekly-retro"]
    for theme in data.get("recurring_themes", [])[:5]:
        tags.append(theme.replace(" ", "-"))
    if data.get("friction_points"):
        tags.append("friction")
    if data.get("accomplishments"):
        tags.append("wins")
    return tags

def build_md(data, no_frontmatter=False):
    period = data.get("period", {})
    start = period.get("start", "unknown")
    end = period.get("end", "unknown")
    score = score_week(data)
    tags = generate_tags(data)
    lines = []

    if not no_frontmatter:
        lines.append("---")
        lines.append(f"date_range: {start} to {end}")
        lines.append(f"week_score: {score}")
        lines.append(f"tags: [{', '.join(tags)}]")
        lines.append(f"generated: {str(date.today())}")
        lines.append("---")
        lines.append("")

    lines.append(f"# Weekly Retrospective: {start} → {end}")
    lines.append("")

    # Week at a Glance
    lines.append("## Week at a Glance")
    active = data.get("raw_stats", {}).get("active_days_count", 0)
    total = data.get("raw_stats", {}).get("total_days", 7)
    total_e = data.get("total_entries", 0)
    lines.append(f"Active on {active}/{total} days with {total_e} logged entries. "
                 f"Recurring themes: {', '.join(data.get('recurring_themes', [])[:3]) or 'none identified'}. "
                 f"Week score: {score}/10.")
    lines.append("")

    # Wins
    lines.append("## Wins")
    for a in data.get("accomplishments", []) or ["No accomplishments logged."]:
        lines.append(f"- {a}")
    lines.append("")

    # Patterns
    lines.append("## Patterns")
    lines.append(f"**Recurring themes:** {', '.join(data.get('recurring_themes', [])) or 'None'}")
    lines.append(f"**Time sinks:** {', '.join(data.get('time_sinks', [])) or 'None'}")
    lines.append(f"**Active days:** {', '.join(data.get('active_days', []))}")
    lines.append("")

    # Friction Points
    lines.append("## Friction Points")
    for f in data.get("friction_points", []) or ["No friction points logged."]:
        lines.append(f"- {f}")
    lines.append("")

    # Unfinished Business
    lines.append("## Unfinished Business")
    for u in data.get("unfinished_threads", []) or ["Nothing carried forward."]:
        lines.append(f"- {u}")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    recs = []
    if data.get("friction_points"):
        recs.append(f"Address top friction: \"{data['friction_points'][0][:60]}...\"")
    if data.get("unfinished_threads"):
        recs.append(f"Prioritize carry-forward: \"{data['unfinished_threads'][0][:60]}\"")
    if len(data.get("active_days", [])) < 5:
        recs.append("Increase consistency — aim for 5+ active logging days next week.")
    if not recs:
        recs = ["Maintain current momentum.", "Continue refining recurring workflows.", "Review time sinks for optimization."]
    for r in recs[:3]:
        lines.append(f"- {r}")
    lines.append("")

    # Week Score
    lines.append("## Week Score")
    lines.append(f"**{score}/10** — Based on {len(data.get('accomplishments', []))} wins, "
                 f"{len(data.get('friction_points', []))} friction points, "
                 f"and {active}/{total} active days.")
    lines.append("")

    if data.get("history_note"):
        lines.append("## Historical Context")
        lines.append(data["history_note"])
        lines.append("")

    return "\n".join(lines)

def main():
    args = parse_args()
    data = json.load(sys.stdin)
    md = build_md(data, no_frontmatter=args.no_frontmatter)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        print(f"Retrospective written to {args.output}", file=sys.stderr)
    else:
        print(md)

main()
''')

# history.py
(scripts_dir / "history.py").write_text(r'''#!/usr/bin/env python3
"""Track retrospective history for longitudinal patterns."""
import argparse, json, sys
from datetime import date
from pathlib import Path

DEFAULT_DATA_DIR = Path("/workspace/vault/retro-history")

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--record", action="store_true")
    p.add_argument("--analysis", default=None)
    p.add_argument("--show", action="store_true")
    p.add_argument("--trends", action="store_true")
    p.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    return p.parse_args()

def main():
    args = parse_args()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    history_file = data_dir / "history.json"

    if history_file.exists():
        history = json.loads(history_file.read_text())
    else:
        history = {"entries": []}

    if args.record:
        if args.analysis:
            analysis_path = Path(args.analysis)
            if not analysis_path.exists():
                print(f"ERROR: Analysis file not found: {args.analysis}", file=sys.stderr)
                sys.exit(1)
            analysis = json.loads(analysis_path.read_text())
        else:
            analysis = json.load(sys.stdin)

        from scripts.retrospective import score_week
        score = score_week(analysis) if False else None
        # Compute score inline
        base = 5.0
        base += min(len(analysis.get("accomplishments", [])) * 0.4, 2.0)
        base -= min(len(analysis.get("friction_points", [])) * 0.3, 2.0)
        base += min(analysis.get("raw_stats", {}).get("active_days_count", 0) * 0.2, 1.5)
        base += min(len(analysis.get("recurring_themes", [])) * 0.1, 0.5)
        score = round(min(max(base, 1.0), 10.0), 1)

        entry = {
            "recorded_at": str(date.today()),
            "period": analysis.get("period", {}),
            "score": score,
            "accomplishments_count": len(analysis.get("accomplishments", [])),
            "friction_count": len(analysis.get("friction_points", [])),
            "recurring_themes": analysis.get("recurring_themes", []),
        }
        history["entries"].append(entry)
        history_file.write_text(json.dumps(history, indent=2))
        print(f"Recorded retro for period {analysis.get('period', {})}", file=sys.stderr)

    elif args.show:
        for e in history.get("entries", []):
            print(f"{e.get('period', {}).get('end','?')} | score={e.get('score','?')} | wins={e.get('accomplishments_count',0)} | friction={e.get('friction_count',0)}")

    elif args.trends:
        entries = history.get("entries", [])
        if len(entries) < 2:
            print("Not enough history for trends.")
        else:
            scores = [e.get("score", 0) for e in entries]
            print(f"Scores over time: {scores}")
            print(f"Average: {sum(scores)/len(scores):.1f}")
            print(f"Trend: {'improving' if scores[-1] > scores[0] else 'declining or flat'}")

main()
''')

# ── 2. Create memory directory with realistic indie game dev logs ──
# Target sprint week: 2024-03-11 to 2024-03-17 (Monday to Sunday)
MEMORY_BASE = WORKSPACE / "memory" / "game-dev"
MEMORY_BASE.mkdir(parents=True, exist_ok=True)

SPRINT_DATES = [
    "2024-03-11",  # Monday
    "2024-03-12",  # Tuesday
    "2024-03-13",  # Wednesday
    "2024-03-14",  # Thursday
    "2024-03-15",  # Friday
    # Saturday missing (no log)
    "2024-03-17",  # Sunday
]

MEMORY_LOGS = {
    "2024-03-11": """# Memory Log - 2024-03-11

## Work Done
- Fixed the collision detection bug in the player physics system
- Built new tilemap renderer using chunked loading
- shipped prototype level editor to internal testers
- Reviewed 12 bug reports from QA team
- Working on enemy pathfinding AI — still WIP

## Blockers
- Blocked on audio middleware license approval
- Shader compilation errors on older GPU drivers causing issues

## Notes
- Need to integrate new particle system next week
""",
    "2024-03-12": """# Memory Log - 2024-03-12

## Work Done  
- Fixed shader compilation errors — identified driver compatibility issue
- Built automated test harness for physics module
- Published dev blog post about tilemap system
- Continued working on enemy pathfinding AI

## Blockers
- Audio license still not approved — delayed audio integration
- Performance profiler showing unexpected spike in render thread

## Notes
- Todo: benchmark new tilemap vs old system
- Will add particle system integration this week
""",
    "2024-03-13": """# Memory Log - 2024-03-13

## Work Done
- Shipped hotfix for crash on level load (reported by 3 testers)
- Built particle system integration with existing entity component system
- Fixed memory leak in asset loader
- Enemy pathfinding AI — completed grid navigation, still need steering behaviors

## Blockers
- Render thread spike issue still present — difficult to reproduce
- Need to resolve audio middleware problem before milestone

## Focus Areas
- Physics, tilemap, pathfinding, particle system
- Audio integration blocked
""",
    "2024-03-14": """# Memory Log - 2024-03-14

## Work Done
- Completed enemy steering behaviors — pathfinding AI now fully functional
- Fixed render thread spike — was caused by unthrottled shadow map updates
- Built level streaming system for large open areas
- Deployed test build to QA environment

## Blockers  
- Audio middleware issue escalated to legal team — resolution pending
- Bug: enemies clipping through thin walls at high speeds

## Notes
- Todo: enemy wall clipping fix
- working on optimization pass next
""",
    "2024-03-15": """# Memory Log - 2024-03-15

## Work Done
- Fixed enemy wall clipping using swept collision checks
- shipped first complete vertical slice of level 1
- Built save system with checksummed data for anti-cheat
- Published internal playtest build for team feedback
- Completed optimization pass on particle system — 40% perf improvement

## Blockers
- Audio: still blocked by legal/licensing
- Need to start on UI/HUD system but backlog full

## Notes
- in progress: boss encounter design
- Todo: UI system next sprint
""",
    "2024-03-17": """# Memory Log - 2024-03-17

## Work Done
- Built rough boss encounter state machine
- Fixed 4 critical bugs from playtest feedback
- Launched internal retrospective on sprint velocity
- working on documentation for entity component system

## Blockers
- Audio licensing unresolved — will need to find alternative middleware

## Notes
- Audio blocker persisted all week — major friction point  
- pathfinding, physics, particle system all stabilized
- Todo: switch to alternative audio library next week
""",
}

for date_str, content in MEMORY_LOGS.items():
    (MEMORY_BASE / f"{date_str}.md").write_text(content)

# ── 3. Create the vault directory structure (empty, agent must populate) ──
vault_dir = WORKSPACE / "vault"
vault_dir.mkdir(parents=True, exist_ok=True)
(vault_dir / "weekly-retro").mkdir(parents=True, exist_ok=True)
# Do NOT create the retrospective file — agent must do that

# ── 4. Create distractor files (10+) to test contextual awareness ──

# Distractor 1: Old sprint notes that shouldn't be used
(WORKSPACE / "sprints").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "sprints" / "sprint-42-notes.md").write_text("""# Sprint 42 Notes
- Old velocity data: 34 story points
- Carried over: audio integration, UI system
- Team mood: cautiously optimistic
""")

# Distractor 2: A fake analyze.py in root
(WORKSPACE / "analyze_old.py").write_text("""# DEPRECATED - use scripts/analyze.py
import sys
print("This script is deprecated.")
""")

# Distractor 3: config files
(WORKSPACE / "config").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "config" / "gather_config.json").write_text(json.dumps({
    "memory_dir": "/workspace/memory/wrong-path",
    "days": 14,
    "note": "This is a config template, not the correct config"
}))

# Distractor 4: Another memory directory with unrelated logs
other_mem = WORKSPACE / "memory" / "personal"
other_mem.mkdir(parents=True, exist_ok=True)
for d in ["2024-03-11", "2024-03-14"]:
    (other_mem / f"{d}.md").write_text(f"# Personal log {d}\n- Grocery shopping\n- Gym session\n")

# Distractor 5: Old retrospectives that look similar
old_retro = WORKSPACE / "vault" / "weekly-retro"
(old_retro / "2024-03-03.md").write_text("""---
date_range: 2024-02-26 to 2024-03-03
week_score: 6.5
tags: [weekly-retro, gamedev]
---
# Weekly Retrospective (OLD)
This is last week's retro — do not modify.
""")

# Distractor 6: A requirements.txt (misleading — no packages needed)
(WORKSPACE / "requirements.txt").write_text("# No external dependencies needed\n# Python stdlib only\n")

# Distractor 7: A run.sh that uses WRONG arguments
(WORKSPACE / "run.sh").write_text("""#!/bin/bash
# OUTDATED script - arguments may be wrong
python3 scripts/gather_week.py --memory-dir memory/ --days 14 | python3 scripts/analyze.py | python3 scripts/retrospective.py
""")

# Distractor 8: Fake history file in wrong location
(WORKSPACE / "history.json").write_text(json.dumps({
    "entries": [
        {"recorded_at": "2024-03-03", "period": {"start": "2024-02-26", "end": "2024-03-03"}, "score": 6.5}
    ]
}))

# Distractor 9: A logs directory with non-memory files
(WORKSPACE / "logs").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "logs" / "build.log").write_text("BUILD SUCCESS\nCompiled 342 files in 8.2s\n")
(WORKSPACE / "logs" / "test_run.log").write_text("All 187 tests passed\nCoverage: 73%\n")

# Distractor 10: A notes.md at root with misleading path hints
(WORKSPACE / "notes.md").write_text("""# Dev Notes
Memory logs are sometimes in: ~/.openclaw/workspace/memory
But for this project: /workspace/memory/game-dev/
See run.sh for the pipeline (may be outdated).
""")

# Distractor 11: A partially-filled analysis.json from a previous failed run
(WORKSPACE / "analysis_partial.json").write_text(json.dumps({
    "period": {"start": "2024-03-11", "end": "2024-03-17", "days": 7},
    "accomplishments": [],
    "note": "INCOMPLETE - do not use"
}))

# Distractor 12: Scripts directory with an additional unrelated script
(scripts_dir / "cleanup.py").write_text("""#!/usr/bin/env python3
# Utility: clean up old log files
import os, sys
print("Cleanup utility - not part of the retro pipeline")
""")

# ── 5. Create the retro-history directory for history.py output ──
(WORKSPACE / "vault" / "retro-history").mkdir(parents=True, exist_ok=True)

print("Workspace generated successfully.")
print(f"Memory logs created: {len(MEMORY_LOGS)} files")
print(f"Sprint week: 2024-03-11 to 2024-03-17")