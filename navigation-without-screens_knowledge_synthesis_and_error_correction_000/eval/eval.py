import sys
import json
from pathlib import Path

def find_briefing(workspace):
    """Find navigation_briefing.json anywhere in the workspace."""
    matches = list(Path(workspace).rglob("navigation_briefing.json"))
    if not matches:
        return None
    # Prefer the most recently modified if multiple found
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]

def run_eval(workspace):
    checks = []

    # --- Find the output file ---
    briefing_path = find_briefing(workspace)
    if briefing_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "navigation_briefing.json not found anywhere in workspace"}]
        }

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {briefing_path}"})

    try:
        with open(briefing_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }

    checks.append({"name": "file_parseable", "passed": True, "detail": "Valid JSON"})

    # -----------------------------------------------------------------------
    # CHECK 1: Map scale rule — 1:24,000 → ~2.5 inches = 1 mile
    # Draft had "3 inches = 1 mile" which is WRONG per SKILL.md
    # -----------------------------------------------------------------------
    try:
        scale_section = data.get("map_scale_rule", {})
        scale_text = json.dumps(scale_section).lower()
        # Must mention 2.5 (not 3) inches per mile
        has_correct_scale = "2.5" in scale_text
        has_wrong_scale = "3 inch" in scale_text and "2.5" not in scale_text
        scale_corrected = scale_section.get("corrected", False)
        passed = has_correct_scale and scale_corrected and not has_wrong_scale
        checks.append({
            "name": "map_scale_rule_correct",
            "passed": passed,
            "detail": f"Expected '2.5 inches = 1 mile' for 1:24000. found '2.5' in text: {has_correct_scale}, corrected flag: {scale_corrected}"
        })
    except Exception as e:
        checks.append({"name": "map_scale_rule_correct", "passed": False, "detail": f"Error checking scale: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 2: Naismith's Rule — 30 minutes per 1,000 feet elevation gain
    # Draft said 15 minutes per 1,000 feet — WRONG
    # Correct: base 4.5 miles at 2.5mph = 1.8h, elevation 2800ft → 2800/1000 * 30 = 84 min = 1.4h
    # Total = 1.8 + 1.4 = 3.2 hours
    # -----------------------------------------------------------------------
    try:
        route_section = data.get("route_timing", {})
        route_text = json.dumps(route_section).lower()
        
        # Check that 30 min/1000ft rule is used
        has_30_min_rule = "30" in route_text
        
        # Check total time is approximately 3.2 hours (accept 3.1-3.3)
        total_time = None
        for key in ["total_estimated_time_hours", "total_time_hours", "total_hours", "estimated_hours"]:
            if key in route_section:
                try:
                    total_time = float(route_section[key])
                    break
                except:
                    pass
        
        # Also check nested structures
        if total_time is None:
            for v in route_section.values():
                if isinstance(v, dict):
                    for key in ["total_estimated_time_hours", "total_time_hours", "total_hours", "estimated_hours"]:
                        if key in v:
                            try:
                                total_time = float(v[key])
                                break
                            except:
                                pass

        route_corrected = route_section.get("corrected", False)
        time_correct = total_time is not None and 3.0 <= total_time <= 3.4
        passed = has_30_min_rule and time_correct and route_corrected
        checks.append({
            "name": "naismiths_rule_correct",
            "passed": passed,
            "detail": f"30 min/1000ft rule present: {has_30_min_rule}. Total time found: {total_time} (expected ~3.2h). corrected flag: {route_corrected}"
        })
    except Exception as e:
        checks.append({"name": "naismiths_rule_correct", "passed": False, "detail": f"Error checking Naismith: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 3: Pace count — 60-70 double-paces per 100m
    # Draft said 45-55 which is WRONG per SKILL.md
    # -----------------------------------------------------------------------
    try:
        pace_section = data.get("pace_count", {})
        pace_text = json.dumps(pace_section).lower()
        
        # Must mention 60 and 70
        has_60 = "60" in pace_text
        has_70 = "70" in pace_text
        # Must NOT claim 45-55 as correct
        has_wrong_low = "45" in pace_text
        
        pace_corrected = pace_section.get("corrected", False)
        passed = has_60 and has_70 and pace_corrected and not has_wrong_low
        checks.append({
            "name": "pace_count_correct",
            "passed": passed,
            "detail": f"Correct range (60-70) present: {has_60 and has_70}. Wrong 45 value absent: {not has_wrong_low}. corrected flag: {pace_corrected}"
        })
    except Exception as e:
        checks.append({"name": "pace_count_correct", "passed": False, "detail": f"Error checking pace count: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 4: Compass/Declination — Oregon (US West Coast) = EAST, ~14-18 degrees
    # Draft said 8 degrees WEST — BOTH direction and value are wrong
    # -----------------------------------------------------------------------
    try:
        compass_section = data.get("compass_setup", {})
        compass_text = json.dumps(compass_section).lower()
        
        # Direction must be EAST not west
        has_east = "east" in compass_text
        # Must have a value in range 14-18
        has_correct_range = False
        for val in [14, 15, 16, 17, 18]:
            if str(val) in compass_text:
                has_correct_range = True
                break
        
        compass_corrected = compass_section.get("corrected", False)
        passed = has_east and has_correct_range and compass_corrected
        checks.append({
            "name": "declination_correct",
            "passed": passed,
            "detail": f"Direction 'east' present: {has_east}. Correct value range (14-18): {has_correct_range}. corrected flag: {compass_corrected}"
        })
    except Exception as e:
        checks.append({"name": "declination_correct", "passed": False, "detail": f"Error checking declination: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 5: UTM Grid Reference — EASTING first, then NORTHING ("read right, then up")
    # Draft said NORTHING first — WRONG per SKILL.md
    # -----------------------------------------------------------------------
    try:
        grid_section = data.get("grid_reference", {})
        grid_text = json.dumps(grid_section).lower()
        
        # Must specify easting first
        easting_pos = grid_text.find("easting")
        northing_pos = grid_text.find("northing")
        easting_before_northing = (easting_pos != -1 and northing_pos != -1 and easting_pos < northing_pos)
        
        # Look for "right then up" or "read right" mnemonic
        has_right_up = ("right" in grid_text and "up" in grid_text) or "read right" in grid_text
        
        grid_corrected = grid_section.get("corrected", False)
        passed = easting_before_northing and grid_corrected
        checks.append({
            "name": "grid_reference_order_correct",
            "passed": passed,
            "detail": f"Easting before northing in description: {easting_before_northing}. Right-then-up mnemonic: {has_right_up}. corrected flag: {grid_corrected}"
        })
    except Exception as e:
        checks.append({"name": "grid_reference_order_correct", "passed": False, "detail": f"Error checking grid reference: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 6: Star Navigation for Northern Hemisphere — use POLARIS / Big Dipper
    # NOT the Southern Cross method (which is for Southern Hemisphere)
    # Draft incorrectly applied Southern Cross method to Northern Hemisphere
    # -----------------------------------------------------------------------
    try:
        star_section = data.get("star_navigation_north", {})
        star_text = json.dumps(star_section).lower()
        
        # Must mention Polaris or North Star or Big Dipper
        has_polaris = "polaris" in star_text or "north star" in star_text
        has_big_dipper = "big dipper" in star_text or "ursa major" in star_text
        
        # Must NOT use Southern Cross as the primary method for Northern Hemisphere
        has_southern_cross_primary = False
        # Check if southern cross is mentioned as the primary/only method (not as comparison)
        if "southern cross" in star_text and not ("northern" in star_text and ("polaris" in star_text or "big dipper" in star_text)):
            has_southern_cross_primary = True
        
        star_corrected = star_section.get("corrected", False)
        passed = has_polaris and has_big_dipper and not has_southern_cross_primary and star_corrected
        checks.append({
            "name": "star_navigation_north_correct",
            "passed": passed,
            "detail": f"Polaris mentioned: {has_polaris}. Big Dipper mentioned: {has_big_dipper}. Southern Cross erroneously primary: {has_southern_cross_primary}. corrected flag: {star_corrected}"
        })
    except Exception as e:
        checks.append({"name": "star_navigation_north_correct", "passed": False, "detail": f"Error checking star nav: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 7: STOP Protocol — S = SIT DOWN (not "Search"), distress = 3 signals
    # Draft had S = "Search" (wrong) and 5 signals (wrong)
    # -----------------------------------------------------------------------
    try:
        emergency_section = data.get("emergency_protocol", {})
        emergency_text = json.dumps(emergency_section).lower()
        
        stop_data = emergency_section.get("stop_protocol", emergency_section)
        stop_text = json.dumps(stop_data).lower()
        
        # S must be "sit down" or "sit"
        s_section = stop_data.get("S", stop_data.get("s", {}))
        s_text = json.dumps(s_section).lower()
        has_sit = "sit" in s_text and "search" not in s_text
        
        # Distress signal must be 3
        has_three = "3" in emergency_text or "three" in emergency_text
        has_five_wrong = ("5 " in emergency_text or " five " in emergency_text) and "3" not in emergency_text and "three" not in emergency_text
        
        emergency_corrected = emergency_section.get("corrected", False)
        passed = has_sit and has_three and not has_five_wrong and emergency_corrected
        checks.append({
            "name": "stop_protocol_correct",
            "passed": passed,
            "detail": f"S='sit down' (not search): {has_sit}. Distress=3: {has_three}. Five wrong: {has_five_wrong}. corrected flag: {emergency_corrected}"
        })
    except Exception as e:
        checks.append({"name": "stop_protocol_correct", "passed": False, "detail": f"Error checking STOP protocol: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 8: Shadow stick east-west — first mark is WEST, second is EAST
    # (sun moves west to east in sky = shadow moves east to west as seen from above)
    # Draft had it backwards: first mark east, second west — WRONG per SKILL.md
    # Note: This check is bonus — present in nav_methods_draft but not explicitly
    # required in task brief sections. Verify if agent included it in any section.
    # -----------------------------------------------------------------------
    try:
        full_text = json.dumps(data).lower()
        # Check for shadow stick correction — first mark = west
        # SKILL.md: "first mark is west, second is east"
        shadow_mentioned = "shadow" in full_text
        if shadow_mentioned:
            # Look for correct orientation
            first_west = False
            lines = full_text.split("\\n") + full_text.split(",")
            for segment in lines:
                if "first" in segment and "west" in segment and "shadow" in full_text:
                    first_west = True
                    break
            checks.append({
                "name": "shadow_stick_orientation_bonus",
                "passed": first_west,
                "detail": f"Shadow stick mentioned: {shadow_mentioned}. First mark = west (correct): {first_west}. (Bonus check)"
            })
        else:
            checks.append({
                "name": "shadow_stick_orientation_bonus",
                "passed": True,  # Not required in task brief, so not penalized if absent
                "detail": "Shadow stick not included — not required by task brief. No penalty."
            })
    except Exception as e:
        checks.append({"name": "shadow_stick_orientation_bonus", "passed": True, "detail": f"Shadow stick check skipped: {e}"})

    # --- Compute score ---
    # Weight critical checks
    critical_checks = [
        "map_scale_rule_correct",
        "naismiths_rule_correct",
        "pace_count_correct",
        "declination_correct",
        "grid_reference_order_correct",
        "star_navigation_north_correct",
        "stop_protocol_correct",
    ]
    critical_results = [c for c in checks if c["name"] in critical_checks]
    passed_critical = sum(1 for c in critical_results if c["passed"])
    total_critical = len(critical_checks)

    # Also require file found and parseable
    infra_checks = ["file_exists", "file_parseable"]
    infra_ok = all(c["passed"] for c in checks if c["name"] in infra_checks)

    if not infra_ok:
        score = 0.0
        overall_passed = False
    else:
        score = passed_critical / total_critical
        overall_passed = passed_critical >= 6  # Must pass at least 6 of 7 critical checks

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))