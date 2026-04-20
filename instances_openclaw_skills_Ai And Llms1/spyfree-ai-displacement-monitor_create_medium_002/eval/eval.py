import json, os, re, sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    out = workspace / 'output.json'
    if not out.exists():
        add_check('output_exists', False, 'output.json is missing')
    else:
        add_check('output_exists', True, 'output.json exists')
except Exception as e:
    add_check('output_exists', False, f'error checking file: {e}')

obj = None
try:
    if (workspace / 'output.json').exists():
        obj = json.loads((workspace / 'output.json').read_text(encoding='utf-8'))
        add_check('json_parse', True, 'output.json parsed successfully')
    else:
        add_check('json_parse', False, 'skipped because file missing')
except Exception as e:
    add_check('json_parse', False, f'failed to parse JSON: {e}')

try:
    expected_keys = {'asOf', 'signals', 'composite', 'confidence', 'gaps', 'notes'}
    if isinstance(obj, dict):
        keys_ok = expected_keys.issubset(set(obj.keys())) and len(obj.keys()) == len(expected_keys)
        add_check('schema_keys', keys_ok, f'keys found: {sorted(obj.keys())}')
    else:
        add_check('schema_keys', False, 'output is not a JSON object')
except Exception as e:
    add_check('schema_keys', False, f'error validating schema: {e}')

try:
    sigs = obj.get('signals', []) if isinstance(obj, dict) else []
    ok = isinstance(sigs, list) and len(sigs) == 10
    add_check('ten_signals', ok, f'signal count={len(sigs) if isinstance(sigs, list) else "n/a"}')
except Exception as e:
    add_check('ten_signals', False, f'error checking signals: {e}')

try:
    comp = str(obj.get('composite', '')).strip().upper() if isinstance(obj, dict) else ''
    allowed = {'GREEN', 'YELLOW', 'ORANGE', 'RED'}
    ok = comp in allowed
    add_check('composite_valid', ok, f'composite={comp or "missing"}')
except Exception as e:
    add_check('composite_valid', False, f'error checking composite: {e}')

try:
    gaps = obj.get('gaps', []) if isinstance(obj, dict) else []
    ok = isinstance(gaps, list) and len(gaps) >= 1
    detail = f'gaps={len(gaps) if isinstance(gaps, list) else "n/a"}'
    add_check('gaps_present', ok, detail)
except Exception as e:
    add_check('gaps_present', False, f'error checking gaps: {e}')

try:
    # fuzzy verification of marker presence in either notes or gaps or signal ids/values
    marker_fragments = ['displacement', 'capex', 'bottleneck']
    text = json.dumps(obj).lower() if obj is not None else ''
    ok = all(frag in text for frag in marker_fragments)
    add_check('content_alignment', ok, 'expects discussion of displacement, capex, and bottlenecks')
except Exception as e:
    add_check('content_alignment', False, f'error checking content alignment: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
