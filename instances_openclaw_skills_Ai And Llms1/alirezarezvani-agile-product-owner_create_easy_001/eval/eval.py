import json
import re
import sys
from pathlib import Path


def norm(text):
    try:
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def find_file(workspace, candidates):
    try:
        for name in candidates:
            p = Path(workspace) / name
            if p.exists() and p.is_file():
                return p
    except Exception:
        return None
    return None


def main():
    checks = []
    ws = sys.argv[1] if len(sys.argv) > 1 else "."
    out = find_file(ws, ["sprint_plan.md", "sprint-plan.md", "plan.md", "output.txt"])

    try:
        if out is None:
            checks.append({"name": "output file exists", "passed": False, "detail": "No expected output file found (looked for sprint_plan.md and common variants)."})
            text = ""
        else:
            text = out.read_text(encoding="utf-8", errors="ignore")
            checks.append({"name": "output file exists", "passed": True, "detail": f"Found {out.name}."})
    except Exception as e:
        checks.append({"name": "output file exists", "passed": False, "detail": f"Could not read output file: {e}"})
        text = ""

    ntext = norm(text)

    required_snippets = [
        ("sprint goal", "sprint goal"),
        ("committed stories", "committed"),
        ("stretch stories", "stretch"),
        ("capacity note", "capacity"),
        ("marker alpha", "sprint goal alpha 42"),
        ("marker capacity", "capacity marker 17"),
    ]

    for name, needle in required_snippets:
        try:
            passed = needle in ntext
            detail = f"Matched '{needle}' in content." if passed else f"Did not find '{needle}' in content."
            checks.append({"name": name, "passed": passed, "detail": detail})
        except Exception as e:
            checks.append({"name": name, "passed": False, "detail": f"Check failed with error: {e}"})

    try:
        committed_ids = ["us 101", "us 102", "us 103", "us 104"]
        stretch_ids = ["us 105", "us 106"]
        committed_hits = sum(1 for x in committed_ids if x in ntext)
        stretch_hits = sum(1 for x in stretch_ids if x in ntext)
        passed = committed_hits >= 4 and stretch_hits >= 2
        checks.append({
            "name": "story coverage",
            "passed": passed,
            "detail": f"Found {committed_hits}/4 committed story ids and {stretch_hits}/2 stretch story ids."
        })
    except Exception as e:
        checks.append({"name": "story coverage", "passed": False, "detail": f"Check failed with error: {e}"})

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get("passed"))
        score = passed_count / total if total else 0.0
        passed = passed_count == total
    except Exception:
        score = 0.0
        passed = False

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
