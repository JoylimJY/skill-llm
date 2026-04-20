import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    target = workspace / 'output' / 'safety' / 'runbook.txt'
    if not target.exists():
        add_check('runbook exists', False, 'Missing output/safety/runbook.txt')
    else:
        try:
            text = target.read_text(encoding='utf-8', errors='ignore')
            norm = ''.join(ch.lower() for ch in text)
            required = ['model pinning', 'fallback validation', 'cache staleness', 'session hygiene', 'heartbeat ready']
            missing = [r for r in required if ''.join(ch.lower() for ch in r) not in norm]
            if missing:
                add_check('runbook content', False, 'Missing phrases: ' + ', '.join(missing))
            else:
                add_check('runbook content', True, 'All required phrases found')
        except Exception as e:
            add_check('runbook content', False, f'Could not read file: {e}')
except Exception as e:
    add_check('runbook exists', False, f'Unexpected error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = all(c['passed'] for c in checks) if checks else False
print(json.dumps({"passed": passed, "score": score, "checks": checks}))
