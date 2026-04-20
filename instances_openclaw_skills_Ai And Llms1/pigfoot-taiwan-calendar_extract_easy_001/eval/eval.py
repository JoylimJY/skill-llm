import json
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = str(text)
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[\u3000\t\r\n]+", " ", text)
        return text.strip()
    except Exception:
        return ""


def fuzzy_contains(text, patterns):
    t = normalize(text)
    return all(p in t for p in patterns)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Check 1: file exists
    try:
        target = workspace / "taiwan_calendar_note.md"
        exists = target.exists()
        checks.append({
            "name": "output file exists",
            "passed": bool(exists),
            "detail": "Found taiwan_calendar_note.md" if exists else "taiwan_calendar_note.md is missing"
        })
    except Exception as e:
        checks.append({
            "name": "output file exists",
            "passed": False,
            "detail": f"Error while checking file existence: {e}"
        })

    # Check 2: content includes next working day after 2025-01-06
    try:
        text = (workspace / "taiwan_calendar_note.md").read_text(encoding="utf-8")
        patterns = ["2025", "01", "07"]
        # Flexible acceptance for the next working day; allow mention of Monday / 週一 / Monday
        day_ok = bool(re.search(r"(monday|週一|星期一|mon\b)", normalize(text)))
        workday_ok = fuzzy_contains(text, patterns) and day_ok
        checks.append({
            "name": "mentions next working day",
            "passed": bool(workday_ok),
            "detail": "Contains a plausible reference to 2025-01-07 and Monday-like wording" if workday_ok else "Missing or unclear next working day information"
        })
    except Exception as e:
        checks.append({
            "name": "mentions next working day",
            "passed": False,
            "detail": f"Error while reading/parsing note: {e}"
        })

    # Check 3: content includes next holiday after 2025-01-06
    try:
        text = (workspace / "taiwan_calendar_note.md").read_text(encoding="utf-8")
        # Flexible matching for 2025-01-29 and holiday label / Chinese holiday wording
        date_ok = bool(re.search(r"2025\s*[-/]\s*0?1\s*[-/]\s*2?9", normalize(text)))
        holiday_ok = bool(re.search(r"(holiday|假日|國定假日|春節|new year|lunar new year)", normalize(text)))
        next_holiday_ok = date_ok and holiday_ok
        checks.append({
            "name": "mentions next holiday",
            "passed": bool(next_holiday_ok),
            "detail": "Contains a plausible reference to 2025-01-29 and a holiday label" if next_holiday_ok else "Missing or unclear next holiday information"
        })
    except Exception as e:
        checks.append({
            "name": "mentions next holiday",
            "passed": False,
            "detail": f"Error while reading/parsing note: {e}"
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    score = (passed_count / total) if total else 0.0
    result = {
        "passed": passed_count == total,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
