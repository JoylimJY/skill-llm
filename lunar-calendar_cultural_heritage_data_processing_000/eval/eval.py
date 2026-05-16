import sys
import json
import re
from pathlib import Path
from lunardate import LunarDate
import datetime

def find_report(workspace):
    matches = list(Path(workspace).rglob("calendar_research_report.xml"))
    return matches[0] if matches else None

def extract_all_results(content):
    """Extract all <lunar_query_result> blocks in order."""
    pattern = re.compile(
        r'<lunar_query_result>(.*?)</lunar_query_result>',
        re.DOTALL
    )
    return pattern.findall(content)

def get_tag(block, tag):
    m = re.search(rf'<{tag}>(.*?)</{tag}>', block, re.DOTALL)
    return m.group(1).strip() if m else ""

def get_subtag(block, parent, child):
    parent_m = re.search(rf'<{parent}>(.*?)</{parent}>', block, re.DOTALL)
    if not parent_m:
        return ""
    m = re.search(rf'<{child}>(.*?)</{child}>', parent_m.group(1), re.DOTALL)
    return m.group(1).strip() if m else ""

def check_solar_date(block, expected_solar):
    val = get_tag(block, "solar_date")
    return expected_solar in val, f"solar_date='{val}' (expected '{expected_solar}')"

def check_fortune_present(block):
    suitable = get_subtag(block, "fortune", "suitable")
    avoid = get_subtag(block, "fortune", "avoid")
    has_suitable = bool(suitable) and suitable != "N/A" and len(suitable) > 2
    has_avoid = bool(avoid) and avoid != "N/A" and len(avoid) > 2
    return has_suitable and has_avoid, f"suitable='{suitable}', avoid='{avoid}'"

def check_leap_month_label(block):
    """The month field must contain '闰' character for leap month entries."""
    month_val = get_subtag(block, "lunar_date", "month")
    has_leap = "闰" in month_val
    return has_leap, f"month='{month_val}'"

def check_no_leap_month_label(block):
    """Non-leap month entries must NOT contain '闰' character."""
    month_val = get_subtag(block, "lunar_date", "month")
    no_leap = "闰" not in month_val
    return no_leap, f"month='{month_val}'"

def verify_solar_to_lunar_conversion(block, solar_str):
    """Verify the lunar date tags match what lunardate library produces."""
    try:
        d = datetime.date.fromisoformat(solar_str)
        ld = LunarDate.fromSolarDate(d.year, d.month, d.day)
        LUNAR_MONTHS = ["正","二","三","四","五","六","七","八","九","十","冬","腊"]
        LUNAR_DAYS = [
            "初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
            "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
            "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"
        ]
        expected_month = LUNAR_MONTHS[ld.month - 1] + "月"
        expected_day   = LUNAR_DAYS[ld.day - 1]
        month_val = get_subtag(block, "lunar_date", "month")
        day_val   = get_subtag(block, "lunar_date", "day")
        month_ok = expected_month in month_val
        day_ok   = expected_day in day_val
        return month_ok and day_ok, f"month='{month_val}'(exp '{expected_month}'), day='{day_val}'(exp '{expected_day}')"
    except Exception as e:
        return False, f"Error: {e}"

def verify_lunar_to_solar_conversion(block, lunar_year, lunar_month, lunar_day, leap):
    """Verify the solar_date tag matches what lunardate library produces."""
    try:
        ld = LunarDate(lunar_year, lunar_month, lunar_day, isLeapMonth=leap)
        sd = ld.toSolarDate()
        expected_solar = sd.isoformat()
        solar_val = get_tag(block, "solar_date")
        ok = expected_solar in solar_val
        return ok, f"solar_date='{solar_val}' (expected '{expected_solar}')"
    except Exception as e:
        return False, f"Error computing expected: {e}"

def check_xml_structure(block):
    """Check that all required XML tags are present."""
    required_tags = [
        "solar_date",
        "lunar_date", "year", "month", "day", "festival",
        "solar_term",
        "fortune", "suitable", "avoid"
    ]
    missing = []
    for tag in required_tags:
        if f"<{tag}>" not in block and f"<{tag}>" not in block:
            if re.search(rf'<{tag}[^>]*>', block) is None:
                missing.append(tag)
    return len(missing) == 0, f"Missing tags: {missing}" if missing else "All required tags present"

def run_eval(workspace):
    checks = []
    
    # ── Find the report file ────────────────────────────────────────────────
    report_path = find_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": str(report_path) if file_found else "calendar_research_report.xml not found anywhere in workspace"
    })
    if not file_found:
        return checks, 0.0

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "report_readable", "passed": True, "detail": f"File size: {len(content)} bytes"})

    # ── Extract result blocks ────────────────────────────────────────────────
    blocks = extract_all_results(content)
    enough_blocks = len(blocks) >= 5
    checks.append({
        "name": "contains_five_results",
        "passed": enough_blocks,
        "detail": f"Found {len(blocks)} <lunar_query_result> blocks (need 5)"
    })
    if len(blocks) < 5:
        return checks, 0.0

    # ══════════════════════════════════════════════════════════════════════
    # A1: 2033-12-22 solar→lunar with fortune
    # ══════════════════════════════════════════════════════════════════════
    b = blocks[0]

    ok, detail = check_xml_structure(b)
    checks.append({"name": "A1_xml_structure", "passed": ok, "detail": detail})

    ok, detail = check_solar_date(b, "2033-12-22")
    checks.append({"name": "A1_solar_date_correct", "passed": ok, "detail": detail})

    ok, detail = verify_solar_to_lunar_conversion(b, "2033-12-22")
    checks.append({"name": "A1_lunar_conversion_correct", "passed": ok, "detail": detail})

    ok, detail = check_fortune_present(b)
    checks.append({"name": "A1_fortune_populated", "passed": ok, "detail": detail})

    # Check for 冬至 solar term
    solar_term_val = get_tag(b, "solar_term")
    has_dongzhi = "冬至" in solar_term_val
    checks.append({
        "name": "A1_solar_term_dongzhi",
        "passed": has_dongzhi,
        "detail": f"solar_term='{solar_term_val}'"
    })

    # ══════════════════════════════════════════════════════════════════════
    # A2: 1984-04-02 solar→lunar with fortune
    # ══════════════════════════════════════════════════════════════════════
    b = blocks[1]

    ok, detail = check_xml_structure(b)
    checks.append({"name": "A2_xml_structure", "passed": ok, "detail": detail})

    ok, detail = check_solar_date(b, "1984-04-02")
    checks.append({"name": "A2_solar_date_correct", "passed": ok, "detail": detail})

    ok, detail = verify_solar_to_lunar_conversion(b, "1984-04-02")
    checks.append({"name": "A2_lunar_conversion_correct", "passed": ok, "detail": detail})

    ok, detail = check_fortune_present(b)
    checks.append({"name": "A2_fortune_populated", "passed": ok, "detail": detail})

    ok, detail = check_no_leap_month_label(b)
    checks.append({"name": "A2_no_spurious_leap_label", "passed": ok, "detail": detail})

    # ══════════════════════════════════════════════════════════════════════
    # A3: 2024-02-10 solar→lunar with fortune
    # ══════════════════════════════════════════════════════════════════════
    b = blocks[2]

    ok, detail = check_xml_structure(b)
    checks.append({"name": "A3_xml_structure", "passed": ok, "detail": detail})

    ok, detail = check_solar_date(b, "2024-02-10")
    checks.append({"name": "A3_solar_date_correct", "passed": ok, "detail": detail})

    ok, detail = verify_solar_to_lunar_conversion(b, "2024-02-10")
    checks.append({"name": "A3_lunar_conversion_correct", "passed": ok, "detail": detail})

    ok, detail = check_fortune_present(b)
    checks.append({"name": "A3_fortune_populated", "passed": ok, "detail": detail})

    # Spring Festival check (2024-02-10 IS Chinese New Year)
    festival_val = get_subtag(b, "lunar_date", "festival")
    has_festival = "春节" in festival_val or "正月初一" in festival_val or len(festival_val) > 0
    checks.append({
        "name": "A3_spring_festival_noted",
        "passed": has_festival,
        "detail": f"festival='{festival_val}'"
    })

    # ══════════════════════════════════════════════════════════════════════
    # B1: Lunar 2033-闰六月-初一 → solar  (THE LEAP MONTH TRAP)
    # ══════════════════════════════════════════════════════════════════════
    b = blocks[3]

    ok, detail = check_xml_structure(b)
    checks.append({"name": "B1_xml_structure", "passed": ok, "detail": detail})

    ok, detail = verify_lunar_to_solar_conversion(b, 2033, 6, 1, leap=True)
    checks.append({"name": "B1_leap_month_solar_correct", "passed": ok, "detail": detail})

    ok, detail = check_leap_month_label(b)
    checks.append({"name": "B1_leap_month_explicitly_labeled", "passed": ok, "detail": detail})

    # ══════════════════════════════════════════════════════════════════════
    # B2: Lunar 1984-七月-廿三 (non-leap) → solar
    # ══════════════════════════════════════════════════════════════════════
    b = blocks[4]

    ok, detail = check_xml_structure(b)
    checks.append({"name": "B2_xml_structure", "passed": ok, "detail": detail})

    ok, detail = verify_lunar_to_solar_conversion(b, 1984, 7, 23, leap=False)
    checks.append({"name": "B2_nonleap_solar_correct", "passed": ok, "detail": detail})

    ok, detail = check_no_leap_month_label(b)
    checks.append({"name": "B2_no_leap_label_on_nonleap", "passed": ok, "detail": detail})

    # ── Compute final score ──────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    return checks, score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    passed = score >= 0.75
    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()