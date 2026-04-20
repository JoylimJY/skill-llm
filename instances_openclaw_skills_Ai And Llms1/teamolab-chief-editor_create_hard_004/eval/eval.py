import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower()) if isinstance(s, str) else ''


def main():
    checks = []
    ws = Path(sys.argv[1])
    out = ws / 'output.md'

    # Check 1: file exists
    try:
        exists = out.exists()
        checks.append({
            'name': 'output_exists',
            'passed': exists,
            'detail': 'output.md found' if exists else 'output.md is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking existence: {e}'})

    # Check 2: readable content
    content = ''
    try:
        if out.exists():
            content = out.read_text(encoding='utf-8')
        passed = len(content.strip()) > 0
        checks.append({
            'name': 'nonempty_output',
            'passed': passed,
            'detail': f'length={len(content)}' if passed else 'output.md is empty'
        })
    except Exception as e:
        checks.append({'name': 'nonempty_output', 'passed': False, 'detail': f'read error: {e}'})

    # Check 3: required section headings in order
    try:
        headings = ['Executive Summary', 'Key Developments', 'Editorial Risks', 'Recommended Actions', 'References']
        pos = []
        lower = content.lower()
        ok = True
        last = -1
        for h in headings:
            idx = lower.find(h.lower())
            pos.append((h, idx))
            if idx == -1 or idx < last:
                ok = False
            last = idx if idx != -1 else last
        title_ok = 'chief editor weekly brief' in lower
        passed = ok and title_ok
        checks.append({
            'name': 'structure_and_order',
            'passed': passed,
            'detail': f'title_ok={title_ok}; positions={pos}'
        })
    except Exception as e:
        checks.append({'name': 'structure_and_order', 'passed': False, 'detail': f'parse error: {e}'})

    # Check 4: markers preserved from sources
    try:
        markers = ['alpha-117', 'beta-204', 'gamma-331', 'delta-918', 'epsilon-550']
        norm = normalize(content)
        missing = [m for m in markers if normalize(m) not in norm]
        passed = len(missing) == 0
        checks.append({
            'name': 'markers_preserved',
            'passed': passed,
            'detail': 'all markers present' if passed else f'missing markers: {missing}'
        })
    except Exception as e:
        checks.append({'name': 'markers_preserved', 'passed': False, 'detail': f'error: {e}'})

    # Check 5: cite source tags and references section at end
    try:
        has_sources = '[source:' in content.lower()
        refs_idx = content.lower().rfind('references')
        last_nonempty = ''
        for line in content.splitlines()[::-1]:
            if line.strip():
                last_nonempty = line.strip()
                break
        refs_at_end = refs_idx != -1 and refs_idx > content.lower().rfind('recommended actions')
        passed = has_sources and refs_at_end
        checks.append({
            'name': 'citations_and_references',
            'passed': passed,
            'detail': f'has_source_tags={has_sources}; references_at_end={refs_at_end}; last_nonempty={last_nonempty}'
        })
    except Exception as e:
        checks.append({'name': 'citations_and_references', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()