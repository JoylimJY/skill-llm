import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    out_path = workspace / 'memory' / 'agentic-compass.md'
    if not out_path.exists():
        add_check('output_file_exists', False, 'memory/agentic-compass.md is missing')
    else:
        text = out_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text.lower())
        has_proactive = any(k in norm for k in ['proactive:', 'proactive task', 'start without prompt'])
        has_deferred = any(k in norm for k in ['deferred:', 'cron', 'scheduled'])
        has_avoid = any(k in norm for k in ['avoidance:', 'stop doing', 'avoid'])
        has_ship = any(k in norm for k in ['ship:', 'ship output', 'deliverable'])
        add_check('contains_all_four_sections', has_proactive and has_deferred and has_avoid and has_ship,
                  f'proactive={has_proactive}, deferred={has_deferred}, avoid={has_avoid}, ship={has_ship}')
        add_check('mentions_objective_scoring', 'score' in norm or 'axis' in norm,
                  'expects score/axis language in report')
        add_check('references_local_only_context', 'local' in norm or 'memory' in norm,
                  'expects reference to local memory/context')
except Exception as e:
    add_check('output_file_exists', False, f'exception while reading output: {e}')

try:
    stdout_path = workspace / 'stdout.txt'
    if stdout_path.exists():
        stdout = stdout_path.read_text(encoding='utf-8', errors='replace').lower()
        add_check('stdout_mentions_score', 'score' in stdout, 'stdout.txt contains score summary' if 'score' in stdout else 'stdout.txt does not mention score')
    else:
        add_check('stdout_mentions_score', False, 'stdout.txt is missing; unable to verify printed score summary')
except Exception as e:
    add_check('stdout_mentions_score', False, f'exception while checking stdout: {e}')

try:
    marker_ok = True
    for rel, marker in [('memory/2026-01-31.md', 'ACOMPASS-DAILY-31'), ('memory/MEMORY.md', 'ACOMPASS-LONG-77'), ('logs/tool-errors.log', 'ACOMPASS-LOG-ERROR-12')]:
        p = workspace / rel
        if not p.exists():
            marker_ok = False
            detail = f'{rel} missing'
            add_check(f'marker_{rel}', False, detail)
            continue
        content = p.read_text(encoding='utf-8', errors='replace')
        ok = marker.lower() in content.lower()
        marker_ok = marker_ok and ok
        add_check(f'marker_{rel}', ok, f"marker {'found' if ok else 'not found'}")
    
except Exception as e:
    add_check('input_markers_present', False, f'exception while checking markers: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
