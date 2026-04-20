from pathlib import Path
import json

# Deterministic input generation
workspace = Path('.').resolve()

inputs = {
    'skill_name.txt': 'telegram-footer-patch\n',
    'seed_marker.txt': 'MARKER: Telegram private-chat footer\n',
    'reference.json': {
        'operation': 'create',
        'required_phrase': 'Telegram private-chat footer',
        'difficulty': 'easy'
    }
}

for name, content in inputs.items():
    p = workspace / name
    if isinstance(content, dict):
        p.write_text(json.dumps(content, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    else:
        p.write_text(content, encoding='utf-8')
