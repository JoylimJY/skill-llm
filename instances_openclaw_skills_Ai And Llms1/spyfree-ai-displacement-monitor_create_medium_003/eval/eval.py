import json
import os
import sys
from pathlib import Path


def normalize(s):
    try:
        return "".join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ""


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main():
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    checks = []

    # Check 1: required input file exists and has marker
    try:
        marker_path = ws / "marker.txt"
        if not marker_path.exists():
            checks.append({"name": "marker file exists", "passed": False, "detail": "marker.txt missing"})
        else:
            content, err = safe_read(marker_path)
            if content is None:
                checks.append({"name": "marker file exists", "passed": False, "detail": f"could not read marker.txt: {err}"})
            else:
                ok = "aidisplacementmonitormarker7f3a" in normalize(content)
                checks.append({"name": "marker file exists", "passed": ok, "detail": "marker content verified" if ok else "marker content not found"})
    except Exception as e:
        checks.append({"name": "marker file exists", "passed": False, "detail": f"exception: {e}"})

    # Check 2: output.json exists
    try:
        out_path = ws / "output.json"
        ok = out_path.exists()
        checks.append({"name": "output.json exists", "passed": ok, "detail": "found" if ok else "output.json missing"})
    except Exception as e:
        checks.append({"name": "output.json exists", "passed": False, "detail": f"exception: {e}"})

    # Check 3: JSON structure
    parsed = None
    try:
        if (ws / "output.json").exists():
            content, err = safe_read(ws / "output.json")
            if content is None:
                checks.append({"name": "output JSON parsable", "passed": False, "detail": f"could not read output.json: {err}"})
            else:
                try:
                    parsed = json.loads(content)
                    ok = isinstance(parsed, dict)
                    checks.append({"name": "output JSON parsable", "passed": ok, "detail": "parsed" if ok else "top-level JSON is not an object"})
                except Exception as e:
                    checks.append({"name": "output JSON parsable", "passed": False, "detail": f"json parse failed: {e}"})
        else:
            checks.append({"name": "output JSON parsable", "passed": False, "detail": "output.json missing"})
    except Exception as e:
        checks.append({"name": "output JSON parsable", "passed": False, "detail": f"exception: {e}"})

    # Check 4: required keys
    try:
        required = ["asOf", "signals", "composite", "confidence", "gaps", "notes"]
        if isinstance(parsed, dict):
            missing = [k for k in required if k not in parsed]
            ok = not missing
            checks.append({"name": "required output keys", "passed": ok, "detail": "all keys present" if ok else f"missing: {missing}"})
        else:
            checks.append({"name": "required output keys", "passed": False, "detail": "output not parsed as object"})
    except Exception as e:
        checks.append({"name": "required output keys", "passed": False, "detail": f"exception: {e}"})

    # Check 5: signal count and ids
    try:
        if isinstance(parsed, dict) and isinstance(parsed.get("signals"), list):
            sigs = parsed.get("signals", [])
            ids = [str(s.get("id", "")) for s in sigs if isinstance(s, dict)]
            ok = len(sigs) == 10 and all(x in ids for x in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3"])
            checks.append({"name": "signal board completeness", "passed": ok, "detail": f"count={len(sigs)} ids={ids}"})
        else:
            checks.append({"name": "signal board completeness", "passed": False, "detail": "signals missing or not a list"})
    except Exception as e:
        checks.append({"name": "signal board completeness", "passed": False, "detail": f"exception: {e}"})

    # Check 6: composite and expected direction
    try:
        if isinstance(parsed, dict):
            comp = str(parsed.get("composite", ""))
            ok = normalize(comp) in {"orange", "yellow", "red", "green"} and normalize(comp) == "orange"
            checks.append({"name": "composite risk light", "passed": ok, "detail": f"value={comp}"})
        else:
            checks.append({"name": "composite risk light", "passed": False, "detail": "missing composite"})
    except Exception as e:
        checks.append({"name": "composite risk light", "passed": False, "detail": f"exception: {e}"})

    # Check 7: threshold-triggered flags present on at least 5 signals
    try:
        triggered = 0
        if isinstance(parsed, dict) and isinstance(parsed.get("signals"), list):
            for s in parsed["signals"]:
                if isinstance(s, dict) and s.get("triggered") is True:
                    triggered += 1
        ok = triggered >= 5
        checks.append({"name": "triggered signal coverage", "passed": ok, "detail": f"triggered={triggered}"})
    except Exception as e:
        checks.append({"name": "triggered signal coverage", "passed": False, "detail": f"exception: {e}"})

    # Check 8: gaps mention stale/partial coverage
    try:
        if isinstance(parsed, dict) and isinstance(parsed.get("gaps"), list):
            text = " ".join(str(x) for x in parsed.get("gaps", []))
            ok = any(k in normalize(text) for k in ["stale", "partial", "missing", "coverage"])
            checks.append({"name": "data gaps noted", "passed": ok, "detail": text[:200] if text else "empty gaps"})
        else:
            checks.append({"name": "data gaps noted", "passed": False, "detail": "gaps missing or not list"})
    except Exception as e:
        checks.append({"name": "data gaps noted", "passed": False, "detail": f"exception: {e}"})

    # Check 9: score calculation
    try:
        passed_count = sum(1 for c in checks if c.get("passed"))
        expected_score = passed_count / len(checks) if checks else 0.0
        score = expected_score
        passed = passed_count == len(checks)
    except Exception:
        score = 0.0
        passed = False

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}))
