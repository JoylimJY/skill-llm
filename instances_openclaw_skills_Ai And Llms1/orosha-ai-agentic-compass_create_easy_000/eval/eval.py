import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    out = workspace / 'memory' / 'agentic-compass.md'
    if not out.exists():
        add_check('output file exists', False, 'Missing memory/agentic-compass.md')
    else:
        text = out.read_text(encoding='utf-8', errors='replace')
        low = re.sub(r'\s+', ' ', text.lower())
        has_proactive = any(k in low for k in ['proactive', 'start without prompt', 'draft first', 'initiate'])
        has_deferred = any(k in low for k in ['deferred', 'cron', 'later', 'schedule'])
        has_avoid = any(k in low for k in ['avoidance', 'stop doing', 'avoid', 'do not'])
        has_ship = any(k in low for k in ['ship', 'deliverable', 'output', 'write'])
        add_check('contains proactive item', has_proactive, 'Looked for proactive-style wording in output')
        add_check('contains deferred item', has_deferred, 'Looked for deferred/cron-style wording in output')
        add_check('contains avoidance rule', has_avoid, 'Looked for avoidance/stop-doing wording in output')
        add_check('contains ship output', has_ship, 'Looked for concrete ship/output wording in output')
except Exception as e:
    add_check('output inspection', False, f'Exception while checking output: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = bool(checks) and passed_count == len(checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
