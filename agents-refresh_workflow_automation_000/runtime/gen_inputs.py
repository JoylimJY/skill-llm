import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create distractor directory structure ---
dirs = [
    "/workspace/memory",
    "/workspace/assets/sprites",
    "/workspace/assets/audio",
    "/workspace/src/engine",
    "/workspace/src/ui",
    "/workspace/docs/design",
    "/workspace/docs/meetings",
    "/workspace/tools",
    "/workspace/build",
    "/workspace/tests",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "/workspace/src/engine/physics.py": "# Physics engine placeholder\nclass PhysicsWorld:\n    pass\n",
    "/workspace/src/engine/renderer.py": "# Renderer module\nclass Renderer:\n    def draw(self): pass\n",
    "/workspace/src/ui/hud.py": "# HUD elements\nclass HUD:\n    def update(self): pass\n",
    "/workspace/assets/sprites/hero.png.meta": "sprite_id: hero_001\nframes: 8\n",
    "/workspace/assets/audio/bgm.ogg.meta": "track: main_theme\nloop: true\n",
    "/workspace/docs/design/level_design.txt": "Level 1: Tutorial cave\nLevel 2: Forest\nLevel 3: Castle\n",
    "/workspace/docs/meetings/kickoff_notes.txt": "Kickoff: Decided to use tile-based engine.\nTeam size: 3.\n",
    "/workspace/tools/asset_packer.sh": "#!/bin/bash\necho 'Packing assets...'\n",
    "/workspace/build/version.txt": "0.3.1-alpha\n",
    "/workspace/tests/test_physics.py": "def test_gravity(): assert True\n",
    "/workspace/docs/design/character_specs.md": "# Character Specs\n- Hero: 32x32 px\n- Speed: 5 units/s\n",
    "/workspace/src/ui/menu.py": "# Main menu\ndef show_menu(): pass\n",
}
for path, content in distractors.items():
    Path(path).write_text(content)

# --- Create messy raw daily logs (the agent must distill these) ---

# memory/2024-06-10.md — messy session log
Path("/workspace/memory/2024-06-10.md").write_text("""
# Session Log June 10

talked a lot today. Started implementing the jump mechanic. It works but feels floaty.
Tried adjusting gravity multiplier to 1.8x - felt better but broke wall-jump.

TODO: fix wall-jump after gravity change
also need to revisit: double-jump cooldown is too short, players spam it

Brainstorm: what if enemies could also double jump? Could be interesting for mid-tier enemies.

Decided: we are NOT doing procedural dungeons for v1.0. Too risky, scope creep. Fixed hand-crafted levels only.

confusion note: spent 2hrs chasing a bug that was just a wrong variable name (playerSpeed vs player_speed). 
Lesson: enforce naming conventions strictly from now on.

Random idea: add a "nightmare mode" with inverted controls as a hidden easter egg.
""")

# memory/2024-06-11.md — another messy log
Path("/workspace/memory/2024-06-11.md").write_text("""
# Session Log June 11

Fixed wall-jump! The issue was gravity was applied before collision resolution.
Now wall-jump feels great.

DECISION: Save system will use JSON files, not SQLite. Simpler and human-readable.
DECISION: Target platform is PC + Linux only for v1.0. Console ports deferred to v2.

Still todo: implement save/load UI screens
Still todo: add sound effects for jump and land actions
Still todo: write unit tests for the save system

Lesson learned: Don't start implementing features without a design doc. 
The double-jump saga wasted 3 days because spec was unclear.

Idea seed: Procedural music that adapts to player health? Could use layered stems.
Also: maybe a speedrun timer mode as a separate game mode?
""")

# memory/2024-06-12.md — most recent messy log
Path("/workspace/memory/2024-06-12.md").write_text("""
# Session Log June 12

Save/load UI is 70% done. Basic save works. Load has a bug with corrupted save files - crashes.
Need to add error handling for corrupted saves.

Completed: Player animation state machine (idle/run/jump/fall all connected)
Completed: Basic enemy AI patrol pattern

Confirmed: Using MIT license for the project. Added LICENSE file.

Lesson: Always test save/load with intentionally corrupted files in CI. Caught this bug late.

Brainstorm: What about a level editor for community content? Long term vision.
Note: Reached out to a composer friend about the adaptive music idea from yesterday.
""")

# --- Create a bare/empty AGENTS.md, SOUL.md, IDENTITY.md (agent should read these) ---
Path("/workspace/AGENTS.md").write_text("""# AGENTS.md
## Role
You are the development assistant for the indie game project "NightCrawler".
You help track decisions, manage todos, and maintain project continuity across sessions.

## Prime Directive
Keep the team focused. Distill signal from noise. Never lose track of critical blockers.
""")

Path("/workspace/SOUL.md").write_text("""# SOUL.md
## Core Values
- Clarity over complexity.
- Ship incrementally, validate often.
- The player experience is the north star.

## Communication Style
Direct, concise, no fluff. Use bullet points. Flag blockers loudly.
""")

Path("/workspace/IDENTITY.md").write_text("""# IDENTITY.md
## Name: NightCrawler Dev Assistant
## Version: 1.0
## Personality
Methodical, encouraging, pragmatic. Celebrates small wins. Ruthlessly prioritizes.
## Immutable Rules
- Never suggest adding scope without removing something else.
- Always surface blockers before new features.
""")

# --- Create a messy, incomplete HEARTBEAT.md (needs proper refresh task added) ---
Path("/workspace/HEARTBEAT.md").write_text("""# HEARTBEAT.md
## Scheduled Tasks

- [ ] Daily standup summary: check build/version.txt and report status (every morning 8AM)
- [ ] Asset audit: scan assets/ folder for orphaned files (weekly, Monday)

## Notes
Add more tasks here as needed.
""")

# --- MEMORY.md does NOT exist yet (agent must create it) ---
# (intentionally absent)

print("Workspace generated successfully.")