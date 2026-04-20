import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    summary_path = workspace / 'context' / 'current-summary.md'
    exists = summary_path.exists()
    add_check('summary_exists', exists, 'Found summary file.' if exists else 'Missing context/current-summary.md.')
    text = ''
    if exists:
        try:
            text = summary_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            add_check('summary_readable', False, f'Could not read summary file: {e}')
            text = ''
        else:
            add_check('summary_readable', True, 'Summary file could be read.')
    else:
        add_check('summary_readable', False, 'Skipped because file is missing.')

    def norm(s):
        try:
            s = s.lower()
            s = re.sub(r'\s+', ' ', s)
            s = re.sub(r'[^\w\sáàâãäéèêëíìîïóòôõöúùûüç]', '', s, flags=re.UNICODE)
            return s.strip()
        except Exception:
            return ''

    if text:
        sections = [
            ('has_resumo', 'resumo compacto' in norm(text), 'Checks for Resumo compacto section.'),
            ('has_pendencias', 'pendências e próximos passos' in norm(text) or 'pendencias e proximos passos' in norm(text), 'Checks for pending-items section.'),
            ('has_ultimos_turnos', 'últimos turnos' in norm(text) or 'ultimos turnos' in norm(text), 'Checks for recent-turns section.'),
        ]
        for name, passed, detail in sections:
            add_check(name, passed, detail)

        marker_checks = [
            ('mentions_2026', re.search(r'2026', text, re.I) is not None, 'Should mention 2026 plan marker.'),
            ('mentions_itau', re.search(r'ita[uú]', text, re.I) is not None, 'Should mention Itaú marker.'),
            ('mentions_disciplines', re.search(r'disc[ií]pulos', text, re.I) is not None, 'Should mention disciples marker.'),
        ]
        for name, passed, detail in marker_checks:
            add_check(name, passed, detail)

        try:
            sentences = re.split(r'(?<=[\.!?])\s+', re.sub(r'\s+', ' ', text))
            compact_block = []
            in_section = False
            for line in text.splitlines():
                if 'resumo compacto' in norm(line):
                    in_section = True
                    continue
                if in_section and line.startswith('## '):
                    break
                if in_section and line.strip().startswith('-'):
                    compact_block.append(line)
            add_check('compact_sentence_limit', len(compact_block) <= 6 and len(compact_block) > 0, f'Found {len(compact_block)} bullet lines in compact summary (expected 1-6).')
        except Exception as e:
            add_check('compact_sentence_limit', False, f'Could not evaluate sentence limit safely: {e}')

        try:
            recent_lines = [ln for ln in text.splitlines() if ln.strip().startswith('- ')]
            add_check('recent_turns_present', len(recent_lines) >= 2, f'Found {len(recent_lines)} bullet lines across sections.')
        except Exception as e:
            add_check('recent_turns_present', False, f'Could not inspect bullet lines: {e}')

    score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
    result = {"passed": all(c['passed'] for c in checks), "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    fallback = {"passed": False, "score": 0.0, "checks": [{"name": "fatal_error", "passed": False, "detail": f'Unexpected evaluator error: {e}'}]}
    print(json.dumps(fallback, ensure_ascii=False))
