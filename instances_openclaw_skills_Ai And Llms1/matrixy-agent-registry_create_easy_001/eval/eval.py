import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


output_path = workspace / "registry-summary.json"
input_path = workspace / "agents_input.json"

# Check 1: output exists
try:
    exists = output_path.exists()
    add_check("output_exists", exists, "registry-summary.json found" if exists else "registry-summary.json is missing")
except Exception as e:
    add_check("output_exists", False, f"Error checking output existence: {e}")

# Check 2: output is valid JSON and has list payload
payload = None
try:
    if output_path.exists():
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        ok = isinstance(payload, dict) and isinstance(payload.get("agents"), list)
        add_check("json_shape", ok, "Output contains an 'agents' list" if ok else "Output JSON missing 'agents' list")
    else:
        add_check("json_shape", False, "Skipped because output file is missing")
except Exception as e:
    add_check("json_shape", False, f"Could not parse output JSON: {e}")

# Check 3: names from input are represented fuzzily in output
try:
    if input_path.exists() and payload is not None and isinstance(payload.get("agents"), list):
        source = json.loads(input_path.read_text(encoding="utf-8"))
        out_text = json.dumps(payload).lower()
        expected_names = [str(item.get("name", "")).strip().lower() for item in source if isinstance(item, dict)]
        matched = 0
        for name in expected_names:
            if name and name in out_text:
                matched += 1
        passed = len(expected_names) > 0 and matched == len(expected_names)
        add_check(
            "contains_all_agent_names",
            passed,
            f"Matched {matched}/{len(expected_names)} agent names"
        )
    else:
        add_check("contains_all_agent_names", False, "Skipped because input or output data is unavailable")
except Exception as e:
    add_check("contains_all_agent_names", False, f"Error validating names: {e}")

# Check 4: at least one marker from inputs is preserved or referenced
try:
    if input_path.exists() and payload is not None:
        source = json.loads(input_path.read_text(encoding="utf-8"))
        markers = [str(item.get("marker", "")).strip().lower() for item in source if isinstance(item, dict)]
        out_text = json.dumps(payload).lower()
        found = any(marker and marker in out_text for marker in markers)
        add_check("marker_preserved", found, "At least one known marker appears in output" if found else "No known marker found in output")
    else:
        add_check("marker_preserved", False, "Skipped because required files are unavailable")
except Exception as e:
    add_check("marker_preserved", False, f"Error checking markers: {e}")

# Check 5: score is based on passed checks
try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total else 0.0
    passed = passed_count == total
except Exception:
    score = 0.0
    passed = False

result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
