import json
import re
import sys
from pathlib import Path


def norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='replace'), None
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    summary_path = workspace / 'context' / 'summary.txt'
    history_path = workspace / 'context' / 'history.txt'

    try:
        summary_exists = summary_path.exists()
    except Exception as e:
        summary_exists = False
        checks.append({"name": "summary file exists", "passed": False, "detail": f"exception checking file: {e}"})
    else:
        checks.append({"name": "summary file exists", "passed": summary_exists, "detail": "found" if summary_exists else "missing context/summary.txt"})

    if summary_exists:
        try:
            summary = summary_path.read_text(encoding='utf-8', errors='replace')
            nsummary = norm(summary)
            has_marker = 'marker alpha 7812' in nsummary
            has_recent = ('latest four turns' in nsummary) or ('last 4 turns' in nsummary) or ('recent turns' in nsummary)
            has_pending = ('todo' in nsummary) or ('follow up' in nsummary) or ('pending decision' in nsummary) or ('open decision' in nsummary)
            checks.append({"name": "preserves marker", "passed": has_marker, "detail": "marker found" if has_marker else "marker missing"})
            checks.append({"name": "mentions recent turns", "passed": has_recent, "detail": "recent-turn language present" if has_recent else "recent-turn language missing"})
            checks.append({"name": "surfaces pending items", "passed": has_pending, "detail": "pending/task language present" if has_pending else "no pending-item language found"})
        except Exception as e:
            checks.extend([
                {"name": "preserves marker", "passed": False, "detail": f"read/parse error: {e}"},
                {"name": "mentions recent turns", "passed": False, "detail": f"read/parse error: {e}"},
                {"name": "surfaces pending items", "passed": False, "detail": f"read/parse error: {e}"},
            ])
    else:
        checks.extend([
            {"name": "preserves marker", "passed": False, "detail": "summary missing"},
            {"name": "mentions recent turns", "passed": False, "detail": "summary missing"},
            {"name": "surfaces pending items", "passed": False, "detail": "summary missing"},
        ])

    try:
        history_exists = history_path.exists()
    except Exception as e:
        history_exists = False
        checks.append({"name": "history file exists", "passed": False, "detail": f"exception checking file: {e}"})
    else:
        checks.append({"name": "history file exists", "passed": history_exists, "detail": "found" if history_exists else "missing context/history.txt"})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = passed / total if total else 0.0
    result = {"passed": passed == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}))