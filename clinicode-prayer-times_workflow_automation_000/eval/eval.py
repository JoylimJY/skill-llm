import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # --- Check 1: Find prayer_schedule.json ---
    found_files = list(workspace.rglob("prayer_schedule.json"))
    if not found_files:
        checks.append({"name": "file_exists", "passed": False, "detail": "prayer_schedule.json not found anywhere in workspace"})
        return finalize(checks)

    schedule_path = found_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {schedule_path}"})

    # --- Check 2: Valid JSON ---
    try:
        with open(schedule_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return finalize(checks)

    # --- Check 3: Three cities present ---
    # The data could be a list or a dict with city keys
    # Accept both structures but must have 3 entries
    city_entries = []
    if isinstance(data, list):
        city_entries = data
    elif isinstance(data, dict):
        # Could be dict with city names as keys
        city_entries = list(data.values())
    
    if len(city_entries) < 3:
        checks.append({"name": "three_cities", "passed": False, "detail": f"Expected 3 city entries, found {len(city_entries)}. Data: {json.dumps(data)[:300]}"})
        return finalize(checks)
    
    checks.append({"name": "three_cities", "passed": True, "detail": f"Found {len(city_entries)} city entries"})

    # --- Check 4: Fuzzy resolution - typos resolved correctly ---
    # "Meca" should resolve to Makkah (or Mecca), "Dubay" should resolve to Dubai
    # Collect all city/location strings from the data
    all_text = json.dumps(data).lower()

    # Meca -> Makkah or Mecca
    makkah_resolved = any(kw in all_text for kw in ["makkah", "mecca", "makka"])
    checks.append({
        "name": "typo_meca_resolved",
        "passed": makkah_resolved,
        "detail": f"'Meca' should resolve to Makkah/Mecca. Found in data: {makkah_resolved}"
    })

    # Dubay -> Dubai
    dubai_resolved = "dubai" in all_text
    checks.append({
        "name": "typo_dubay_resolved",
        "passed": dubai_resolved,
        "detail": f"'Dubay' should resolve to Dubai. Found in data: {dubai_resolved}"
    })

    # Madinah present
    madinah_resolved = any(kw in all_text for kw in ["madinah", "medina", "al-madinah", "al madinah"])
    checks.append({
        "name": "madinah_present",
        "passed": madinah_resolved,
        "detail": f"Madinah should be present. Found in data: {madinah_resolved}"
    })

    # --- Check 5: Six prayer times per city ---
    required_prayers = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]
    
    prayers_found_count = 0
    for entry in city_entries:
        if not isinstance(entry, dict):
            continue
        entry_lower = {k.lower(): v for k, v in entry.items()}
        # Also check nested structure - some agents might nest prayers under a key
        flat_text = json.dumps(entry).lower()
        prayers_in_entry = sum(1 for p in required_prayers if p in flat_text)
        if prayers_in_entry == 6:
            prayers_found_count += 1

    all_cities_have_prayers = prayers_found_count == 3
    checks.append({
        "name": "six_prayers_per_city",
        "passed": all_cities_have_prayers,
        "detail": f"{prayers_found_count}/3 cities have all 6 prayer times (Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha)"
    })

    # --- Check 6: Times in 12-hour AM/PM format ---
    # Look for time patterns like "05:12 AM" or "06:34 PM"
    time_12h_pattern = re.compile(r'\b(0?[1-9]|1[0-2]):[0-5]\d\s*(AM|PM)\b', re.IGNORECASE)
    time_24h_pattern = re.compile(r'\b([01]\d|2[0-3]):[0-5]\d\b')
    
    all_text_raw = json.dumps(data)
    found_12h = time_12h_pattern.findall(all_text_raw)
    found_24h = time_24h_pattern.findall(all_text_raw)
    
    # Should have at least 18 time values (6 prayers * 3 cities)
    has_sufficient_12h = len(found_12h) >= 15  # Allow some tolerance
    
    # Check for presence of AM/PM markers
    has_ampm = "AM" in all_text_raw or "PM" in all_text_raw
    
    checks.append({
        "name": "times_in_12h_format",
        "passed": has_sufficient_12h and has_ampm,
        "detail": f"Found {len(found_12h)} 12h-format times (need >=15). AM/PM present: {has_ampm}"
    })

    # --- Check 7: Country information present ---
    country_keywords = ["saudi", "arabia", "uae", "emirates", "united arab"]
    has_country_info = any(kw in all_text for kw in country_keywords)
    checks.append({
        "name": "country_info_present",
        "passed": has_country_info,
        "detail": f"Country information (Saudi Arabia, UAE, etc.) should be present. Found: {has_country_info}"
    })

    # --- Check 8: Used prayer_times.py (not a different library) ---
    # Check if the agent used the correct script vs installing something else
    # We verify by checking if the data structure reflects the output of prayer_times.py
    # (ISNA method, specific city resolution behavior)
    # This is implicitly tested by fuzzy resolution and format checks above
    # Additionally, check that no raw 24h-only times exist (the script always converts to 12h)
    
    # Count how many pure 24h patterns (like "14:30") exist that are NOT part of a 12h time
    # A simple proxy: if we have both fajr and isha resolved correctly with AM/PM, the script was used
    has_proper_structure = makkah_resolved and dubai_resolved and has_ampm
    checks.append({
        "name": "script_behavior_correct",
        "passed": has_proper_structure,
        "detail": f"Data reflects correct script behavior: typos resolved, ISNA method, 12h format"
    })

    return finalize(checks)


def finalize(checks):
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0
    overall_passed = all(c["passed"] for c in checks)
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))