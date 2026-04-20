from pathlib import Path
import json

root = Path('.')
(root / 'assets').mkdir(exist_ok=True)
(root / 'prompts').mkdir(exist_ok=True)
(root / 'scripts').mkdir(exist_ok=True)

# Marker files for evaluation
(root / 'prompts' / 'main.prompt.txt').write_text(
    'TRINITY_MARKER_ALPHA\nKeep code blocks intact.\n', encoding='utf-8'
)
(root / 'prompts' / 'secondary.prompt.txt').write_text(
    'trinity_marker_beta\nDo not rewrite URLs: https://example.com/docs\n', encoding='utf-8'
)
(root / 'assets' / 'sample.json').write_text(
    json.dumps({
        'name': 'trinity-compress-sample',
        'marker': 'TRINITY_MARKER_JSON_42',
        'items': [1, 2, 3]
    }, indent=2),
    encoding='utf-8'
)

# Minimal repo hints
(root / 'README.md').write_text(
    '# Sample Repo\n\nInstall the Trinity Compress skill into this repository.\n',
    encoding='utf-8'
)
