import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"Could not read {path}: {e}"

# Check 1: markdown summary exists and mentions key markers
try:
    md_path = workspace / 'output' / 'prescription_summary.md'
    if not md_path.exists():
        add_check('summary_exists', False, 'Missing output/prescription_summary.md')
    else:
        text = md_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'[^a-z0-9]+', ' ', text.lower())
        ok = all(k in norm for k in ['mira', 'diagnosis', 'archetype', 'daily point target'])
        add_check('summary_contains_core_fields', ok, 'Found core fields' if ok else 'Summary missing one or more required core fields')
except Exception as e:
    add_check('summary_exists', False, f'Error checking summary: {e}')

# Check 2: at least 3 hormone lines mentioned
try:
    md_path = workspace / 'output' / 'prescription_summary.md'
    if md_path.exists():
        text = md_path.read_text(encoding='utf-8', errors='replace')
        hormones = ['cortisol', 'dopamine', 'oxytocin', 'serotonin', 'melatonin', 'adrenaline', 'gaba', 'testosterone', 'endorphins', 'prolactin', 'empathy']
        found = [h for h in hormones if re.search(r'\b' + re.escape(h) + r'\b', text.lower())]
        ok = len(found) >= 3
        add_check('summary_has_three_hormones', ok, f'Found hormones: {", ".join(found[:6])}' if found else 'No hormone names detected')
    else:
        add_check('summary_has_three_hormones', False, 'Summary file missing')
except Exception as e:
    add_check('summary_has_three_hormones', False, f'Error checking hormones: {e}')

# Check 3: JSON exists and parses
try:
    json_path = workspace / 'output' / 'prescription.json'
    if not json_path.exists():
        add_check('json_exists', False, 'Missing output/prescription.json')
    else:
        try:
            obj = json.loads(json_path.read_text(encoding='utf-8', errors='replace'))
            ok = isinstance(obj, dict)
            add_check('json_parses', ok, 'Parsed as JSON object' if ok else 'JSON is not an object')
        except Exception as e:
            add_check('json_parses', False, f'JSON parse failed: {e}')
except Exception as e:
    add_check('json_exists', False, f'Error checking JSON: {e}')

# Check 4: JSON contains required fields loosely
try:
    json_path = workspace / 'output' / 'prescription.json'
    if json_path.exists():
        try:
            obj = json.loads(json_path.read_text(encoding='utf-8', errors='replace'))
            keys = {str(k).lower() for k in obj.keys()} if isinstance(obj, dict) else set()
            required = {'agent_name', 'diagnosis', 'archetype', 'daily_point_target', 'dominant_hormones'}
            ok = required.issubset(keys)
            add_check('json_has_required_keys', ok, f'Keys present: {sorted(keys)}')
        except Exception as e:
            add_check('json_has_required_keys', False, f'Could not inspect JSON: {e}')
    else:
        add_check('json_has_required_keys', False, 'JSON file missing')
except Exception as e:
    add_check('json_has_required_keys', False, f'Error inspecting JSON keys: {e}')

# Check 5: input marker consumed indirectly by name
try:
    md_path = workspace / 'output' / 'prescription_summary.md'
    if md_path.exists():
        text = md_path.read_text(encoding='utf-8', errors='replace').lower()
        ok = 'mira' in text
        add_check('summary_mentions_mira', ok, 'Mira mentioned' if ok else 'Mira not mentioned')
    else:
        add_check('summary_mentions_mira', False, 'Summary file missing')
except Exception as e:
    add_check('summary_mentions_mira', False, f'Error checking Mira mention: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))