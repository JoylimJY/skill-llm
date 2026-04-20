import json
import re
from pathlib import Path
import sys

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

# 1) Markdown brief exists and mentions key ideas from input.
try:
    md_path = workspace / 'creator_brief.md'
    if not md_path.exists():
        add_check('markdown_exists', False, 'creator_brief.md is missing')
    else:
        text = md_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text).lower()
        passed = ('concise' in norm and 'friendly' in norm and 'actionable' in norm)
        detail = 'Contains expected summary terms' if passed else 'Missing one or more expected theme words'
        add_check('markdown_exists', passed, detail)
except Exception as e:
    add_check('markdown_exists', False, f'Error while checking markdown: {e}')

# 2) JSON metadata exists and has 5 tags.
try:
    js_path = workspace / 'metadata.json'
    if not js_path.exists():
        add_check('metadata_json', False, 'metadata.json is missing')
    else:
        try:
            data = json.loads(js_path.read_text(encoding='utf-8', errors='replace'))
            title = str(data.get('title', '')).strip().lower()
            desc = str(data.get('description', '')).strip().lower()
            tags = data.get('tags', [])
            passed = bool(title) and bool(desc) and isinstance(tags, list) and len(tags) == 5
            detail = 'JSON has title, description, and exactly five tags' if passed else 'JSON structure or tag count is incorrect'
            add_check('metadata_json', passed, detail)
        except Exception as e:
            add_check('metadata_json', False, f'Could not parse metadata.json: {e}')
except Exception as e:
    add_check('metadata_json', False, f'Error while checking metadata: {e}')

# 3) Quote sheet exists and contains exactly three non-empty quote lines.
try:
    quote_path = workspace / 'quote_sheet.txt'
    if not quote_path.exists():
        add_check('quote_sheet', False, 'quote_sheet.txt is missing')
    else:
        text = quote_path.read_text(encoding='utf-8', errors='replace')
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        passed = len(lines) == 3
        detail = f'Found {len(lines)} non-empty lines' if not passed else 'Contains exactly three non-empty lines'
        add_check('quote_sheet', passed, detail)
except Exception as e:
    add_check('quote_sheet', False, f'Error while checking quote sheet: {e}')

# 4) Source marker awareness: output should reflect the provided source file content indirectly.
try:
    src_path = workspace / 'source_notes.txt'
    out_path = workspace / 'creator_brief.md'
    if not src_path.exists() or not out_path.exists():
        add_check('marker_reflection', False, 'Required files are missing for comparison')
    else:
        src = src_path.read_text(encoding='utf-8', errors='replace').lower()
        out = out_path.read_text(encoding='utf-8', errors='replace').lower()
        marker_ok = 'marker_alpha' in src
        reflected = any(word in out for word in ['writing', 'planning', 'editing', 'delivery'])
        passed = marker_ok and reflected
        detail = 'Output reflects source themes' if passed else 'Output does not sufficiently reflect source themes'
        add_check('marker_reflection', passed, detail)
except Exception as e:
    add_check('marker_reflection', False, f'Error while checking marker reflection: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks) if checks else False
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
