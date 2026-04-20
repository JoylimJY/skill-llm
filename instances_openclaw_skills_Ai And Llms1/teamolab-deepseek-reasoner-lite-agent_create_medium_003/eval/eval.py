import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


try:
    brief = workspace / 'launch_brief.txt'
    social = workspace / 'social_posts.txt'
    milestones = workspace / 'milestones.csv'
    source = workspace / 'source_notes.json'

    try:
        source_data = json.loads(source.read_text(encoding='utf-8')) if source.exists() else {}
    except Exception as e:
        source_data = {}
        add_check('source_notes_readable', False, f'Could not parse source_notes.json: {e}')
    else:
        add_check('source_notes_readable', True, 'source_notes.json parsed successfully')

    try:
        text = brief.read_text(encoding='utf-8')
        lowered = text.lower()
        ok = all(k.lower() in lowered for k in ['northstar note', 'launch', 'marker_campaign_brief_7f3a'])
        add_check('launch_brief_content', ok, 'Checked product name, launch language, and marker presence')
    except Exception as e:
        add_check('launch_brief_content', False, f'launch_brief.txt missing or unreadable: {e}')

    try:
        text = social.read_text(encoding='utf-8')
        lowered = text.lower()
        ok = sum(1 for term in ['northstar note', 'fast note capture', 'team sharing', 'task follow-up'] if term in lowered) >= 2
        add_check('social_posts_content', ok, 'Checked for at least two campaign-related phrases')
    except Exception as e:
        add_check('social_posts_content', False, f'social_posts.txt missing or unreadable: {e}')

    try:
        csv_text = milestones.read_text(encoding='utf-8')
        lines = [ln for ln in csv_text.splitlines() if ln.strip()]
        ok = len(lines) >= 5 and '2025-06' in csv_text
        add_check('milestones_csv_shape', ok, 'Checked for header plus at least four milestone rows and June 2025 dates')
    except Exception as e:
        add_check('milestones_csv_shape', False, f'milestones.csv missing or unreadable: {e}')

except Exception as e:
    add_check('fatal', False, f'Unexpected evaluator error: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
