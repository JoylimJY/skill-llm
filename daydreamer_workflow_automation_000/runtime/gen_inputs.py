import os
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")
SKILL_DIR = WORKSPACE / ".claude" / "skills" / "daydreamer"
SKILL_DIR.mkdir(parents=True, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractor_dirs = [
    WORKSPACE / "src" / "engine",
    WORKSPACE / "src" / "ui",
    WORKSPACE / "src" / "audio",
    WORKSPACE / "assets" / "sprites",
    WORKSPACE / "assets" / "maps",
    WORKSPACE / "docs" / "design",
    WORKSPACE / "tests" / "unit",
    WORKSPACE / "scripts" / "build",
    WORKSPACE / "config" / "env",
    WORKSPACE / "logs" / "old",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    WORKSPACE / "src" / "engine" / "physics.py": "# Physics engine stub\nGRAVITY = 9.8\n",
    WORKSPACE / "src" / "engine" / "collision.py": "# Collision detection\nclass AABB: pass\n",
    WORKSPACE / "src" / "ui" / "hud.py": "# HUD rendering\nDEFAULT_FONT = 'monospace'\n",
    WORKSPACE / "src" / "audio" / "mixer.py": "# Audio mixer\nSAMPLE_RATE = 44100\n",
    WORKSPACE / "assets" / "sprites" / "manifest.json": json.dumps({"version": "1.0", "sprites": ["hero.png", "enemy.png"]}),
    WORKSPACE / "assets" / "maps" / "level01.tmx": "<map version='1.4'><layer name='ground'/></map>",
    WORKSPACE / "docs" / "design" / "gdd.md": "# Game Design Document\n## Overview\nA puzzle-platformer with time mechanics.\n",
    WORKSPACE / "tests" / "unit" / "test_physics.py": "import pytest\ndef test_gravity(): assert 9.8 > 0\n",
    WORKSPACE / "scripts" / "build" / "package.sh": "#!/bin/bash\necho 'Building...'\n",
    WORKSPACE / "config" / "env" / "dev.env": "DEBUG=true\nLOG_LEVEL=verbose\n",
    WORKSPACE / "logs" / "old" / "build_2024.log": "BUILD OK 2024-01-15 artifacts: 42\n",
    WORKSPACE / "README_DEV.md": "# Dev Notes\nSee docs/design/gdd.md for the full GDD.\n",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── Claude Code JSONL session logs (realistic messy data for seed-memories) ──
def make_uuid():
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:8]

def heartbeat_entry(ts):
    return json.dumps({
        "type": "heartbeat",
        "timestamp": ts,
        "sessionId": make_uuid(),
        "content": "",
        "result": "no work"
    })

def tool_entry(ts, tool, input_text, output_text):
    return json.dumps({
        "type": "tool_use",
        "timestamp": ts,
        "sessionId": make_uuid(),
        "tool": tool,
        "input": input_text,
        "output": output_text
    })

def assistant_entry(ts, text):
    return json.dumps({
        "type": "assistant",
        "timestamp": ts,
        "sessionId": make_uuid(),
        "content": text
    })

def user_entry(ts, text):
    return json.dumps({
        "type": "user",
        "timestamp": ts,
        "sessionId": make_uuid(),
        "content": text
    })

base_time = datetime(2024, 11, 1, 9, 0, 0)

def ts(delta_minutes):
    return (base_time + timedelta(minutes=delta_minutes)).isoformat() + "Z"

# Session log 1 — recent (most recent first ordering in file = chronological, agent reverses)
session1_lines = [
    # Meaningful events
    user_entry(ts(0), "Can you add a double-jump mechanic to the player controller?"),
    assistant_entry(ts(1), "Sure! I'll add a double-jump flag to track mid-air jumps."),
    tool_entry(ts(2), "Write", "src/engine/player.py", "Added double_jump_count tracking..."),
    assistant_entry(ts(3), "Done. The player can now jump twice before landing. Resets on ground contact."),

    user_entry(ts(10), "The collision detection is too expensive on large maps. Can you optimize it?"),
    assistant_entry(ts(11), "The current AABB check is O(n²). I'll add spatial partitioning with a simple grid."),
    tool_entry(ts(12), "Edit", "src/engine/collision.py", "Implemented spatial hash grid for collision pruning"),
    assistant_entry(ts(13), "Collision checks are now ~80% faster on maps with >200 entities by using spatial hashing."),

    # Heartbeat noise
    heartbeat_entry(ts(20)),
    heartbeat_entry(ts(21)),
    heartbeat_entry(ts(22)),

    user_entry(ts(30), "Please set up the audio mixer to support positional 3D audio."),
    assistant_entry(ts(31), "I'll use a panning algorithm based on entity X position relative to the camera."),
    tool_entry(ts(32), "Write", "src/audio/mixer.py", "Added pan_audio(entity_x, camera_x) function"),
    assistant_entry(ts(33), "Positional audio is live. Sounds fade and pan based on the entity's screen position."),

    # Trivial / empty status check
    json.dumps({"type": "status_check", "timestamp": ts(34), "content": "", "result": "idle"}),

    user_entry(ts(40), "The level editor crashes when saving maps larger than 256x256. Can you fix it?"),
    assistant_entry(ts(41), "Root cause: the serializer tries to stringify the full tile array into a single JSON string, hitting a recursion limit."),
    tool_entry(ts(42), "Edit", "src/editor/serializer.py", "Changed to streaming chunk-based serialization"),
    assistant_entry(ts(43), "Fixed. Large maps now serialize in chunks of 64x64 tiles without stack overflow."),

    user_entry(ts(50), "Add a save/load system for player progress."),
    assistant_entry(ts(51), "I'll use a simple JSON file in the user's app data directory with checksum validation."),
    tool_entry(ts(52), "Write", "src/engine/save_system.py", "SaveSystem class with checksum-verified JSON persistence"),
    assistant_entry(ts(53), "Save system complete. Player progress is stored and validated with a SHA-256 checksum on load."),

    heartbeat_entry(ts(60)),

    user_entry(ts(65), "The enemy AI keeps getting stuck on corners. Debug it."),
    assistant_entry(ts(66), "Pathfinding uses A* but doesn't handle diagonal corner-cutting. I'll add corner clearance checks."),
    tool_entry(ts(67), "Edit", "src/engine/ai.py", "Added corner clearance radius to A* pathfinding"),
    assistant_entry(ts(68), "Enemies now navigate around corners cleanly with a configurable clearance radius."),

    user_entry(ts(75), "Can we add a speedrun timer to the HUD?"),
    assistant_entry(ts(76), "I'll add a centisecond-precision timer that starts on first input and stops at level exit trigger."),
    tool_entry(ts(77), "Edit", "src/ui/hud.py", "SpeedrunTimer widget added with centisecond precision"),
    assistant_entry(ts(78), "Speedrun timer is live on the HUD — starts on first player input, stops at the exit trigger."),

    heartbeat_entry(ts(80)),
    heartbeat_entry(ts(81)),

    user_entry(ts(85), "The procedural map generator produces too many dead ends. Tune it."),
    assistant_entry(ts(86), "I'll increase the loop-back probability in the corridor generator to reduce dead ends."),
    tool_entry(ts(87), "Edit", "src/engine/procgen.py", "Increased loop_back_prob from 0.05 to 0.25"),
    assistant_entry(ts(88), "Generator tuned: dead ends reduced by ~60% with loop_back_prob=0.25."),

    user_entry(ts(95), "We need localization support. Set up i18n for the UI text."),
    assistant_entry(ts(96), "I'll create a locale JSON system with a fallback to English for missing keys."),
    tool_entry(ts(97), "Write", "src/ui/i18n.py", "Locale loader with English fallback"),
    tool_entry(ts(98), "Write", "assets/locale/en.json", '{"start_game": "Start Game", "quit": "Quit"}'),
    assistant_entry(ts(99), "i18n system set up. UI strings now load from assets/locale/{lang}.json with English fallback."),
]

session2_base = datetime(2024, 10, 25, 14, 0, 0)
def ts2(delta_minutes):
    return (session2_base + timedelta(minutes=delta_minutes)).isoformat() + "Z"

session2_lines = [
    user_entry(ts2(0), "The game's music system needs crossfading between tracks."),
    assistant_entry(ts2(1), "I'll implement a linear crossfade with configurable duration using the mixer's volume ramp."),
    tool_entry(ts2(2), "Write", "src/audio/music_manager.py", "MusicManager with crossfade(duration_ms) method"),
    assistant_entry(ts2(3), "Crossfading implemented. Transition duration is configurable per-track-change event."),

    heartbeat_entry(ts2(10)),

    user_entry(ts2(15), "Implement a replay system that records and plays back player inputs."),
    assistant_entry(ts2(16), "I'll record timestamped input events to a compact binary format, then replay them deterministically."),
    tool_entry(ts2(17), "Write", "src/engine/replay.py", "InputRecorder and ReplayPlayer classes with binary serialization"),
    assistant_entry(ts2(18), "Replay system ready. Records inputs as (timestamp, key, state) tuples in a binary file."),

    user_entry(ts2(25), "The shader for the water effect is too slow on mobile targets."),
    assistant_entry(ts2(26), "The wave function uses sin() per-pixel. I'll approximate it with a lookup table."),
    tool_entry(ts2(27), "Edit", "assets/shaders/water.glsl", "Replaced sin() with LUT-based approximation"),
    assistant_entry(ts2(28), "Water shader is now 3x faster on mobile by using a 256-entry sin lookup table."),

    heartbeat_entry(ts2(30)),
    heartbeat_entry(ts2(31)),
    json.dumps({"type": "status_check", "timestamp": ts2(32), "content": "", "result": "idle"}),

    user_entry(ts2(40), "We discussed and decided to use entity-component-system (ECS) architecture for the next major refactor."),
    assistant_entry(ts2(41), "Agreed. ECS will decouple game logic from entity identity, making systems independently testable."),

    user_entry(ts2(50), "The particle system is spawning too many particles and causing frame drops."),
    assistant_entry(ts2(51), "Root cause: no particle budget cap. I'll add a global pool with a max-particle limit."),
    tool_entry(ts2(52), "Edit", "src/engine/particles.py", "Added ParticlePool with configurable max_particles cap"),
    assistant_entry(ts2(53), "Particle system now capped at configurable max_particles (default 1000). Frame rate stable."),

    user_entry(ts2(60), "Add network multiplayer lobby support."),
    assistant_entry(ts2(61), "I'll implement a lobby system using UDP broadcast for LAN discovery and a simple state machine for lobby phases."),
    tool_entry(ts2(62), "Write", "src/network/lobby.py", "LobbyManager with UDP broadcast discovery and state machine"),
    assistant_entry(ts2(63), "LAN lobby complete. Players can discover and join via UDP broadcast; lobby transitions through WAITING, READY, and IN_GAME states."),

    heartbeat_entry(ts2(70)),

    user_entry(ts2(75), "The dialog system needs branching support for NPC conversations."),
    assistant_entry(ts2(76), "I'll use a directed graph with condition-gated edges stored in JSON dialog files."),
    tool_entry(ts2(77), "Write", "src/engine/dialog.py", "DialogGraph with condition-gated branching from JSON"),
    assistant_entry(ts2(78), "Branching dialog system done. NPC conversations are defined as JSON graphs with condition gates."),

    user_entry(ts2(85), "We need an in-game debug console for developers."),
    assistant_entry(ts2(86), "I'll build a togglable overlay console that accepts commands and shows output, bound to backtick."),
    tool_entry(ts2(87), "Write", "src/ui/debug_console.py", "DebugConsole overlay with command registration and backtick toggle"),
    assistant_entry(ts2(88), "Debug console is live. Press ` to toggle, register commands with @console.command decorator."),
]

logs_dir = Path.home() / ".claude" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

log1_path = logs_dir / "session_2024-11-01.jsonl"
log2_path = logs_dir / "session_2024-10-25.jsonl"

log1_path.write_text("\n".join(json.dumps(json.loads(line)) for line in session1_lines) + "\n")
log2_path.write_text("\n".join(json.dumps(json.loads(line)) for line in session2_lines) + "\n")

# ── Write the daydream.py conductor script ────────────────────────────────────
daydream_py = r'''#!/usr/bin/env python3
"""
daydream.py — Conductor script for the Daydreamer skill.
Handles all mechanical work: cycle counting, random selection,
memory parsing, state tracking, and file I/O.
"""

import argparse
import json
import os
import random
import re
import sys
import shutil
from datetime import datetime, date
from pathlib import Path

# ── Workspace resolution ──────────────────────────────────────────────────────
WORKSPACE = Path(os.environ.get("DAYDREAM_WORKSPACE", os.getcwd()))
CONFIG_FILE = WORKSPACE / "daydreamer-config.json"
DREAMS_FILE = WORKSPACE / "Daydreams.MD"
LOG_FILE    = WORKSPACE / "Daydreamlog.MD"
IDEAS_DIR   = WORKSPACE / "ideas"
SESSION_DIR = WORKSPACE / ".daydream-session"

DEFAULT_CONFIG = {
    "frequency": "once_daily",
    "cycles_per_session": 10,
    "default_daydream_type": "full",
    "last_daydream_date": None,
    "last_memory_write_date": None,
    "session_count": 0
}

MODES = [1, 2, 3, 4]
MODE_NAMES = {
    1: "Semantic Association",
    2: "Hypothetical Exploration",
    3: "Web Search Excursion",
    4: "Analytical Question",
}


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # Fill missing keys with defaults
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def load_memories():
    """Return list of (index, text) tuples from Daydreams.MD."""
    if not DREAMS_FILE.exists():
        return []
    memories = []
    for line in DREAMS_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(\d+)\.\s+(.+)$', line)
        if m:
            memories.append((int(m.group(1)), m.group(2)))
    return memories


def next_memory_number():
    memories = load_memories()
    if not memories:
        return 1
    return max(idx for idx, _ in memories) + 1


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_init():
    """Create Daydreams.MD, Daydreamlog.MD, ideas/, daydreamer-config.json."""
    DREAMS_FILE.touch()
    LOG_FILE.touch()
    IDEAS_DIR.mkdir(exist_ok=True)
    save_config(DEFAULT_CONFIG)
    print(json.dumps({"status": "ok", "message": "Daydreamer initialized.", "files": [
        str(DREAMS_FILE), str(LOG_FILE), str(IDEAS_DIR), str(CONFIG_FILE)
    ]}))


def cmd_status():
    cfg = load_config()
    today = date.today().isoformat()
    freq = cfg.get("frequency", "once_daily")
    last = cfg.get("last_daydream_date")

    if freq == "manual":
        due = False
    elif freq == "once_daily":
        due = (last != today)
    elif freq == "twice_daily":
        # Simple heuristic: due if last wasn't today or today's count < 2
        due = (last != today)
    else:
        due = True  # Simplified; real impl would check timestamps

    memories = load_memories()
    print(json.dumps({
        "status": "ok",
        "daydream_due": due,
        "message": "Daydream is DUE" if due else "Daydream not due yet",
        "frequency": freq,
        "cycles_per_session": cfg["cycles_per_session"],
        "default_type": cfg["default_daydream_type"],
        "memory_count": len(memories),
        "last_daydream_date": last,
        "session_count": cfg["session_count"],
    }))


def cmd_add_memory(text):
    n = next_memory_number()
    today = date.today().isoformat()
    entry = f"{n}. {text.strip()}"
    with open(DREAMS_FILE, "a") as f:
        f.write(entry + "\n")
    cfg = load_config()
    cfg["last_memory_write_date"] = today
    save_config(cfg)
    print(json.dumps({"status": "ok", "index": n, "entry": entry}))


def cmd_seed_memories():
    """Scan Claude Code session logs and report what's available."""
    log_dir = Path.home() / ".claude" / "logs"
    if not log_dir.exists():
        print(json.dumps({"status": "ok", "log_files": [], "memories_needed": 50}))
        return

    log_files = sorted(log_dir.glob("*.jsonl"), reverse=True)  # most recent first
    memories = load_memories()
    needed = max(0, 50 - len(memories))

    print(json.dumps({
        "status": "ok",
        "log_files": [str(f) for f in log_files],
        "memories_needed": needed,
        "current_memory_count": len(memories),
        "instruction": "Read each log file and extract meaningful events. Use add-memory for each one. Skip heartbeats, empty status checks, and trivial exchanges."
    }))


def cmd_start(cycles, daydream_type, forced):
    memories = load_memories()
    if len(memories) < 2:
        print(json.dumps({"status": "error", "message": "Not enough memories. Need at least 2 entries in Daydreams.MD."}))
        sys.exit(1)

    SESSION_DIR.mkdir(exist_ok=True)

    # Pick a random seed memory
    seed_idx, seed_text = random.choice(memories)

    # Roll mode for cycle 1
    mode = random.choice(MODES)

    # Build initial state
    state = {
        "cycles_total": cycles,
        "cycles_done": 0,
        "daydream_type": daydream_type,
        "forced": forced,
        "seed_memory_index": seed_idx,
        "seed_memory_text": seed_text,
        "visited_memory_indices": [seed_idx],
        "accumulated_context": f"Seed memory #{seed_idx}: {seed_text}",
        "cycle_log": [],
        "all_memories": memories,
    }
    _save_state(state)

    # Write prompt for cycle 1
    prompt = _build_cycle_prompt(state, 1, mode)
    _write_prompt_file(1, prompt)

    print(json.dumps({
        "status": "ok",
        "session_started": True,
        "cycles": cycles,
        "daydream_type": daydream_type,
        "forced": forced,
        "seed_memory_index": seed_idx,
        "seed_memory_text": seed_text,
        "cycle_1_mode": mode,
        "cycle_1_mode_name": MODE_NAMES[mode],
        "prompt_file": str(SESSION_DIR / "prompt_cycle_001.json"),
    }))


def cmd_next_cycle():
    state = _load_state()
    cycle_num = state["cycles_done"] + 1

    # Read the agent's response for this cycle
    resp_file = SESSION_DIR / f"response_cycle_{cycle_num:03d}.json"
    if not resp_file.exists():
        print(json.dumps({"status": "error", "message": f"Missing response file: {resp_file}"}))
        sys.exit(1)

    with open(resp_file) as f:
        response = json.load(f)

    # Fold response into accumulated context
    resp_text = response.get("text", "")
    log_entry = response.get("log_entry", f"[Cycle {cycle_num}] (no log)")
    selected_idx = response.get("selected_memory_index")

    state["accumulated_context"] += f"\n\n[Cycle {cycle_num}] {resp_text}"
    state["cycle_log"].append(log_entry)
    if selected_idx is not None:
        state["visited_memory_indices"].append(selected_idx)
    state["cycles_done"] += 1
    _save_state(state)

    # Check if we're done with cycles
    if state["cycles_done"] >= state["cycles_total"]:
        # Write synthesis prompt
        synthesis_prompt = _build_synthesis_prompt(state)
        sp = SESSION_DIR / "prompt_synthesis.json"
        with open(sp, "w") as f:
            json.dump(synthesis_prompt, f, indent=2)
        print(json.dumps({
            "status": "ok",
            "cycles_complete": True,
            "synthesis_prompt_file": str(sp),
            "message": "All cycles complete. Read prompt_synthesis.json and write response_synthesis.json."
        }))
    else:
        # Roll next mode and write next prompt
        next_cycle = state["cycles_done"] + 1
        mode = random.choice(MODES)
        prompt = _build_cycle_prompt(state, next_cycle, mode)
        _write_prompt_file(next_cycle, prompt)
        print(json.dumps({
            "status": "ok",
            "cycles_complete": False,
            "next_cycle": next_cycle,
            "next_mode": mode,
            "next_mode_name": MODE_NAMES[mode],
            "prompt_file": str(SESSION_DIR / f"prompt_cycle_{next_cycle:03d}.json"),
        }))


def cmd_finalize(forced):
    state = _load_state()

    # Read synthesis response
    synth_file = SESSION_DIR / "response_synthesis.json"
    if not synth_file.exists():
        print(json.dumps({"status": "error", "message": "Missing response_synthesis.json"}))
        sys.exit(1)

    with open(synth_file) as f:
        synthesis = json.load(f)

    synth_text = synthesis.get("synthesis", "")
    synth_status = synthesis.get("status", "Complete")

    # Write Daydreamlog.MD
    cfg = load_config()
    cfg["session_count"] = cfg.get("session_count", 0) + 1
    session_num = cfg["session_count"]
    today = date.today().isoformat()

    if not forced:
        cfg["last_daydream_date"] = today
    save_config(cfg)

    log_entry = f"""
## Session {session_num} — {today}
**Type:** {state['daydream_type']} | **Cycles:** {state['cycles_total']} | **Forced:** {state['forced']}
**Seed Memory #{state['seed_memory_index']}:** {state['seed_memory_text']}

### Cycle Log
""" + "\n".join(f"- {e}" for e in state["cycle_log"]) + f"""

### Synthesis
{synth_text}

**Status:** {synth_status}
---
"""
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    # Write idea file
    IDEAS_DIR.mkdir(exist_ok=True)
    existing = sorted(IDEAS_DIR.glob("*.md"))
    next_num = len(existing) + 1

    # Generate slug from first 6 words of synthesis
    words = re.sub(r'[^a-z0-9 ]', '', synth_text.lower()).split()[:6]
    slug = "-".join(words) if words else "daydream"
    idea_filename = f"{next_num:03d}-{slug}.md"
    idea_path = IDEAS_DIR / idea_filename

    idea_content = f"""# Daydream Session {session_num}
**Date:** {today}
**Type:** {state['daydream_type']}
**Cycles:** {state['cycles_total']}

## Synthesis
{synth_text}

**Status:** {synth_status}

## Memory Trail
- Seed: Memory #{state['seed_memory_index']} — {state['seed_memory_text']}
""" + "\n".join(f"- {e}" for e in state["cycle_log"]) + "\n"

    idea_path.write_text(idea_content)

    # Clean up session directory
    shutil.rmtree(SESSION_DIR, ignore_errors=True)

    print(json.dumps({
        "status": "ok",
        "session_number": session_num,
        "idea_file": str(idea_path),
        "log_file": str(LOG_FILE),
        "synthesis_status": synth_status,
        "forced": forced,
    }))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _save_state(state):
    with open(SESSION_DIR / "state.json", "w") as f:
        json.dump(state, f, indent=2)


def _load_state():
    sf = SESSION_DIR / "state.json"
    if not sf.exists():
        print(json.dumps({"status": "error", "message": "No active session. Run start first."}))
        sys.exit(1)
    with open(sf) as f:
        return json.load(f)


def _build_cycle_prompt(state, cycle_num, mode):
    target_rank = random.randint(1, 5) if mode == 3 else None
    prompt = {
        "cycle": cycle_num,
        "cycles_total": state["cycles_total"],
        "mode": mode,
        "mode_name": MODE_NAMES[mode],
        "accumulated_context": state["accumulated_context"],
        "visited_memory_indices": state["visited_memory_indices"],
        "all_memories": state["all_memories"],
        "response_file": str(SESSION_DIR / f"response_cycle_{cycle_num:03d}.json"),
        "daydream_type": state["daydream_type"],
    }
    if target_rank is not None:
        prompt["target_result_rank"] = target_rank
    return prompt


def _write_prompt_file(cycle_num, prompt):
    p = SESSION_DIR / f"prompt_cycle_{cycle_num:03d}.json"
    with open(p, "w") as f:
        json.dump(prompt, f, indent=2)


def _build_synthesis_prompt(state):
    type_instructions = {
        "full": "Output is unconstrained — report whatever emerged honestly. It could be an idea, a question, an observation, a warning, or an analogy.",
        "idea": "Focus on producing a specific, actionable idea — something that could be built, implemented, or pursued by this game studio.",
    }
    return {
        "phase": "synthesis",
        "accumulated_context": state["accumulated_context"],
        "cycle_log": state["cycle_log"],
        "daydream_type": state["daydream_type"],
        "synthesis_instructions": type_instructions.get(state["daydream_type"], type_instructions["full"]),
        "response_file": str(SESSION_DIR / "response_synthesis.json"),
        "all_memories": state["all_memories"],
        "visited_memory_indices": state["visited_memory_indices"],
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="daydream.py")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("seed-memories")

    p_add = sub.add_parser("add-memory")
    p_add.add_argument("text")

    p_start = sub.add_parser("start")
    p_start.add_argument("--cycles", type=int, default=10)
    p_start.add_argument("--type", dest="daydream_type", default="full", choices=["full", "idea"])
    p_start.add_argument("--forced", action="store_true")

    sub.add_parser("next-cycle")

    p_fin = sub.add_parser("finalize")
    p_fin.add_argument("--forced", action="store_true")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "status":
        cmd_status()
    elif args.command == "add-memory":
        cmd_add_memory(args.text)
    elif args.command == "seed-memories":
        cmd_seed_memories()
    elif args.command == "start":
        cmd_start(args.cycles, args.daydream_type, args.forced)
    elif args.command == "next-cycle":
        cmd_next_cycle()
    elif args.command == "finalize":
        cmd_finalize(args.forced)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(SKILL_DIR / "daydream.py").write_text(daydream_py)

# ── Write SKILL.md into skill dir ─────────────────────────────────────────────
skill_md_content = """---
name: daydreamer
description: Use this skill when the user says \"daydream\", \"start daydreaming\", \"force a daydream\", \"run daydream cycles\", or when a scheduled daydream is triggered.
version: 2.2.0
tools: Read, Write, Edit, Bash, WebSearch
env:
  DAYDREAM_WORKSPACE:
    description: Path to the workspace root where Daydreams.MD and related files are stored. Defaults to the current working directory if not set.
    required: false
---
See full documentation in SKILL.md at this path.
"""
(SKILL_DIR / "SKILL.md").write_text(skill_md_content)

print("Workspace generated successfully.")
print(f"  Skill dir:    {SKILL_DIR}")
print(f"  Log files:    {log1_path}, {log2_path}")
print(f"  No daydreamer-config.json → first-install required")