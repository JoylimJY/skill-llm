from pathlib import Path
import json

base = Path('.')
(base / 'memory' / 'rpg' / 'neon_ash').mkdir(parents=True, exist_ok=True)

world = {
    "campaign_name": "neon_ash",
    "system": "d20",
    "setting": "Cyberpunk",
    "tone": "Gritty",
    "location": "Night Market District",
    "time": "midnight",
    "weather": "acid rain",
    "flags": {
        "marker_world": "NEON_MARKER_WORLD"
    }
}
character = {
    "name": "Mara Vex",
    "archetype": "Street Samurai",
    "hp": 24,
    "inventory": ["mono-knife", "smartlink visor"],
    "status": ["alert"],
    "markers": {
        "marker_char": "NEON_MARKER_CHAR"
    }
}
npcs = {
    "boss": {
        "name": "Sable Kade",
        "agenda": "find the stolen chip",
        "marker_npc": "NEON_MARKER_NPC"
    }
}
journal = "[NEON_MARKER_JOURNAL] Campaign initialized for Mara Vex in Neon Ash.\n"

(base / 'memory' / 'rpg' / 'neon_ash' / 'world.json').write_text(json.dumps(world, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_ash' / 'character.json').write_text(json.dumps(character, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_ash' / 'npcs.json').write_text(json.dumps(npcs, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_ash' / 'journal.md').write_text(journal, encoding='utf-8')
