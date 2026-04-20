import json
import re
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s):
    if s is None:
        return ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s


def main():
    import sys
    checks = []
    workspace = Path(sys.argv[1])

    # Check 1: final output file exists
    try:
        output_file = workspace / 'output' / 'final_report.txt'
        exists = output_file.exists()
        checks.append({
            'name': 'final report exists',
            'passed': exists,
            'detail': 'output/final_report.txt found' if exists else 'output/final_report.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'final report exists', 'passed': False, 'detail': f'error while checking file existence: {e}'})

    # Check 2: output contains threshold summary
    try:
        text, err = safe_read_text(workspace / 'output' / 'final_report.txt')
        if text is None:
            checks.append({'name': 'threshold summary present', 'passed': False, 'detail': f'could not read final_report.txt: {err}'})
        else:
            n = normalize(text)
            ok = all(token in n for token in ['75', '90', '95']) and ('threshold' in n or 'warning' in n)
            checks.append({
                'name': 'threshold summary present',
                'passed': ok,
                'detail': 'found threshold-related content' if ok else 'missing one or more threshold indicators'
            })
    except Exception as e:
        checks.append({'name': 'threshold summary present', 'passed': False, 'detail': f'error while inspecting report: {e}'})

    # Check 3: markers from inputs are preserved or referenced
    try:
        text, err = safe_read_text(workspace / 'output' / 'final_report.txt')
        if text is None:
            checks.append({'name': 'markers referenced', 'passed': False, 'detail': f'could not read final_report.txt: {err}'})
        else:
            n = normalize(text)
            markers = ['MARKER_ALPHA', 'MARKER_BETA']
            found = sum(1 for m in markers if normalize(m) in n)
            ok = found >= 2
            checks.append({
                'name': 'markers referenced',
                'passed': ok,
                'detail': f'found {found}/{len(markers)} required markers'
            })
    except Exception as e:
        checks.append({'name': 'markers referenced', 'passed': False, 'detail': f'error while checking markers: {e}'})

    # Check 4: report mentions the computed remaining amount in a forgiving way
    try:
        text, err = safe_read_text(workspace / 'output' / 'final_report.txt')
        if text is None:
            checks.append({'name': 'remaining amount mentioned', 'passed': False, 'detail': f'could not read final_report.txt: {err}'})
        else:
            n = normalize(text)
            ok = ('44000' in n) or ('44k' in n) or ('remaining' in n and 'tokens' in n)
            checks.append({
                'name': 'remaining amount mentioned',
                'passed': ok,
                'detail': 'remaining token amount appears to be included' if ok else 'remaining amount not clearly present'
            })
    except Exception as e:
        checks.append({'name': 'remaining amount mentioned', 'passed': False, 'detail': f'error while checking remaining amount: {e}'})

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    result = {
        'passed': passed_count == total,
        'score': passed_count / total,
        'checks': checks,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
