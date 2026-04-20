import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    rules_path = workspace / "rules.json"
    state_path = workspace / "state.json"
    samples_path = workspace / "input_samples.json"
    add_check("rules_file_exists", rules_path.exists(), f"rules.json exists: {rules_path.exists()}")
    add_check("state_file_exists", state_path.exists(), f"state.json exists: {state_path.exists()}")
    add_check("samples_file_exists", samples_path.exists(), f"input_samples.json exists: {samples_path.exists()}")

    try:
        rules = json.loads(rules_path.read_text(encoding='utf-8')) if rules_path.exists() else {}
    except Exception as e:
        rules = {}
        add_check("rules_parse", False, f"Could not parse rules.json: {e}")
    else:
        models = rules.get("models", {})
        ok = all(k in models for k in ["cheap", "default", "pro"])
        add_check("rules_models", ok, f"models present: {sorted(models.keys())}")

    try:
        state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    except Exception as e:
        state = {}
        add_check("state_parse", False, f"Could not parse state.json: {e}")
    else:
        ok = state.get("mode") == "auto" and isinstance(state.get("feedback"), dict)
        add_check("state_structure", ok, f"mode={state.get('mode')}, feedback_keys={sorted((state.get('feedback') or {}).keys())}")

    try:
        samples = json.loads(samples_path.read_text(encoding='utf-8')) if samples_path.exists() else {}
    except Exception as e:
        samples = {}
        add_check("samples_parse", False, f"Could not parse input_samples.json: {e}")
    else:
        sample_override = str(samples.get("sample_override", ""))
        sample_status = str(samples.get("sample_status", ""))
        sample_feedback = str(samples.get("sample_feedback", ""))
        ok = ("@pro" in sample_override.lower()) and ("router status" in sample_status.lower()) and ("feedback" in sample_feedback.lower())
        add_check("samples_markers", ok, "marker phrases present in generated inputs")

    score = (sum(1 for c in checks if c["passed"]) / len(checks)) if checks else 0.0
    passed = all(c["passed"] for c in checks)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal_error", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
