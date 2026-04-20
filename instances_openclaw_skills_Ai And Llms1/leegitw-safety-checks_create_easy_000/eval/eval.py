import json
import os
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

checks = []
score = 0.0


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, f"Could not read {path}: {e}"


def main(workspace_dir):
    base = Path(workspace_dir)

    # Check 1: config file exists and is parseable enough for key inspection
    cfg_path = base / '.openclaw' / 'safety-checks.yaml'
    try:
        if not cfg_path.exists():
            add_check('config exists', False, f'Missing file: {cfg_path}')
        else:
            text = cfg_path.read_text(encoding='utf-8', errors='replace')
            lower = text.lower()
            has_model = 'model' in lower
            has_expected = 'expected' in lower
            has_strict = 'strict' in lower
            has_pin = 'anthropic-opus-4-5-20251101' in lower
            add_check(
                'config contains pinned model and strict mode',
                bool(has_model and has_expected and has_strict and has_pin),
                f'Found model={has_model}, expected={has_expected}, strict={has_strict}, pin={has_pin}'
            )
    except Exception as e:
        add_check('config contains pinned model and strict mode', False, f'Error while checking config: {e}')

    # Check 2: fallback chains exist
    try:
        if not cfg_path.exists():
            add_check('fallback chains exist', False, 'Config file missing, cannot verify fallbacks')
        else:
            text = cfg_path.read_text(encoding='utf-8', errors='replace').lower()
            model_ok = ('fallbacks' in text and 'model' in text and 'primary-model' in text and 'fallback-model' in text)
            storage_ok = ('storage' in text and 'primary-path' in text and 'backup-path' in text)
            add_check('fallback chains exist', bool(model_ok and storage_ok), f'model_ok={model_ok}, storage_ok={storage_ok}')
    except Exception as e:
        add_check('fallback chains exist', False, f'Error while checking fallbacks: {e}')

    # Check 3: output log exists and contains marker
    log_path = base / 'output' / 'safety' / 'session-state.log'
    try:
        if not log_path.exists():
            add_check('session log exists with marker', False, f'Missing file: {log_path}')
        else:
            text = log_path.read_text(encoding='utf-8', errors='replace')
            marker_ok = 'session_ok' in text.lower()
            add_check('session log exists with marker', bool(marker_ok), f'Marker present={marker_ok}')
    except Exception as e:
        add_check('session log exists with marker', False, f'Error while checking log: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    score = (passed_count / total) if total else 0.0
    passed = passed_count == total
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            checks.append({"name": "argument count", "passed": False, "detail": "Expected exactly one argument: workspace directory path"})
            print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))
        else:
            main(sys.argv[1])
    except Exception as e:
        # Absolute last-resort fallback; never crash
        try:
            checks.append({"name": "fatal error handling", "passed": False, "detail": f'Unhandled error: {e}'})
            passed_count = sum(1 for c in checks if c['passed'])
            total = len(checks) if checks else 1
            score = passed_count / total
            print(json.dumps({"passed": False, "score": score, "checks": checks}, ensure_ascii=False))
        except Exception:
            print('{"passed": false, "score": 0.0, "checks": []}')
