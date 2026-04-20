from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})


def safe_read_text(path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: summary.txt exists and contains key phrases
# Look in output/ directory first, then root
try:
    summary_path = workspace / 'output' / 'summary.txt'
    if not summary_path.exists():
        summary_path = workspace / 'summary.txt'
    
    if summary_path.exists():
        text = summary_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'[^a-z0-9]+', ' ', text.lower())
        ok = ('duplicate' in norm) and ('quota' in norm) and ('gemini' in norm)
        add_check('summary_exists_and_mentions_key_topics', ok, 'summary.txt found' if ok else 'summary.txt missing required themes')
    else:
        add_check('summary_exists_and_mentions_key_topics', False, 'summary.txt is missing')
except Exception as e:
    add_check('summary_exists_and_mentions_key_topics', False, f'error reading summary.txt: {e}')

# Check 2: report.json exists and has expected structure
# Look in output/ directory first, then root
try:
    report_path = workspace / 'output' / 'report.json'
    if not report_path.exists():
        report_path = workspace / 'report.json'
    
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text(encoding='utf-8', errors='replace'))
            # Check for essential elements: project info, quota data, and duplicate burst detection
            # Be flexible about structure - accept various reasonable formats
            has_project = 'project' in data or 'model' in data
            has_quota = any(k in data for k in ['quota', 'total_tokens', 'tokens', 'usage', 'limit'])
            has_bursts = 'duplicate_bursts' in data or 'bursts' in data or 'alerts' in data
            ok = has_project and has_quota and has_bursts
            add_check('report_exists_and_has_structure', ok, 'report.json structure looks valid' if ok else 'report.json missing required keys')
        except Exception as e:
            add_check('report_exists_and_has_structure', False, f'failed to parse report.json: {e}')
    else:
        add_check('report_exists_and_has_structure', False, 'report.json is missing')
except Exception as e:
    add_check('report_exists_and_has_structure', False, f'error checking report.json: {e}')

# Check 3: report includes marker and correct model name approximately
# Look in output/ directory first, then root
try:
    report_path = workspace / 'output' / 'report.json'
    if not report_path.exists():
        report_path = workspace / 'report.json'
    
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text(encoding='utf-8', errors='replace'))
            blob = json.dumps(data).lower()
            ok = ('tg_marker_9f3a2c' in blob) and ('gemini-3-flash' in blob)
            add_check('report_contains_marker_and_model', ok, 'marker/model present' if ok else 'marker or model missing')
        except Exception as e:
            add_check('report_contains_marker_and_model', False, f'parse error: {e}')
    else:
        add_check('report_contains_marker_and_model', False, 'report.json is missing')
except Exception as e:
    add_check('report_contains_marker_and_model', False, f'error: {e}')

# Check 4: alert file should exist because there is a duplicate burst
# Accept both alert.txt and alerts.txt in output/ or root
try:
    alert_path = workspace / 'output' / 'alerts.txt'
    if not alert_path.exists():
        alert_path = workspace / 'output' / 'alert.txt'
    if not alert_path.exists():
        alert_path = workspace / 'alerts.txt'
    if not alert_path.exists():
        alert_path = workspace / 'alert.txt'
    
    if alert_path.exists():
        text = alert_path.read_text(encoding='utf-8', errors='replace').lower()
        ok = ('duplicate' in text) or ('burst' in text) or ('runaway' in text)
        add_check('alert_created_for_duplicate_burst', ok, 'alert file found with alert wording' if ok else 'alert file does not mention duplicate burst')
    else:
        add_check('alert_created_for_duplicate_burst', False, 'alert file is missing')
except Exception as e:
    add_check('alert_created_for_duplicate_burst', False, f'error reading alert file: {e}')

# Check 5: score is computed from checks
passed_count = sum(1 for c in checks if c['passed'])
total_count = len(checks)
score = (passed_count / total_count) if total_count else 0.0
passed = passed_count == total_count

print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))