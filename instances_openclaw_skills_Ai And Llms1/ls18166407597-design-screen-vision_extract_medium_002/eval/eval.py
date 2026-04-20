from pathlib import Path
import json, sys, re

checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    workspace = Path(sys.argv[1])
except Exception as e:
    print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'argument', 'passed': False, 'detail': f'missing or invalid workspace argument: {e}'}]}))
    raise SystemExit(0)

# Check 1: expected input exists
try:
    gt = workspace / 'ground_truth.json'
    if gt.exists():
        data = json.loads(gt.read_text(encoding='utf-8'))
        ok = all(k in data for k in ['expected_title', 'expected_balance', 'expected_alerts', 'marker'])
        add_check('ground_truth_present', ok, 'ground_truth.json found and parsed' if ok else 'ground_truth.json missing required keys')
    else:
        add_check('ground_truth_present', False, 'ground_truth.json not found')
except Exception as e:
    add_check('ground_truth_present', False, f'error reading ground_truth.json: {e}')

# Check 2: screenshot exists
try:
    shot = workspace / 'screenshot.png'
    add_check('screenshot_exists', shot.exists(), 'screenshot.png found' if shot.exists() else 'screenshot.png not found')
except Exception as e:
    add_check('screenshot_exists', False, f'error checking screenshot.png: {e}')

# Check 3: output report exists and contains required content
try:
    # Look for output.json first, then any JSON file
    out = workspace / 'output.json'
    if not out.exists():
        # Fallback: find any JSON file in workspace
        json_files = list(workspace.glob('*.json'))
        json_files = [f for f in json_files if f.name != 'ground_truth.json']
        if json_files:
            out = json_files[0]
        else:
            add_check('output_report', False, 'output.json not found')
            add_check('coordinates', False, 'output.json not found')
            passed = all(c['passed'] for c in checks)
            score = sum(1 for c in checks if c['passed']) / max(1, len(checks))
            print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
            raise SystemExit(0)
    
    try:
        obj = json.loads(out.read_text(encoding='utf-8'))
        
        # Flexible key matching for title - handle nested structures
        title_val = obj.get('title', '')
        if isinstance(title_val, dict):
            title = str(title_val.get('text', '') or title_val.get('title', '') or '')
        else:
            title = str(title_val or obj.get('main_title', '') or obj.get('mainTitle', '') or '')
        
        # Flexible key matching for balance - handle nested structures
        balance_val = obj.get('balance', '')
        if isinstance(balance_val, dict):
            balance = str(balance_val.get('text', '') or balance_val.get('value', '') or '')
        else:
            balance = str(balance_val or obj.get('balance_value', '') or obj.get('balanceValue', '') or '')
        
        # Flexible key matching for alerts/counter - handle nested structures
        alerts_val = obj.get('alerts', '')
        if isinstance(alerts_val, dict):
            alerts = str(alerts_val.get('text', '') or alerts_val.get('value', '') or '')
        else:
            alerts = str(alerts_val or obj.get('counter', '') or obj.get('alert_count', '') or obj.get('alertCount', '') or '')
        
        # Flexible key matching for marker (optional - not in prompt)
        marker_val = obj.get('marker', '')
        if isinstance(marker_val, dict):
            marker = str(marker_val.get('text', '') or marker_val.get('value', '') or '')
        else:
            marker = str(marker_val or obj.get('screenvision_marker', '') or '')
        
        # Flexible validation with fuzzy matching
        title_ok = ('finance' in title.lower() or 'dashboard' in title.lower())
        balance_ok = ('1284' in balance or '1284.50' in balance or '128450' in balance)
        alerts_ok = ('7' in str(alerts))
        marker_ok = ('screenvision' in marker.lower()) if marker else True  # marker is optional
        
        ok = title_ok and balance_ok and alerts_ok and marker_ok
        detail = f"title={obj.get('title') or obj.get('main_title')}, balance={obj.get('balance')}, alerts={obj.get('alerts') or obj.get('counter')}, marker={obj.get('marker')}"
        add_check('output_report', ok, detail)
    except Exception as e:
        add_check('output_report', False, f'output.json malformed: {e}')
except Exception as e:
    add_check('output_report', False, f'error checking output.json: {e}')

# Check 4: coordinates present in a forgiving way - search nested structures
try:
    out = workspace / 'output.json'
    if not out.exists():
        json_files = list(workspace.glob('*.json'))
        json_files = [f for f in json_files if f.name != 'ground_truth.json']
        if json_files:
            out = json_files[0]
    
    if out.exists():
        obj = json.loads(out.read_text(encoding='utf-8'))
        
        ok = False
        detail = 'coordinates missing'
        
        # Helper function to check if a coordinate dict is valid
        def check_coords(coord_obj):
            if isinstance(coord_obj, dict):
                x = coord_obj.get('x')
                y = coord_obj.get('y')
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    return 0 <= x <= 1200 and 0 <= y <= 800, f'({x}, {y})'
            elif isinstance(coord_obj, (list, tuple)) and len(coord_obj) >= 2:
                x, y = coord_obj[0], coord_obj[1]
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    return 0 <= x <= 1200 and 0 <= y <= 800, f'({x}, {y})'
            return False, None
        
        # Check nested structures first (title.coordinates, balance.label_coordinates, etc.)
        for key in ['title', 'balance', 'alerts', 'counter', 'main_title']:
            val = obj.get(key, {})
            if isinstance(val, dict):
                for coord_key in ['coordinates', 'coords', 'label_coordinates', 'label_coords', 'position', 'bbox']:
                    coord_val = val.get(coord_key)
                    if coord_val:
                        is_valid, coord_str = check_coords(coord_val)
                        if is_valid:
                            ok = True
                            detail = f'{key}.{coord_key}={coord_str}'
                            break
                if ok:
                    break
        
        # Also check for separate coord keys like title_coords, balance_coords, counter_coords
        if not ok:
            for key in ['title_coords', 'balance_coords', 'counter_coords', 'first_label_coords', 'coordinates']:
                if key in obj:
                    is_valid, coord_str = check_coords(obj[key])
                    if is_valid:
                        ok = True
                        detail = f'{key}={coord_str}'
                        break
        
        # Check coordinates.first_label format
        if not ok:
            coords = obj.get('coordinates', {})
            if isinstance(coords, dict):
                first = coords.get('first_label')
                if first:
                    is_valid, coord_str = check_coords(first)
                    if is_valid:
                        ok = True
                        detail = f'coordinates.first_label={coord_str}'
        
        # Check coordinates.title, coordinates.balance, coordinates.alerts format (agent's structure)
        if not ok:
            coords = obj.get('coordinates', {})
            if isinstance(coords, dict):
                for key in ['title', 'balance', 'alerts', 'counter', 'main_title']:
                    coord_val = coords.get(key)
                    if coord_val:
                        is_valid, coord_str = check_coords(coord_val)
                        if is_valid:
                            ok = True
                            detail = f'coordinates.{key}={coord_str}'
                            break
        
        add_check('coordinates', ok, detail)
    else:
        add_check('coordinates', False, 'output.json not found')
except Exception as e:
    add_check('coordinates', False, f'error parsing coordinates: {e}')

passed = all(c['passed'] for c in checks)
score = sum(1 for c in checks if c['passed']) / max(1, len(checks))
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))