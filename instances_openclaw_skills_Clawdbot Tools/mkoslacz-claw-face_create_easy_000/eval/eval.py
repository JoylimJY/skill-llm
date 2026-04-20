import json
import re
from pathlib import Path
import sys


def normalize(text):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    except Exception:
        return ''


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    try:
        input_path = workspace / 'input.txt'
        if input_path.exists():
            content = input_path.read_text(encoding='utf-8', errors='replace')
            passed = 'clawface_marker_7a3d' in content.lower()
            checks.append({'name': 'input marker present', 'passed': passed, 'detail': 'Marker found' if passed else 'Marker missing'})
        else:
            checks.append({'name': 'input marker present', 'passed': False, 'detail': 'input.txt is missing'})
    except Exception as e:
        checks.append({'name': 'input marker present', 'passed': False, 'detail': f'Error reading input.txt: {e}'})

    try:
        output_path = workspace / 'output.txt'
        if output_path.exists():
            content = output_path.read_text(encoding='utf-8', errors='replace')
            norm = normalize(content)
            passed = ('friendly' in norm or 'happy' in norm or 'neutral' in norm) and ('avatar' in norm or 'clawface' in norm)
            checks.append({'name': 'output summary', 'passed': passed, 'detail': 'Output content looks relevant' if passed else 'Output content is missing expected terms'})
        else:
            checks.append({'name': 'output summary', 'passed': False, 'detail': 'output.txt is missing'})
    except Exception as e:
        checks.append({'name': 'output summary', 'passed': False, 'detail': f'Error reading output.txt: {e}'})

    try:
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / len(checks) if checks else 0.0
        result = {'passed': passed_count == len(checks) and len(checks) > 0, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()