import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    workspace = Path(workspace_dir)
    
    # Find the output file
    target_files = list(workspace.rglob("cultural_calendar_2025.json"))
    
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "cultural_calendar_2025.json not found anywhere in workspace"}]
        }
    
    target_file = target_files[0]
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_file}"})
    
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "score": 0.05,
            "checks": checks + [{"name": "valid_json", "passed": False, "detail": f"Invalid JSON: {e}"}]
        }
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": f"Cannot read file: {e}"}]
        }
    
    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    
    data_str = json.dumps(data, ensure_ascii=False)
    
    # CHECK 1: Spring Festival date
    # 2025 Spring Festival (农历正月初一) = 2025-01-29
    check_spring = False
    try:
        # Look for spring festival date anywhere in the data
        if "2025-01-29" in data_str or "01-29" in data_str or "January 29" in data_str.lower():
            check_spring = True
        # Also accept it in a spring_festival or similar key
        spring_val = str(data).lower()
        if "01-29" in spring_val or "january 29" in spring_val or "jan 29" in spring_val:
            check_spring = True
    except:
        pass
    checks.append({
        "name": "spring_festival_date_2025-01-29",
        "passed": check_spring,
        "detail": "Spring Festival (春节) 2025 should be 2025-01-29. Looked for '2025-01-29' or '01-29' in JSON."
    })
    
    # CHECK 2: Mid-Autumn Festival date
    # 2025 Mid-Autumn (农历八月十五) = 2025-10-06
    check_midautumn = False
    try:
        if "2025-10-06" in data_str or "10-06" in data_str or "10/06" in data_str:
            check_midautumn = True
    except:
        pass
    checks.append({
        "name": "mid_autumn_festival_date_2025-10-06",
        "passed": check_midautumn,
        "detail": "Mid-Autumn Festival (中秋节) 2025 should be 2025-10-06. Looked for '2025-10-06' or '10-06' in JSON."
    })
    
    # CHECK 3: Dragon Boat Festival date
    # 2025 Dragon Boat (农历五月初五) = 2025-05-31
    check_dragon = False
    try:
        if "2025-05-31" in data_str or "05-31" in data_str:
            check_dragon = True
    except:
        pass
    checks.append({
        "name": "dragon_boat_festival_date_2025-05-31",
        "passed": check_dragon,
        "detail": "Dragon Boat Festival (端午节) 2025 should be 2025-05-31. Looked for '2025-05-31' or '05-31' in JSON."
    })
    
    # CHECK 4: Qingming (清明) solar term date = 2025-04-04
    check_qingming = False
    try:
        if "2025-04-04" in data_str or "04-04" in data_str:
            check_qingming = True
    except:
        pass
    checks.append({
        "name": "qingming_solar_term_2025-04-04",
        "passed": check_qingming,
        "detail": "Qingming (清明) solar term in 2025 should be 2025-04-04. Looked for '2025-04-04' or '04-04' in JSON."
    })
    
    # CHECK 5: Winter Solstice (冬至) solar term date = 2025-12-22
    check_dongzhi = False
    try:
        if "2025-12-22" in data_str or "12-22" in data_str:
            check_dongzhi = True
    except:
        pass
    checks.append({
        "name": "dongzhi_winter_solstice_2025-12-22",
        "passed": check_dongzhi,
        "detail": "Winter Solstice (冬至) in 2025 should be 2025-12-22. Looked for '2025-12-22' or '12-22' in JSON."
    })
    
    # CHECK 6: Easter 2025 = 2025-04-20
    check_easter = False
    try:
        if "2025-04-20" in data_str or "04-20" in data_str or "April 20" in data_str:
            check_easter = True
    except:
        pass
    checks.append({
        "name": "easter_2025-04-20",
        "passed": check_easter,
        "detail": "Easter 2025 should be 2025-04-20. Looked for '2025-04-20' or '04-20' in JSON."
    })
    
    # CHECK 7: Thanksgiving 2025 = 2025-11-27 (4th Thursday of November)
    check_thanksgiving = False
    try:
        if "2025-11-27" in data_str or "11-27" in data_str:
            check_thanksgiving = True
    except:
        pass
    checks.append({
        "name": "thanksgiving_2025-11-27",
        "passed": check_thanksgiving,
        "detail": "Thanksgiving 2025 should be 2025-11-27 (4th Thursday of November). Looked for '2025-11-27' or '11-27' in JSON."
    })
    
    # CHECK 8: Lunar calendar info for Spring Festival (ganzhi year info)
    # 2025 is 乙巳年 (Snake year)
    check_ganzhi = False
    try:
        if "乙巳" in data_str or "蛇" in data_str or "snake" in data_str.lower() or "yi si" in data_str.lower():
            check_ganzhi = True
    except:
        pass
    checks.append({
        "name": "ganzhi_snake_year_2025",
        "passed": check_ganzhi,
        "detail": "2025 is 乙巳年（蛇年）. JSON should contain '乙巳' or '蛇' (Snake) year info."
    })
    
    # CHECK 9: Mother's Day 2025 = 2025-05-11 (2nd Sunday of May)
    check_mothers = False
    try:
        if "2025-05-11" in data_str or "05-11" in data_str:
            check_mothers = True
    except:
        pass
    checks.append({
        "name": "mothers_day_2025-05-11",
        "passed": check_mothers,
        "detail": "Mother's Day 2025 should be 2025-05-11 (2nd Sunday of May). Looked for '2025-05-11' or '05-11' in JSON."
    })
    
    # CHECK 10: The JSON has meaningful structure (not just a flat string dump)
    check_structure = False
    try:
        if isinstance(data, dict) and len(data) >= 2:
            check_structure = True
        elif isinstance(data, list) and len(data) >= 3:
            check_structure = True
    except:
        pass
    checks.append({
        "name": "json_has_meaningful_structure",
        "passed": check_structure,
        "detail": f"JSON should be a dict with >=2 keys or a list with >=3 items. Got type: {type(data).__name__}"
    })
    
    # Compute score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.7
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))