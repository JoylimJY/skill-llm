from pathlib import Path
import json

root = Path('.')
skill = root / 'skill'
skill.mkdir(exist_ok=True)

(skill / 'SKILL.md').write_text('''---
name: pincer
description: Security-first wrapper for installing agent skills.
---

# pincer

Scan skills for suspicious patterns.

## Notes
- This skill contains a few markers for evaluation.
- The word D0WNLOAD and the token MARKER-ALPHA should be detectable.
- A harmless example path appears here: /tmp/example
''', encoding='utf-8')

(skill / 'README.txt').write_text('''This is a deterministic input file.
Important marker: MARKER-BETA
Another marker: suspicious pattern mention.
''', encoding='utf-8')

(root / 'manifest.json').write_text(json.dumps({
    'skill_name': 'pincer',
    'publisher': 'openclaw',
    'marker': 'MARKER-GAMMA',
    'downloads': 7363
}, indent=2), encoding='utf-8')
