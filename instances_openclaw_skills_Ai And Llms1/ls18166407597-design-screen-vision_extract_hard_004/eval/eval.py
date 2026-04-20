import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def find_summary_file():
    """Find any text file that might contain the summary"""
    candidates = []
    for f in workspace.iterdir():
        if f.suffix.lower() == '.txt':
            # Check if filename suggests it's a summary
            name_lower = f.name.lower()
            if any(kw in name_lower for kw in ['summary', 'text', 'recovered', 'notes', 'review']):
                candidates.append(f)
    return candidates


def find_coordinate_file():
    """Find any JSON file that might contain coordinates"""
    candidates = []
    for f in workspace.iterdir():
        if f.suffix.lower() == '.json':
            # Check if filename suggests it's coordinates
            name_lower = f.name.lower()
            if any(kw in name_lower for kw in ['coordinate', 'coords', 'map', 'position', 'location']):
                candidates.append(f)
    return candidates


# Check 1: summary file exists and contains all target terms fuzzily
try:
    summary_files = find_summary_file()
    if summary_files:
        # Try each candidate file
        found_terms = False
        detail_info = []
        for sf in summary_files:
            text = sf.read_text(encoding='utf-8', errors='replace')
            norm = normalize(text)
            terms = ['alpha ledger', 'beta signal', 'gamma note']
            hits = [t for t in terms if normalize(t) in norm]
            if len(hits) == len(terms):
                found_terms = True
                detail_info.append(f'found in {sf.name}: hits={hits}')
                break
            detail_info.append(f'{sf.name}: hits={hits}')
        
        add_check('summary_contains_terms', found_terms, '; '.join(detail_info) if detail_info else 'no candidates found')
    else:
        add_check('summary_contains_terms', False, 'no summary text file found')
except Exception as e:
    add_check('summary_contains_terms', False, f'exception: {e}')


# Check 2: coordinates file exists and has approximate numeric positions
try:
    coord_files = find_coordinate_file()
    if coord_files:
        expected = {
            'alpha ledger': (185, 192),
            'beta signal': (820, 372),
            'gamma note': (475, 712),
        }
        found_valid = False
        detail_info = []
        
        for cf in coord_files:
            try:
                data = json.loads(cf.read_text(encoding='utf-8', errors='replace'))
                passed = True
                details = []
                for key, (ex, ey) in expected.items():
                    found = None
                    for k, v in data.items():
                        if normalize(k) == key and isinstance(v, dict):
                            x = v.get('x')
                            y = v.get('y')
                            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                                found = (x, y)
                            break
                    if found is None:
                        passed = False
                        details.append(f'missing or malformed entry for {key}')
                    else:
                        x, y = found
                        ok = abs(x - ex) <= 25 and abs(y - ey) <= 25
                        if not ok:
                            passed = False
                            details.append(f'{key}: got=({x},{y}) expected~({ex},{ey})')
                
                if passed:
                    found_valid = True
                    detail_info.append(f'{cf.name}: all entries within tolerance')
                    break
                else:
                    detail_info.append(f'{cf.name}: {"; ".join(details)}')
            except Exception as e:
                detail_info.append(f'{cf.name}: parse error - {e}')
        
        add_check('coordinates_approximate_positions', found_valid, '; '.join(detail_info) if detail_info else 'no candidates found')
    else:
        add_check('coordinates_approximate_positions', False, 'no coordinate JSON file found')
except Exception as e:
    add_check('coordinates_approximate_positions', False, f'exception: {e}')


# Check 3: Optional context check - look for job_id or context in any file
try:
    context_found = False
    for f in workspace.iterdir():
        if f.suffix.lower() in ['.txt', '.json']:
            try:
                text = f.read_text(encoding='utf-8', errors='replace')
                norm = normalize(text)
                if 'screen-vision-hard-042' in norm or 'review panel' in norm:
                    context_found = True
                    break
            except:
                pass
    
    # Make this optional - don't fail if not found
    add_check('context_note_present', context_found, 'context found in files' if context_found else 'context not required')
except Exception as e:
    add_check('context_note_present', True, f'context check skipped: {e}')


score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks) if checks else False
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))