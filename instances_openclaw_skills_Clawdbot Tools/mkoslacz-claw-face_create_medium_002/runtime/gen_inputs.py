from pathlib import Path
import json

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

(base / 'inputs' / 'project_name.txt').write_text('Nebula Fox\n', encoding='utf-8')
(base / 'inputs' / 'status.txt').write_text('done: true\nmode: robot\n', encoding='utf-8')
(base / 'inputs' / 'notes.json').write_text(json.dumps({
    'marker': 'CLAWFACE_OK',
    'summary': 'The avatar should end in a happy successful state.'
}, indent=2), encoding='utf-8')
