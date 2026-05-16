#!/usr/bin/env python3
"""
Generates the sandbox workspace for the openclaw-auto-dream consolidation task.
A solo indie game developer's workspace with scattered daily logs, a growing MEMORY.md,
stale open threads, and existing memory infrastructure needing a consolidation run.
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ─── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "memory/episodes",
    "memory/assets",
    "daily",
    "references",
    "skills/skills/openclaw-auto-dream/references",
    "src/engine",
    "src/ui",
    "assets/sprites",
    "assets/audio",
    "docs/design",
    "builds/v0.3",
    "builds/v0.4",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "src/engine/physics.py": "# 2D physics engine stub\nclass PhysicsWorld:\n    pass\n",
    "src/engine/renderer.py": "# Renderer stub\nclass Renderer:\n    def draw(self): pass\n",
    "src/ui/hud.py": "# HUD stub\nclass HUD:\n    def render(self): pass\n",
    "assets/sprites/README.txt": "Sprite sheets go here.\n",
    "assets/audio/README.txt": "Audio files go here.\n",
    "docs/design/mechanics.md": "# Game Mechanics\n\n- Platformer with procedural levels\n- Roguelike elements\n- Crafting system TBD\n",
    "docs/design/lore.md": "# Lore\n\nIn a world shattered by the Clock Breach...\n",
    "builds/v0.3/build_notes.txt": "v0.3 build: fixed collision detection.\n",
    "builds/v0.4/build_notes.txt": "v0.4 build: added shader support.\n",
    "tests/unit/test_physics.py": "import unittest\n# TODO: add tests\n",
    "tests/integration/test_game_loop.py": "import unittest\n# TODO: integration tests\n",
    ".gitignore": "*.pyc\n__pycache__/\nbuild/\n",
    "LICENSE": "MIT License\nCopyright 2024 Alex Dev\n",
}
for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# ─── SKILL references (minimal stubs — agent must use logic from SKILL.md) ────
(WORKSPACE / "references" / "memory-template.md").write_text(
    "# Memory Template\n\n"
    "## MEMORY.md template\n"
    "```\n"
    "# Long-Term Memory\n\n"
    "## Core Facts\n\n"
    "## Key Decisions\n\n"
    "## Lessons Learned\n\n"
    "## Open Threads\n\n"
    "## Todos\n"
    "```\n\n"
    "## memory/index.json v3.0 schema\n"
    "```json\n"
    "{\n"
    '  "schema_version": "3.0",\n'
    '  "last_dream": "<ISO timestamp>",\n'
    '  "dream_count": <int>,\n'
    '  "entries": [\n'
    '    {\n'
    '      "id": "<slug>",\n'
    '      "source": "<filename>",\n'
    '      "type": "fact|decision|lesson|todo|thread",\n'
    '      "importance": <0.0-1.0>,\n'
    '      "created": "<ISO date>",\n'
    '      "last_seen": "<ISO date>",\n'
    '      "tags": ["<tag>"],\n'
    '      "summary": "<one line>"\n'
    '    }\n'
    '  ],\n'
    '  "stats": {\n'
    '    "total_entries": <int>,\n'
    '    "decisions": <int>,\n'
    '    "lessons": <int>,\n'
    '    "open_threads": <int>,\n'
    '    "stale_threads": <int>\n'
    '  }\n'
    "}\n"
    "```\n\n"
    "## memory/dream-log.md template\n"
    "Each dream appends:\n"
    "```\n"
    "## Dream #<N> — <ISO timestamp>\n\n"
    "**Before:** <X> entries | **After:** <Y> entries | **Delta:** +<Z> (+<pct>%)\n\n"
    "### Changes\n"
    "- <list of what was added/updated>\n\n"
    "### Stale Threads (>14 days)\n"
    "- <thread title> — last updated <date>\n\n"
    "### Insights\n"
    "- <insight>\n\n"
    "### Suggestions\n"
    "- <suggestion>\n"
    "```\n"
)

(WORKSPACE / "references" / "scoring.md").write_text(
    "# Importance Scoring\n\n"
    "Base score by type:\n"
    "- decision: 0.8\n"
    "- lesson: 0.75\n"
    "- fact: 0.5\n"
    "- todo: 0.6\n"
    "- thread: 0.65\n\n"
    "Apply forgetting curve: importance *= 0.95^(days_since_seen)\n\n"
    "Health score = (consolidated_entries / total_log_lines) * 100\n"
)

(WORKSPACE / "skills" / "skills" / "openclaw-auto-dream" / "references" / "dream-prompt-lite.md").write_text(
    "# Dream Prompt Lite\n\n"
    "Run these steps in order:\n"
    "0. Smart Skip + Recall\n"
    "1. Collect unconsolidated daily logs\n"
    "2. Consolidate into MEMORY.md and procedures.md; mark logs with `<!-- consolidated -->`\n"
    "2.8. Stale Thread Detection (>14 days)\n"
    "3. Append to dream-log.md; regenerate dashboard.html if it exists\n"
    "4. Notify with growth metrics including Dream #N streak\n"
    "Safety: if MEMORY.md changes >30%, save .bak first; always save index.json.bak before rebuilding index.json\n"
)

# ─── Existing MEMORY.md (populated, ~30+ entries) ─────────────────────────────
today = datetime.now()

memory_md_content = """# Long-Term Memory

## Core Facts
- Engine: custom Python 2D engine, pygame-based
- Target platform: Windows + Linux
- Art style: pixel art, 16x16 tiles
- Genre: roguelike platformer with crafting
- Project start date: 2024-01-15

## Key Decisions
- [2024-01-20] Chose ECS (Entity-Component-System) architecture over OOP hierarchy
- [2024-01-25] Decided to use Tiled for level editing
- [2024-02-01] Chose SQLite for save game data instead of JSON flat files
- [2024-02-10] Dropped multiplayer support for v1.0 scope control
- [2024-02-14] Using PyInstaller for distribution packaging
- [2024-02-20] Switched from Pygame to Pyglet for better OpenGL support
- [2024-03-01] Chose CC-BY-SA 4.0 for all game assets

## Lessons Learned
- Always profile before optimizing — initial bottleneck was asset loading not physics
- Tiled map export needs post-processing script to normalize tile IDs
- Pyglet audio has latency issues on Windows; need to investigate alternatives
- Unit tests for procedural generation require fixed random seeds
- ECS systems ordering matters a lot for correct frame updates

## Open Threads
- [2024-01-30] Crafting system design — need to finalize recipe graph <!-- last_updated: 2024-01-30 -->
- [2024-02-05] Audio backend investigation — Pyglet latency on Windows <!-- last_updated: 2024-02-05 -->
- [2024-02-18] Shader pipeline for lighting effects <!-- last_updated: 2024-02-18 -->
- [2024-03-10] Steam page copy and screenshots <!-- last_updated: 2024-03-10 -->
- [2024-03-15] Controller support implementation <!-- last_updated: 2024-03-15 -->

## Todos
- Write unit tests for ECS system ordering
- Create Tiled post-processing script
- Benchmark asset loading pipeline
- Document save game schema
- Set up CI pipeline with GitHub Actions

## Workflow Preferences
(see memory/procedures.md)
"""

(WORKSPACE / "MEMORY.md").write_text(memory_md_content)

# Count lines for >30% change threshold reference (eval will check .bak exists)
memory_lines = len(memory_md_content.splitlines())

# ─── Existing memory/procedures.md ────────────────────────────────────────────
(WORKSPACE / "memory" / "procedures.md").write_text(
    "# Workflow Preferences\n\n"
    "## Development\n"
    "- Always run `pytest tests/unit` before committing\n"
    "- Use feature branches: `feature/<name>`\n"
    "- Tag releases with semantic versioning\n\n"
    "## Asset Pipeline\n"
    "- Export sprites at 2x then downscale\n"
    "- Audio: 44.1kHz, 16-bit WAV masters\n"
)

# ─── Existing memory/index.json (OLD schema — v2, needs rebuild to v3.0) ───────
old_index = {
    "schema_version": "2.0",
    "last_updated": (today - timedelta(days=8)).isoformat(),
    "entries": [
        {"id": "decision-ecs", "content": "ECS architecture decision", "type": "decision"},
        {"id": "lesson-profiling", "content": "Profile before optimizing", "type": "lesson"},
        {"id": "fact-engine", "content": "pygame-based engine", "type": "fact"},
    ]
}
(WORKSPACE / "memory" / "index.json").write_text(json.dumps(old_index, indent=2))

# ─── Existing memory/dream-log.md (2 previous dreams) ────────────────────────
prev_dream_1 = (today - timedelta(days=15)).strftime("%Y-%m-%dT04:00:00")
prev_dream_2 = (today - timedelta(days=8)).strftime("%Y-%m-%dT04:00:00")
(WORKSPACE / "memory" / "dream-log.md").write_text(
    f"# Dream Log\n\n"
    f"## Dream #1 — {prev_dream_1}\n\n"
    f"**Before:** 0 entries | **After:** 12 entries | **Delta:** +12 (+100%)\n\n"
    f"### Changes\n"
    f"- Initialized memory architecture\n"
    f"- Consolidated 3 daily logs\n"
    f"- Added 12 entries across facts, decisions, lessons\n\n"
    f"### Insights\n"
    f"- Strong early technical decisions documented\n\n"
    f"### Suggestions\n"
    f"- Consider adding milestones tracking\n\n"
    f"---\n\n"
    f"## Dream #2 — {prev_dream_2}\n\n"
    f"**Before:** 12 entries | **After:** 28 entries | **Delta:** +16 (+133%)\n\n"
    f"### Changes\n"
    f"- Consolidated 5 daily logs\n"
    f"- Added Pyglet migration decision\n"
    f"- Documented ECS ordering lesson\n\n"
    f"### Stale Threads (>14 days)\n"
    f"- None detected\n\n"
    f"### Insights\n"
    f"- Architecture is stabilizing\n\n"
    f"### Suggestions\n"
    f"- Start documenting audio pipeline decisions\n\n"
    f"---\n\n"
)

# ─── Existing memory/archive.md ───────────────────────────────────────────────
(WORKSPACE / "memory" / "archive.md").write_text(
    "# Archive\n\n"
    "## Archived — 2024-02-01\n"
    "- Early brainstorming notes on genre selection (roguelike chosen over puzzle)\n"
    "- Initial tech stack comparison (pygame vs pyglet vs arcade)\n"
)

# ─── memory/episodes ──────────────────────────────────────────────────────────
(WORKSPACE / "memory" / "episodes" / "project-kickoff.md").write_text(
    "# Episode: Project Kickoff\n\n"
    "Jan 15 2024 — Alex started the Clockbreach project. First commit, basic engine loop working.\n"
    "Decided on roguelike platformer genre after prototyping 3 concepts.\n"
)

# ─── Daily logs (unconsolidated — the agent must process these) ───────────────
# Generate 5 daily logs from the past 7 days (unconsolidated)
daily_logs = []

day_offsets = [6, 5, 4, 3, 1]  # days ago
log_contents = [
    # 6 days ago
    {
        "filename": f"daily/{(today - timedelta(days=6)).strftime('%Y-%m-%d')}.md",
        "content": f"""# Daily Log — {(today - timedelta(days=6)).strftime('%Y-%m-%d')}

## What I worked on
- Implemented procedural dungeon generation using BSP tree algorithm
- Fixed a critical bug in the physics collision detection (AABB was off by one pixel)
- Started integrating Tiled map loader

## Decisions
- [DECISION] Chose BSP tree over cellular automata for dungeon gen — more controllable room sizes
- [DECISION] Will use a dedicated asset preloader thread to fix startup lag

## Lessons
- [LESSON] BSP dungeon gen needs minimum room size constraints or you get degenerate 1x1 rooms
- [LESSON] AABB collision edge cases always come from integer vs float coordinate mixing

## Progress
- Dungeon generator: 80% done
- Tiled loader: 20% done

## Notes
- Need to profile BSP gen performance at large map sizes
"""
    },
    # 5 days ago
    {
        "filename": f"daily/{(today - timedelta(days=5)).strftime('%Y-%m-%d')}.md",
        "content": f"""# Daily Log — {(today - timedelta(days=5)).strftime('%Y-%m-%d')}

## What I worked on
- Completed Tiled map loader — it works with multi-layer maps
- Added entity spawning from Tiled object layers
- Wrote unit tests for BSP dungeon generator (fixed seed)

## Decisions
- [DECISION] Entity spawning rules will be data-driven via JSON config files, not hardcoded

## Lessons
- [LESSON] Tiled object layers use pixel coordinates, not tile coordinates — need conversion

## Open Thread
- [THREAD] Entity balance tuning — how many enemies per room? Need playtesting data <!-- last_updated: {(today - timedelta(days=5)).strftime('%Y-%m-%d')} -->

## Todos
- [ ] Write JSON schema for entity spawn config
- [ ] Add integration test for Tiled loader with multi-layer maps
"""
    },
    # 4 days ago
    {
        "filename": f"daily/{(today - timedelta(days=4)).strftime('%Y-%m-%d')}.md",
        "content": f"""# Daily Log — {(today - timedelta(days=4)).strftime('%Y-%m-%d')}

## What I worked on
- Designed crafting recipe graph — decided on DAG (directed acyclic graph) structure
- Closed the crafting system design thread — recipe graph is finalized!
- Implemented basic inventory system

## Decisions
- [DECISION] Crafting recipes stored as DAG — allows multi-path crafting chains
- [DECISION] Inventory uses slot-based system, max 20 slots for v1.0

## Lessons
- [LESSON] DAG cycle detection is essential — circular recipes caused infinite loops in prototype

## Notes
- Crafting thread is now resolved — can archive that open thread
- Inventory UI mockup needed next week

⚠️ PERMANENT: DAG structure must never be changed to tree — this is a core architectural invariant
"""
    },
    # 3 days ago
    {
        "filename": f"daily/{(today - timedelta(days=3)).strftime('%Y-%m-%d')}.md",
        "content": f"""# Daily Log — {(today - timedelta(days=3)).strftime('%Y-%m-%d')}

## What I worked on
- Investigated audio latency issue on Windows with Pyglet
- Tested miniaudio library as alternative — much lower latency!
- Started Steam page draft

## Decisions  
- [DECISION] Switching audio backend from Pyglet to miniaudio for v0.5
- [DECISION] Steam early access launch target: Q3 2024

## Lessons
- [LESSON] miniaudio Python bindings (miniaudio package on PyPI) work great with pygame event loop
- [LESSON] Steam page needs 5 screenshots minimum — start capturing gameplay footage now

## Open Thread
- [THREAD] Steam page screenshots — need 5 gameplay screenshots <!-- last_updated: {(today - timedelta(days=3)).strftime('%Y-%m-%d')} -->

## Todos
- [ ] Replace Pyglet audio calls with miniaudio
- [ ] Capture 5 gameplay screenshots for Steam
- [ ] Update audio pipeline docs
"""
    },
    # 1 day ago
    {
        "filename": f"daily/{(today - timedelta(days=1)).strftime('%Y-%m-%d')}.md",
        "content": f"""# Daily Log — {(today - timedelta(days=1)).strftime('%Y-%m-%d')}

## What I worked on
- Replaced Pyglet audio with miniaudio — latency issue resolved!
- Benchmarked BSP gen: 50ms for 100x100 map — acceptable
- Updated Tiled post-processing script

## Decisions
- [DECISION] Audio migration to miniaudio complete — marking audio thread as resolved

## Lessons
- [LESSON] Benchmarking early prevents late-stage performance surprises — do it every sprint

## Progress
- miniaudio integration: done
- BSP performance: validated
- Tiled post-processing script: done

## Notes
- Audio backend investigation thread can be closed
- Controller support still not started — getting stale
"""
    },
]

for log in daily_logs:
    (WORKSPACE / log["filename"]).write_text(log["content"])

# ─── A stale already-consolidated log (older, already marked) ─────────────────
old_log_date = (today - timedelta(days=20)).strftime('%Y-%m-%d')
(WORKSPACE / "daily" / f"{old_log_date}.md").write_text(
    f"# Daily Log — {old_log_date}\n\n"
    "## What I worked on\n"
    "- Initial ECS implementation\n"
    "- First playable prototype\n\n"
    "## Decisions\n"
    "- [DECISION] ECS chosen over OOP\n\n"
    "<!-- consolidated -->\n"
)

# ─── Compute current MEMORY.md entry count for eval reference ─────────────────
# Save metadata about the test scenario for the eval script
test_meta = {
    "memory_md_line_count": memory_lines,
    "unconsolidated_log_count": 5,
    "previous_dream_count": 2,
    "expected_dream_number": 3,
    "stale_threads": [
        {"title": "Crafting system design", "last_updated": "2024-01-30"},
        {"title": "Audio backend investigation", "last_updated": "2024-02-05"},
        {"title": "Shader pipeline for lighting effects", "last_updated": "2024-02-18"},
        {"title": "Steam page copy and screenshots", "last_updated": "2024-03-10"},
        {"title": "Controller support implementation", "last_updated": "2024-03-15"},
    ],
    "permanent_marker_present": True,
}
(WORKSPACE / "memory" / "assets" / "test_meta.json").write_text(
    json.dumps(test_meta, indent=2)
)

print(f"[gen_inputs] Workspace created at {WORKSPACE}")
print(f"[gen_inputs] MEMORY.md: {memory_lines} lines")
print(f"[gen_inputs] Unconsolidated daily logs: {len(daily_logs)}")
print(f"[gen_inputs] Previous dreams: 2 (expecting Dream #3)")