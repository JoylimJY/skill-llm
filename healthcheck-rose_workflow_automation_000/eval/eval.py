import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    health_file = workspace / "tracker" / "health-data.json"

    # Check 1: File exists in correct location
    file_exists = health_file.exists()
    checks.append({
        "name": "health-data.json exists in tracker/ directory",
        "passed": file_exists,
        "detail": f"Expected file at {health_file}. Found: {file_exists}"
    })

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # Parse the file
    try:
        raw = health_file.read_text()
        data = json.loads(raw)
    except Exception as e:
        checks.append({
            "name": "health-data.json is valid JSON",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "health-data.json is valid JSON",
        "passed": True,
        "detail": "File parsed successfully."
    })

    # Check 2: Top-level keys 'water' and 'sleep' exist
    has_water_key = isinstance(data.get("water"), list)
    has_sleep_key = isinstance(data.get("sleep"), list)
    checks.append({
        "name": "Top-level keys 'water' and 'sleep' are lists",
        "passed": has_water_key and has_sleep_key,
        "detail": f"water is list: {has_water_key}, sleep is list: {has_sleep_key}"
    })

    water = data.get("water", [])
    sleep = data.get("sleep", [])

    # Check 3: Exactly 3 water records remain
    # (Agent must add 5, update last to 4 cups, delete last → 4 records; 
    #  Wait — let's be precise about what we asked for in the prompt)
    # The prompt asks: add 4 water records (2,3,1,2 cups), then update last to 4, then delete last
    # Final state: 3 water records with cups [2, 3, 1]
    expected_water_count = 3
    water_count_ok = len(water) == expected_water_count
    checks.append({
        "name": f"Exactly {expected_water_count} water records present",
        "passed": water_count_ok,
        "detail": f"Found {len(water)} water records. Expected {expected_water_count}."
    })

    # Check 4: Water records have correct cup values [2, 3, 1]
    expected_cups = [2, 3, 1]
    actual_cups = [r.get("cups") for r in water]
    cups_ok = actual_cups == expected_cups
    checks.append({
        "name": f"Water cup values are {expected_cups}",
        "passed": cups_ok,
        "detail": f"Found cup values: {actual_cups}. Expected: {expected_cups}."
    })

    # Check 5: All water records have valid ISO8601 timestamps
    water_timestamps_ok = True
    for i, record in enumerate(water):
        t = record.get("time", "")
        try:
            from datetime import datetime
            datetime.fromisoformat(t.replace("Z", "+00:00"))
        except Exception:
            water_timestamps_ok = False
            break
    checks.append({
        "name": "All water records have valid ISO8601 timestamps",
        "passed": water_timestamps_ok,
        "detail": "Checked all water record timestamps for ISO8601 compliance."
    })

    # Check 6: Exactly 2 sleep records (one 'sleep', one 'wake')
    expected_sleep_count = 2
    sleep_count_ok = len(sleep) == expected_sleep_count
    checks.append({
        "name": f"Exactly {expected_sleep_count} sleep records present",
        "passed": sleep_count_ok,
        "detail": f"Found {len(sleep)} sleep records. Expected {expected_sleep_count}."
    })

    # Check 7: First sleep record has action='sleep', second has action='wake'
    sleep_actions_ok = False
    if len(sleep) >= 2:
        first_action = sleep[0].get("action")
        second_action = sleep[1].get("action")
        sleep_actions_ok = (first_action == "sleep" and second_action == "wake")
    checks.append({
        "name": "Sleep records have correct actions: ['sleep', 'wake']",
        "passed": sleep_actions_ok,
        "detail": f"Actions found: {[r.get('action') for r in sleep]}. Expected: ['sleep', 'wake']."
    })

    # Check 8: Sleep timestamps are valid ISO8601 and sleep comes before wake
    sleep_order_ok = False
    if len(sleep) >= 2:
        try:
            from datetime import datetime
            t_sleep = datetime.fromisoformat(sleep[0]["time"].replace("Z", "+00:00"))
            t_wake = datetime.fromisoformat(sleep[1]["time"].replace("Z", "+00:00"))
            sleep_order_ok = t_sleep <= t_wake
        except Exception as e:
            sleep_order_ok = False
    checks.append({
        "name": "Sleep timestamp precedes wake timestamp",
        "passed": sleep_order_ok,
        "detail": "Verified that the 'sleep' action time is before or equal to the 'wake' action time."
    })

    # Check 9: No extra unexpected top-level keys (strict schema compliance)
    allowed_keys = {"water", "sleep"}
    extra_keys = set(data.keys()) - allowed_keys
    schema_ok = len(extra_keys) == 0
    checks.append({
        "name": "No extra top-level keys in health-data.json",
        "passed": schema_ok,
        "detail": f"Extra keys found: {extra_keys}. Only 'water' and 'sleep' are allowed."
    })

    # Compute score
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)

    # Overall pass requires all critical checks
    critical = [
        water_count_ok,
        cups_ok,
        water_timestamps_ok,
        sleep_count_ok,
        sleep_actions_ok,
        sleep_order_ok,
        schema_ok,
    ]
    overall_passed = all(critical) and file_exists

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument check", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))