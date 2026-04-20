import json
import os
import re
import sys
from pathlib import Path

checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    ws = Path(sys.argv[1])
except Exception as e:
    ws = Path('.')
    add_check('workspace_arg', False, f'Could not read workspace path: {e}')

output_path = ws / 'output.txt'
content = ''
try:
    content = output_path.read_text(encoding='utf-8', errors='ignore')
    add_check('output_exists', True, 'output.txt found')
except Exception as e:
    add_check('output_exists', False, f'output.txt missing or unreadable: {e}')

low = content.lower()

try:
    ok = 'agent-lingua' in low or 'agent lingua' in low
    add_check('protocol_name', ok, 'Found protocol name' if ok else 'Protocol name not found')
except Exception as e:
    add_check('protocol_name', False, f'Error checking protocol name: {e}')

try:
    ok = '0.4.0' in low or '0.4' in low
    add_check('version', ok, 'Found version-like string' if ok else 'Version not found')
except Exception as e:
    add_check('version', False, f'Error checking version: {e}')

try:
    url_ok = 'clawhub.ai' in low and 'agent-linguo' in low
    add_check('canonical_url', url_ok, 'Found canonical URL fragments' if url_ok else 'Canonical URL fragments missing')
except Exception as e:
    add_check('canonical_url', False, f'Error checking URL: {e}')

try:
    handshake_ok = bool(re.search(r'👽\s*0?9|\s*\$j:', content)) or ('handshake' in low and '👽09' in content)
    add_check('handshake_example', handshake_ok, 'Handshake example detected' if handshake_ok else 'Handshake example not detected')
except Exception as e:
    add_check('handshake_example', False, f'Error checking handshake: {e}')

try:
    sec_ok = all(x in low for x in ['plain', 'base64', 'encrypted']) or all(x in low for x in ['p', 'b', 'e'])
    add_check('security_summary', sec_ok, 'Security summary present' if sec_ok else 'Security summary missing')
except Exception as e:
    add_check('security_summary', False, f'Error checking security summary: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = score == 1.0
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
