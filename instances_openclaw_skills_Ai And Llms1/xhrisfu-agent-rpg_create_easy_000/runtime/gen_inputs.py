from pathlib import Path
import json

base = Path('.')
marker = 'MARKER_NEON_DREAM_001'

(base / 'memory' / 'rpg' / 'neon_dream').mkdir(parents=True, exist_ok=True)

world = {
    'campaign_name': 'neon_dream',
    'system': 'd20',
    'setting': 'Cyberpunk',
    'tone': 'Gritty',
    'session_zero_started': False,
    'marker': marker
}
character = {
    'name': 'Zris',
    'archetype': 'Hacker',
    'hp': 10,
    'inventory': ['data shard'],
    'marker': marker
}

(base / 'memory' / 'rpg' / 'neon_dream' / 'world.json').write_text(json.dumps(world, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_dream' / 'character.json').write_text(json.dumps(character, indent=2), encoding='utf-8')
(base / 'memory' / 'rpg' / 'neon_dream' / 'journal.md').write_text(f'# Campaign Journal\n\n{marker}\nSession zero has not started yet.\n', encoding='utf-8')
