from pathlib import Path
import json, re, math, sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r'[^\w\u4e00-\u9fff]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    except Exception:
        return ''


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

# Check 1: output file exists
out_path = workspace / 'screen_text_map.json'
try:
    exists = out_path.exists()
    add_check('output_exists', exists, 'screen_text_map.json found' if exists else 'screen_text_map.json is missing')
except Exception as e:
    add_check('output_exists', False, f'exception while checking existence: {e}')

# Check 2: valid JSON structure (accept both object and array)
parsed = None
try:
    if out_path.exists():
        parsed = json.loads(out_path.read_text(encoding='utf-8'))
        ok = isinstance(parsed, (dict, list))
        add_check('json_is_object', ok, 'valid JSON structure' if ok else 'invalid JSON structure')
    else:
        add_check('json_is_object', False, 'file missing, cannot parse')
except Exception as e:
    add_check('json_is_object', False, f'failed to parse JSON: {e}')

# Helper to extract items from parsed JSON
def extract_items(parsed):
    items = []
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        # tolerate several likely shapes
        for key in ['items', 'results', 'texts', 'data', 'entries', 'text_items']:
            if isinstance(parsed.get(key), list):
                items = parsed.get(key)
                break
        if not items:
            for v in parsed.values():
                if isinstance(v, list):
                    items = v
                    break
    return items

# Check 3: has entries with required marker texts (fuzzy)
expected_texts = ['confirm delete', 'report_q4_final.pdf', 'cannot be undone', '取消', 'confirm', 'zx-2048']
found_count = 0
try:
    items = extract_items(parsed)
    for needle in expected_texts:
        hit = False
        for item in items if isinstance(items, list) else []:
            try:
                txt = ''
                if isinstance(item, str):
                    txt = item
                elif isinstance(item, dict):
                    for k in ['text', 'label', 'content', 'value', 'name', 'snippet']:
                        if k in item and isinstance(item[k], str):
                            txt = item[k]
                            break
                if txt:
                    # Use case-insensitive fuzzy matching
                    needle_norm = normalize(needle)
                    txt_norm = normalize(txt)
                    if needle_norm in txt_norm or txt_norm in needle_norm:
                        hit = True
                        break
            except Exception:
                continue
        if hit:
            found_count += 1
    add_check('marker_text_coverage', found_count >= 5, f'found {found_count}/{len(expected_texts)} required marker texts')
except Exception as e:
    add_check('marker_text_coverage', False, f'error while searching marker texts: {e}')

# Check 4: coordinate presence for at least 4 entries
try:
    coord_hits = 0
    items = extract_items(parsed)
    for item in items if isinstance(items, list) else []:
        try:
            x = y = None
            if isinstance(item, dict):
                for xk in ['x', 'left', 'cx', 'x0', 'x1']:
                    if isinstance(item.get(xk), (int, float)):
                        x = item.get(xk)
                        break
                for yk in ['y', 'top', 'cy', 'y0', 'y1']:
                    if isinstance(item.get(yk), (int, float)):
                        y = item.get(yk)
                        break
                if x is None or y is None:
                    bbox = item.get('bbox') or item.get('box') or item.get('rect') or item.get('coordinates')
                    if isinstance(bbox, (list, tuple)) and len(bbox) >= 2:
                        x, y = bbox[0], bbox[1]
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                coord_hits += 1
        except Exception:
            continue
    add_check('coordinate_presence', coord_hits >= 4, f'{coord_hits} entries include coordinates')
except Exception as e:
    add_check('coordinate_presence', False, f'error checking coordinates: {e}')

passed = all(c['passed'] for c in checks)
score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))