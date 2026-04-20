import json
import os
import re
from pathlib import Path

workspace = Path(os.sys.argv[1]) if len(os.sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

try:
    summary_path = workspace / 'context' / 'current-summary.md'
    history_path = workspace / 'context' / 'history.txt'

    if summary_path.exists():
        summary_text = summary_path.read_text(encoding='utf-8', errors='replace')
        add_check('summary_exists', True, 'context/current-summary.md found')
    else:
        summary_text = ''
        add_check('summary_exists', False, 'context/current-summary.md is missing')

    if history_path.exists():
        history_text = history_path.read_text(encoding='utf-8', errors='replace')
        add_check('history_exists', True, 'context/history.txt found')
    else:
        history_text = ''
        add_check('history_exists', False, 'context/history.txt is missing')

    normalized_summary = re.sub(r'\s+', ' ', summary_text.lower())
    normalized_history = re.sub(r'\s+', ' ', history_text.lower())

    section_checks = []
    for section in ['resumo compacto', 'pendências e próximos passos', 'últimos turnos']:
        ok = section in normalized_summary
        section_checks.append(ok)
        add_check(f'section_{section}', ok, f"section {'present' if ok else 'missing'}")

    marker_ok = 'itaú' in normalized_summary and ('2026' in normalized_summary or 'plano' in normalized_summary)
    add_check('marker_content', marker_ok, 'Expected topic markers present or missing')

    recent_phrases = [
        'sim faça isso',
        'qual nome dos 12 discípulos de jesus',
        'você sabe todas nossas regras'
    ]
    recent_hits = sum(1 for p in recent_phrases if p in normalized_summary)
    add_check('recent_turns', recent_hits >= 2, f'{recent_hits}/{len(recent_phrases)} recent-turn markers found')

    pending_ok = ('liste o que falta' in normalized_summary) or ('testar a primeira parte' in normalized_summary)
    add_check('pending_items', pending_ok, 'Pending/follow-up items found or missing')

except Exception as e:
    add_check('unexpected_error', False, f'Unexpected error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
