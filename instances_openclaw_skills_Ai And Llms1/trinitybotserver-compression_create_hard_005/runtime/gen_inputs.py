from pathlib import Path
import json

root = Path('.')
(root / 'skill').mkdir(exist_ok=True)
(root / 'docs').mkdir(exist_ok=True)

skill_md = '''# Trinity Compress (Skill)

Pre-run prompt compression for iterative AI dev loops.

**Goal:** reduce input tokens every iteration by compressing prompt files *before* your loop runs.

- Works with Ralph-style loops, agent/skill directories, and most token-billed providers.
- Runs as a **local script** (no model calls).
- Creates **.bak** backups and supports instant undo.

## What it installs into a repo
- `trinity-compress.config.json` — rules + targets
- `scripts/trinity-compress.sh` — compression script
- Makefile snippet (optional): `optimize-prompts`, `optimize-undo`, etc.
- `.gitignore` snippet: ignore `*.bak`
- Installers:
  - `scripts/install.ps1` (Windows)
  - `scripts/install.sh` (bash)

## Requirements
- bash 4+
- `jq`
- `bc`

## Use
1) Install into your repo (copy assets or use the included installer scripts)
2) Run:
   - `bash scripts/trinity-compress.sh balanced`
   - or via Makefile target

## Undo
- Restores all `*.bak` backups from the last run.

## Notes
- This tool does not rewrite code blocks, URLs, file paths, or variable names.
- Aggressive mode may reduce clarity; review before committing.
'''

(root / 'skill' / 'SKILL.md').write_text(skill_md, encoding='utf-8')

(root / 'docs' / 'marker.txt').write_text('MARKER_TRINITY_COMPRESSION_7F3A2C\n', encoding='utf-8')

manifest = {
    'marker': 'MARKER_TRINITY_COMPRESSION_7F3A2C',
    'files': ['skill/SKILL.md', 'docs/marker.txt']
}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
