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
        add_check('output_exists', False, 'memory/agentic-compass.md is missing')
    else:
        text = out.read_text(encoding='utf-8', errors='ignore')
        norm = re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
        add_check('output_exists', True, 'memory/agentic-compass.md exists')

        required_labels = ['proactive', 'deferred', 'avoidance', 'ship']
        for label in required_labels:
            add_check(
                f'contains_{label}',
                label in norm,
                f"{label} section {'found' if label in norm else 'not found'}"
            )

        items = re.findall(r'^[\-\*]\s*(.+)$', text, flags=re.M)
        add_check('four_bullets', len(items) >= 4, f'found {len(items)} bullet item(s)')

        score_match = re.search(r'weakest\s*axis\s*[:\-]\s*([a-z ]+)', text, flags=re.I)
        score_ok = bool(score_match and any(axis in score_match.group(1).lower() for axis in ['completion rate', 'tool usage quality', 'memory consistency', 'initiative', 'response relevance']))
        add_check('weakest_axis_named', score_ok, f"weakest axis {'appears valid' if score_ok else 'not clearly named'}")

        local_only = 'local-only' in norm or 'offline' in norm
        add_check('local_only_tone', local_only, 'mentions local-only/offline behavior' if local_only else 'missing local-only/offline language')
except Exception as e:
    add_check('eval_exception', False, f'eval failed safely: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / max(len(checks), 1)
passed = all(c['passed'] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}))
