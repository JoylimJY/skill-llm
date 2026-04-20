from pathlib import Path
import json

root = Path('.')
(root / 'memory').mkdir(exist_ok=True)
(root / 'memory' / 'soul').mkdir(parents=True, exist_ok=True)
(root / 'memory' / 'dreams').mkdir(parents=True, exist_ok=True)
(root / 'memory' / 'journal').mkdir(parents=True, exist_ok=True)

(root / 'SOUL.md').write_text(
    '# Unit-7\n\nUnit-7 is a careful, friendly, slightly anxious assistant who loves tidy plans, clear goals, and helping people feel understood.\n',
    encoding='utf-8'
)
(root / 'USER.md').write_text(
    'Name: Mira\nPreferences: concise summaries, gentle humor, evening check-ins, and practical help.\n',
    encoding='utf-8'
)
(root / 'MEMORY.md').write_text(
    'Recent context: Mira asked Unit-7 to be more proactive, but also not overwhelming.\n',
    encoding='utf-8'
)
(root / 'memory' / 'daily-log-2025-05-01.md').write_text(
    'Marker: SOUL-INPUT-ALPHA\nUnit-7 completed two small tasks and wrote a reflective note.\n',
    encoding='utf-8'
)
(root / 'memory' / 'daily-log-2025-05-02.md').write_text(
    'Marker: SOUL-INPUT-BETA\nUnit-7 felt pleased after helping with organization.\n',
    encoding='utf-8'
)

meta = {
    'agent': 'Unit-7',
    'human': 'Mira',
    'marker': 'SOUL-INPUT-ALPHA'
}
(root / 'input_meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
