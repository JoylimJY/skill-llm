import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    checks = []

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        out_path = workspace / 'cleaned_email.txt'
        if not out_path.exists():
            add_check('output_exists', False, 'cleaned_email.txt is missing')
            content = ''
        else:
            content = out_path.read_text(encoding='utf-8', errors='replace')
            add_check('output_exists', True, 'cleaned_email.txt found')
    except Exception as e:
        add_check('output_exists', False, f'Could not read cleaned_email.txt: {e}')
        content = ''

    try:
        c = content
        banned = [
            'at the end of the day',
            'it is important to note',
            'first,',
            'secondly,',
            'finally,',
            'i hope this helps',
            'let me know if you have any questions'
        ]
        present = [p for p in banned if p in c.lower()]
        add_check('removed_ai_phrases', len(present) == 0, 'Remaining phrases: ' + (', '.join(present) if present else 'none'))
    except Exception as e:
        add_check('removed_ai_phrases', False, f'Phrase check failed: {e}')

    try:
        marker_ok = False
        input_path = workspace / 'input_email.txt'
        if input_path.exists() and out_path.exists():
            original = input_path.read_text(encoding='utf-8', errors='replace')
            out_norm = norm(content)
            # Check for key concepts: project and delay appearing in output
            marker_ok = 'project' in out_norm and 'delay' in out_norm
        add_check('preserves_core_message', marker_ok, 'Core message about project delay should remain recognizable')
    except Exception as e:
        add_check('preserves_core_message', False, f'Core message check failed: {e}')

    try:
        length_ok = len(content.strip()) > 0 and len(content) < 1000
        add_check('reasonable_length', length_ok, f'Output length: {len(content)}')
    except Exception as e:
        add_check('reasonable_length', False, f'Length check failed: {e}')

    passed = all(ch['passed'] for ch in checks)
    score = sum(1 for ch in checks if ch['passed']) / len(checks) if checks else 0.0
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main()