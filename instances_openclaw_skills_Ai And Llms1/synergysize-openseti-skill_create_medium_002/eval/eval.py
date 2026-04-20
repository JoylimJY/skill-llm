import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return path.read_text(errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Check 1: required output file exists
    try:
        out = workspace / 'output.txt'
        if out.exists():
            checks.append({'name': 'output_exists', 'passed': True, 'detail': 'output.txt found'})
        else:
            checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.txt is missing'})
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output existence: {e}'})

    # Check 2: output contains human-readable summary and JSON line with candidate details
    try:
        if (workspace / 'output.txt').exists():
            text = (workspace / 'output.txt').read_text(errors='ignore')
            lower = text.lower()
            has_summary = any(k in lower for k in ['anomaly', 'candidate', 'signal', 'open seti', 'openseti'])
            has_jsonish = '{' in text and '}' in text and 'score' in lower
            passed = bool(has_summary and has_jsonish)
            detail = 'contains summary and JSON-like candidate line' if passed else 'missing summary keywords or JSON-like details'
            checks.append({'name': 'output_content', 'passed': passed, 'detail': detail})
        else:
            checks.append({'name': 'output_content', 'passed': False, 'detail': 'output.txt missing; cannot inspect content'})
    except Exception as e:
        checks.append({'name': 'output_content', 'passed': False, 'detail': f'error reading output.txt: {e}'})

    # Check 3: dataset marker file exists and contains expected marker
    try:
        manifest = workspace / 'dataset_manifest.json'
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text(errors='ignore'))
                marker = str(data.get('marker', '')).lower()
                passed = 'openseti_marker_7f3a'.replace('_', '') in marker.replace('_', '') or 'openseti_marker_7f3a' in marker
                checks.append({'name': 'manifest_marker', 'passed': passed, 'detail': f"marker={'present' if passed else 'not matched'}"})
            except Exception as e:
                checks.append({'name': 'manifest_marker', 'passed': False, 'detail': f'could not parse manifest: {e}'})
        else:
            checks.append({'name': 'manifest_marker', 'passed': False, 'detail': 'dataset_manifest.json is missing'})
    except Exception as e:
        checks.append({'name': 'manifest_marker', 'passed': False, 'detail': f'error checking manifest: {e}'})

    # Check 4: strongest candidate file marker in generated npz
    try:
        npz = workspace / 'observation_001.npz'
        if npz.exists():
            import numpy as np
            try:
                data = np.load(npz, allow_pickle=True)
                marker_arr = data.get('marker')
                marker_text = ''
                if marker_arr is not None:
                    try:
                        marker_text = str(marker_arr.tolist())
                    except Exception:
                        marker_text = str(marker_arr)
                passed = 'openseti_marker_7f3a' in marker_text.lower().replace('_', '') or 'openseti_marker_7f3a' in marker_text.lower()
                checks.append({'name': 'npz_marker', 'passed': passed, 'detail': f'marker text inspected: {marker_text[:80]}'})
            except Exception as e:
                checks.append({'name': 'npz_marker', 'passed': False, 'detail': f'could not inspect npz: {e}'})
        else:
            checks.append({'name': 'npz_marker', 'passed': False, 'detail': 'observation_001.npz is missing'})
    except Exception as e:
        checks.append({'name': 'npz_marker', 'passed': False, 'detail': f'error checking npz: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
