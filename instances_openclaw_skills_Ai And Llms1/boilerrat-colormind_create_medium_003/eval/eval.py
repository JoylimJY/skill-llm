import json
import os
import re
import sys
from pathlib import Path

checks = []

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, e

# Check 1: output.json exists and is valid JSON
try:
    output_path = workspace / 'output.json'
    if not output_path.exists():
        add_check('output_json_exists', False, 'output.json is missing')
        data = None
    else:
        try:
            data = json.loads(output_path.read_text(encoding='utf-8'))
            add_check('output_json_exists', True, 'output.json exists and parsed as JSON')
        except Exception as e:
            data = None
            add_check('output_json_exists', False, f'output.json could not be parsed: {e}')
except Exception as e:
    data = None
    add_check('output_json_exists', False, f'unexpected error: {e}')

# Check 2: output contains a palette-like structure
try:
    palette = None
    if isinstance(data, dict):
        for key in ['palette', 'colors', 'result']:
            if key in data:
                palette = data[key]
                break
        if palette is None and any(isinstance(v, list) for v in data.values()):
            palette = next(v for v in data.values() if isinstance(v, list))
    if isinstance(palette, list) and len(palette) == 5:
        add_check('palette_length', True, 'Found 5 palette entries')
    else:
        add_check('palette_length', False, f'Expected 5 palette entries, got {type(palette).__name__ if palette is not None else "none"}')
except Exception as e:
    add_check('palette_length', False, f'Error while checking palette: {e}')

# Check 3: summary.txt exists and mentions required items fuzzily
try:
    summary_path = workspace / 'summary.txt'
    if not summary_path.exists():
        add_check('summary_exists', False, 'summary.txt is missing')
        summary = ''
    else:
        summary = summary_path.read_text(encoding='utf-8')
        add_check('summary_exists', True, 'summary.txt exists')
except Exception as e:
    summary = ''
    add_check('summary_exists', False, f'Could not read summary.txt: {e}')

try:
    s = re.sub(r'\s+', ' ', summary.lower())
    has_ui = 'ui' in s
    has_brand = ('0,122,255' in s) or ('rgb(0,122,255)' in s.replace(' ', '')) or ('0 122 255' in s)
    has_hex_like = bool(re.search(r'#[0-9a-f]{6}', s))
    passed = has_ui and has_brand and has_hex_like
    detail = f'ui={has_ui}, brand_color={has_brand}, hex_present={has_hex_like}'
    add_check('summary_content', passed, detail)
except Exception as e:
    add_check('summary_content', False, f'Error while checking summary content: {e}')

# Check 4: input marker file exists and contains deterministic marker
try:
    marker_path = workspace / 'input_marker.json'
    if not marker_path.exists():
        add_check('marker_file', False, 'input_marker.json is missing')
    else:
        marker = json.loads(marker_path.read_text(encoding='utf-8'))
        token = str(marker.get('token', ''))
        brand = marker.get('brand_color_rgb', [])
        passed = 'COLORMIND_MARKER_2025_04' in token and brand == [0, 122, 255]
        add_check('marker_file', passed, f'token_present={"COLORMIND_MARKER_2025_04" in token}, brand_ok={brand == [0, 122, 255]}')
except Exception as e:
    add_check('marker_file', False, f'Could not parse input_marker.json: {e}')

# Score and final result
try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    passed = passed_count == total
    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception:
    # Absolute fallback: never crash
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))
