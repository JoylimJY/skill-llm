import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r"[\u2013\u2014]", "-", text)
        text = re.sub(r"[^a-z0-9\n\- ]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        return ""


def count_bullets(text):
    try:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        bullets = [line for line in lines if re.match(r"^[-*•]\s+", line)]
        return bullets
    except Exception:
        return []


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    output_path = workspace / "output.txt"
    notes_path = workspace / "notes.txt"
    marker_path = workspace / "marker.json"

    # Check 1: output exists
    try:
        exists = output_path.exists()
        checks.append({
            "name": "output_exists",
            "passed": bool(exists),
            "detail": "output.txt found" if exists else "output.txt is missing"
        })
    except Exception as e:
        checks.append({
            "name": "output_exists",
            "passed": False,
            "detail": f"error checking output existence: {e}"
        })

    # Check 2: output has exactly 3 bullets
    try:
        text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        bullets = count_bullets(text)
        passed = len(bullets) == 3
        checks.append({
            "name": "three_bullets",
            "passed": passed,
            "detail": f"found {len(bullets)} bullet lines"
        })
    except Exception as e:
        checks.append({
            "name": "three_bullets",
            "passed": False,
            "detail": f"error reading bullets: {e}"
        })

    # Check 3: mentions Groq fast inference and professional tone / no title
    try:
        text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        norm = normalize(text)
        has_groq = "groq" in norm and ("fast inference" in norm or "fast" in norm and "inference" in norm)
        no_title = not any(line.strip().lower().startswith("title") for line in text.splitlines() if line.strip())
        sentence_count_ok = True
        for line in [ln.strip() for ln in text.splitlines() if ln.strip()]:
            if re.match(r"^[-*•]\s+", line):
                content = re.sub(r"^[-*•]\s+", "", line).strip()
                # forgiving: at most two sentence terminators per bullet
                if len(re.findall(r"[.!?]", content)) > 2:
                    sentence_count_ok = False
        passed = bool(has_groq and no_title and sentence_count_ok)
        detail = f"groq_fast_inference={has_groq}, no_title={no_title}, sentence_shape_ok={sentence_count_ok}"
        checks.append({"name": "content_constraints", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({
            "name": "content_constraints",
            "passed": False,
            "detail": f"error validating content: {e}"
        })

    # Check 4: inputs exist and marker is present
    try:
        notes_ok = notes_path.exists()
        marker_ok = False
        marker_detail = "marker missing"
        if marker_path.exists():
            try:
                marker = json.loads(marker_path.read_text(encoding="utf-8"))
                marker_ok = normalize(str(marker.get("marker", ""))) == normalize("GROQ_SUMMARY_TASK_V1")
                marker_detail = f"marker={marker.get('marker', '')}"
            except Exception as e:
                marker_detail = f"malformed marker: {e}"
        passed = notes_ok and marker_ok
        checks.append({
            "name": "input_marker",
            "passed": passed,
            "detail": f"notes_exists={notes_ok}; {marker_detail}"
        })
    except Exception as e:
        checks.append({
            "name": "input_marker",
            "passed": False,
            "detail": f"error checking inputs: {e}"
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    score = passed_count / total if total else 0.0
    result = {"passed": passed_count == total, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
