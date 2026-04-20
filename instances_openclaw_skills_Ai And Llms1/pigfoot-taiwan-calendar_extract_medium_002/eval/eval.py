import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    try:
        return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text.lower())
    except Exception:
        return ""


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    try:
        workspace = Path(sys.argv[1])
    except Exception:
        workspace = Path(".")

    # Check 1: output file exists
    try:
        out_path = workspace / "output.txt"
        exists = out_path.exists()
        detail = "output.txt found" if exists else "output.txt is missing"
        checks.append({"name": "output_file_exists", "passed": exists, "detail": detail})
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": f"error checking existence: {e}"})

    # Check 2: output mentions the correct working-day status for 2025-01-06
    try:
        text, err = safe_read(workspace / "output.txt")
        if text is None:
            checks.append({"name": "status_text", "passed": False, "detail": f"could not read output.txt: {err}"})
        else:
            n = norm(text)
            target_date = "20250106"
            # 2025-01-06 is a Monday and a working day; fuzzy checks allow English/Chinese phrasing.
            has_date = target_date in n or "2025-01-06" in text or "2025/01/06" in text
            has_working = any(k in n for k in ["workingday", "workday", "isworkingday", "工作日", "上班日"])
            passed = has_date and has_working
            detail = "date and working-day status detected" if passed else f"missing date or working-day wording; normalized={n[:200]}"
            checks.append({"name": "status_text", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "status_text", "passed": False, "detail": f"error parsing output: {e}"})

    # Check 3: output mentions the next holiday after 2025-01-06
    try:
        text, err = safe_read(workspace / "output.txt")
        if text is None:
            checks.append({"name": "next_holiday", "passed": False, "detail": f"could not read output.txt: {err}"})
        else:
            n = norm(text)
            # In the provided skill data, the next holiday after 2025-01-06 is 2025-01-29 (春節)
            date_ok = "20250129" in n or "01-29" in text or "1/29" in text or "2025-01-29" in text
            holiday_ok = any(k in n for k in ["holiday", "holidays", "springfestival", "springfestival", "春節", "假日"])
            passed = date_ok and holiday_ok
            detail = "next holiday appears correct" if passed else f"missing expected next-holiday information; normalized={n[:200]}"
            checks.append({"name": "next_holiday", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "next_holiday", "passed": False, "detail": f"error parsing output: {e}"})

    # Check 4: input marker exists and remains untouched
    try:
        text, err = safe_read(workspace / "input.txt")
        if text is None:
            checks.append({"name": "input_marker", "passed": False, "detail": f"could not read input.txt: {err}"})
        else:
            passed = "TAIWAN_CALENDAR_TASK_2025_01" in text
            detail = "marker found in input.txt" if passed else "marker missing from input.txt"
            checks.append({"name": "input_marker", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "input_marker", "passed": False, "detail": f"error checking marker: {e}"})

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get("passed"))
        score = passed_count / total if total else 0.0
        passed = passed_count == total
        print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
    except Exception:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))


if __name__ == "__main__":
    main()
