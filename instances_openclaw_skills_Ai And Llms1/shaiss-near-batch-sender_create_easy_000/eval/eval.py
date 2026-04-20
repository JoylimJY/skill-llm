import json
import os
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    # Check 1: recipients.json exists and is valid JSON with marker content.
    try:
        p = workspace / "recipients.json"
        if not p.exists():
            checks.append({"name": "recipients_file_exists", "passed": False, "detail": "recipients.json is missing"})
        else:
            data = json.loads(p.read_text(encoding="utf-8"))
            recipients = data.get("recipients", []) if isinstance(data, dict) else []
            names = [str(item.get("account", "")).strip().lower() for item in recipients if isinstance(item, dict)]
            amounts = [str(item.get("amount", "")).strip() for item in recipients if isinstance(item, dict)]
            ok = ("bob.near" in names) and ("carol.near" in names) and ("1.5" in amounts) and ("0.5" in amounts)
            checks.append({"name": "recipients_content", "passed": ok, "detail": f"Found accounts={names}, amounts={amounts}"})
    except Exception as e:
        checks.append({"name": "recipients_content", "passed": False, "detail": f"Error reading/parsing recipients.json: {e}"})

    # Check 2: marker file exists and contains marker string.
    try:
        p = workspace / "marker.txt"
        if not p.exists():
            checks.append({"name": "marker_file_exists", "passed": False, "detail": "marker.txt is missing"})
        else:
            text = p.read_text(encoding="utf-8", errors="ignore")
            ok = "NEAR_BATCH_MARKER" in text.upper()
            checks.append({"name": "marker_content", "passed": ok, "detail": f"Content preview: {text[:80]}"})
    except Exception as e:
        checks.append({"name": "marker_content", "passed": False, "detail": f"Error reading marker.txt: {e}"})

    # Check 3: output file from task should exist (gracefully fail if missing).
    try:
        p = workspace / "output.txt"
        if not p.exists():
            checks.append({"name": "output_exists", "passed": False, "detail": "output.txt is missing"})
        else:
            text = p.read_text(encoding="utf-8", errors="ignore")
            ok = bool(text.strip())
            checks.append({"name": "output_exists", "passed": ok, "detail": f"output.txt present, length={len(text)}"})
    except Exception as e:
        checks.append({"name": "output_exists", "passed": False, "detail": f"Error reading output.txt: {e}"})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get("passed"))
    score = passed_count / total if total else 0.0
    result = {"passed": passed_count == total, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": "Unhandled error in eval script"}]}
        print(json.dumps(result))
