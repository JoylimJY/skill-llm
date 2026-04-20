import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f"read error: {e}"

# Check 1: input files exist and contain marker
try:
    p = workspace / 'input.json'
    if p.exists():
        text, err = safe_read(p)
        if text is None:
            add_check('input_json_exists', False, err)
        else:
            ok = 'AI_DISPLACEMENT_BENCHMARK_MARKER_7F3C' in text
            add_check('input_json_exists', ok, 'marker found' if ok else 'marker missing')
    else:
        add_check('input_json_exists', False, 'input.json missing')
except Exception as e:
    add_check('input_json_exists', False, f'exception: {e}')

# Check 2: reference thresholds file exists and is valid JSON with 10 indicators
try:
    p = workspace / 'references' / 'thresholds.example.json'
    if p.exists():
        text, err = safe_read(p)
        if text is None:
            add_check('thresholds_file', False, err)
        else:
            try:
                data = json.loads(text)
                inds = data.get('indicators', []) if isinstance(data, dict) else []
                ok = len(inds) == 10 and all(isinstance(x, dict) and 'id' in x for x in inds)
                add_check('thresholds_file', ok, f'indicator_count={len(inds)}')
            except Exception as e:
                add_check('thresholds_file', False, f'json parse error: {e}')
    else:
        add_check('thresholds_file', False, 'thresholds.example.json missing')
except Exception as e:
    add_check('thresholds_file', False, f'exception: {e}')

# Check 3: user generated a result file
expected_outputs = ['output.json']
existing = [f for f in expected_outputs if (workspace / f).exists()]
add_check('output_file_exists', len(existing) == len(expected_outputs), f'found={existing}')

# Check 4: validate output schema and content if present
try:
    out_path = workspace / 'output.json'
    if not out_path.exists():
        add_check('output_schema', False, 'output.json missing')
    else:
        text, err = safe_read(out_path)
        if text is None:
            add_check('output_schema', False, err)
        else:
            try:
                obj = json.loads(text)
                top_ok = isinstance(obj, dict)
                keys_ok = top_ok and set(obj.keys()) == {'asOf', 'signals', 'composite', 'confidence', 'gaps', 'notes'}
                signals_ok = False
                if keys_ok and isinstance(obj.get('signals'), list):
                    signals_ok = len(obj['signals']) == 10
                    ids = [s.get('id') for s in obj['signals'] if isinstance(s, dict)]
                    signals_ok = signals_ok and len(set(ids)) >= 8
                composite_ok = keys_ok and isinstance(obj.get('composite'), str) and obj['composite'].upper() in {'GREEN', 'YELLOW', 'ORANGE', 'RED'}
                confidence_ok = keys_ok and isinstance(obj.get('confidence'), str) and obj['confidence'].lower() in {'low', 'medium', 'high'}
                gaps_ok = keys_ok and isinstance(obj.get('gaps'), list)
                notes_ok = keys_ok and isinstance(obj.get('notes'), list) and len(obj['notes']) >= 1
                all_ok = all([top_ok, keys_ok, signals_ok, composite_ok, confidence_ok, gaps_ok, notes_ok])
                detail = f"keys_ok={keys_ok}, signals={len(obj.get('signals', [])) if top_ok else 'n/a'}, composite={obj.get('composite') if top_ok else 'n/a'}"
                add_check('output_schema', all_ok, detail)
            except Exception as e:
                add_check('output_schema', False, f'json parse error: {e}')
except Exception as e:
    add_check('output_schema', False, f'exception: {e}')

# Check 5: fuzzy marker propagation in output or notes
try:
    out_path = workspace / 'output.json'
    if out_path.exists():
        text, err = safe_read(out_path)
        if text is None:
            add_check('marker_propagation', False, err)
        else:
            norm = re.sub(r'[^a-z0-9]+', '', text.lower())
            marker_norm = re.sub(r'[^a-z0-9]+', '', 'AI_DISPLACEMENT_BENCHMARK_MARKER_7F3C'.lower())
            ok = marker_norm in norm
            add_check('marker_propagation', ok, 'marker present' if ok else 'marker absent')
    else:
        add_check('marker_propagation', False, 'output.json missing')
except Exception as e:
    add_check('marker_propagation', False, f'exception: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / max(len(checks), 1)
passed = passed_count == len(checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
