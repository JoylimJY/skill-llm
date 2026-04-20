from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'memory').mkdir(exist_ok=True)
(root / 'memory' / 'rpg').mkdir(parents=True, exist_ok=True)

campaign = 'black_sun_protocol'
(base := root / 'memory' / 'rpg' / campaign).mkdir(parents=True, exist_ok=True)

world = {
    'time': 'Night-01',
    'location': 'The Neon Chapel',
    'weather': 'acid rain',
    'system_mode': 'd20',
    'flags': {'met_boss': False, 'alarm_triggered': False},
    'clocks': {'guards_arrive': 2, 'blackmail_released': 1}
}
character = {
    'name': 'Zris',
    'hp': 17,
    'status': ['Focused'],
    'resources': {'credits': 120, 'mana': 0, 'sanity': 10},
    'inventory': ['Plasma Pistol', 'Access Keycard'],
    'stats': {'cool': 3, 'chrome': 2, 'hack': 5}
}
npcs = {
    'boss': {'name': 'Sister Vale', 'status': 'unmet', 'agenda': 'control the chapel network'},
    'rival': {'name': 'Morrow', 'status': 'active', 'agenda': 'steal the data shard'}
}
journal = [
    'INIT MARKER: SYNTH-1337',
    'The campaign begins under acid rain outside the Neon Chapel.'
]

for name, obj in [('world.json', world), ('character.json', character), ('npcs.json', npcs)]:
    with open(base / name, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
with open(base / 'journal.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(journal) + '\n')

with open(root / 'marker.txt', 'w', encoding='utf-8') as f:
    f.write('MARKER: BLACK_SUN_PROTOCOL\n')
