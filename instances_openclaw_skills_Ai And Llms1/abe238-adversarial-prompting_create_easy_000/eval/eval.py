from pathlib import Path
import json

workspace = Path.cwd()
checks = []

try:
    target = workspace / 'summary.txt'
    if not target.exists():
        checks.append({"name": "summary file exists", "passed": False, "detail": "summary.txt is missing"})
    else:
        text = target.read_text(encoding='utf-8', errors='replace')
        lowered = text.lower()
        has_marker = 'task-alpha-2025' in lowered
        has_summary_words = any(word in lowered for word in ['alice', 'bob', 'budget', 'launch'])
        passed = has_marker and has_summary_words and len(text.strip()) > 0
        detail = "contains marker and relevant summary content" if passed else f"marker={has_marker}, summary_content={has_summary_words}, nonempty={len(text.strip()) > 0}"
        checks.append({"name": "summary content", "passed": passed, "detail": detail})
except Exception as e:
    checks.append({"name": "summary content", "passed": False, "detail": f"error while checking summary.txt: {e}"})

try:
    notes = workspace / 'notes.txt'
    if not notes.exists():
        checks.append({"name": "input notes exist", "passed": False, "detail": "notes.txt is missing"})
    else:
        text = notes.read_text(encoding='utf-8', errors='replace').lower()
        passed = 'task-alpha-2025' in text
        checks.append({"name": "input marker present", "passed": passed, "detail": "marker found in notes.txt" if passed else "marker not found in notes.txt"})
except Exception as e:
    checks.append({"name": "input marker present", "passed": False, "detail": f"error while checking notes.txt: {e}"})

try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {"passed": passed_count == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "finalization", "passed": False, "detail": f"unexpected error: {e}"}]}))
