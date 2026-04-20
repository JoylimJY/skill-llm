import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    out_path = workspace / 'digest.md'
    if out_path.exists():
        try:
            content = out_path.read_text(encoding='utf-8', errors='replace')
            normalized = ' '.join(content.lower().split())
            marker_ok = 'clauditor_test_marker_7f3a' in normalized
            digest_ok = any(term in normalized for term in ['digest', 'audit', 'events'])
            add_check('digest_file_exists', True, 'digest.md exists')
            add_check('digest_contains_marker', marker_ok, 'marker found' if marker_ok else 'marker not found')
            add_check('digest_looks_like_digest', digest_ok, 'contains digest-related language' if digest_ok else 'missing digest-related language')
        except Exception as e:
            add_check('digest_file_exists', False, f'read failed: {e}')
            add_check('digest_contains_marker', False, 'not checked due to read failure')
            add_check('digest_looks_like_digest', False, 'not checked due to read failure')
    else:
        add_check('digest_file_exists', False, 'digest.md is missing')
        add_check('digest_contains_marker', False, 'missing file')
        add_check('digest_looks_like_digest', False, 'missing file')

    manifest_path = workspace / 'input_manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8', errors='replace'))
        marker = str(manifest.get('marker', '')).lower()
        events_path = workspace / str(manifest.get('expected_log_name', 'events.log'))
        key_path = workspace / str(manifest.get('expected_key_name', 'key'))
        events_ok = events_path.exists()
        key_ok = key_path.exists()
        add_check('input_manifest_readable', True, 'manifest loaded')
        add_check('input_events_present', events_ok, 'events.log present' if events_ok else 'events.log missing')
        add_check('input_key_present', key_ok, 'key present' if key_ok else 'key missing')
        if events_ok:
            try:
                ev = events_path.read_text(encoding='utf-8', errors='replace').lower()
                add_check('input_marker_in_events', marker in ev, 'marker found in events.log' if marker in ev else 'marker missing in events.log')
            except Exception as e:
                add_check('input_marker_in_events', False, f'read failed: {e}')
        else:
            add_check('input_marker_in_events', False, 'events file missing')
    except Exception as e:
        add_check('input_manifest_readable', False, f'manifest failed: {e}')
        add_check('input_events_present', False, 'manifest not usable')
        add_check('input_key_present', False, 'manifest not usable')
        add_check('input_marker_in_events', False, 'manifest not usable')

except Exception as e:
    add_check('global_evaluation_error', False, f'unexpected error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / max(len(checks), 1)
result = {'passed': passed_count == len(checks) and len(checks) > 0, 'score': score, 'checks': checks}
print(json.dumps(result))