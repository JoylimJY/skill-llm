import json
import sys
from pathlib import Path


def normalize(s):
    try:
        return "".join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ""


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: config file exists
    try:
        config_path = workspace / "config.json"
        if not config_path.exists():
            checks.append({"name": "config_exists", "passed": False, "detail": "config.json is missing"})
        else:
            checks.append({"name": "config_exists", "passed": True, "detail": "config.json exists"})
    except Exception as e:
        checks.append({"name": "config_exists", "passed": False, "detail": f"error checking config existence: {e}"})

    # Check 2: config contents
    try:
        config_path = workspace / "config.json"
        if not config_path.exists():
            checks.append({"name": "config_contents", "passed": False, "detail": "cannot inspect missing config.json"})
        else:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            letter_ok = normalize(data.get("letter")) == normalize("C")
            name_ok = normalize(data.get("name")) == normalize("CLAUDE")
            timeout_val = data.get("idle_timeout")
            timeout_ok = False
            try:
                timeout_ok = int(timeout_val) == 600
            except Exception:
                timeout_ok = False
            marker_ok = normalize(data.get("marker")) == normalize("INPUT_MARKER_47A9")
            passed = letter_ok and name_ok and timeout_ok and marker_ok
            detail = f"letter_ok={letter_ok}, name_ok={name_ok}, timeout_ok={timeout_ok}, marker_ok={marker_ok}"
            checks.append({"name": "config_contents", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "config_contents", "passed": False, "detail": f"error reading/parsing config: {e}"})

    # Check 3: notes marker file
    try:
        notes_path = workspace / "notes.txt"
        if not notes_path.exists():
            checks.append({"name": "marker_file", "passed": False, "detail": "notes.txt is missing"})
        else:
            txt = notes_path.read_text(encoding="utf-8", errors="ignore")
            passed = normalize("INPUT_MARKER_47A9") in normalize(txt)
            checks.append({"name": "marker_file", "passed": passed, "detail": "marker found" if passed else "marker not found in notes.txt"})
    except Exception as e:
        checks.append({"name": "marker_file", "passed": False, "detail": f"error reading notes.txt: {e}"})

    passed_count = sum(1 for c in checks if c.get("passed"))
    total = len(checks) if checks else 1
    score = passed_count / total
    result = {"passed": passed_count == total, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
