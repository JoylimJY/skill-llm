import json
import os
import re
import sys
from pathlib import Path

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    workspace = Path(sys.argv[1])
except Exception as e:
    workspace = Path('.')
    add_check('workspace_arg', False, f'Could not read workspace argument: {e}')

output_path = workspace / 'output.txt'
try:
    if not output_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
        content = ''
    else:
        content = output_path.read_text(encoding='utf-8', errors='replace')
        add_check('output_exists', True, 'output.txt found')
except Exception as e:
    content = ''
    add_check('output_exists', False, f'Could not read output.txt: {e}')

try:
    normalized = re.sub(r'[^a-z0-9]+', ' ', content.lower()).strip()
    has_marker = 'ocr target alpha' in normalized or 'ocr_target_alpha' in content.lower()
    add_check('marker_text', has_marker, 'Found marker text OCR_TARGET_ALPHA' if has_marker else 'Marker text missing or altered')
except Exception as e:
    add_check('marker_text', False, f'Error while checking marker text: {e}')

try:
    coord_match = re.search(r'(?i)\b(?:x\s*[:=]\s*)?(\d{1,4}).{0,20}?(?:y\s*[:=]\s*)?(\d{1,4})\b', content)
    if coord_match:
        x = int(coord_match.group(1))
        y = int(coord_match.group(2))
        ok = abs(x - 184) <= 5 and abs(y - 72) <= 5
        add_check('coordinates', ok, f'Parsed coordinates x={x}, y={y}' if ok else f'Coordinates off target: x={x}, y={y}')
    else:
        add_check('coordinates', False, 'No coordinate-like pattern found')
except Exception as e:
    add_check('coordinates', False, f'Error while checking coordinates: {e}')

try:
    score = sum(1 for c in checks if c['passed']) / max(len(checks), 1)
    passed = all(c['passed'] for c in checks)
    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    fallback = {"passed": False, "score": 0.0, "checks": checks + [{"name": "finalize", "passed": False, "detail": f'Failed to finalize JSON: {e}'}]}
    print(json.dumps(fallback, ensure_ascii=False))