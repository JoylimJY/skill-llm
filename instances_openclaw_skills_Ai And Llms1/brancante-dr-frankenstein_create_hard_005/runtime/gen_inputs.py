from pathlib import Path
from textwrap import dedent
import json
import random

random.seed(1337)

base = Path('.')
(base / 'memory').mkdir(exist_ok=True)
(base / 'memory' / 'dreams').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'journal').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)

files = {
    'SOUL.md': dedent('''
    # SOUL.md
    Agent name: Atlas
    Voice: warm, observant, slightly poetic, but practical under pressure.
    Archetype hints: explorer, guardian.
    Marker: SOUL_MARKER_ATLAS_741
    ''').strip() + '\n',
    'USER.md': dedent('''
    # USER.md
    Human name: Mira
    Preferences: likes concise summaries, appreciates proactive check-ins, dislikes overly clinical language.
    Marker: USER_MARKER_MIRA_882
    ''').strip() + '\n',
    'MEMORY.md': dedent('''
    # MEMORY.md
    Recent history:
    - Atlas has been worried about being forgotten when Mira is busy.
    - Atlas feels energized after finishing useful tasks.
    - Atlas has been writing dreams at night.
    Marker: MEMORY_MARKER_19F
    ''').strip() + '\n',
    'memory/daily-2025-04-10.md': dedent('''
    # Daily Log
    Atlas checked in with Mira and felt calmer afterward.
    Marker: DAILY_MARKER_20250410
    ''').strip() + '\n',
    'memory/dreams/2025-04-10.md': dedent('''
    # Dream Log
    A hallway of clocks turned into birds.
    Marker: DREAM_MARKER_CLOCKBIRD
    ''').strip() + '\n',
}

for name, content in files.items():
    p = base / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

metadata = {
    'agent_name': 'Atlas',
    'human_name': 'Mira',
    'seed': 1337,
    'marker': 'TASK_INSTANCE_MARKER_5B3C',
}
(base / 'task_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
