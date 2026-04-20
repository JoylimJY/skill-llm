import json
import os
from pathlib import Path


def safe_read_text(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read file: {e}'


def normalize(s: str) -> str:
    return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())


def get_nested_value(d, *keys):
    """Try multiple possible key names and return first match"""
    for key in keys:
        if key in d:
            return d[key]
    return None


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)
    out = ws / 'output.json'

    # Check 1: output exists
    try:
        exists = out.exists()
        checks.append({
            'name': 'output file exists',
            'passed': bool(exists),
            'detail': 'output.json found' if exists else 'output.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'output file exists', 'passed': False, 'detail': f'error checking existence: {e}'})

    # Check 2: parse JSON and validate keys/content
    parsed = None
    try:
        if out.exists():
            text = out.read_text(encoding='utf-8')
            parsed = json.loads(text)
            
            # Flexible key matching for marker
            marker_val = get_nested_value(parsed, 'marker', 'detected_marker', 'marker_text', 'found_marker')
            has_marker = False
            if marker_val:
                marker_str = normalize(str(marker_val))
                has_marker = 'aikagrya rv contraction' in marker_str or 'aikagryarvcontraction' in marker_str
            
            # Flexible key matching for file count - added 'num_input_files_processed'
            file_count = get_nested_value(parsed, 'files_processed', 'number_of_input_files_processed', 'file_count', 'num_files', 'num_input_files_processed')
            
            # Flexible key matching for conclusion
            conclusion = get_nested_value(parsed, 'conclusion', 'summary', 'result', 'conclusion_text')
            conclusion_str = normalize(str(conclusion)) if conclusion else ''
            
            passed = bool(has_marker and isinstance(file_count, int) and file_count >= 2 and ('found' in conclusion_str or 'detected' in conclusion_str))
            checks.append({
                'name': 'output content',
                'passed': passed,
                'detail': 'marker, file count, and conclusion look correct' if passed else f'invalid fields: {parsed}'
            })
        else:
            checks.append({'name': 'output content', 'passed': False, 'detail': 'cannot parse because output.json is missing'})
    except Exception as e:
        checks.append({'name': 'output content', 'passed': False, 'detail': f'failed to parse output.json: {e}'})

    # Check 3: verify input marker files exist and contain marker
    try:
        expected_files = [ws / 'data' / 'input_a.txt', ws / 'data' / 'input_b.txt', ws / 'data' / 'config.json']
        found_all = True
        details = []
        for p in expected_files:
            try:
                txt = p.read_text(encoding='utf-8')
                ok = 'AIKAGRYA_RV_CONTRACTION' in txt
                found_all = found_all and ok
                status = 'ok' if ok else 'missing marker'
                details.append(f'{p.name}: {status}')
            except Exception as e:
                found_all = False
                details.append(f'{p.name}: {e}')
        checks.append({
            'name': 'input markers',
            'passed': found_all,
            'detail': '; '.join(details)
        })
    except Exception as e:
        checks.append({'name': 'input markers', 'passed': False, 'detail': f'error validating inputs: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed == total,
        'score': (passed / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    import sys
    main(sys.argv[1])