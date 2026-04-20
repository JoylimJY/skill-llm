import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    briefing = workspace / 'briefing.md'
    summary = workspace / 'summary.json'
    notes = workspace / 'input' / 'notes.json'
    source = workspace / 'input' / 'source.txt'

    try:
        notes_data = json.loads(notes.read_text(encoding='utf-8')) if notes.exists() else {}
    except Exception as e:
        notes_data = {}
        add_check('notes_read', False, f'Could not read notes.json: {e}')

    marker = str(notes_data.get('marker', '')).lower()
    project = str(notes_data.get('project', '')).lower()
    owner = str(notes_data.get('owner', '')).lower()
    milestone = str(notes_data.get('milestone', '')).lower()

    try:
        briefing_text = briefing.read_text(encoding='utf-8') if briefing.exists() else ''
        if not briefing.exists():
            add_check('briefing_exists', False, 'briefing.md is missing')
        else:
            txt = briefing_text.lower()
            ok = all(k in txt for k in [project, owner, milestone]) and ('marker' in txt and marker in txt)
            add_check('briefing_content', ok, 'briefing.md should mention the project, owner, milestone, and marker')
    except Exception as e:
        add_check('briefing_content', False, f'Error reading briefing.md: {e}')

    try:
        summary_text = summary.read_text(encoding='utf-8') if summary.exists() else ''
        if not summary.exists():
            add_check('summary_exists', False, 'summary.json is missing')
        else:
            data = json.loads(summary_text)
            ok = True
            detail_parts = []
            for field in ['project', 'owner', 'milestone', 'marker']:
                val = str(data.get(field, '')).lower()
                expected = str(notes_data.get(field, '')).lower()
                field_ok = bool(val) and (expected in val or val in expected or val == expected)
                ok = ok and field_ok
                detail_parts.append(f'{field}={field_ok}')
            add_check('summary_content', ok, '; '.join(detail_parts))
    except Exception as e:
        add_check('summary_content', False, f'Error parsing summary.json: {e}')

    try:
        source_text = source.read_text(encoding='utf-8') if source.exists() else ''
        if not source.exists():
            add_check('source_exists', False, 'input/source.txt is missing')
        else:
            ok = marker in source_text.lower()
            add_check('source_marker', ok, 'source file marker verification')
    except Exception as e:
        add_check('source_marker', False, f'Error reading source.txt: {e}')

except Exception as e:
    add_check('fatal', False, f'Unexpected error: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
