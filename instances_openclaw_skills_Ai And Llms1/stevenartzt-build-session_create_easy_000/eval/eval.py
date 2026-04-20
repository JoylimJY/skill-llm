import json
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise e


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def check_contains(text: str, phrases):
    t = norm(text)
    return all(norm(p) in t for p in phrases)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    target = workspace / "session_log.md"

    # Check 1: file exists
    try:
        exists = target.exists()
        checks.append({
            "name": "session_log_exists",
            "passed": bool(exists),
            "detail": "session_log.md found" if exists else "session_log.md is missing",
        })
    except Exception as e:
        checks.append({"name": "session_log_exists", "passed": False, "detail": f"error checking file existence: {e}"})

    # Check 2: title/date structure
    try:
        text = safe_read(target) if target.exists() else ""
        has_title = bool(re.search(r"^\s*#\s+.*2025.*", text, flags=re.IGNORECASE | re.MULTILINE))
        checks.append({
            "name": "title_includes_date",
            "passed": has_title,
            "detail": "title includes a 2025 date marker" if has_title else "title does not appear to include the expected date",
        })
    except Exception as e:
        checks.append({"name": "title_includes_date", "passed": False, "detail": f"error reading/parsing session_log.md: {e}"})

    # Check 3: required sections
    try:
        text = safe_read(target) if target.exists() else ""
        required = ["what i built", "key insights", "git"]
        ok = check_contains(text, required)
        checks.append({
            "name": "required_sections",
            "passed": ok,
            "detail": "contains What I Built, Key Insights, and Git sections" if ok else "one or more required sections are missing",
        })
    except Exception as e:
        checks.append({"name": "required_sections", "passed": False, "detail": f"error validating sections: {e}"})

    # Check 4: at least one bullet under Key Insights
    try:
        text = safe_read(target) if target.exists() else ""
        m = re.search(r"key insights\s*\n(?P<body>.*?)(?:\n\s*#|\Z)", text, flags=re.IGNORECASE | re.DOTALL)
        body = m.group("body") if m else ""
        bullet_ok = bool(re.search(r"^\s*[-*+]\s+\S+", body, flags=re.MULTILINE))
        checks.append({
            "name": "key_insights_bullet",
            "passed": bullet_ok,
            "detail": "found at least one bullet point under Key Insights" if bullet_ok else "no bullet point found under Key Insights",
        })
    except Exception as e:
        checks.append({"name": "key_insights_bullet", "passed": False, "detail": f"error checking bullets: {e}"})

    # Check 5: Git status line present and non-empty
    try:
        text = safe_read(target) if target.exists() else ""
        m = re.search(r"git\s*[:\-]?\s*(.+)", text, flags=re.IGNORECASE)
        ok = bool(m and m.group(1).strip())
        checks.append({
            "name": "git_status_line",
            "passed": ok,
            "detail": f"git status line found: {m.group(1).strip()}" if ok else "git status line missing or empty",
        })
    except Exception as e:
        checks.append({"name": "git_status_line", "passed": False, "detail": f"error checking git line: {e}"})

    passed_count = sum(1 for c in checks if c.get("passed"))
    score = passed_count / len(checks) if checks else 0.0
    result = {
        "passed": passed_count == len(checks),
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": f"unexpected error: {e}"}]}))
