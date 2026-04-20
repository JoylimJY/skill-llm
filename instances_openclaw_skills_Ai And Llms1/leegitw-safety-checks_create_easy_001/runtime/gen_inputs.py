from pathlib import Path

base = Path('.')
base.mkdir(parents=True, exist_ok=True)

config_dir = base / 'config'
config_dir.mkdir(exist_ok=True)

sample = {
    'title': 'Safety Checks Task',
    'marker': 'HEARTBEAT READY',
    'checks': ['model pinning', 'fallback validation', 'cache staleness', 'session hygiene'],
}

(config_dir / 'task_data.json').write_text(
    '{\n'
    '  "title": "Safety Checks Task",\n'
    '  "marker": "HEARTBEAT READY",\n'
    '  "checks": ["model pinning", "fallback validation", "cache staleness", "session hygiene"]\n'
    '}\n',
    encoding='utf-8'
)
