import json
import re
import sys
from pathlib import Path


def norm(s):
    try:
        s = str(s).lower()
        s = re.sub(r'[^a-z0-9]+', '', s)
        return s
    except Exception:
        return ''


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        return None, f'failed to read/parse {path}: {e}'


def find_file(workspace, candidates):
    for c in candidates:
        p = Path(workspace) / c
        if p.exists():
            return p
    return None


def main():
    checks = []
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    ws = Path(workspace)

    try:
        summaries_path = find_file(ws, ['cache/gmail-inbox-summaries.json', 'gmail-inbox-summaries.json'])
        ok = summaries_path is not None and summaries_path.exists()
        detail = f'found {summaries_path}' if ok else 'missing inbox summaries json'
        checks.append({'name': 'inbox_summaries_exists', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'inbox_summaries_exists', 'passed': False, 'detail': str(e)})
        summaries_path = None

    try:
        voice_path = find_file(ws, ['references/voice.md', 'voice.md'])
        ok = voice_path is not None and voice_path.exists()
        detail = f'found {voice_path}' if ok else 'missing voice reference markdown'
        checks.append({'name': 'voice_reference_exists', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'voice_reference_exists', 'passed': False, 'detail': str(e)})
        voice_path = None

    try:
        labels_path = find_file(ws, ['cache/gmail-triage-labels.json', 'gmail-triage-labels.json'])
        ok = labels_path is not None and labels_path.exists()
        detail = f'found {labels_path}' if ok else 'missing triage labels json'
        checks.append({'name': 'labels_exists', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'labels_exists', 'passed': False, 'detail': str(e)})
        labels_path = None

    expected_labels = {
        'msg-001': 'school',
        'msg-002': 'receiptbilling',
        'msg-003': 'clubs',
        'msg-004': 'adminaccounts',
        'msg-005': 'clubs',
    }

    try:
        data, err = load_json(labels_path) if labels_path else (None, 'labels file missing')
        ok = isinstance(data, list)
        detail = 'valid list' if ok else f'labels invalid: {err}'
        checks.append({'name': 'labels_json_shape', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'labels_json_shape', 'passed': False, 'detail': str(e)})
        data = None

    try:
        if isinstance(data, list):
            found = {}
            for item in data:
                try:
                    mid = str(item.get('id', ''))
                    lab = norm(item.get('label', ''))
                    if mid:
                        found[mid] = lab
                except Exception:
                    pass
            passed = True
            details = []
            for mid, exp in expected_labels.items():
                got = found.get(mid, '')
                ok = exp in got or got in exp
                passed = passed and ok
                details.append(f'{mid}:{got or "missing"}')
            checks.append({'name': 'labels_classification', 'passed': passed, 'detail': '; '.join(details)})
        else:
            checks.append({'name': 'labels_classification', 'passed': False, 'detail': 'no usable labels data'})
    except Exception as e:
        checks.append({'name': 'labels_classification', 'passed': False, 'detail': str(e)})

    try:
        if voice_path and voice_path.exists():
            txt = voice_path.read_text(encoding='utf-8', errors='ignore')
            snippets_ok = ('Representative micro-snippets' in txt) or ('micro-snippets' in txt.lower())
            rules_ok = ('Keep it short' in txt) or ('Avoid filler' in txt)
            checks.append({'name': 'voice_content', 'passed': bool(snippets_ok and rules_ok), 'detail': 'voice heuristics and snippets present' if snippets_ok and rules_ok else 'voice markdown missing expected content'})
        else:
            checks.append({'name': 'voice_content', 'passed': False, 'detail': 'voice file missing'})
    except Exception as e:
        checks.append({'name': 'voice_content', 'passed': False, 'detail': str(e)})

    try:
        total = len(checks) if checks else 1
        passed_n = sum(1 for c in checks if c.get('passed'))
        score = passed_n / total
        passed = passed_n == total
        result = {'passed': passed, 'score': score, 'checks': checks}
        print(json.dumps(result))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))


if __name__ == '__main__':
    main()
