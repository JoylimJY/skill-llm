import sys
import json
import math
from pathlib import Path

def load_report(workspace):
    candidates = list(Path(workspace).rglob("departure_safety_report.json"))
    if not candidates:
        return None, "File 'departure_safety_report.json' not found anywhere in workspace."
    # Prefer the expected location
    expected = Path(workspace) / "harbor_ops/safety/reports/departure_safety_report.json"
    if expected.exists():
        path = expected
    else:
        path = candidates[0]
    try:
        with open(path) as f:
            data = json.load(f)
        return data, str(path)
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def check_peak_high_tide(report):
    """The peak_high_tide section must contain a time and height."""
    checks = []
    section = report.get("peak_high_tide")
    if not section:
        return [{"name": "peak_high_tide_exists", "passed": False, "detail": "Missing 'peak_high_tide' key in report."}]
    
    has_time = False
    has_height = False
    peak_time_str = None
    peak_height = None

    # Accept various key names agents might use
    for k in ["time", "timestamp", "datetime", "event_time", "utc_time"]:
        if k in section:
            has_time = True
            peak_time_str = section[k]
            break
    for k in ["height", "height_m", "tide_height", "value", "tide_height_m", "meters", "height_meters"]:
        if k in section:
            has_height = True
            peak_height = section[k]
            break

    checks.append({
        "name": "peak_high_tide_has_time",
        "passed": has_time,
        "detail": f"peak_high_tide time found: {peak_time_str}" if has_time else "No time field found in peak_high_tide."
    })
    checks.append({
        "name": "peak_high_tide_has_height",
        "passed": has_height,
        "detail": f"peak_high_tide height found: {peak_height}" if has_height else "No height field found in peak_high_tide."
    })

    # Height must be a positive number (Brest is a macrotidal port, HW typically 4-8m above chart datum)
    if has_height:
        try:
            h = float(peak_height)
            reasonable = (0.5 <= h <= 15.0)
            checks.append({
                "name": "peak_high_tide_height_reasonable",
                "passed": reasonable,
                "detail": f"Height value {h:.3f} m {'is' if reasonable else 'is NOT'} in plausible range [0.5, 15.0] m."
            })
        except (TypeError, ValueError) as e:
            checks.append({"name": "peak_high_tide_height_reasonable", "passed": False, "detail": f"Could not parse height as float: {e}"})

    # Time must fall within the analysis window 2026-02-15 to 2026-02-17
    if has_time and peak_time_str:
        try:
            from dateutil import parser as dtparser
            dt = dtparser.parse(str(peak_time_str))
            from datetime import datetime, timezone
            start = datetime(2026, 2, 15, 0, 0, 0, tzinfo=timezone.utc)
            end = datetime(2026, 2, 17, 0, 0, 0, tzinfo=timezone.utc)
            # Make dt timezone aware if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            in_window = (start <= dt <= end)
            checks.append({
                "name": "peak_high_tide_time_in_window",
                "passed": in_window,
                "detail": f"Peak time {dt.isoformat()} {'is' if in_window else 'is NOT'} within 2026-02-15 to 2026-02-17."
            })
        except Exception as e:
            checks.append({"name": "peak_high_tide_time_in_window", "passed": False, "detail": f"Could not parse peak time: {e}"})

    return checks

def check_pre_peak_reading(report):
    """pre_peak_reading must be the tide height exactly 1 hour before the peak."""
    checks = []
    section = report.get("pre_peak_reading")
    if not section:
        return [{"name": "pre_peak_reading_exists", "passed": False, "detail": "Missing 'pre_peak_reading' key in report."}]

    has_time = False
    has_height = False
    pre_time_str = None
    pre_height = None

    for k in ["time", "timestamp", "datetime", "event_time", "utc_time"]:
        if k in section:
            has_time = True
            pre_time_str = section[k]
            break
    for k in ["height", "height_m", "tide_height", "value", "tide_height_m", "meters", "height_meters"]:
        if k in section:
            has_height = True
            pre_height = section[k]
            break

    checks.append({
        "name": "pre_peak_reading_has_time",
        "passed": has_time,
        "detail": f"pre_peak_reading time found: {pre_time_str}" if has_time else "No time field in pre_peak_reading."
    })
    checks.append({
        "name": "pre_peak_reading_has_height",
        "passed": has_height,
        "detail": f"pre_peak_reading height found: {pre_height}" if has_height else "No height field in pre_peak_reading."
    })

    # Verify the pre_peak time is exactly 1 hour before peak
    peak_section = report.get("peak_high_tide", {})
    peak_time_str = None
    for k in ["time", "timestamp", "datetime", "event_time", "utc_time"]:
        if k in peak_section:
            peak_time_str = peak_section[k]
            break

    if has_time and pre_time_str and peak_time_str:
        try:
            from dateutil import parser as dtparser
            from datetime import timezone, timedelta
            pre_dt = dtparser.parse(str(pre_time_str))
            peak_dt = dtparser.parse(str(peak_time_str))
            if pre_dt.tzinfo is None:
                pre_dt = pre_dt.replace(tzinfo=timezone.utc)
            if peak_dt.tzinfo is None:
                peak_dt = peak_dt.replace(tzinfo=timezone.utc)
            diff_seconds = (peak_dt - pre_dt).total_seconds()
            # Should be 3600 seconds (1 hour), allow ±60s tolerance
            correct_offset = abs(diff_seconds - 3600) <= 60
            checks.append({
                "name": "pre_peak_is_1_hour_before_peak",
                "passed": correct_offset,
                "detail": f"Time difference between pre_peak and peak is {diff_seconds:.0f}s (expected ~3600s). {'OK' if correct_offset else 'FAIL — must be exactly 1 hour before peak.'}"
            })
        except Exception as e:
            checks.append({"name": "pre_peak_is_1_hour_before_peak", "passed": False, "detail": f"Could not compute time offset: {e}"})

    # Height should be a reasonable positive number
    if has_height:
        try:
            h = float(pre_height)
            reasonable = (0.0 <= h <= 15.0)
            checks.append({
                "name": "pre_peak_height_reasonable",
                "passed": reasonable,
                "detail": f"Pre-peak height {h:.3f} m {'is' if reasonable else 'is NOT'} in plausible range."
            })
        except (TypeError, ValueError) as e:
            checks.append({"name": "pre_peak_height_reasonable", "passed": False, "detail": f"Could not parse pre_peak height: {e}"})

    return checks

def check_weather_snapshot(report):
    """weather_snapshot must contain wind and temperature data."""
    checks = []
    section = report.get("weather_snapshot")
    if not section:
        return [{"name": "weather_snapshot_exists", "passed": False, "detail": "Missing 'weather_snapshot' key in report."}]

    checks.append({"name": "weather_snapshot_exists", "passed": True, "detail": "weather_snapshot key present."})

    # Must contain wind data (wind/surface/0)
    has_wind = False
    wind_value = None
    def search_nested(obj, keys):
        """Recursively search for any of the keys in a nested dict/list."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(kw in k.lower() for kw in keys):
                    return True, v
                found, val = search_nested(v, keys)
                if found:
                    return True, val
        elif isinstance(obj, list):
            for item in obj:
                found, val = search_nested(item, keys)
                if found:
                    return True, val
        return False, None

    has_wind, wind_value = search_nested(section, ["wind"])
    has_temp, temp_value = search_nested(section, ["tmp", "temp", "temperature"])

    checks.append({
        "name": "weather_has_wind_data",
        "passed": has_wind,
        "detail": f"Wind data {'found' if has_wind else 'NOT found'} in weather_snapshot."
    })
    checks.append({
        "name": "weather_has_temperature_data",
        "passed": has_temp,
        "detail": f"Temperature data {'found' if has_temp else 'NOT found'} in weather_snapshot."
    })

    # Weather data should not be empty
    is_nonempty = bool(section) and section != {} and section != []
    checks.append({
        "name": "weather_snapshot_nonempty",
        "passed": is_nonempty,
        "detail": "weather_snapshot contains data." if is_nonempty else "weather_snapshot is empty."
    })

    return checks

def check_location_correctness(report):
    """Verify the report references the Brest location."""
    checks = []
    report_str = json.dumps(report).lower()
    
    # Check for Brest or coordinates near 48.38, -4.48
    has_brest_name = "brest" in report_str
    
    # Check for latitude ~48.38 and longitude ~-4.48 
    has_lat = False
    has_lon = False
    def find_coord(obj, key_hints, expected, tolerance=0.5):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(h in k.lower() for h in key_hints):
                    try:
                        if abs(float(v) - expected) < tolerance:
                            return True
                    except:
                        pass
                if find_coord(v, key_hints, expected, tolerance):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if find_coord(item, key_hints, expected, tolerance):
                    return True
        return False

    has_lat = find_coord(report, ["lat"], 48.3833)
    has_lon = find_coord(report, ["lon"], -4.4833)

    location_identified = has_brest_name or (has_lat and has_lon)
    checks.append({
        "name": "correct_location_referenced",
        "passed": location_identified,
        "detail": f"Location reference: brest_name={has_brest_name}, lat_ok={has_lat}, lon_ok={has_lon}."
    })
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    
    # 1. Find and load the report
    report, detail = load_report(workspace)
    file_found = report is not None
    all_checks.append({
        "name": "report_file_found_and_parseable",
        "passed": file_found,
        "detail": detail
    })
    
    if not file_found:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result, indent=2))
        return

    # 2. Check peak_high_tide section
    all_checks.extend(check_peak_high_tide(report))

    # 3. Check pre_peak_reading section
    all_checks.extend(check_pre_peak_reading(report))

    # 4. Check weather_snapshot section
    all_checks.extend(check_weather_snapshot(report))

    # 5. Check location correctness
    all_checks.extend(check_location_correctness(report))

    # === Scoring ===
    # Weight critical checks more heavily
    critical_checks = {
        "report_file_found_and_parseable": 3,
        "peak_high_tide_has_time": 2,
        "peak_high_tide_has_height": 2,
        "peak_high_tide_height_reasonable": 2,
        "peak_high_tide_time_in_window": 2,
        "pre_peak_reading_has_time": 2,
        "pre_peak_reading_has_height": 2,
        "pre_peak_is_1_hour_before_peak": 4,   # KEY proprietary trap
        "pre_peak_height_reasonable": 1,
        "weather_snapshot_exists": 2,
        "weather_has_wind_data": 2,
        "weather_has_temperature_data": 2,
        "weather_snapshot_nonempty": 1,
        "correct_location_referenced": 1,
    }

    total_weight = 0
    earned_weight = 0
    for check in all_checks:
        weight = critical_checks.get(check["name"], 1)
        total_weight += weight
        if check["passed"]:
            earned_weight += weight

    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass the critical one-hour-before-peak check and have a found file to overall pass
    critical_passed = all(
        c["passed"] for c in all_checks
        if c["name"] in {"report_file_found_and_parseable", "pre_peak_is_1_hour_before_peak",
                         "peak_high_tide_time_in_window", "weather_snapshot_exists"}
    )

    result = {
        "passed": critical_passed and score >= 0.70,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()