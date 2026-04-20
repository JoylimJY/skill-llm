import json
import os
from pathlib import Path


def load_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def normalize(text):
    try:
        return ''.join(ch.lower() for ch in text if ch.isalnum())
    except Exception:
        return ''


def main():
    workspace = Path(__import__('sys').argv[1])
    checks = []

    input_data, err = load_json_file(workspace / 'input.json')
    if err:
        checks.append({'name': 'input_present', 'passed': False, 'detail': f'Could not read input.json: {err}'})
    else:
        checks.append({'name': 'input_present', 'passed': True, 'detail': 'input.json readable'})

    out_data, out_err = load_json_file(workspace / 'output.json')
    if out_err:
        checks.append({'name': 'output_json_present', 'passed': False, 'detail': f'Could not read output.json: {out_err}'})
    else:
        ok = isinstance(out_data, dict)
        checks.append({'name': 'output_json_present', 'passed': ok, 'detail': 'output.json is a JSON object' if ok else 'output.json is not a JSON object'})

    summary_path = workspace / 'summary.txt'
    try:
        summary_text = summary_path.read_text(encoding='utf-8')
        checks.append({'name': 'summary_present', 'passed': True, 'detail': 'summary.txt readable'})
    except Exception as e:
        summary_text = ''
        checks.append({'name': 'summary_present', 'passed': False, 'detail': f'Could not read summary.txt: {e}'})

    expected_sum = None
    expected_group_max = {}
    marker_notes = []
    try:
        if isinstance(input_data, list):
            marker_records = [r for r in input_data if isinstance(r, dict) and str(r.get('id', '')).startswith('marker_')]
            expected_sum = sum(int(r.get('value', 0)) for r in marker_records)
            for r in input_data:
                if isinstance(r, dict):
                    g = str(r.get('group', ''))
                    try:
                        v = int(r.get('value', 0))
                    except Exception:
                        v = 0
                    if g not in expected_group_max or v > expected_group_max[g]:
                        expected_group_max[g] = v
            marker_notes = [str(r.get('note', '')) for r in marker_records]
    except Exception as e:
        checks.append({'name': 'input_processing', 'passed': False, 'detail': f'Failed to process input.json: {e}'})
    else:
        checks.append({'name': 'input_processing', 'passed': expected_sum is not None, 'detail': f'Computed expected aggregates' if expected_sum is not None else 'Could not compute expected aggregates'})

    output_ok = False
    try:
        if isinstance(out_data, dict) and expected_sum is not None:
            s_val = out_data.get('marker_value_sum')
            gmx = out_data.get('group_max')
            notes = out_data.get('marker_notes')
            c1 = isinstance(s_val, int) and s_val == expected_sum
            c2 = isinstance(gmx, dict) and all(str(g) in gmx and int(gmx[str(g)]) == int(v) for g, v in expected_group_max.items())
            c3 = isinstance(notes, list) and all(any(normalize(n) == normalize(en) for n in notes) for en in marker_notes)
            output_ok = c1 and c2 and c3
            checks.append({'name': 'output_values', 'passed': output_ok, 'detail': f'sum={s_val}, group_max_keys={list(gmx.keys()) if isinstance(gmx, dict) else None}'})
        else:
            checks.append({'name': 'output_values', 'passed': False, 'detail': 'Missing or malformed output data'})
    except Exception as e:
        checks.append({'name': 'output_values', 'passed': False, 'detail': f'Error validating output values: {e}'})

    summary_ok = False
    try:
        if summary_text:
            summary_ok = ('marker_alpha_91' in normalize(summary_text) and 'marker_beta_84' in normalize(summary_text) and 'marker_gamma_77' in normalize(summary_text))
        checks.append({'name': 'summary_mentions_markers', 'passed': summary_ok, 'detail': 'Summary includes all marker notes' if summary_ok else 'Summary missing one or more marker notes'})
    except Exception as e:
        checks.append({'name': 'summary_mentions_markers', 'passed': False, 'detail': f'Error checking summary: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed == total,
        'score': (passed / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
