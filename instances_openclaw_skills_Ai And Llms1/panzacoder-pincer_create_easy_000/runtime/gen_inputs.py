from pathlib import Path
import json

root = Path('.')
skill_dir = root / 'sample_skill'
skill_dir.mkdir(parents=True, exist_ok=True)

(skill_dir / 'SKILL.md').write_text(
    '''---
name: sample-skill
description: A harmless demo skill for scanning.
homepage: https://example.com/sample-skill
---

# Sample Skill

This skill is intentionally simple and safe.

## Notes
- Marker: SAFE_MARKER_7F3A
- No binaries included.
- No suspicious commands.
''',
    encoding='utf-8'
)

(skill_dir / 'README.txt').write_text(
    'This directory contains the marker SAFE_MARKER_7F3A for eval verification.\n',
    encoding='utf-8'
)

(root / 'expected_marker.txt').write_text('SAFE_MARKER_7F3A\n', encoding='utf-8')

metadata = {
    'skill_dir': 'sample_skill',
    'marker': 'SAFE_MARKER_7F3A'
}
(root / 'input_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
