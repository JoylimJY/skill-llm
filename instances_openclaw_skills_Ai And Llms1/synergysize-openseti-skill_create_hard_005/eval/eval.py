import json
import os
import re
import sys
from pathlib import Path

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: output file exists
try:
    out_path = workspace / 'output.txt'
    if out_path.exists():
        add_check('output_exists', True, 'output.txt found')
    else:
        add_check('output_exists', False, 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'error checking file existence: {e}')

# Check 2: content contains required sample ID and marker-aware classification
try:
    text = ''
    if out_path.exists():
        try:
            text = out_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            add_check('output_readable', False, f'could not read output.txt: {e}')
            text = ''
    normalized = re.sub(r'\s+', ' ', text.lower())
    sample_ok = 'bl-gbt-2025-0017' in normalized
    class_ok = 'anomaly_flagged' in normalized or 'anomaly flagged' in normalized
    add_check('contains_sample_id', sample_ok, 'sample ID present' if sample_ok else 'sample ID missing or altered')
    add_check('contains_classification', class_ok, 'classification present' if class_ok else 'expected anomaly classification not found')
except Exception as e:
    add_check('content_checks', False, f'content inspection failed: {e}')

# Check 3: report mentions the key metrics with fuzzy matching
try:
    text = ''
    if out_path.exists():
        try:
            text = out_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            add_check('metrics_readable', False, f'could not read output.txt for metrics: {e}')
            text = ''
    t = text.lower()
    metric_hits = 0
    metric_hits += 1 if ('1420.405' in t or '1420.41' in t or '1420 mhz' in t or 'water hole' in t) else 0
    metric_hits += 1 if ('4.8' in t or '4 hz' in t or 'narrowband' in t) else 0
    metric_hits += 1 if ('-0.31' in t or 'drift' in t or 'doppler' in t) else 0
    metric_hits += 1 if ('18.7' in t or 'snr' in t) else 0
    passed = metric_hits >= 3
    add_check('mentions_key_metrics', passed, f'{metric_hits}/4 metrics matched' if text else 'output missing')
except Exception as e:
    add_check('mentions_key_metrics', False, f'metric parsing failed: {e}')

# Check 4: recommendation line exists and is concise-ish
try:
    text = ''
    if out_path.exists():
        try:
            text = out_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            add_check('recommendation_readable', False, f'could not read output.txt for recommendation: {e}')
            text = ''
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rec_ok = any(re.search(r'(recommend|follow.?up|investigate|re.?scan|review)', ln, re.I) for ln in lines)
    length_ok = len(text) < 1200
    add_check('has_recommendation', rec_ok, 'recommendation-like line found' if rec_ok else 'no recommendation line found')
    add_check('concise_enough', length_ok, f'length={len(text)}' if text else 'output missing')
except Exception as e:
    add_check('recommendation_checks', False, f'recommendation parsing failed: {e}')

# Score calculation
try:
    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    score = passed_count / total
    passed = passed_count == total
except Exception:
    score = 0.0
    passed = False

result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
