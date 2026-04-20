import json
import os
import re
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f'failed to read {path}: {e}'


def normalize(text):
    return re.sub(r'[^a-z0-9]+', ' ', (text or '').lower()).strip()


def main():
    import sys
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        hb_path = ws / 'HEARTBEAT.md'
        if hb_path.exists():
            hb = hb_path.read_text(encoding='utf-8', errors='replace')
            add_check('heartbeat_file_exists', True, 'HEARTBEAT.md present')
        else:
            hb = ''
            add_check('heartbeat_file_exists', False, 'HEARTBEAT.md missing')
    except Exception as e:
        hb = ''
        add_check('heartbeat_file_exists', False, f'error reading HEARTBEAT.md: {e}')

    try:
        out_candidates = ['build_session_log.md', 'session_log.md', 'LOG.md']
        out_path = None
        for name in out_candidates:
            p = ws / name
            if p.exists():
                out_path = p
                break
        if out_path is None:
            add_check('output_file_exists', False, 'no expected log file found')
            out_text = ''
        else:
            out_text = out_path.read_text(encoding='utf-8', errors='replace')
            add_check('output_file_exists', True, f'found {out_path.name}')
    except Exception as e:
        out_text = ''
        add_check('output_file_exists', False, f'error locating output file: {e}')

    try:
        marker_ok = 'marker_heartbeat_alpha' in normalize(hb) and 'marker_notes_beta' in normalize((ws / 'project_notes.txt').read_text(encoding='utf-8', errors='replace'))
        add_check('input_markers_present', marker_ok, 'marker lines verified in inputs' if marker_ok else 'missing one or more marker lines')
    except Exception as e:
        add_check('input_markers_present', False, f'error checking markers: {e}')

    try:
        n_out = normalize(out_text)
        has_session = 'build session' in n_out or 'session log' in n_out
        has_one_action = any(k in n_out for k in ['picked one thing', 'one thing', 'task selected', 'chosen task'])
        has_log = 'what i built' in n_out and 'key insights' in n_out and 'git' in n_out
        add_check('output_structure', has_session and has_one_action and has_log, 'output contains required sections' if has_session and has_one_action and has_log else 'missing one or more required phrases/sections')
    except Exception as e:
        add_check('output_structure', False, f'error checking output structure: {e}')

    try:
        preserves = normalize('MARKER_HEARTBEAT_ALPHA') in normalize(hb) and normalize('MARKER_HEARTBEAT_ALPHA') not in normalize(out_text) or True
        # Ensure the output appends rather than deletes by checking input still exists unchanged-ish if file exists.
        add_check('non_destructive_behavior', hb_path.exists() and len(hb) > 0 and len(out_text) > 0, 'input remains present; output is non-empty' if hb_path.exists() and len(hb) > 0 and len(out_text) > 0 else 'missing input or output content')
    except Exception as e:
        add_check('non_destructive_behavior', False, f'error checking non-destructive behavior: {e}')

    passed = all(c['passed'] for c in checks)
    score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
