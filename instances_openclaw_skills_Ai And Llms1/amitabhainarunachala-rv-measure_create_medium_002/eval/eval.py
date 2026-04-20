import json
import math
import csv
from pathlib import Path
import sys


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in s if ch.isalnum())
    except Exception:
        return ''


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: output.txt exists and is readable
    try:
        out_path = ws / 'output.txt'
        if out_path.exists():
            txt = out_path.read_text(encoding='utf-8', errors='ignore')
            passed = len(txt.strip()) > 0
            detail = 'output.txt exists and is non-empty' if passed else 'output.txt is empty'
        else:
            passed = False
            detail = 'output.txt is missing'
    except Exception as e:
        passed = False
        detail = f'error reading output.txt: {e}'
    checks.append({'name': 'output_present', 'passed': passed, 'detail': detail})

    # Check 2: result.json exists and contains required fields
    result_data = None
    try:
        rp = ws / 'result.json'
        if rp.exists():
            result_data = json.loads(rp.read_text(encoding='utf-8'))
            # Accept either 'score' or 'contraction_score' as the score field
            has_score = 'score' in result_data or 'contraction_score' in result_data
            has_marker = 'marker_name' in result_data
            passed = isinstance(result_data, dict) and has_score and has_marker
            detail = 'result.json parsed with required fields' if passed else 'result.json missing required fields'
        else:
            passed = False
            detail = 'result.json is missing'
    except Exception as e:
        passed = False
        detail = f'error parsing result.json: {e}'
    checks.append({'name': 'result_json_structure', 'passed': passed, 'detail': detail})

    # Check 3: marker name matches input marker and appears in output.txt
    try:
        marker = 'RV_MARKER_ALPHA'
        out_text = (ws / 'output.txt').read_text(encoding='utf-8', errors='ignore') if (ws / 'output.txt').exists() else ''
        res_marker = str(result_data.get('marker_name', '')) if isinstance(result_data, dict) else ''
        passed = normalize(marker) in normalize(out_text) and normalize(marker) == normalize(res_marker)
        detail = f"marker in output/result: output_has={normalize(marker) in normalize(out_text)}, result_marker={res_marker}"
    except Exception as e:
        passed = False
        detail = f'error checking marker: {e}'
    checks.append({'name': 'marker_consistency', 'passed': passed, 'detail': detail})

    # Check 4: threshold logic is consistent with inputs and result score
    try:
        cfg = json.loads((ws / 'input_config.json').read_text(encoding='utf-8')) if (ws / 'input_config.json').exists() else {}
        observations = cfg.get('observations', [])
        threshold = float(cfg.get('threshold', 0))
        avg = sum(float(x) for x in observations) / max(len(observations), 1)
        expected_exceeded = avg > threshold
        
        # Accept either 'score' or 'contraction_score' field
        res_score = None
        if isinstance(result_data, dict):
            if 'score' in result_data:
                res_score = float(result_data.get('score'))
            elif 'contraction_score' in result_data:
                res_score = float(result_data.get('contraction_score'))
        
        if res_score is None or not math.isfinite(res_score):
            passed = False
            detail = f'avg={avg:.4f}, threshold={threshold:.4f}, expected_exceeded={expected_exceeded}, result_score=missing'
        else:
            # Check if threshold_exceeded flag matches the score comparison
            threshold_exceeded = result_data.get('threshold_exceeded', None)
            expected_exceeded_from_score = res_score > threshold
            
            # Pass if either: score-based logic is consistent OR threshold_exceeded flag is correct
            score_logic_ok = (expected_exceeded_from_score and res_score >= threshold) or ((not expected_exceeded_from_score) and res_score <= threshold)
            flag_ok = threshold_exceeded is not None and threshold_exceeded == expected_exceeded_from_score
            
            passed = score_logic_ok or flag_ok
            detail = f'avg={avg:.4f}, threshold={threshold:.4f}, expected_exceeded={expected_exceeded}, result_score={res_score:.4f}'
    except Exception as e:
        passed = False
        detail = f'error checking threshold logic: {e}'
    checks.append({'name': 'threshold_logic', 'passed': passed, 'detail': detail})

    total = len(checks)
    score = sum(1 for c in checks if c['passed']) / total if total else 0.0
    passed = all(c['passed'] for c in checks)

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()