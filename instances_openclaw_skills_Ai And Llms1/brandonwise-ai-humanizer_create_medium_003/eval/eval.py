import json
import os
import re
import sys
from pathlib import Path


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r"[^a-z0-9\s]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s
    except Exception:
        return ""


def main():
    checks = []
    try:
        workspace = Path(sys.argv[1])
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace argument", "passed": False, "detail": f"missing or invalid argument: {e}"}]}))
        return

    output_path = workspace / "output.txt"
    notes_path = workspace / "notes.txt"
    source_path = workspace / "draft.txt"

    # Check 1: output exists
    try:
        exists = output_path.exists()
        checks.append({"name": "output exists", "passed": exists, "detail": "output.txt found" if exists else "output.txt is missing"})
    except Exception as e:
        checks.append({"name": "output exists", "passed": False, "detail": f"error checking output.txt: {e}"})

    # Check 2: notes exists
    try:
        exists = notes_path.exists()
        checks.append({"name": "notes exists", "passed": exists, "detail": "notes.txt found" if exists else "notes.txt is missing"})
    except Exception as e:
        checks.append({"name": "notes exists", "passed": False, "detail": f"error checking notes.txt: {e}"})

    # Check 3: marker preserved in output
    try:
        src = source_path.read_text(encoding="utf-8", errors="replace") if source_path.exists() else ""
        out = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        marker = "cedar harbor protocol"
        passed = marker in normalize(out)
        checks.append({"name": "marker preserved", "passed": passed, "detail": "marker phrase present" if passed else "marker phrase not found in output"})
    except Exception as e:
        checks.append({"name": "marker preserved", "passed": False, "detail": f"error reading text: {e}"})

    # Check 4: output is meaningfully rewritten and not identical to source
    try:
        src_n = normalize(source_path.read_text(encoding="utf-8", errors="replace")) if source_path.exists() else ""
        out_n = normalize(output_path.read_text(encoding="utf-8", errors="replace")) if output_path.exists() else ""
        similar = out_n == src_n or (src_n and out_n and out_n in src_n and len(out_n) > 0)
        passed = bool(out_n) and not similar and len(out_n) > 100
        checks.append({"name": "rewritten text", "passed": passed, "detail": "output differs from source and has sufficient length" if passed else "output appears unchanged, too short, or unreadable"})
    except Exception as e:
        checks.append({"name": "rewritten text", "passed": False, "detail": f"error comparing text: {e}"})

    # Check 5: notes mention changes
    try:
        notes = notes_path.read_text(encoding="utf-8", errors="replace") if notes_path.exists() else ""
        n = normalize(notes)
        keywords = ["tone", "ai", "rewrite", "remove", "filler", "style"]
        passed = sum(1 for k in keywords if k in n) >= 2 and len(n) > 20
        checks.append({"name": "notes content", "passed": passed, "detail": "notes describe changes" if passed else "notes are missing detail or too sparse"})
    except Exception as e:
        checks.append({"name": "notes content", "passed": False, "detail": f"error reading notes: {e}"})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    score = passed_count / total if total else 0.0
    result = {"passed": passed_count == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
