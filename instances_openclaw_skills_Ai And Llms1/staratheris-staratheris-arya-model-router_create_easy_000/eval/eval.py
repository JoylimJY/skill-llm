import json
import sys
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def check_file_contains(path, needle):
    try:
        text = Path(path).read_text(encoding='utf-8', errors='ignore')
        return needle.lower() in text.lower(), f'found {needle!r}' if needle.lower() in text.lower() else f'missing {needle!r}'
    except Exception as e:
        return False, f'error reading file: {e}'


def main():
    checks = []
    workspace = Path(sys.argv[1])

    rules_path = workspace / 'inputs' / 'rules.json'
    status_path = workspace / 'inputs' / 'status_note.txt'

    try:
        exists = rules_path.exists()
        checks.append({"name": "rules file exists", "passed": exists, "detail": str(rules_path)})
    except Exception as e:
        checks.append({"name": "rules file exists", "passed": False, "detail": f'error: {e}'})

    try:
        exists = status_path.exists()
        checks.append({"name": "status note exists", "passed": exists, "detail": str(status_path)})
    except Exception as e:
        checks.append({"name": "status note exists", "passed": False, "detail": f'error: {e}'})

    try:
        ok, detail = check_file_contains(rules_path, 'openai/gpt-4o-mini')
        checks.append({"name": "cheap model configured", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "cheap model configured", "passed": False, "detail": f'error: {e}'})

    try:
        ok1, d1 = check_file_contains(rules_path, '@cheap')
        ok2, d2 = check_file_contains(rules_path, 'router auto off')
        ok = ok1 and ok2
        detail = f'{d1}; {d2}'
        checks.append({"name": "manual overrides present", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "manual overrides present", "passed": False, "detail": f'error: {e}'})

    try:
        ok1, d1 = check_file_contains(status_path, 'cheap_first')
        ok2, d2 = check_file_contains(status_path, 'daily reports should stay short')
        ok = ok1 and ok2
        detail = f'{d1}; {d2}'
        checks.append({"name": "status note marker and guidance", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "status note marker and guidance", "passed": False, "detail": f'error: {e}'})

    try:
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / len(checks) if checks else 0.0
        passed = passed_count == len(checks)
    except Exception:
        score = 0.0
        passed = False

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
