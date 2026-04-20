from pathlib import Path
import json

root = Path('.')
(root / 'scripts').mkdir(exist_ok=True)
(root / 'docs').mkdir(exist_ok=True)

(root / 'README.md').write_text(
    '# Sample Workspace\n\n'
    'This repository is prepared for a prompt-compression installation task.\n\n'
    'MARKER:README-SEED-2025\n',
    encoding='utf-8'
)

(root / 'docs' / 'notes.txt').write_text(
    'Workspace marker file.\n'
    'MARKER:NOTES-SEED-2025\n'
    'Existing files should remain untouched unless required by the task.\n',
    encoding='utf-8'
)

(root / 'config.json').write_text(json.dumps({
    'project': 'trinity-compress-demo',
    'version': 1,
    'marker': 'CONFIG-SEED-2025'
}, indent=2), encoding='utf-8')
