import json
import os
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)
    out = ws / 'output.txt'

    try:
        if out.exists():
            text = out.read_text(encoding='utf-8', errors='replace')
            normalized = ''.join(ch.lower() for ch in text)
            passed = 'rv-contraction-ok' in normalized
            checks.append({'name': 'output_exists_and_contains_marker', 'passed': passed, 'detail': 'marker found' if passed else 'marker missing'})
        else:
            checks.append({'name': 'output_exists_and_contains_marker', 'passed': False, 'detail': 'output.txt missing'})
    except Exception as e:
        checks.append({'name': 'output_exists_and_contains_marker', 'passed': False, 'detail': f'error reading output.txt: {e}'})

    try:
        sample = ws / 'data' / 'sample.json'
        if sample.exists():
            data = json.loads(sample.read_text(encoding='utf-8'))
            meas = data.get('measurements', [])
            avg = sum(meas) / max(len(meas), 1)
            ok = abs(avg - 0.2) < 0.05
            checks.append({'name': 'input_marker_and_value_check', 'passed': ok, 'detail': f'avg={avg:.3f}' if ok else f'unexpected avg={avg:.3f}'})
        else:
            checks.append({'name': 'input_marker_and_value_check', 'passed': False, 'detail': 'sample.json missing'})
    except Exception as e:
        checks.append({'name': 'input_marker_and_value_check', 'passed': False, 'detail': f'error parsing sample.json: {e}'})

    try:
        passed_count = sum(1 for c in checks if c['passed'])
        score = passed_count / len(checks) if checks else 0.0
        passed = passed_count == len(checks) and len(checks) > 0
    except Exception:
        passed = False
        score = 0.0

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
