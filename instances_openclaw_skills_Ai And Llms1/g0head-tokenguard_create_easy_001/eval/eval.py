import json
import os
from pathlib import Path


def safe_read_text(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Check 1: export file exists
    export_path = workspace / 'tokenguard_export.json'
    try:
        exists = export_path.exists()
        checks.append({
            'name': 'export_file_exists',
            'passed': bool(exists),
            'detail': 'Found tokenguard_export.json' if exists else 'tokenguard_export.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'export_file_exists', 'passed': False, 'detail': f'Error checking file existence: {e}'})

    # Check 2: JSON content has limit near 25 and includes the log description
    try:
        if export_path.exists():
            data = json.loads(export_path.read_text(encoding='utf-8'))
            text_blob = json.dumps(data).lower()
            limit_val = None
            spent_val = None
            try:
                if isinstance(data, dict):
                    for key in data.keys():
                        kl = str(key).lower()
                        if 'limit' in kl:
                            limit_val = data[key]
                        if 'spent' in kl:
                            spent_val = data[key]
            except Exception:
                pass

            limit_ok = False
            try:
                if isinstance(limit_val, (int, float)):
                    limit_ok = abs(float(limit_val) - 25.0) < 0.01 or (24.5 <= float(limit_val) <= 25.5)
                else:
                    limit_ok = '25' in text_blob
            except Exception:
                limit_ok = '25' in text_blob

            desc_ok = 'demo classification call' in text_blob
            amount_ok = '4.75' in text_blob or '4,75' in text_blob
            checks.append({
                'name': 'export_contains_expected_budget_and_log',
                'passed': bool(limit_ok and desc_ok and amount_ok),
                'detail': f'limit_ok={limit_ok}, desc_ok={desc_ok}, amount_ok={amount_ok}, spent={spent_val}'
            })
        else:
            checks.append({
                'name': 'export_contains_expected_budget_and_log',
                'passed': False,
                'detail': 'Cannot inspect export because file is missing'
            })
    except Exception as e:
        checks.append({
            'name': 'export_contains_expected_budget_and_log',
            'passed': False,
            'detail': f'Failed to parse export JSON: {e}'
        })

    # Check 3: input marker exists to verify task context
    try:
        marker_path = workspace / 'input_manifest.json'
        if marker_path.exists():
            txt = marker_path.read_text(encoding='utf-8').lower()
            marker_ok = 'known_marker_tokenguard_input' in txt and 'tg-demo-001' in txt
            checks.append({
                'name': 'input_marker_present',
                'passed': bool(marker_ok),
                'detail': 'Marker content verified' if marker_ok else 'Marker content missing or altered'
            })
        else:
            checks.append({
                'name': 'input_marker_present',
                'passed': False,
                'detail': 'input_manifest.json is missing'
            })
    except Exception as e:
        checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'Error reading marker file: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = passed / total if total else 0.0
    result = {
        'passed': passed == total,
        'score': score,
        'checks': checks
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
