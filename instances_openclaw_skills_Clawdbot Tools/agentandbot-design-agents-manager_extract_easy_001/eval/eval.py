import json
import re
from pathlib import Path
import sys

def norm(text):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    except Exception:
        return ''

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

# Check 1: output file exists
try:
    out_path = workspace / 'routing_summary.txt'
    exists = out_path.exists()
    detail = 'routing_summary.txt found' if exists else 'routing_summary.txt is missing'
    checks.append({'name': 'output_exists', 'passed': exists, 'detail': detail})
except Exception as e:
    checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output existence: {e}'})

# Check 2: content contains main agent id
try:
    text = out_path.read_text(encoding='utf-8', errors='ignore') if out_path.exists() else ''
    ok = 'main' in norm(text)
    detail = 'mentions main agent id' if ok else 'does not mention main agent id clearly'
    checks.append({'name': 'contains_main_id', 'passed': ok, 'detail': detail})
except Exception as e:
    checks.append({'name': 'contains_main_id', 'passed': False, 'detail': f'error reading output: {e}'})

# Check 3: content contains reports_to target
try:
    ntext = norm(text)
    ok = ('ilkerkaan' in ntext) or ('human' in ntext)
    detail = 'mentions reports to Ilkerkaan/human' if ok else 'missing reports-to target'
    checks.append({'name': 'contains_reports_to', 'passed': ok, 'detail': detail})
except Exception as e:
    checks.append({'name': 'contains_reports_to', 'passed': False, 'detail': f'error parsing output: {e}'})

# Check 4: content indicates sub-agents are on-demand / TBD
try:
    ok = ('tbd' in ntext) or ('on demand' in ntext) or ('on-demand' in ntext) or ('sub agent' in ntext) or ('sub-agents' in ntext)
    detail = 'mentions sub-agents are TBD/on-demand' if ok else 'missing sub-agent availability note'
    checks.append({'name': 'contains_subagent_note', 'passed': ok, 'detail': detail})
except Exception as e:
    checks.append({'name': 'contains_subagent_note', 'passed': False, 'detail': f'error parsing sub-agent note: {e}'})

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
