from pathlib import Path
import json
import re
import sys


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text):
    text = text or ''
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out = workspace / 'output.txt'
    inputs = workspace / 'inputs' / 'benchmark.json'
    notes = workspace / 'inputs' / 'notes.txt'

    try:
        if out.exists():
            output_text = out.read_text(encoding='utf-8')
            checks.append({'name': 'output_exists', 'passed': True, 'detail': 'output.txt found'})
        else:
            output_text = ''
            checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.txt is missing'})
    except Exception as e:
        output_text = ''
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'Could not read output.txt: {e}'})

    try:
        data = json.loads(inputs.read_text(encoding='utf-8')) if inputs.exists() else {}
        target = normalize(data.get('target', ''))
        bottleneck = normalize(data.get('baseline_bottleneck', ''))
        change = normalize(data.get('optimization_change', ''))
        benefit = normalize(data.get('expected_benefit', ''))
        ok = all([target, bottleneck, change, benefit])
        checks.append({'name': 'input_marker_parse', 'passed': ok, 'detail': 'Parsed benchmark.json markers' if ok else 'Missing or malformed marker data'})
    except Exception as e:
        target = bottleneck = change = benefit = ''
        checks.append({'name': 'input_marker_parse', 'passed': False, 'detail': f'Could not parse benchmark.json: {e}'})

    try:
        notes_text = notes.read_text(encoding='utf-8') if notes.exists() else ''
        norm_out = normalize(output_text)
        required = [
            ('target mention', target),
            ('bottleneck mention', 'sequential coordination'),
            ('change mention', 'parallel'),
            ('benefit mention', 'latency')
        ]
        passed = True
        details = []
        for name, needle in required:
            if needle and needle in norm_out:
                details.append(f'{name}: ok')
            else:
                passed = False
                details.append(f'{name}: missing')
        checks.append({'name': 'content_match', 'passed': passed, 'detail': '; '.join(details)})
    except Exception as e:
        checks.append({'name': 'content_match', 'passed': False, 'detail': f'Could not inspect output content: {e}'})

    try:
        lines = [ln for ln in output_text.splitlines() if ln.strip()]
        passed = len(lines) <= 8 and len(output_text.strip()) > 0
        checks.append({'name': 'length_constraint', 'passed': passed, 'detail': f'{len(lines)} non-empty lines found' if output_text else 'output is empty'})
    except Exception as e:
        checks.append({'name': 'length_constraint', 'passed': False, 'detail': f'Could not evaluate length: {e}'})

    score = sum(1 for c in checks if c['passed']) / max(len(checks), 1)
    result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
