import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        s = str(s)
    except Exception:
        return ""
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def find_output_file(workspace: Path):
    candidates = [workspace / 'output.txt']
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    try:
        marker_path = workspace / 'task_marker.json'
        marker_ok = False
        marker_detail = 'missing'
        try:
            marker = json.loads(marker_path.read_text(encoding='utf-8')) if marker_path.exists() else {}
            marker_ok = norm(marker.get('marker', '')) == 'wolfram-alpha-hard-001'
            marker_detail = 'found' if marker_ok else f"unexpected marker: {marker.get('marker')!r}"
        except Exception as e:
            marker_detail = f'could not read marker file: {type(e).__name__}'
        checks.append({'name': 'marker file present', 'passed': marker_ok, 'detail': marker_detail})
    except Exception as e:
        checks.append({'name': 'marker file present', 'passed': False, 'detail': f'check error: {type(e).__name__}'})

    out_path = None
    try:
        out_path = find_output_file(workspace)
        passed = out_path is not None
        detail = str(out_path) if out_path else 'output.txt not found'
        checks.append({'name': 'output file exists', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output file exists', 'passed': False, 'detail': f'check error: {type(e).__name__}'})

    content = ''
    try:
        if out_path is not None:
            content = out_path.read_text(encoding='utf-8', errors='replace')
        passed = bool(content.strip())
        checks.append({'name': 'output file non-empty', 'passed': passed, 'detail': f'length={len(content)}'})
    except Exception as e:
        checks.append({'name': 'output file non-empty', 'passed': False, 'detail': f'read error: {type(e).__name__}'})

    try:
        n = norm(content)
        has_85 = bool(re.search(r'\b85\b', n))
        has_integral = 'integral' in n or 'integrate' in n or 'definite integral' in n
        has_query_terms = all(term in n for term in ['3x', 'x=0', 'x=5'])
        passed = has_85 and (has_integral or has_query_terms)
        detail = f'has_85={has_85}, has_integral={has_integral}, has_query_terms={has_query_terms}'
        checks.append({'name': 'output contains expected answer', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output contains expected answer', 'passed': False, 'detail': f'analysis error: {type(e).__name__}'})

    try:
        n = norm(content)
        # Fuzzy check for a short one-line note mentioning result or answer.
        note_ok = any(k in n for k in ['result', 'answer', 'final'])
        checks.append({'name': 'output includes a short note', 'passed': note_ok, 'detail': 'mentions result/answer/final' if note_ok else 'no note-like wording found'})
    except Exception as e:
        checks.append({'name': 'output includes a short note', 'passed': False, 'detail': f'analysis error: {type(e).__name__}'})

    try:
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / max(len(checks), 1)
        passed = score == 1.0
        print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
    except Exception:
        # Absolute fallback to guarantee no traceback
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
