import json
import os
import re
import sys
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "."
checks = []
score = 0.0


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

try:
    out_path = Path(workspace) / "output.txt"
    if not out_path.exists():
        add_check("output_exists", False, "output.txt is missing")
    else:
        try:
            content = out_path.read_text(encoding="utf-8", errors="ignore")
            n = norm(content)
            has_marker = "hydrogen hole alpha" in n or "marker hydrogen hole alpha" in n
            has_class = "anomaly flagged" in n or "anomaly_flagged" in n
            has_score = "0 87" in n or "0.87" in content
            passed = has_marker and has_class and has_score
            add_check("output_content", passed, f"marker={has_marker}, class={has_class}, score={has_score}")
        except Exception as e:
            add_check("output_content", False, f"Could not read/parse output.txt: {e}")

    try:
        inp = Path(workspace) / "input.json"
        if not inp.exists():
            add_check("input_marker", False, "input.json is missing")
        else:
            data = json.loads(inp.read_text(encoding="utf-8", errors="ignore"))
            marker_ok = norm(str(data.get("marker_name", ""))) == "hydrogen hole alpha"
            class_ok = norm(str(data.get("classification_hint", ""))) == "anomaly flagged"
            score_ok = abs(float(data.get("score_hint", -1)) - 0.87) < 1e-9
            add_check("input_marker", marker_ok and class_ok and score_ok, f"marker_ok={marker_ok}, class_ok={class_ok}, score_ok={score_ok}")
    except Exception as e:
        add_check("input_marker", False, f"Could not parse input.json: {e}")

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = (passed_count / total) if total else 0.0
    passed = total > 0 and passed_count == total
    print(json.dumps({"passed": passed, "score": score, "checks": checks}))
except Exception as e:
    # Final fallback: never crash
    try:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal_error", "passed": False, "detail": str(e)}]}))
    except Exception:
        pass
