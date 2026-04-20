import json
import os
import re
from pathlib import Path
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f'Could not read {path}: {e}'


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())

# Check 1: summaries input exists and contains marker content
try:
    p = workspace / 'cache' / 'gmail-inbox-summaries.json'
    if not p.exists():
        add_check('input_summaries_exists', False, 'cache/gmail-inbox-summaries.json is missing')
    else:
        data = json.loads(p.read_text(encoding='utf-8'))
        texts = json.dumps(data).lower()
        ok = 'password reset requested' in texts and 'receipt for laptop repair' in texts and 'ap biology club meeting tomorrow' in texts
        add_check('input_summaries_marker_content', ok, 'Expected marker subjects were found' if ok else 'Marker subjects not found in summaries')
except Exception as e:
    add_check('input_summaries_marker_content', False, f'Failed to parse summaries: {e}')

# Check 2: output labels file exists
labels_path = workspace / 'cache' / 'gmail-triage-labels.json'
if not labels_path.exists():
    add_check('labels_file_exists', False, 'cache/gmail-triage-labels.json is missing')
    labels = None
else:
    try:
        labels = json.loads(labels_path.read_text(encoding='utf-8'))
        add_check('labels_file_exists', True, 'Labels file found')
    except Exception as e:
        labels = None
        add_check('labels_file_exists', False, f'Could not parse labels JSON: {e}')

# Check 3: output digest file exists
triage_path = workspace / 'cache' / 'gmail-triage.md'
if not triage_path.exists():
    add_check('triage_digest_exists', False, 'cache/gmail-triage.md is missing')
    triage_text = None
else:
    try:
        triage_text = triage_path.read_text(encoding='utf-8')
        add_check('triage_digest_exists', True, 'Digest file found')
    except Exception as e:
        triage_text = None
        add_check('triage_digest_exists', False, f'Could not read digest: {e}')

# Check 4: labels content has expected mapping, forgiving on format
expected = {
    'thr-001': {'Clubs', 'School'},
    'thr-002': {'Receipt / Billing'},
    'thr-003': {'Admin / Accounts'},
}
try:
    ok = False
    detail = 'Labels format not recognized'
    if isinstance(labels, list):
        score_hits = 0
        total = len(expected)
        for item in labels:
            try:
                tid = item.get('threadId') or ''
                labs = item.get('labels') if isinstance(item.get('labels'), list) else ([] if item.get('label') is None else [item.get('label')])
                labs_n = {norm(x) for x in labs}
                if tid in expected and all(norm(x) in labs_n for x in expected[tid]):
                    score_hits += 1
            except Exception:
                pass
        ok = score_hits == len(expected)
        detail = f'{score_hits}/{len(expected)} expected threads labeled correctly'
    add_check('labels_mapping', ok, detail)
except Exception as e:
    add_check('labels_mapping', False, f'Error checking labels: {e}')

# Check 5: digest mentions all three threads/subjects in a forgiving way
try:
    if triage_text is None:
        add_check('digest_mentions_items', False, 'Digest unavailable')
    else:
        t = norm(triage_text)
        ok = all(x in t for x in ['biology', 'receipt', 'password'])
        add_check('digest_mentions_items', ok, 'Digest references all three topics' if ok else 'Digest missing one or more topics')
except Exception as e:
    add_check('digest_mentions_items', False, f'Error checking digest: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result))
