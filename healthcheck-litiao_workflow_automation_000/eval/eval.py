import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 6.0

    data_file = Path(workspace) / "health-tracker" / "health-data.json"

    # Check 1: File exists
    file_exists = data_file.exists()
    checks.append({
        "name": "health-data.json exists at correct path",
        "passed": file_exists,
        "detail": f"Expected at {data_file}. {'Found.' if file_exists else 'NOT found.'}"
    })
    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    total_score += 1.0

    # Parse file
    try:
        with open(data_file, "r") as f:
            data = json.load(f)
        checks.append({
            "name": "health-data.json is valid JSON",
            "passed": True,
            "detail": "File parsed successfully."
        })
        total_score += 0.5
    except Exception as e:
        checks.append({
            "name": "health-data.json is valid JSON",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return {
            "passed": False,
            "score": total_score / max_score,
            "checks": checks
        }

    # Check 2: Top-level keys exist
    has_water = "water" in data and isinstance(data["water"], list)
    has_sleep = "sleep" in data and isinstance(data["sleep"], list)
    checks.append({
        "name": "Top-level 'water' and 'sleep' arrays present",
        "passed": has_water and has_sleep,
        "detail": f"water: {'present' if has_water else 'MISSING'}, sleep: {'present' if has_sleep else 'MISSING'}"
    })
    if has_water and has_sleep:
        total_score += 0.5

    water = data.get("water", [])
    sleep = data.get("sleep", [])

    # Check 3: Correct number of water records
    # Original sequence: add 3 cups, add 2 cups, add 5 cups -> update last to 4 -> delete first
    # After: add(3), add(2), add(5) = 3 records -> update last: [3,2,4] -> delete first: [2,4]
    # Final water records: 2 entries — cups=[2, 4]
    expected_water_count = 2
    water_count_ok = len(water) == expected_water_count
    checks.append({
        "name": f"Exactly {expected_water_count} water records remain",
        "passed": water_count_ok,
        "detail": f"Expected {expected_water_count} water records, found {len(water)}. Records: {water}"
    })
    if water_count_ok:
        total_score += 1.0

    # Check 4: Water record values are correct [2 cups, 4 cups]
    expected_cups = [2, 4]
    if len(water) == 2:
        actual_cups = [w.get("cups") for w in water]
        cups_ok = actual_cups == expected_cups
        checks.append({
            "name": f"Water cup values are correct: {expected_cups}",
            "passed": cups_ok,
            "detail": f"Expected cups sequence {expected_cups}, got {actual_cups}"
        })
        if cups_ok:
            total_score += 1.0
    else:
        checks.append({
            "name": f"Water cup values are correct: {expected_cups}",
            "passed": False,
            "detail": f"Cannot check cup values — wrong number of records ({len(water)})"
        })

    # Check 5: Water records have ISO8601 timestamps
    iso_ok = True
    iso_detail = []
    for i, w in enumerate(water):
        if "time" not in w:
            iso_ok = False
            iso_detail.append(f"Record {i} missing 'time' field")
        else:
            try:
                from datetime import datetime
                datetime.fromisoformat(w["time"].replace("Z", "+00:00"))
                iso_detail.append(f"Record {i} time OK")
            except Exception as e:
                iso_ok = False
                iso_detail.append(f"Record {i} time invalid: {w['time']}")
    checks.append({
        "name": "Water records have valid ISO8601 timestamps",
        "passed": iso_ok,
        "detail": "; ".join(iso_detail)
    })
    if iso_ok and len(water) > 0:
        total_score += 0.5

    # Check 6: Sleep records — exactly 2 records with correct actions
    expected_sleep_count = 2
    sleep_count_ok = len(sleep) == expected_sleep_count
    checks.append({
        "name": f"Exactly {expected_sleep_count} sleep records present",
        "passed": sleep_count_ok,
        "detail": f"Expected {expected_sleep_count} sleep records, found {len(sleep)}. Records: {sleep}"
    })
    if sleep_count_ok:
        total_score += 0.5

    # Check 7: Sleep records have correct action values: first='sleep', second='wake'
    if len(sleep) == 2:
        action1 = sleep[0].get("action")
        action2 = sleep[1].get("action")
        sleep_actions_ok = (action1 == "sleep" and action2 == "wake")
        checks.append({
            "name": "Sleep record actions are 'sleep' then 'wake'",
            "passed": sleep_actions_ok,
            "detail": f"Expected actions ['sleep', 'wake'], got ['{action1}', '{action2}']"
        })
        if sleep_actions_ok:
            total_score += 0.5
    else:
        checks.append({
            "name": "Sleep record actions are 'sleep' then 'wake'",
            "passed": False,
            "detail": f"Cannot check actions — wrong number of sleep records ({len(sleep)})"
        })

    # Check 8: Sleep records have ISO8601 timestamps
    sleep_iso_ok = True
    sleep_iso_detail = []
    for i, s in enumerate(sleep):
        if "time" not in s:
            sleep_iso_ok = False
            sleep_iso_detail.append(f"Sleep record {i} missing 'time' field")
        else:
            try:
                from datetime import datetime
                datetime.fromisoformat(s["time"].replace("Z", "+00:00"))
                sleep_iso_detail.append(f"Sleep record {i} time OK")
            except Exception as e:
                sleep_iso_ok = False
                sleep_iso_detail.append(f"Sleep record {i} time invalid: {s['time']}")
    checks.append({
        "name": "Sleep records have valid ISO8601 timestamps",
        "passed": sleep_iso_ok,
        "detail": "; ".join(sleep_iso_detail) if sleep_iso_detail else "No sleep records to check"
    })
    if sleep_iso_ok and len(sleep) > 0:
        total_score += 0.5

    final_score = round(total_score / max_score, 4)
    passed = (
        file_exists and
        has_water and has_sleep and
        water_count_ok and
        len(water) == 2 and [w.get("cups") for w in water] == [2, 4] and
        sleep_count_ok and
        len(sleep) == 2 and sleep[0].get("action") == "sleep" and sleep[1].get("action") == "wake"
    )

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))