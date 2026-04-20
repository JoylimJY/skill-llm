import json
import os
import sys
from pathlib import Path


def normalize(text):
    try:
        import re
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^a-z0-9]+', '', text)
        return text
    except Exception:
        return ''


def read_text_file(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: input PDF exists
    try:
        pdf_path = workspace / 'announcement_draft.pdf'
        exists = pdf_path.exists()
        checks.append({
            'name': 'input_pdf_exists',
            'passed': bool(exists),
            'detail': 'announcement_draft.pdf found' if exists else 'announcement_draft.pdf is missing'
        })
    except Exception as e:
        checks.append({'name': 'input_pdf_exists', 'passed': False, 'detail': f'Error checking PDF existence: {e}'})

    # Check 2: output file exists
    try:
        out_path = workspace / 'output.txt'
        exists = out_path.exists()
        checks.append({
            'name': 'output_exists',
            'passed': bool(exists),
            'detail': 'output.txt found' if exists else 'output.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'Error checking output existence: {e}'})

    # Check 3: output contains a polished reference to the marker phrase or the draft topic
    try:
        out_path = workspace / 'output.txt'
        if out_path.exists():
            content, err = read_text_file(out_path)
            if content is None:
                checks.append({'name': 'output_readable', 'passed': False, 'detail': f'Could not read output.txt: {err}'})
            else:
                n = normalize(content)
                marker_ok = ('orangeowl2049' in n) or ('internalannouncement' in n) or ('announcementdraft' in n)
                checks.append({
                    'name': 'output_mentions_topic',
                    'passed': bool(marker_ok),
                    'detail': 'Output appears related to the announcement draft and marker phrase' if marker_ok else 'Output does not appear related to the provided draft'
                })
        else:
            checks.append({'name': 'output_readable', 'passed': False, 'detail': 'output.txt missing, cannot read'})
    except Exception as e:
        checks.append({'name': 'output_mentions_topic', 'passed': False, 'detail': f'Error reading output: {e}'})

    # Check 4: output is not empty and has at least 2 lines
    try:
        out_path = workspace / 'output.txt'
        if out_path.exists():
            content, err = read_text_file(out_path)
            if content is None:
                checks.append({'name': 'output_nonempty_multiline', 'passed': False, 'detail': f'Could not read output.txt: {err}'})
            else:
                lines = [ln for ln in content.splitlines() if ln.strip()]
                ok = len(lines) >= 2
                checks.append({
                    'name': 'output_nonempty_multiline',
                    'passed': bool(ok),
                    'detail': f'Output has {len(lines)} non-empty line(s)' if ok else 'Output should contain at least 2 non-empty lines'
                })
        else:
            checks.append({'name': 'output_nonempty_multiline', 'passed': False, 'detail': 'output.txt missing'})
    except Exception as e:
        checks.append({'name': 'output_nonempty_multiline', 'passed': False, 'detail': f'Error checking output format: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks) if checks else 1
    score = passed_count / total
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
