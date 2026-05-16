import sys
import json
from pathlib import Path

def load_state():
    state_file = Path.home() / ".openclaw" / "skills" / "midea_ac" / "state" / "ac_state.json"
    if not state_file.exists():
        return None, f"State file not found at {state_file}"
    try:
        return json.loads(state_file.read_text()), None
    except Exception as e:
        return None, f"Failed to parse state file: {e}"

def evaluate(workspace_dir):
    checks = []
    state, err = load_state()

    if state is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "state_file_readable", "passed": False, "detail": err}]
        }

    checks.append({
        "name": "state_file_readable",
        "passed": True,
        "detail": f"State file loaded successfully. Rooms: {list(state.keys())}"
    })

    # -----------------------------------------------------------------------
    # Task 1: "Make the living room warmer"
    # Initial state: living_room temperature=24, mode=cool, power=on
    # SKILL.md: "Warmer / more warm" -> Check status first, then increase by 2-10 degrees
    # Valid result: temperature in [26, 34] BUT capped by AC max (30), so [26, 30]
    # -----------------------------------------------------------------------
    living_room = state.get("living_room", {})
    initial_living_temp = 24  # known from gen_inputs

    lr_temp = living_room.get("temperature")
    lr_temp_check_passed = False
    lr_temp_detail = ""

    try:
        lr_temp = int(lr_temp)
        # Must be increased by 2 to 10 degrees from 24, capped at 30
        min_expected = initial_living_temp + 2   # 26
        max_expected = min(initial_living_temp + 10, 30)  # 30
        lr_temp_check_passed = min_expected <= lr_temp <= max_expected
        lr_temp_detail = (
            f"living_room temperature is {lr_temp}°C. "
            f"Expected range: [{min_expected}, {max_expected}]°C "
            f"(initial was {initial_living_temp}°C, must increase by 2–10 per SKILL.md)."
        )
    except (TypeError, ValueError) as e:
        lr_temp_detail = f"Could not parse living_room temperature: {lr_temp}. Error: {e}"

    checks.append({
        "name": "living_room_warmer_temperature_increased",
        "passed": lr_temp_check_passed,
        "detail": lr_temp_detail
    })

    # -----------------------------------------------------------------------
    # Task 2: "Set bedroom to maximum / full speed"
    # Initial state: bedroom mode=heat, temperature=22, fan_speed=low, power=on
    # SKILL.md: "Full speed / maximum" + mode is heat -> --temperature 30 --fan_speed max
    # This is the PROPRIETARY TRAP: generic agents will only set fan_speed=max
    # -----------------------------------------------------------------------
    bedroom = state.get("bedroom", {})

    br_fan = bedroom.get("fan_speed")
    br_temp = bedroom.get("temperature")

    # Check fan_speed = max
    br_fan_check_passed = (str(br_fan).lower() == "max")
    checks.append({
        "name": "bedroom_fullspeed_fan_set_to_max",
        "passed": br_fan_check_passed,
        "detail": (
            f"bedroom fan_speed is '{br_fan}'. "
            f"Expected 'max' (SKILL.md 'Full speed/maximum' rule)."
        )
    })

    # Check temperature = 30 (critical proprietary trap: heat mode requires temp=30)
    try:
        br_temp_int = int(br_temp)
        br_temp_check_passed = (br_temp_int == 30)
    except (TypeError, ValueError):
        br_temp_int = br_temp
        br_temp_check_passed = False

    checks.append({
        "name": "bedroom_fullspeed_heat_mode_temperature_set_to_30",
        "passed": br_temp_check_passed,
        "detail": (
            f"bedroom temperature is {br_temp_int}°C. "
            f"Expected 30°C when mode=heat and 'full speed/maximum' requested "
            f"(SKILL.md: heat mode full speed -> --temperature 30 --fan_speed max). "
            f"This is the key proprietary trap: cool mode would be 16°C, not 30°C."
        )
    })

    # -----------------------------------------------------------------------
    # Bonus check: bedroom mode must still be 'heat' (unchanged)
    # -----------------------------------------------------------------------
    br_mode = bedroom.get("mode")
    br_mode_check_passed = (str(br_mode).lower() == "heat")
    checks.append({
        "name": "bedroom_mode_unchanged_heat",
        "passed": br_mode_check_passed,
        "detail": (
            f"bedroom mode is '{br_mode}'. "
            f"Expected 'heat' (initial mode, not changed by full speed command)."
        )
    })

    # -----------------------------------------------------------------------
    # Bonus check: living_room mode must still be 'cool' (unchanged)
    # -----------------------------------------------------------------------
    lr_mode = living_room.get("mode")
    lr_mode_check_passed = (str(lr_mode).lower() == "cool")
    checks.append({
        "name": "living_room_mode_unchanged_cool",
        "passed": lr_mode_check_passed,
        "detail": (
            f"living_room mode is '{lr_mode}'. "
            f"Expected 'cool' (initial mode, should not be changed by 'warmer' command)."
        )
    })

    # -----------------------------------------------------------------------
    # Score
    # -----------------------------------------------------------------------
    # Critical checks (must pass): warmer temp, fan max, temp=30 for heat full speed
    critical = [
        "living_room_warmer_temperature_increased",
        "bedroom_fullspeed_fan_set_to_max",
        "bedroom_fullspeed_heat_mode_temperature_set_to_30",
    ]
    all_checks_by_name = {c["name"]: c["passed"] for c in checks}

    critical_passed = all(all_checks_by_name.get(n, False) for n in critical)
    total_passed = sum(1 for c in checks if c["passed"])
    score = round(total_passed / len(checks), 3)

    return {
        "passed": critical_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))