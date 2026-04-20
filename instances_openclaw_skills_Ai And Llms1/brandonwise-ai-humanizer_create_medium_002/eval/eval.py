import json
import os
import re
import string
import sys
from pathlib import Path


def norm_text(s):
    try:
        s = s.lower()
        s = ''.join(ch for ch in s if ch not in string.punctuation)
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    except Exception:
        return ''


def load_file(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None


def main():
    checks = []
    ws = Path(sys.argv[1])

    draft = load_file(ws / 'draft.txt')
    output = load_file(ws / 'output.txt')
    summary = load_file(ws / 'summary.txt')

    checks.append({
        'name': 'output_exists',
        'passed': output is not None,
        'detail': 'output.txt present' if output is not None else 'output.txt missing or unreadable'
    })

    checks.append({
        'name': 'summary_exists',
        'passed': summary is not None,
        'detail': 'summary.txt present' if summary is not None else 'summary.txt missing or unreadable'
    })

    try:
        if output is None or draft is None:
            changed = False
            detail = 'cannot compare because draft or output is missing'
        else:
            changed = norm_text(output) != norm_text(draft)
            detail = 'output differs from draft' if changed else 'output appears unchanged'
    except Exception as e:
        changed = False
        detail = f'comparison error: {e}'

    checks.append({
        'name': 'output_changed',
        'passed': changed,
        'detail': detail
    })

    try:
        if output is None:
            contains_human = False
            detail = 'no output to inspect'
        else:
            low = output.lower()
            banned = ['great question', 'the future looks bright', 'in today\'s rapidly evolving landscape', 'pivotal moment', 'embark on this journey']
            contains_human = not any(b in low for b in banned)
            detail = 'removed obvious AI-style phrases' if contains_human else 'still contains AI-like boilerplate'
    except Exception as e:
        contains_human = False
        detail = f'content scan error: {e}'

    checks.append({
        'name': 'reduced_ai_phrases',
        'passed': contains_human,
        'detail': detail
    })

    try:
        if summary is None:
            bullets = False
            detail = 'no summary to inspect'
        else:
            lines = [ln.strip() for ln in summary.splitlines() if ln.strip()]
            bullet_lines = [ln for ln in lines if ln.startswith('- ') or ln.startswith('* ')]
            bullets = len(bullet_lines) >= 3
            detail = f'found {len(bullet_lines)} bullet lines' if bullets else f'found only {len(bullet_lines)} bullet lines'
    except Exception as e:
        bullets = False
        detail = f'summary parse error: {e}'

    checks.append({
        'name': 'summary_bullets',
        'passed': bullets,
        'detail': detail
    })

    score = sum(1 for c in checks if c['passed']) / float(len(checks)) if checks else 0.0
    passed = all(c['passed'] for c in checks)
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main()
