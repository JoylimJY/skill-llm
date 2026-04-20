import json
import os
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def main():
    import sys
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

    try:
        out_txt = ws / 'output.txt'
        if out_txt.exists():
            txt, err = safe_read(out_txt)
            if txt is None:
                add_check('output.txt readable', False, f'read error: {err}')
            else:
                n = normalize(txt)
                ok = ('orbit payments v2' in n) and ('platform observability' in n) and ('gradual rollout' in n)
                add_check('output.txt contains summary markers', ok, 'found required marker-derived phrases' if ok else 'missing one or more required phrases')
        else:
            add_check('output.txt exists', False, 'output.txt is missing')
    except Exception as e:
        add_check('output.txt check', False, f'exception: {e}')

    try:
        plan = ws / 'optimized_plan.json'
        if plan.exists():
            data_txt, err = safe_read(plan)
            if data_txt is None:
                add_check('optimized_plan.json readable', False, f'read error: {err}')
            else:
                try:
                    data = json.loads(data_txt)
                    agents = data.get('agents', []) if isinstance(data, dict) else []
                    targets = data.get('targets', {}) if isinstance(data, dict) else {}
                    constraints = data.get('constraints', {}) if isinstance(data, dict) else {}
                    ok = (
                        isinstance(data, dict)
                        and any('db' in str(a).lower() for a in agents)
                        and any('app' in str(a).lower() for a in agents)
                        and targets.get('latency_reduction_pct') is not None
                        and targets.get('cost_reduction_pct') is not None
                        and constraints.get('rollout_mode') is not None
                    )
                    detail = 'structured plan has required sections' if ok else 'missing required fields or agent entries'
                    add_check('optimized_plan.json structure', ok, detail)
                except Exception as e:
                    add_check('optimized_plan.json parse', False, f'json parse error: {e}')
        else:
            add_check('optimized_plan.json exists', False, 'optimized_plan.json is missing')
    except Exception as e:
        add_check('optimized_plan.json check', False, f'exception: {e}')

    try:
        metrics = ws / 'metrics.csv'
        trace = ws / 'workload_trace.csv'
        ok = metrics.exists() and trace.exists()
        add_check('input artifacts present', ok, 'all required input files found' if ok else 'one or more input artifacts missing')
    except Exception as e:
        add_check('input artifacts check', False, f'exception: {e}')

    try:
        score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
        passed = all(c['passed'] for c in checks) if checks else False
        result = {'passed': passed, 'score': float(score), 'checks': checks}
        print(json.dumps(result))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': 'unexpected failure'}]}))


if __name__ == '__main__':
    main()
