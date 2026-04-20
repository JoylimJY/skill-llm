from pathlib import Path
import json

base = Path('.').resolve()
(base / 'memory' / 'rpg' / 'neon_drift').mkdir(parents=True, exist_ok=True)

world = {
    "campaign_name": "neon_drift",
    "system": "d20",
    "setting": "Cyberpunk",
    "tone": "Gritty",
    "time": "Night",
    "location": "Neo-Tokyo Slums",
    "weather": "Rain",
    "flags": {
        "session_zero_started": True,
        "marker": "WORLD_MARKER_42"
    },
    "clocks": []
}
character = {
    "name": "Mira",
    "archetype": "Hacker",
    "hp": 10,
    "status": [],
    "inventory": ["Cheap Datajack", "MARKER_ITEM_ALPHA"],
    "stats": {
        "cool": 2,
        "int": 3,
        "tech": 4,
        "edge": 1
    }
}
npcs = {
    "npcs": [],
    "marker": "NPC_MARKER_7"
}

(base / 'memory' / 'rpg' / 'neon_drift' / 'world.json').write_text(json.dumps(world, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_drift' / 'character.json').write_text(json.dumps(character, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_drift' / 'npcs.json').write_text(json.dumps(npcs, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_drift' / 'journal.md').write_text('# Session Zero\nSession Zero has begun for neon_drift. MARKER_JOURNAL_99\n', encoding='utf-8')
