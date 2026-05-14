#!/usr/bin/env python3
"""
Evaluation script for the seasonal planting guide task.
Checks:
1. dragon-tongue-bean was added to the calendar as a custom plant
2. It was registered for zones 6b AND 7a
3. The full year calendar for zone 7a was exported to farm_schedule_7a.md in an allowed location
4. The exported file contains dragon-tongue-bean (or Dragon Tongue Bean) in the May section
5. The exported file is well-structured with monthly sections
"""

import sys
import json
import re
from pathlib import Path

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    checks = []
    overall_passed = True

    # ── Check 1: planting_calendar.json exists and has custom entry ──────────
    calendar_path = Path.home() / ".openclaw" / "workspace" / "planting_calendar.json"
    calendar_data = None
    custom_plant = None

    try:
        if not calendar_path.exists():
            raise FileNotFoundError(f"Calendar not found at {calendar_path}")
        with open(calendar_path) as f:
            calendar_data = json.load(f)
        checks.append({
            "name": "calendar_json_exists",
            "passed": True,
            "detail": f"planting_calendar.json found at {calendar_path}"
        })
    except Exception as e:
        checks.append({
            "name": "calendar_json_exists",
            "passed": False,
            "detail": f"Failed to load calendar: {e}"
        })
        overall_passed = False

    # ── Check 2: Custom plant 'dragon-tongue-bean' (or similar key) exists ───
    if calendar_data is not None:
        try:
            custom_plants = calendar_data.get("custom", {})
            # Look for dragon-tongue-bean under various possible keys
            dragon_key = None
            for key in custom_plants:
                if "dragon" in key.lower() and "bean" in key.lower():
                    dragon_key = key
                    custom_plant = custom_plants[key]
                    break
                if "dragon" in key.lower() and "tongue" in key.lower():
                    dragon_key = key
                    custom_plant = custom_plants[key]
                    break

            if custom_plant is not None:
                checks.append({
                    "name": "dragon_tongue_bean_registered",
                    "passed": True,
                    "detail": f"Found custom plant under key '{dragon_key}': {custom_plant.get('name', dragon_key)}"
                })
            else:
                checks.append({
                    "name": "dragon_tongue_bean_registered",
                    "passed": False,
                    "detail": f"No dragon tongue bean found in custom plants. Keys found: {list(custom_plants.keys())}"
                })
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "dragon_tongue_bean_registered",
                "passed": False,
                "detail": f"Error checking custom plant: {e}"
            })
            overall_passed = False

    # ── Check 3: Registered for zone 6b AND zone 7a ──────────────────────────
    if custom_plant is not None:
        try:
            zones_data = custom_plant.get("zones", {})
            has_6b = "6b" in zones_data
            has_7a = "7a" in zones_data
            both_zones = has_6b and has_7a
            checks.append({
                "name": "registered_in_zones_6b_and_7a",
                "passed": both_zones,
                "detail": (
                    f"Zone 6b: {'✓' if has_6b else '✗'}, Zone 7a: {'✓' if has_7a else '✗'}. "
                    f"Zones registered: {list(zones_data.keys())}"
                )
            })
            if not both_zones:
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "registered_in_zones_6b_and_7a",
                "passed": False,
                "detail": f"Error checking zones: {e}"
            })
            overall_passed = False

    # ── Check 4: Has planting months including may for zone 7a ───────────────
    if custom_plant is not None:
        try:
            zones_data = custom_plant.get("zones", {})
            zone_7a_months = zones_data.get("7a", [])
            has_may_7a = "may" in [m.lower() for m in zone_7a_months]
            checks.append({
                "name": "zone_7a_includes_may",
                "passed": has_may_7a,
                "detail": f"Zone 7a planting months: {zone_7a_months}. May present: {has_may_7a}"
            })
            if not has_may_7a:
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "zone_7a_includes_may",
                "passed": False,
                "detail": f"Error checking zone 7a months: {e}"
            })
            overall_passed = False

    # ── Check 5: farm_schedule_7a.md exported to a valid path ────────────────
    exported_file = None
    try:
        # Search in allowed locations
        safe_dirs = [
            Path.home() / ".openclaw" / "workspace",
            Path("/tmp"),
            Path.home(),
        ]
        candidates = []
        for safe_dir in safe_dirs:
            if safe_dir.exists():
                for f in safe_dir.rglob("farm_schedule_7a.md"):
                    candidates.append(f)

        if candidates:
            exported_file = candidates[0]
            checks.append({
                "name": "farm_schedule_7a_md_exported",
                "passed": True,
                "detail": f"Export file found at: {exported_file}"
            })
        else:
            checks.append({
                "name": "farm_schedule_7a_md_exported",
                "passed": False,
                "detail": "farm_schedule_7a.md not found in any allowed directory (~/.openclaw/workspace, /tmp, home)"
            })
            overall_passed = False
    except Exception as e:
        checks.append({
            "name": "farm_schedule_7a_md_exported",
            "passed": False,
            "detail": f"Error searching for exported file: {e}"
        })
        overall_passed = False

    # ── Check 6: Exported file is a zone 7a annual calendar ──────────────────
    if exported_file is not None:
        try:
            content = exported_file.read_text()
            has_zone_7a = "7a" in content or "Zone 7a" in content
            has_annual_structure = bool(re.search(r'## (January|February|March|April|May|June|July|August|September|October|November|December)', content, re.IGNORECASE))
            structure_ok = has_zone_7a and has_annual_structure
            checks.append({
                "name": "exported_file_is_annual_zone7a_calendar",
                "passed": structure_ok,
                "detail": (
                    f"Has zone 7a reference: {has_zone_7a}, "
                    f"Has monthly sections (## Month format): {has_annual_structure}"
                )
            })
            if not structure_ok:
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "exported_file_is_annual_zone7a_calendar",
                "passed": False,
                "detail": f"Error reading exported file: {e}"
            })
            overall_passed = False

    # ── Check 7: Dragon tongue bean appears in May section of export ─────────
    if exported_file is not None:
        try:
            content = exported_file.read_text()
            # Find the May section
            may_section_match = re.search(
                r'## May\b(.*?)(?=## \w|\Z)',
                content,
                re.IGNORECASE | re.DOTALL
            )
            dragon_in_may = False
            may_section_text = ""
            if may_section_match:
                may_section_text = may_section_match.group(1)
                dragon_in_may = bool(re.search(r'dragon.{0,10}(tongue|bean)', may_section_text, re.IGNORECASE))

            checks.append({
                "name": "dragon_tongue_bean_in_may_export",
                "passed": dragon_in_may,
                "detail": (
                    f"Dragon tongue bean found in May section: {dragon_in_may}. "
                    f"May section preview: {may_section_text[:200].strip() if may_section_text else 'Section not found'}"
                )
            })
            if not dragon_in_may:
                overall_passed = False
        except Exception as e:
            checks.append({
                "name": "dragon_tongue_bean_in_may_export",
                "passed": False,
                "detail": f"Error checking May section: {e}"
            })
            overall_passed = False

    # ── Compute score ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3) if checks else 0.0

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()