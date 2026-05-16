import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

def compute_expected(workspace_path):
    """Compute all expected values using the exact SKILL.md formulas."""
    STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    ZODIAC = {
        '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
        '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
        '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
    }
    WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    REFERENCE_DATE = date(1983, 2, 5)

    def get_year_gz(year):
        cycle_pos = (year - 4) % 60
        stem_idx = cycle_pos % 10
        branch_idx = cycle_pos % 12
        branch = BRANCHES[branch_idx]
        return STEMS[stem_idx] + branch, ZODIAC[branch]

    def get_month_gz(year, month):
        cycle_pos = (year - 4) % 60
        year_stem_idx = cycle_pos % 10
        month_branch_idx = (month + 1) % 12
        month_stem_idx = (year_stem_idx * 2 + month) % 10
        return STEMS[month_stem_idx] + BRANCHES[month_branch_idx]

    def get_day_gz(d):
        delta = (d - REFERENCE_DATE).days
        stem_idx = delta % 10
        branch_idx = delta % 12
        return STEMS[stem_idx] + BRANCHES[branch_idx]

    start_date = date(2031, 2, 26)
    year = 2031
    year_gz, animal = get_year_gz(year)

    rows = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        month_gz = get_month_gz(d.year, d.month)
        day_gz = get_day_gz(d)
        weekday = WEEKDAYS[d.weekday()]
        rows.append({
            "date": d,
            "date_str": f"{d.month}月{d.day}日",
            "weekday": weekday,
            "month_gz": month_gz,
            "day_gz": day_gz,
        })

    return {
        "year_gz": year_gz,
        "animal": animal,
        "rows": rows,
    }

def evaluate(workspace_path):
    checks = []
    workspace = Path(workspace_path)

    # Find the output file
    candidates = list(workspace.rglob("almanac_2031.md"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "almanac_2031.md file exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} matching file(s)" if file_found else "File almanac_2031.md not found anywhere in workspace"
    })

    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Compute ground truth
    expected = compute_expected(workspace_path)
    year_gz = expected["year_gz"]
    animal = expected["animal"]
    rows = expected["rows"]

    # Check 1: Year header — must contain 辛亥 and 猪
    year_header_ok = year_gz in content and animal in content
    checks.append({
        "name": f"Year header contains {year_gz}({animal}年)",
        "passed": year_header_ok,
        "detail": f"Expected '{year_gz}' and '{animal}' in header. Content snippet: {content[:200]}"
    })

    # Check 2: Markdown table header row present
    table_header_ok = ("| Date |" in content or "|Date|" in content.replace(" ", ""))
    checks.append({
        "name": "Markdown table header present",
        "passed": table_header_ok,
        "detail": "Looking for '| Date |' in content"
    })

    # Check 3: All 7 day_gz values correct (most sensitive — tests reference date)
    day_gz_results = []
    for row in rows:
        dstr = row["date_str"]
        day_gz = row["day_gz"]
        found = day_gz in content
        day_gz_results.append((dstr, day_gz, found))

    all_day_gz_ok = all(r[2] for r in day_gz_results)
    failed_days = [(d, gz) for d, gz, ok in day_gz_results if not ok]
    checks.append({
        "name": "All 7 日天干地支 values correct (reference date 1983-02-05 = 甲子日)",
        "passed": all_day_gz_ok,
        "detail": (
            f"All day GZ correct" if all_day_gz_ok
            else f"Wrong/missing day GZ for: {failed_days}. "
                 f"Expected values: {[(r[0], r[1]) for r in day_gz_results]}"
        )
    })

    # Check 4: Month boundary — Feb rows have 庚卯月, Mar rows have 辛辰月
    # Feb 26 - Feb 28 = 庚卯月 (month=2: branch_idx=(2+1)%12=3=卯, year_stem_idx=7, stem_idx=(7*2+2)%10=6=庚)
    # Mar 1 - Mar 4 = 辛辰月 (month=3: branch_idx=(3+1)%12=4=辰, stem_idx=(7*2+3)%10=7=辛)
    feb_month_gz = rows[0]["month_gz"]  # 庚卯月 for Feb
    mar_month_gz = rows[3]["month_gz"]  # 辛辰月 for Mar (day index 3 = Mar 1)

    feb_ok = feb_month_gz in content
    mar_ok = mar_month_gz in content
    both_months_ok = feb_ok and mar_ok

    checks.append({
        "name": f"February month GZ ({feb_month_gz}) present",
        "passed": feb_ok,
        "detail": f"Expected '{feb_month_gz}' for Feb 2031 rows"
    })
    checks.append({
        "name": f"March month GZ ({mar_month_gz}) present",
        "passed": mar_ok,
        "detail": f"Expected '{mar_month_gz}' for Mar 2031 rows"
    })
    checks.append({
        "name": "Month boundary correctly handled (two different month GZ in same table)",
        "passed": both_months_ok,
        "detail": f"Feb: {feb_month_gz}={'found' if feb_ok else 'MISSING'}, Mar: {mar_month_gz}={'found' if mar_ok else 'MISSING'}"
    })

    # Check 5: Correct date range — 2031-02-26 through 2031-03-04 (7 days)
    first_date_ok = "2月26日" in content or "02月26日" in content
    last_date_ok = "3月4日" in content or "03月4日" in content or "3月04日" in content
    date_range_ok = first_date_ok and last_date_ok
    checks.append({
        "name": "Date range is 2031-02-26 to 2031-03-04",
        "passed": date_range_ok,
        "detail": f"First date (2月26日): {'found' if first_date_ok else 'MISSING'}, Last date (3月4日): {'found' if last_date_ok else 'MISSING'}"
    })

    # Check 6: Exactly 7 data rows (not counting header/separator)
    data_rows = [line for line in content.splitlines()
                 if line.strip().startswith("|")
                 and "Date" not in line
                 and "----" not in line
                 and line.strip() != "|"]
    seven_rows_ok = len(data_rows) == 7
    checks.append({
        "name": "Table contains exactly 7 data rows",
        "passed": seven_rows_ok,
        "detail": f"Found {len(data_rows)} data rows, expected 7"
    })

    # Check 7: Weekday values present (spot check Feb 26 = Wednesday = 周三, Mar 1 = Saturday = 周六)
    # Feb 26 2031: date(2031,2,26).weekday() = 2 => 周三
    # Mar 1 2031: date(2031,3,1).weekday() = 5 => 周六
    weekday_feb26 = "周三"
    weekday_mar1 = "周六"
    wd_ok = weekday_feb26 in content and weekday_mar1 in content
    checks.append({
        "name": f"Weekdays correct ({weekday_feb26} for Feb 26, {weekday_mar1} for Mar 1)",
        "passed": wd_ok,
        "detail": f"周三: {'found' if weekday_feb26 in content else 'MISSING'}, 周六: {'found' if weekday_mar1 in content else 'MISSING'}"
    })

    # Check 8: Verify specific day GZ values for key dates (explicit reference-date trap)
    # date(2031,2,26): delta = (date(2031,2,26) - date(1983,2,5)).days
    from datetime import date as dt
    ref = dt(1983, 2, 5)
    d_feb26 = dt(2031, 2, 26)
    delta_feb26 = (d_feb26 - ref).days
    expected_day_gz_feb26_stem = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'][delta_feb26 % 10]
    expected_day_gz_feb26_branch = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][delta_feb26 % 12]
    expected_feb26_gz = expected_day_gz_feb26_stem + expected_day_gz_feb26_branch

    feb26_gz_ok = expected_feb26_gz in content
    checks.append({
        "name": f"Feb 26 日天干地支 = {expected_feb26_gz} (validates 1983-02-05 reference)",
        "passed": feb26_gz_ok,
        "detail": f"Expected '{expected_feb26_gz}' for 2031-02-26. delta={delta_feb26}, stem_idx={delta_feb26%10}, branch_idx={delta_feb26%12}"
    })

    # Scoring
    critical_checks = [
        checks[0],   # file exists
        checks[3],   # all 7 day GZ correct
        checks[4],   # feb month GZ
        checks[5],   # mar month GZ
        checks[7],   # date range
        checks[10],  # specific feb26 GZ
    ]
    all_checks_passed = all(c["passed"] for c in checks)
    critical_passed = all(c["passed"] for c in critical_checks)

    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    overall_passed = critical_passed and score >= 0.8

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))