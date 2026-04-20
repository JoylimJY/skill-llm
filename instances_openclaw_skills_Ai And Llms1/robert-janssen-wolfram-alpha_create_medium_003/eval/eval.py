import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text):
    return re.sub(r'[^a-z0-9]+', '', (text or '').lower())


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: output.txt exists and contains marker phrase
    try:
        output_path = workspace / 'output.txt'
        if not output_path.exists():
            checks.append({
                'name': 'output_exists_and_contains_marker',
                'passed': False,
                'detail': 'output.txt is missing'
            })
        else:
            text = output_path.read_text(encoding='utf-8', errors='replace')
            marker_ok = 'wolfram_verification_token_7f3a' in normalize(text)
            checks.append({
                'name': 'output_exists_and_contains_marker',
                'passed': marker_ok,
                'detail': 'marker found' if marker_ok else 'marker not found in output.txt'
            })
    except Exception as e:
        checks.append({'name': 'output_exists_and_contains_marker', 'passed': False, 'detail': f'error reading output.txt: {e}'})

    # Check 2: summary.json exists and has expected structure
    try:
        summary_path = workspace / 'summary.json'
        if not summary_path.exists():
            checks.append({
                'name': 'summary_json_structure',
                'passed': False,
                'detail': 'summary.json is missing'
            })
        else:
            try:
                data = json.loads(summary_path.read_text(encoding='utf-8'))
                ok = isinstance(data, dict) and 'main_findings' in data and 'computed_values' in data
                checks.append({
                    'name': 'summary_json_structure',
                    'passed': ok,
                    'detail': 'required keys present' if ok else 'missing required keys'
                })
            except Exception as e:
                checks.append({
                    'name': 'summary_json_structure',
                    'passed': False,
                    'detail': f'could not parse summary.json: {e}'
                })
    except Exception as e:
        checks.append({'name': 'summary_json_structure', 'passed': False, 'detail': f'error checking summary.json: {e}'})

    # Check 3: report mentions at least two numeric results in a forgiving way
    try:
        output_path = workspace / 'output.txt'
        if not output_path.exists():
            checks.append({
                'name': 'output_mentions_two_quantities',
                'passed': False,
                'detail': 'output.txt is missing'
            })
        else:
            text = output_path.read_text(encoding='utf-8', errors='replace')
            nums = re.findall(r'\b\d+(?:\.\d+)?\b', text)
            ok = len(nums) >= 2
            checks.append({
                'name': 'output_mentions_two_quantities',
                'passed': ok,
                'detail': f'found {len(nums)} numeric values' if ok else 'fewer than two numeric values found'
            })
    except Exception as e:
        checks.append({'name': 'output_mentions_two_quantities', 'passed': False, 'detail': f'error checking numeric values: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks) if checks else 1
    result = {
        'passed': passed_count == total,
        'score': passed_count / total,
        'checks': checks,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
