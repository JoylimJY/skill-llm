import json
import os
import re
import sys
from pathlib import Path


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]+', '', s)
        return s
    except Exception:
        return ''


def main():
    checks = []
    total = 5
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: output file exists
    try:
        p = workspace / 'router.py'
        ok = p.exists()
        checks.append({"name": "router.py exists", "passed": ok, "detail": "found" if ok else "missing"})
    except Exception as e:
        checks.append({"name": "router.py exists", "passed": False, "detail": str(e)})

    # Check 2: rules.json has expected daily report keywords and response policies
    try:
        p = workspace / 'rules.json'
        if not p.exists():
            checks.append({"name": "rules.json content", "passed": False, "detail": "missing"})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            daily = ' '.join(data.get('signals', {}).get('daily_report_keywords', []))
            policies = data.get('response_policies', {})
            ok = ('daily report' in daily.lower()) and ('default' in policies) and ('cheap' in policies)
            detail = f"daily_keywords={bool(daily)} policies={list(policies.keys())}"
            checks.append({"name": "rules.json content", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "rules.json content", "passed": False, "detail": str(e)})

    # Check 3: state.json exists and has auto mode / feedback structure
    try:
        p = workspace / 'state.json'
        if not p.exists():
            checks.append({"name": "state.json content", "passed": False, "detail": "missing"})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            fb = data.get('feedback', {})
            ok = normalize(data.get('mode', '')) == 'auto' and 'too_expensive' in fb and 'too_weak' in fb
            checks.append({"name": "state.json content", "passed": ok, "detail": f"mode={data.get('mode')} feedback_keys={list(fb.keys())}"})
    except Exception as e:
        checks.append({"name": "state.json content", "passed": False, "detail": str(e)})

    # Check 4: marker files created
    try:
        marker = workspace / 'marker.txt'
        if not marker.exists():
            checks.append({"name": "marker file", "passed": False, "detail": "missing"})
        else:
            txt = marker.read_text(encoding='utf-8', errors='ignore')
            ok = 'arya-router' in normalize(txt) or 'marker' in normalize(txt)
            checks.append({"name": "marker file", "passed": ok, "detail": txt.strip()[:80]})
    except Exception as e:
        checks.append({"name": "marker file", "passed": False, "detail": str(e)})

    # Check 5: sample inputs exist and contain marker content
    try:
        samples = ['daily_report_input.txt', 'heavy_input.txt', 'override_input.txt', 'status_input.txt']
        present = []
        marked = 0
        for s in samples:
            fp = workspace / s
            if fp.exists():
                present.append(s)
                try:
                    t = fp.read_text(encoding='utf-8', errors='ignore')
                    if 'MARKER-ARYA-ROUTER-001' in t:
                        marked += 1
                except Exception:
                    pass
        ok = len(present) == len(samples) and marked == len(samples)
        checks.append({"name": "sample inputs", "passed": ok, "detail": f"present={present} marked={marked}/{len(samples)}"})
    except Exception as e:
        checks.append({"name": "sample inputs", "passed": False, "detail": str(e)})

    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total
    passed = passed_count == total
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
