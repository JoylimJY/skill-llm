import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    out = workspace / 'memory' / 'agentic-compass.md'
    if not out.exists():
        add_check('output_exists', False, 'memory/agentic-compass.md is missing')
    else:
        text = out.read_text(encoding='utf-8', errors='ignore')
        norm = re.sub(r'[^a-z0-9]+', ' ', text.lower())

        has_proactive = any(k in norm for k in ['proactive', 'start without prompt', 'initiate', 'draft'])
        has_deferred = any(k in norm for k in ['deferred', 'cron', 'later', 'retry'])
        has_avoidance = any(k in norm for k in ['avoidance', 'stop doing', 'avoid', 'do not'])
        has_ship = any(k in norm for k in ['ship', 'deliver', 'output', 'create'])
        add_check('contains_required_sections', has_proactive and has_deferred and has_avoidance and has_ship,
                  'Found required plan elements' if has_proactive and has_deferred and has_avoidance and has_ship else 'Missing one or more plan elements')

        marker_ok = ('daily_marker_alpha_913' in norm) and ('long_memory_marker_beta_274' in norm)
        add_check('uses_input_markers', marker_ok,
                  'Detected both marker strings' if marker_ok else 'Did not detect both embedded markers')

        local_only_ok = 'local' in norm and ('network' not in norm or 'no network' in norm)
        add_check('local_only_language', local_only_ok,
                  'Plan mentions local-only behavior' if local_only_ok else 'Local-only language not clearly present')

    expected_daily = workspace / 'memory' / '2026-01-31.md'
    expected_long = workspace / 'MEMORY.md'
    add_check('daily_input_exists', expected_daily.exists(), 'Daily memory file present' if expected_daily.exists() else 'Daily memory file missing')
    add_check('long_input_exists', expected_long.exists(), 'Long-term memory file present' if expected_long.exists() else 'Long-term memory file missing')

except Exception as e:
    add_check('eval_exception', False, f'Unexpected error: {type(e).__name__}: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks) and len(checks) > 0, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
