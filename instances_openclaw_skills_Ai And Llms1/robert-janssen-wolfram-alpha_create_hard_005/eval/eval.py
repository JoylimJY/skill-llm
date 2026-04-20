import json
import math
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())
    except Exception:
        return ''

checks = []
workspace = None
try:
    import sys
    workspace = Path(sys.argv[1])
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_parse", "passed": False, "detail": f"invalid workspace argument: {e}"}]}))
    raise SystemExit(0)

# Check 1: report exists
try:
    report_path = workspace / 'output' / 'report.txt'
    if report_path.exists():
        checks.append({"name": "report_exists", "passed": True, "detail": "output/report.txt found"})
    else:
        checks.append({"name": "report_exists", "passed": False, "detail": "output/report.txt is missing"})
except Exception as e:
    checks.append({"name": "report_exists", "passed": False, "detail": f"error checking report: {e}"})

# Check 2: summary json exists and parses
summary = None
try:
    summary_path = workspace / 'output' / 'summary.json'
    if not summary_path.exists():
        checks.append({"name": "summary_exists", "passed": False, "detail": "output/summary.json is missing"})
    else:
        try:
            summary = json.loads(summary_path.read_text(encoding='utf-8'))
            checks.append({"name": "summary_parses", "passed": True, "detail": "summary.json parsed successfully"})
        except Exception as e:
            checks.append({"name": "summary_parses", "passed": False, "detail": f"summary.json parse error: {e}"})
except Exception as e:
    checks.append({"name": "summary_exists", "passed": False, "detail": f"error checking summary: {e}"})

# Check 3: marker text in report
try:
    text, err = safe_read_text(workspace / 'output' / 'report.txt')
    if text is None:
        checks.append({"name": "marker_in_report", "passed": False, "detail": f"cannot read report: {err}"})
    else:
        ok = 'wa-audit-2025' in normalize(text)
        checks.append({"name": "marker_in_report", "passed": ok, "detail": "marker present" if ok else "marker string missing from report"})
except Exception as e:
    checks.append({"name": "marker_in_report", "passed": False, "detail": f"error checking marker: {e}"})

# Check 4: CSV summary values
try:
    import csv
    csv_path = workspace / 'data' / 'measurements.csv'
    values = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                values.append(float(row.get('value', '').strip()))
            except Exception:
                pass
    if len(values) < 2:
        checks.append({"name": "csv_stats", "passed": False, "detail": "not enough numeric values in CSV"})
    else:
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        stdev = math.sqrt(var)
        mn, mx = min(values), max(values)
        detail = f"expected mean={mean:.4f}, stdev={stdev:.4f}, min={mn:.4f}, max={mx:.4f}"
        ok = False
        if text is not None:
            ntext = normalize(text)
            ok = all(tok in ntext for tok in [f"mean {mean:.4f}".replace('.', ''),])
        # more forgiving numeric presence checks
        if text is not None:
            candidates = [f"{mean:.4f}", f"{stdev:.4f}", f"{mn:.4f}", f"{mx:.4f}"]
            ok = all(any(c.replace('.', '')[:4] in normalize(text) or c[:5] in text for c in [cand]) for cand in candidates)
        checks.append({"name": "csv_stats", "passed": ok, "detail": detail})
except Exception as e:
    checks.append({"name": "csv_stats", "passed": False, "detail": f"error computing CSV stats: {e}"})

# Check 5: summary json schema / verified flag
try:
    if summary is None:
        checks.append({"name": "summary_verified", "passed": False, "detail": "summary.json not available"})
    else:
        verified = bool(summary.get('verified', False))
        has_keys = all(k in summary for k in ['csv', 'wolfram']) or all(k in summary for k in ['mean', 'stdev'])
        ok = verified and isinstance(summary, dict)
        checks.append({"name": "summary_verified", "passed": ok, "detail": f"verified={verified}, keys_present={has_keys}"})
except Exception as e:
    checks.append({"name": "summary_verified", "passed": False, "detail": f"error checking summary fields: {e}"})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / max(len(checks), 1)
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result))