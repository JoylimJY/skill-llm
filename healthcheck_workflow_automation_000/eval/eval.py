import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -------------------------------------------------------------------------
    # CHECK 1: health-data.json exists somewhere in the workspace
    # -------------------------------------------------------------------------
    health_files = list(workspace.rglob("health-data.json"))
    
    if not health_files:
        checks.append({
            "name": "health-data.json exists",
            "passed": False,
            "detail": "No health-data.json file found anywhere in workspace."
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Use the first found file (there should only be one)
    health_file = health_files[0]
    checks.append({
        "name": "health-data.json exists",
        "passed": True,
        "detail": f"Found at: {health_file}"
    })
    total_score += 0.1

    # -------------------------------------------------------------------------
    # CHECK 2: File is valid JSON with correct top-level structure
    # -------------------------------------------------------------------------
    try:
        raw = health_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        checks.append({
            "name": "Valid JSON structure",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    has_water_key = "water" in data and isinstance(data["water"], list)
    has_sleep_key = "sleep" in data and isinstance(data["sleep"], list)

    top_level_ok = has_water_key and has_sleep_key
    checks.append({
        "name": "Top-level keys: water[] and sleep[]",
        "passed": top_level_ok,
        "detail": f"Keys present: {list(data.keys())}. water is list: {has_water_key}, sleep is list: {has_sleep_key}"
    })
    if top_level_ok:
        total_score += 0.1

    # -------------------------------------------------------------------------
    # CHECK 3: Exactly 2 water records remain
    # Expected: [{cups:3,...}, {cups:2,...}] after add 3, add 2, add 1, update to 4, delete last
    # -------------------------------------------------------------------------
    water_records = data.get("water", [])
    water_count_ok = len(water_records) == 2
    checks.append({
        "name": "Exactly 2 water records in final state",
        "passed": water_count_ok,
        "detail": f"Found {len(water_records)} water records. Expected 2 (add 3 cups, add 2 cups, add 1 cup -> update last to 4 -> delete last = 2 remain)."
    })
    if water_count_ok:
        total_score += 0.15

    # -------------------------------------------------------------------------
    # CHECK 4: Water records have correct cups values: [3, 2]
    # -------------------------------------------------------------------------
    if water_count_ok:
        cups_values = [r.get("cups") for r in water_records]
        # cups should be numeric (int or float)
        cups_correct = (cups_values[0] == 3 and cups_values[1] == 2)
        checks.append({
            "name": "Water cups values are [3, 2]",
            "passed": cups_correct,
            "detail": f"Found cups values: {cups_values}. Expected [3, 2]."
        })
        if cups_correct:
            total_score += 0.2
    else:
        # Still check partial credit for any correct cups values
        cups_values = [r.get("cups") for r in water_records]
        checks.append({
            "name": "Water cups values are [3, 2]",
            "passed": False,
            "detail": f"Cannot verify cups values; wrong number of records. Found cups: {cups_values}"
        })

    # -------------------------------------------------------------------------
    # CHECK 5: Water records have 'time' field in ISO8601 format
    # -------------------------------------------------------------------------
    water_has_timestamps = all(
        "time" in r and isinstance(r.get("time"), str) and "T" in r.get("time", "")
        for r in water_records
    ) if water_records else False

    checks.append({
        "name": "Water records have ISO8601 timestamps",
        "passed": water_has_timestamps,
        "detail": f"Timestamp check on {len(water_records)} water records. All have 'T' in time string: {water_has_timestamps}"
    })
    if water_has_timestamps:
        total_score += 0.1

    # -------------------------------------------------------------------------
    # CHECK 6: Exactly 2 sleep records
    # Expected: [{action:"sleep",...}, {action:"wake",...}]
    # -------------------------------------------------------------------------
    sleep_records = data.get("sleep", [])
    sleep_count_ok = len(sleep_records) == 2
    checks.append({
        "name": "Exactly 2 sleep records in final state",
        "passed": sleep_count_ok,
        "detail": f"Found {len(sleep_records)} sleep records. Expected 2 (one sleep, one wake)."
    })
    if sleep_count_ok:
        total_score += 0.1

    # -------------------------------------------------------------------------
    # CHECK 7: Sleep records have correct action values: ["sleep", "wake"]
    # -------------------------------------------------------------------------
    if sleep_count_ok:
        actions = [r.get("action") for r in sleep_records]
        # Must use exact strings "sleep" and "wake" as defined in SKILL.md
        sleep_actions_correct = (actions[0] == "sleep" and actions[1] == "wake")
        checks.append({
            "name": "Sleep action values are ['sleep', 'wake'] (exact strings)",
            "passed": sleep_actions_correct,
            "detail": f"Found action values: {actions}. Expected ['sleep', 'wake'] exactly."
        })
        if sleep_actions_correct:
            total_score += 0.15
    else:
        actions = [r.get("action") for r in sleep_records]
        checks.append({
            "name": "Sleep action values are ['sleep', 'wake'] (exact strings)",
            "passed": False,
            "detail": f"Cannot verify; wrong number of sleep records. Found actions: {actions}"
        })

    # -------------------------------------------------------------------------
    # CHECK 8: Sleep records have 'time' field in ISO8601 format
    # -------------------------------------------------------------------------
    sleep_has_timestamps = all(
        "time" in r and isinstance(r.get("time"), str) and "T" in r.get("time", "")
        for r in sleep_records
    ) if sleep_records else False

    checks.append({
        "name": "Sleep records have ISO8601 timestamps",
        "passed": sleep_has_timestamps,
        "detail": f"Timestamp check on {len(sleep_records)} sleep records. All have 'T' in time string: {sleep_has_timestamps}"
    })
    if sleep_has_timestamps:
        total_score += 0.05

    # -------------------------------------------------------------------------
    # CHECK 9: No extra keys in water records (only 'time' and 'cups')
    # -------------------------------------------------------------------------
    water_clean_schema = all(
        set(r.keys()) == {"time", "cups"}
        for r in water_records
    ) if water_records else False

    checks.append({
        "name": "Water records have only 'time' and 'cups' fields",
        "passed": water_clean_schema,
        "detail": f"Field sets: {[set(r.keys()) for r in water_records]}. Expected {{'time', 'cups'}} for each."
    })
    if water_clean_schema:
        total_score += 0.05

    # -------------------------------------------------------------------------
    # FINAL VERDICT
    # -------------------------------------------------------------------------
    # Must pass the critical checks: file exists, correct structure, 
    # correct water count+values, correct sleep count+actions
    critical_checks = [
        checks[0]["passed"],  # file exists
        checks[1]["passed"],  # valid JSON with water/sleep keys
        checks[2]["passed"],  # 2 water records
        checks[3]["passed"] if len(checks) > 3 else False,  # cups [3,2]
        checks[5]["passed"] if len(checks) > 5 else False,  # 2 sleep records
        checks[6]["passed"] if len(checks) > 6 else False,  # actions [sleep, wake]
    ]
    passed = all(critical_checks)

    result = {
        "passed": passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "Script invocation", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)
    evaluate(sys.argv[1])