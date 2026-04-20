import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def safe_read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        return None, str(e)


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def fuzzy_contains(text, needles):
    t = norm(text)
    return any(norm(n) in t for n in needles)


def pct_change(before, after):
    try:
        return ((after - before) / before) * 100.0
    except Exception:
        return None


checks = []
ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
report = ws / 'optimization_report.md'
summary = ws / 'summary.json'

# Check 1: report exists and is readable
try:
    if report.exists():
        text = report.read_text(encoding='utf-8')
        passed = len(text.strip()) > 0
        detail = 'optimization_report.md exists and is non-empty.' if passed else 'optimization_report.md is empty.'
    else:
        passed = False
        detail = 'optimization_report.md is missing.'
except Exception as e:
    passed = False
    detail = f'Could not read optimization_report.md: {e}'
checks.append({'name': 'report_exists', 'passed': passed, 'detail': detail})

# Check 2: summary exists and has required fields
try:
    data, err = safe_read_json(summary)
    if data is None:
        passed = False
        detail = f'summary.json could not be parsed: {err}'
    else:
        passed = all(k in data for k in ['system', 'top_bottleneck', 'recommendations'])
        detail = 'summary.json contains required fields.' if passed else 'summary.json is missing required fields.'
except Exception as e:
    passed = False
    detail = f'Error checking summary.json: {e}'
checks.append({'name': 'summary_schema', 'passed': passed, 'detail': detail})

# Load expected input metrics for objective validation
base_metrics, base_err = safe_read_json(Path('inputs') / 'baseline_metrics.json')
after_metrics, after_err = safe_read_json(Path('inputs') / 'after_metrics.json')

# Check 3: mentions checkout-api and marker
try:
    text, err = safe_read_text(report)
    if text is None:
        passed = False
        detail = f'Cannot read report: {err}'
    else:
        passed = fuzzy_contains(text, ['checkout-api']) and fuzzy_contains(text, ['OPTIMIZE-7F3A'])
        detail = 'Report references checkout-api and the marker.' if passed else 'Report does not clearly reference checkout-api and/or marker.'
except Exception as e:
    passed = False
    detail = f'Error inspecting report text: {e}'
checks.append({'name': 'report_mentions_target_and_marker', 'passed': passed, 'detail': detail})

# Check 4: compares before/after for all three metrics categories in a fuzzy way
try:
    text, err = safe_read_text(report)
    if text is None:
        passed = False
        detail = f'Cannot read report: {err}'
    else:
        keywords = ['latency', 'throughput', 'cost', 'before', 'after']
        passed = all(fuzzy_contains(text, [k]) for k in keywords)
        detail = 'Report discusses latency, throughput, cost, and before/after comparison.' if passed else 'Report is missing one or more comparison terms.'
except Exception as e:
    passed = False
    detail = f'Error inspecting report comparison terms: {e}'
checks.append({'name': 'report_compares_metrics', 'passed': passed, 'detail': detail})

# Check 5: exactly three prioritized recommendations in report and summary
try:
    text, err = safe_read_text(report)
    data, jerr = safe_read_json(summary)
    rec_ok = False
    if text is not None and data is not None:
        # Flexible count: lines beginning with numbers or bullets mentioning recommendations
        rec_lines = [line for line in text.splitlines() if re.search(r'(^\s*\d+[\).]|^\s*[-*])', line)]
        # Prefer lines that include recommendation-like words
        rec_lines = [ln for ln in rec_lines if fuzzy_contains(ln, ['recommend', 'priorit', 'optimiz', 'index', 'cache', 'render', 'async'])]
        rec_count_report = len(rec_lines)
        rec_count_summary = len(data.get('recommendations', [])) if isinstance(data.get('recommendations', []), list) else -1
        rec_ok = (rec_count_report >= 3) and (rec_count_summary == 3)
        detail = f'report_recs={rec_count_report}, summary_recs={rec_count_summary}.'
        passed = rec_ok
    else:
        passed = False
        detail = f'Cannot parse report or summary: report_err={err if text is None else None}, summary_err={jerr if data is None else None}'
except Exception as e:
    passed = False
    detail = f'Error checking recommendations: {e}'
checks.append({'name': 'three_recommendations', 'passed': passed, 'detail': detail})

# Check 6: top bottleneck matches input hint or database is identified as worst latency pre-change
try:
    text, err = safe_read_text(report)
    data, jerr = safe_read_json(summary)
    if text is None or data is None:
        passed = False
        detail = f'Cannot read files: report_err={err}, summary_err={jerr}'
    else:
        top = str(data.get('top_bottleneck', ''))
        hint_ok = fuzzy_contains(top, ['database']) or fuzzy_contains(text, ['database'])
        if base_metrics and 'database' in base_metrics:
            # objective backup: database has highest baseline latency in provided data
            worst = max(base_metrics.items(), key=lambda kv: kv[1].get('latency_ms', -1))[0]
            hint_ok = hint_ok and fuzzy_contains(worst, ['database'])
        passed = hint_ok
        detail = f'top_bottleneck={top!r}; database identified as bottleneck.' if passed else f'Unexpected bottleneck: {top!r}'
except Exception as e:
    passed = False
    detail = f'Error checking bottleneck: {e}'
checks.append({'name': 'top_bottleneck_database', 'passed': passed, 'detail': detail})

# Compute score
try:
    total = len(checks)
    passed_n = sum(1 for c in checks if c.get('passed'))
    score = passed_n / total if total else 0.0
    overall = passed_n == total
except Exception:
    score = 0.0
    overall = False

result = {'passed': overall, 'score': score, 'checks': checks}
print(json.dumps(result, indent=2))
