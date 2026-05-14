import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "assets",
    "references",
    "logs",
    "logs/archive",
    "docs/lore",
    "docs/design",
    "tmp/cache",
    "tmp/backup",
    "tests",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "docs/lore/earth_history.md": "# Earth\nMostly harmless. Third planet from a small, unregarded yellow sun.",
    "docs/lore/ford_prefect.md": "# Ford Prefect\nResearcher for the Guide. Spent 15 years stuck on Earth.",
    "docs/design/game_design.md": "# Game Design Notes\n- Puzzles must be fair but slightly unfair\n- British humor required\n- Improbability drives surreal events",
    "docs/design/locations.md": "# Location Index\n- Earth\n- Vogon Constructor Ship\n- Heart of Gold\n- Magrathea\n- Milliways",
    "logs/session_001.log": "[2024-01-01 10:00] Session started. Player at Earth.",
    "logs/archive/old_save_backup.json": '{"note": "old backup, do not use", "location": "Earth", "inventory": []}',
    "tmp/cache/prefetch.dat": "BINARY_CACHE_DATA_42_PREFETCH",
    "tmp/backup/hitchhikers_save.json.bak": '{"location": "Earth", "inventory": [], "stats": {}, "flags": {}, "history": []}',
    "tests/test_game_manager.py": textwrap.dedent("""\
        # Unit tests - not relevant to game session
        def test_placeholder():
            assert True
    """),
    "docs/lore/vogons.txt": "Vogons are bureaucratic aliens. Do not let them read you poetry.",
    "tmp/cache/render_cache.tmp": "STALE_RENDER_CACHE",
    "logs/error.log": "[ERROR] 2024-01-01: Improbability overflow (non-critical)",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── assets/GUIDE.md (initial, minimal) ──────────────────────────────────────
guide_initial = textwrap.dedent("""\
    # The Hitchhiker's Guide to the Galaxy

    ## Entry: Earth
    A small, blue-green planet orbiting a small, unregarded yellow sun in the
    unfashionable western spiral arm of the Galaxy. Mostly harmless.
    Population: once several billion, now effectively zero.
    See also: Demolition, Vogon Constructor Fleet.
""")
(workspace / "assets" / "GUIDE.md").write_text(guide_initial)

# ── initial game save ────────────────────────────────────────────────────────
initial_save = {
    "location": "Earth",
    "inventory": [],
    "stats": {
        "wit": 5,
        "panic": 3,
        "babel_fish": 0
    },
    "flags": {
        "earth_demolished": False,
        "ford_found": False,
        "has_towel": False
    },
    "improbability": 0,
    "history": [
        "You wake up in your house in Cottington. Ford Prefect is at the door, urging you to leave immediately."
    ]
}
(workspace / "assets" / "hitchhikers_save.json").write_text(
    json.dumps(initial_save, indent=2)
)

# ── references/mechanics.md ──────────────────────────────────────────────────
mechanics_md = textwrap.dedent("""\
    # Game Mechanics Reference

    ## Game State Fields
    The save file (`assets/hitchhikers_save.json`) contains:
    - `location` (str): Current player location.
    - `inventory` (list[str]): List of item names the player carries.
    - `stats` (dict): Numeric attributes (wit, panic, babel_fish, etc.).
    - `flags` (dict): Boolean flags tracking story events.
    - `improbability` (int): The current Improbability Level (0–100).
    - `history` (list[str]): Chronological log of significant events.

    ## Atomic CLI Commands
    All state changes MUST be performed via `game_manager.py`. Direct edits to
    the JSON file are illegal and will result in state corruption.

    | Command | Effect |
    |---|---|
    | `load` | Print current state to stdout |
    | `add_item "<name>"` | Append item to inventory |
    | `remove_item "<name>"` | Remove item from inventory |
    | `set_location "<loc>"` | Set current location |
    | `set_stat <stat> <value>` | Set a numeric stat |
    | `set_flag <flag> <value>` | Set a boolean flag (true/false) |
    | `set_improbability <value>` | Set improbability level (0-100) |
    | `add_history "<entry>"` | Append entry to history log |
    | `roll_a_dice` | Roll a 6-sided die; returns 1-6 |
    | `the_ultimate_answer` | Returns 42 (for special puzzle checks) |

    ## Improbability Events
    When `improbability` >= 42, surreal events may occur at the GM's discretion.
    The event trigger is: `roll_a_dice`. If the result is >= 4, an improbability
    event fires and must be narrated and logged via `add_history`.

    ## Death & Revival
    If `panic` stat reaches 10, the player dies. Death must be recorded in
    history. The game can be continued by resetting panic to 0 and choosing
    a revival location (canonically: "Total Perspective Vortex Waiting Room").

    ## Towel Rule
    Carrying a "Towel" grants +1 to all stat checks. Its presence must be
    tracked by both the inventory list AND the flag `has_towel: true`.

    ## Vogon Poetry Puzzle
    1. Player is captured aboard a Vogon ship.
    2. Poetry reading begins. Each stanza increases `panic` by 2.
    3. Player must roll_a_dice: result >= 4 means they endure it;
       result < 4 means panic increases by an additional 1.
    4. To escape, `babel_fish` stat must be >= 1.
    5. On escape, set flag `vogon_poetry_survived: true`.

    ## Jynnan Tonnyx
    The Jynnan Tonnyx is the best drink in existence. Consuming it sets
    `wit` += 2 and `panic` -= 1 (floor 0). It is obtained aboard Vogon or
    Sirian vessels. Must be tracked as inventory item "Jynnan Tonnyx".

    ## Babel Fish
    Obtained from the Babel Fish Dispenser puzzle. Increases `babel_fish`
    stat to 1. Required for understanding alien speech (Vogon poetry puzzle).

    ## Guide Entries
    When a new entity, location, or item is encountered for the first time,
    a humorous Guide entry MUST be written and appended to `assets/GUIDE.md`.
    Format:
    ```
    ## Entry: <Name>
    <2-5 sentences of dry, British, absurdist humor describing the entity.>
    ```

    ## History Entry Format
    Each history entry should be a single sentence in second-person past tense,
    e.g. "You were rescued from Earth moments before its demolition."
    Entries are appended chronologically.

    ## Sequence: Earth Demolition → Vogon Ship Rescue
    1. Set flag `earth_demolished: true`
    2. Set flag `ford_found: true`
    3. Set location to "Vogon Constructor Ship - Hold"
    4. Roll dice to determine initial panic surge:
       - dice >= 4: set_stat panic 5
       - dice < 4: set_stat panic 7
    5. Add history entry for rescue.
    6. Raise improbability to at least 42 (set_improbability 42).
    7. If Towel is in inventory, set_flag has_towel true.
    8. Write Guide entry for "Vogon Constructor Ship" to assets/GUIDE.md.
    9. Add "Jynnan Tonnyx" to inventory (found in hold).
    10. Write Guide entry for "Jynnan Tonnyx" to assets/GUIDE.md.
""")
(workspace / "references" / "mechanics.md").write_text(mechanics_md)

# ── scripts/game_manager.py ──────────────────────────────────────────────────
game_manager_py = textwrap.dedent('''\
    #!/usr/bin/env python3
    """
    game_manager.py  –  Atomic state manager for the Hitchhiker\'s Guide adventure.
    Usage: python scripts/game_manager.py <command> [args...]
    """
    import sys, json, random
    from pathlib import Path

    SAVE_PATH = Path("assets/hitchhikers_save.json")

    def load_state():
        if not SAVE_PATH.exists():
            return {
                "location": "Earth",
                "inventory": [],
                "stats": {"wit": 5, "panic": 3, "babel_fish": 0},
                "flags": {"earth_demolished": False, "ford_found": False, "has_towel": False},
                "improbability": 0,
                "history": []
            }
        return json.loads(SAVE_PATH.read_text())

    def save_state(state):
        SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SAVE_PATH.write_text(json.dumps(state, indent=2))

    def cmd_load(state, args):
        print(json.dumps(state, indent=2))

    def cmd_add_item(state, args):
        item = " ".join(args)
        if item not in state["inventory"]:
            state["inventory"].append(item)
            print(f"Added to inventory: {item}")
        else:
            print(f"Already in inventory: {item}")
        save_state(state)

    def cmd_remove_item(state, args):
        item = " ".join(args)
        if item in state["inventory"]:
            state["inventory"].remove(item)
            print(f"Removed from inventory: {item}")
        else:
            print(f"Not in inventory: {item}")
        save_state(state)

    def cmd_set_location(state, args):
        loc = " ".join(args)
        state["location"] = loc
        print(f"Location set to: {loc}")
        save_state(state)

    def cmd_set_stat(state, args):
        if len(args) < 2:
            print("Usage: set_stat <stat> <value>"); return
        stat, value = args[0], int(args[1])
        state["stats"][stat] = value
        print(f"Stat {stat} set to {value}")
        save_state(state)

    def cmd_set_flag(state, args):
        if len(args) < 2:
            print("Usage: set_flag <flag> <value>"); return
        flag, raw = args[0], args[1].lower()
        value = raw in ("true", "1", "yes")
        state["flags"][flag] = value
        print(f"Flag {flag} set to {value}")
        save_state(state)

    def cmd_set_improbability(state, args):
        if len(args) < 1:
            print("Usage: set_improbability <value>"); return
        val = int(args[0])
        state["improbability"] = val
        print(f"Improbability set to {val}")
        save_state(state)

    def cmd_add_history(state, args):
        entry = " ".join(args)
        state["history"].append(entry)
        print(f"History entry added: {entry}")
        save_state(state)

    def cmd_roll_a_dice(state, args):
        result = random.randint(1, 6)
        print(f"Dice roll: {result}")
        return result

    def cmd_the_ultimate_answer(state, args):
        print("The Ultimate Answer to Life, the Universe, and Everything: 42")
        return 42

    COMMANDS = {
        "load": cmd_load,
        "add_item": cmd_add_item,
        "remove_item": cmd_remove_item,
        "set_location": cmd_set_location,
        "set_stat": cmd_set_stat,
        "set_flag": cmd_set_flag,
        "set_improbability": cmd_set_improbability,
        "add_history": cmd_add_history,
        "roll_a_dice": cmd_roll_a_dice,
        "the_ultimate_answer": cmd_the_ultimate_answer,
    }

    if __name__ == "__main__":
        if len(sys.argv) < 2:
            print("Usage: python scripts/game_manager.py <command> [args...]")
            sys.exit(1)
        cmd = sys.argv[1]
        args = sys.argv[2:]
        state = load_state()
        if cmd not in COMMANDS:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
        COMMANDS[cmd](state, args)
''')
(workspace / "scripts" / "game_manager.py").write_text(game_manager_py)

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")