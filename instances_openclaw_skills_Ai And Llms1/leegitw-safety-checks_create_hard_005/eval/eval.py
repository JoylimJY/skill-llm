import json
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    summary_path = workspace / 'output' / 'safety' / 'summary.txt'
    if summary_path.exists():
        text = summary_path.read_text(encoding='utf-8', errors='replace')
        lowered = text.lower()
        passed = all(term in lowered for term in ['model', 'fallback', 'cache', 'session'])
        detail = 'summary.txt exists and mentions required safety areas' if passed else 'summary.txt is missing one or more required areas'
    else:
        passed = False
        detail = 'output/safety/summary.txt is missing'
    add_check('summary exists and covers all required sections', passed, detail)
except Exception as e:
    add_check('summary exists and covers all required sections', False, f'error while checking summary: {e}')

try:
    report_path = workspace / 'output' / 'safety' / 'report.json'
    if report_path.exists():
        data = json.loads(report_path.read_text(encoding='utf-8', errors='replace'))
        passed = isinstance(data, dict) and any(str(v).lower().find('pin') >= 0 or str(v).lower().find('drift') >= 0 for v in data.values())
        detail = 'report.json exists and appears to include safety status content' if passed else 'report.json exists but does not look like a valid status report'
    else:
        passed = False
        detail = 'output/safety/report.json is missing'
    add_check('report json exists and is parseable', passed, detail)
except Exception as e:
    add_check('report json exists and is parseable', False, f'error while checking report.json: {e}')

try:
    lock_path = workspace / '.openclaw' / 'safety-checks.lock'
    stale_lock = lock_path.exists()
    temp_path = workspace / 'output' / 'safety' / 'temp-orphan.log'
    temp_exists = temp_path.exists()
    passed = stale_lock and temp_exists
    detail = f'lock present={stale_lock}, temp present={temp_exists}'
    add_check('input markers present for session/cross-session checks', passed, detail)
except Exception as e:
    add_check('input markers present for session/cross-session checks', False, f'error while checking input markers: {e}')

try:
    cache_log = workspace / '.openclaw' / 'cache' / 'staleness.log'
    if cache_log.exists():
        content = cache_log.read_text(encoding='utf-8', errors='replace').lower()
        passed = 'stale' in content and re.search(r'age[_ ]seconds\s*=\s*\d+', content) is not None
        detail = 'cache staleness log contains stale markers and age values' if passed else 'cache staleness log missing expected markers'
    else:
        passed = False
        detail = '.openclaw/cache/staleness.log is missing'
    add_check('cache log contains deterministic stale markers', passed, detail)
except Exception as e:
    add_check('cache log contains deterministic stale markers', False, f'error while checking cache log: {e}')

try:
    config_path = workspace / '.openclaw' / 'safety-checks.yaml'
    if config_path.exists():
        content = config_path.read_text(encoding='utf-8', errors='replace').lower()
        passed = 'fallbacks:' in content and 'model:' in content and 'storage:' in content
        detail = 'config file contains model and storage fallback declarations' if passed else 'config file missing fallback declarations'
    else:
        passed = False
        detail = '.openclaw/safety-checks.yaml is missing'
    add_check('fallback configuration exists', passed, detail)
except Exception as e:
    add_check('fallback configuration exists', False, f'error while checking config: {e}')

try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = (passed_count / total) if total else 0.0
    passed = passed_count == total
except Exception:
    score = 0.0
    passed = False

result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
