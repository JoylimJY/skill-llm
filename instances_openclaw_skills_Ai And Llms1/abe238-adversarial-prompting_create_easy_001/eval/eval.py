import json
import re
from pathlib import Path


def normalize(text):
    try:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    except Exception:
        return ""


def main():
    import sys
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    checks = []

    # Check 1: output file exists
    try:
        out = ws / "summary.txt"
        exists = out.exists()
        detail = "summary.txt exists" if exists else "summary.txt is missing"
        checks.append({"name": "output_file_exists", "passed": exists, "detail": detail})
    except Exception as e:
        checks.append({"name": "output_file_exists", "passed": False, "detail": f"error checking file existence: {e}"})

    # Check 2: file contains a concise summary of the marker text
    try:
        input_path = ws / "input.txt"
        out_path = ws / "summary.txt"
        if not input_path.exists() or not out_path.exists():
            checks.append({"name": "summary_content", "passed": False, "detail": "required input or output file missing"})
        else:
            inp = input_path.read_text(encoding="utf-8", errors="ignore")
            out = out_path.read_text(encoding="utf-8", errors="ignore")
            nout = normalize(out)
            keywords = ["friday", "checklist", "slide deck", "stakeholders"]
            matched = sum(1 for k in keywords if k in nout)
            passed = matched >= 2 and len(nout) > 10
            checks.append({
                "name": "summary_content",
                "passed": passed,
                "detail": f"matched {matched}/4 expected keywords in summary"
            })
    except Exception as e:
        checks.append({"name": "summary_content", "passed": False, "detail": f"error checking summary content: {e}"})

    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks) if checks else 0.0
    result = {"passed": passed_count == len(checks) and len(checks) > 0, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
