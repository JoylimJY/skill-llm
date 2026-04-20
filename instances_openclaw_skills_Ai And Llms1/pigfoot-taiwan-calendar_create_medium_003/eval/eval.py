import json
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s: str) -> str:
    try:
        s = s.lower()
        s = re.sub(r"[\s\t\r\n]+", " ", s)
        s = re.sub(r"[\.,;:!\-_/\\()\[\]{}'\"`]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s
    except Exception:
        return ""


def fuzzy_contains(text: str, patterns):
    t = normalize(text)
    for p in patterns:
        if normalize(p) in t:
            return True
    return False


def main():
    checks = []
    try:
        workspace = Path(sys.argv[1])
    except Exception as e:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "workspace-arg", "passed": False, "detail": f"Invalid workspace argument: {e}"}]}
        print(json.dumps(result, ensure_ascii=False))
        return

    # 1) Required input files exist
    for fname in ["dates.txt", "instructions.json"]:
        p = workspace / fname
        passed = p.exists()
        checks.append({"name": f"input-exists-{fname}", "passed": passed, "detail": f"Found" if passed else f"Missing: {fname}"})

    # 2) Output exists
    out = workspace / "report.txt"
    if out.exists():
        text, err = safe_read(out)
        if text is None:
            checks.append({"name": "output-readable", "passed": False, "detail": f"Could not read report.txt: {err}"})
            text = ""
        else:
            checks.append({"name": "output-readable", "passed": True, "detail": "report.txt is readable"})
    else:
        checks.append({"name": "output-present", "passed": False, "detail": "report.txt is missing"})
        text = ""

    # 3) Content checks: must mention all target dates in a reasonable way
    targets = ["2025-01-01", "2025-01-04", "2025-01-06", "2025-01-29"]
    for d in targets:
        passed = d in text or d.replace("-", "/") in text
        checks.append({"name": f"mentions-{d}", "passed": passed, "detail": f"Date {'present' if passed else 'not present'} in report"})

    # 4) Category checks using fuzzy matching on expected labels
    expected_groups = {
        "holiday": ["2025-01-01", "new year", "元旦", "holiday", "non working"],
        "weekend": ["2025-01-04", "weekend", "sat", "星期六"],
        "working-day": ["2025-01-06", "working day", "workday", "monday", "週一"],
        "holiday-2": ["2025-01-29", "spring festival", "chinese new year", "春節", "holiday"],
    }
    for name, pats in expected_groups.items():
        passed = fuzzy_contains(text, pats)
        checks.append({"name": f"category-{name}", "passed": passed, "detail": f"Matched patterns: {', '.join(pats)}"})

    # 5) Must be a short report-like file, not empty
    try:
        line_count = len([ln for ln in text.splitlines() if ln.strip()])
        passed = line_count >= 3
        checks.append({"name": "nontrivial-report", "passed": passed, "detail": f"Non-empty lines: {line_count}"})
    except Exception as e:
        checks.append({"name": "nontrivial-report", "passed": False, "detail": f"Line counting failed: {e}"})

    passed_count = sum(1 for c in checks if c.get("passed"))
    score = passed_count / len(checks) if checks else 0.0
    result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
