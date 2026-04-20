import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    try:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    except Exception:
        return ""


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []
    score = 0.0

    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    out = workspace / "output.md"
    if out.exists():
        text, err = safe_read(out)
        if text is None:
            add("output exists and readable", False, f"Could not read output.md: {err}")
        else:
            n = norm(text)
            has_summary = any(k in n for k in ["summary", "meeting summary", "progress summary"])
            has_actions = any(k in n for k in ["action items", "actions", "next steps"])
            has_next = any(k in n for k in ["next steps", "follow up", "next session"])
            marker_like = "mark" in n and "session" in n
            add("includes summary section", has_summary, "Found summary language." if has_summary else "No clear summary section found.")
            add("includes action items", has_actions, "Found action-oriented language." if has_actions else "No clear action items section found.")
            add("includes next steps", has_next, "Found next-steps language." if has_next else "No clear next-steps section found.")
            add("concise markdown report", len(text) > 50 and len(text) < 5000, f"Output length is {len(text)} characters.")
    else:
        add("output exists and readable", False, "output.md is missing.")
        add("includes summary section", False, "Skipped because file missing.")
        add("includes action items", False, "Skipped because file missing.")
        add("includes next steps", False, "Skipped because file missing.")
        add("concise markdown report", False, "Skipped because file missing.")

    expected_marker = "MARKER-7F3A-BUILD-SESSION"
    marker_file = workspace / "reference_marker.txt"
    if marker_file.exists():
        text, err = safe_read(marker_file)
        if text is None:
            add("input marker available", False, f"Could not read reference_marker.txt: {err}")
        else:
            add("input marker available", expected_marker.lower() in text.lower(), "Marker present." if expected_marker.lower() in text.lower() else "Marker not found in reference file.")
    else:
        add("input marker available", False, "reference_marker.txt is missing.")

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks) if checks else 1
    score = passed_count / total
    passed = all(c["passed"] for c in checks)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))


if __name__ == "__main__":
    main()
