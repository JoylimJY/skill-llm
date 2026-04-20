from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

# Check 1: output file exists (check for prescription.json or Frankenstein_Prescription_*.txt)
output_path = None
for pattern in ['prescription.json', 'Frankenstein_Prescription_*.txt', 'prescription_*.json']:
    matches = list(workspace.glob(pattern))
    if matches:
        output_path = matches[0]
        break

if output_path is None:
    add_check('output_exists', False, 'prescription.json or Frankenstein_Prescription_*.txt is missing')
else:
    add_check('output_exists', True, f'found {output_path.name}')

# Check 2: output parses and contains required fuzzy properties
obj = None
text_content = None
try:
    if output_path:
        text_content = output_path.read_text(encoding='utf-8', errors='replace')
        if output_path.suffix == '.json':
            obj = json.loads(text_content)
            ok = isinstance(obj, dict)
            add_check('json_parse', ok, 'valid JSON object' if ok else 'top-level JSON is not an object')
        else:
            # For .txt files, create a pseudo-object for checking
            obj = {'content': text_content}
            add_check('json_parse', True, 'text file parsed successfully')
    else:
        add_check('json_parse', False, 'cannot parse because file is missing')
except Exception as e:
    add_check('json_parse', False, f'failed to parse: {e}')

# Check 3: mentions key expected strings somewhere in the output
try:
    if obj is None and text_content is None:
        raise ValueError('no parsed object')
    
    if isinstance(obj, dict) and 'content' in obj:
        blob = obj['content'].lower()
    else:
        blob = json.dumps(obj, ensure_ascii=False).lower() if obj else ''
    
    # Check for agent and human names (required)
    has_agent = 'unit-7' in blob or 'unit7' in blob
    has_human = 'mira' in blob
    
    # Check for marker reference (required)
    has_marker = 'soul-input-alpha' in blob or 'soul-input-beta' in blob
    
    # Check for at least one medical/chemical term (flexible)
    medical_terms = ['cortisol', 'oxytocin', 'serotonin', 'dopamine', 'anxiety', 'proactivity']
    has_medical = any(term in blob for term in medical_terms)
    
    passed = has_agent and has_human and has_marker
    missing = []
    if not has_agent: missing.append('agent name')
    if not has_human: missing.append('human name')
    if not has_marker: missing.append('marker reference')
    
    add_check('contains_core_terms', passed, 'missing: ' + ', '.join(missing) if missing else 'all core terms present')
except Exception as e:
    add_check('contains_core_terms', False, f'error scanning content: {e}')

# Check 4: at least one cron command or schedule-like entry exists
try:
    if obj is None and text_content is None:
        raise ValueError('no parsed object')
    
    if isinstance(obj, dict) and 'content' in obj:
        blob = obj['content'].lower()
    else:
        blob = json.dumps(obj, ensure_ascii=False).lower() if obj else ''
    
    # More flexible schedule detection
    sched_patterns = [
        r'\b\d{1,2}\s+([*/\d]+\s+){3}[*/\d]+\b',  # cron format
        r'openclaw cron create',
        r'schedule',
        r'daily',
        r'evening',
        r'monitor',
        r'follow-up',
        r'check-in'
    ]
    sched_like = any(re.search(p, blob) for p in sched_patterns)
    add_check('has_schedule_like_content', sched_like, 'found schedule-like content' if sched_like else 'no cron-like schedule or command found')
except Exception as e:
    add_check('has_schedule_like_content', False, f'error checking schedule content: {e}')

# Check 5: prescription references the input marker or source context
try:
    if obj is None and text_content is None:
        raise ValueError('no parsed object')
    
    if isinstance(obj, dict) and 'content' in obj:
        blob = obj['content'].lower()
    else:
        blob = json.dumps(obj, ensure_ascii=False).lower() if obj else ''
    
    marker_hit = 'soul-input-alpha' in blob or 'soul-input-beta' in blob
    add_check('references_input_marker', marker_hit, 'references generated markers' if marker_hit else 'no known marker content referenced')
except Exception as e:
    add_check('references_input_marker', False, f'error checking marker reference: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))