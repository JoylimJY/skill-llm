from pathlib import Path
from textwrap import dedent
import json

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)

skill_md = dedent('''
---
name: pincer
description: Security-first wrapper for installing agent skills. Scans for malware, prompt injection, and suspicious patterns before installation. Use instead of `clawhub install` for safer skill management.
homepage: https://github.com/panzacoder/pincer
metadata:
  openclaw:
    emoji: "🦞"
    requires:
      bins: ["pincer"]
---

# pincer 🛡️

Security-first wrapper for `clawhub install`. Scans skills for malware, prompt injection, and suspicious patterns before installation.

## Usage

### Safe Install

```bash
pincer install some-skill
pincer install some-skill@1.2.0
```

### Scan Without Installing

```bash
pincer scan some-skill
pincer scan ./path/to/skill
pincer scan some-skill --json
```

### Audit Installed Skills

```bash
pincer audit
pincer audit --json
```

## Risk Levels

- CLEAN: No issues
- CAUTION: Warnings present
- DANGER: Suspicious patterns
- MALWARE: Known malicious
- BLOCKED: On blocklist
''').strip() + '\n'

(root / 'inputs' / 'SKILL.md').write_text(skill_md, encoding='utf-8')

marker = {
    'marker': 'PINCER_RELEASE_NOTE_MARKER_7F3A',
    'expected_topics': ['security-first scanning', 'install', 'scan', 'audit', 'risk levels']
}
(root / 'inputs' / 'marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
