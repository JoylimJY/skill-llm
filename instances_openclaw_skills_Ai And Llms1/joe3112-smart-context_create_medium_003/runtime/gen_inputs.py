from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'input').mkdir(exist_ok=True)
(root / 'docs').mkdir(exist_ok=True)
(root / 'notes').mkdir(exist_ok=True)

files = {
    'input/README.md': '# Workspace Overview\n\nThis workspace contains a small set of documentation and notes.\n\nMarkers: ALPHA-README-91\n',
    'input/spec.txt': 'Primary spec:\n- focus on context efficiency\n- avoid redundant reads\n- prioritize high-signal files\nMarker: SPEC-MARK-204\n',
    'docs/guide.md': '# Guide\n\nUse the README first, then the spec. The guide repeats some guidance from spec.txt.\nMarker: GUIDE-MARK-517\n',
    'notes/todo.txt': 'TODO:\n- clean up duplicate guidance\n- write summary\nMarker: TODO-MARK-772\n',
    'notes/duplicate.md': 'This note repeats the same recommendation as guide.md and spec.txt: read the README first.\nMarker: DUP-MARK-118\n',
}

for rel, content in files.items():
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

metadata = {
    'seed': 1337,
    'files': sorted(files.keys()),
    'workspace_hint': 'Summarize the highest-signal files and note redundant content.',
}
(root / 'input' / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
