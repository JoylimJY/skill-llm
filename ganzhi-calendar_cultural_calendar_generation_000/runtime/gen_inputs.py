import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "scripts",
    "data/raw/2030",
    "data/raw/2031",
    "data/processed",
    "docs/internal",
    "docs/specs",
    "output/drafts",
    "output/archive",
    "config/regional",
    "config/templates",
    "tests/unit",
    "tests/integration",
    "src/utils",
    "src/formatters",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files with plausible but misleading content
distractor_files = {
    "data/raw/2030/dates.csv": (
        "date,event\n2030-01-01,Spring Festival\n2030-02-05,Lantern Festival\n"
    ),
    "data/raw/2031/raw_dates.txt": (
        "2031-02-01\n2031-02-14\n2031-02-26\n2031-03-01\n2031-03-04\n"
    ),
    "data/processed/output_old.md": (
        "# Old Almanac\nThis file is outdated and should not be used.\n"
    ),
    "docs/internal/calendar_notes.txt": (
        "Note: Various calendar systems exist.\n"
        "Some use 1900-01-31 as reference for ganzhi, others use 1864-01-01.\n"
        "Please verify with the official documentation.\n"
    ),
    "docs/specs/format_spec_v1.txt": (
        "Version 1 format (DEPRECATED):\n"
        "Year|Month|Day|Ganzhi\n"
        "Use the newer pipe-delimited markdown table format instead.\n"
    ),
    "docs/specs/format_spec_v2.txt": (
        "Version 2 format notes:\n"
        "Table must use markdown pipe syntax.\n"
        "Columns: Date, Weekday, Nongli, 月天干地支, 日天干地支\n"
        "Year header should appear above table.\n"
    ),
    "config/regional/zh_CN.json": json.dumps({
        "locale": "zh_CN",
        "calendar_type": "lunisolar",
        "week_start": "Monday",
        "ganzhi_ref_note": "Multiple references exist; confirm with scripts."
    }, ensure_ascii=False, indent=2),
    "config/templates/weekly_template.txt": (
        "{{year_ganzhi}}\n"
        "| Date | Weekday | Nongli | 月天干地支 | 日天干地支 |\n"
        "| ---- | ------- | ------ | ---------- | ---------- |\n"
        "{{rows}}\n"
    ),
    "config/regional/holidays.json": json.dumps({
        "2031": {
            "02-26": "普通工作日",
            "03-01": "普通工作日",
            "03-04": "普通工作日"
        }
    }, ensure_ascii=False, indent=2),
    "src/utils/date_helpers.py": (
        "# Utility helpers (stub)\n"
        "def days_between(d1, d2):\n"
        "    return (d2 - d1).days\n"
        "\n"
        "# WARNING: Do not use this for ganzhi calculation\n"
        "# Reference dates in this file are NOT calibrated\n"
        "WRONG_REF = '1900-01-31'  # NOT the correct reference for this project\n"
    ),
    "src/formatters/table.py": (
        "# Table formatter stub\n"
        "def format_row(date, weekday, nongli, month_gz, day_gz):\n"
        "    return f'| {date} | {weekday} | {nongli} | {month_gz} | {day_gz} |'\n"
    ),
    "tests/unit/test_stems.py": (
        "# Unit tests (incomplete)\n"
        "def test_year_stem():\n"
        "    # 2024 should be 甲辰\n"
        "    assert True  # TODO: implement\n"
    ),
    "tests/integration/test_week.py": (
        "# Integration test stub\n"
        "# Test that a 7-day range produces 7 rows\n"
        "assert True  # TODO\n"
    ),
    "output/drafts/attempt_v0.md": (
        "# Draft (WRONG - do not use)\n"
        "This was generated with an incorrect reference date.\n"
        "| Date | Weekday | Nongli | 月天干地支 | 日天干地支 |\n"
        "| ---- | ------- | ------ | ---------- | ---------- |\n"
        "| 2月26日 | 周三 | 农历正月初X | 戊寅月 | 丙子日 |\n"
    ),
    "output/archive/2030_week9.md": (
        "庚戌(狗年) 🐕\n"
        "| Date | Weekday | Nongli | 月天干地支 | 日天干地支 |\n"
        "| ---- | ------- | ------ | ---------- | ---------- |\n"
        "| 3月1日 | 周一 | 农历二月初六 | 庚辰月 | 甲午日 |\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# Create the main calendar script exactly as described in SKILL.md
# The script uses the reference and formulas from the skill
calendar_script = '''\
#!/usr/bin/env python3
"""
Chinese Calendar Calculator
Generates weekly calendar tables with Heavenly Stems and Earthly Branches.
"""
from datetime import date, timedelta

STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
ZODIAC = {
    '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
    '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
    '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
}

WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

LUNAR_MONTHS = ['正月', '二月', '三月', '四月', '五月', '六月',
                '七月', '八月', '九月', '十月', '冬月', '腊月']
LUNAR_DAYS = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
              '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
              '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十']

REFERENCE_DATE = date(1983, 2, 5)  # 甲子日


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


def get_weekday(d):
    return WEEKDAYS[d.weekday()]


def format_date(d):
    return f"{d.month}月{d.day}日"


def get_lunar_date(d):
    # Simplified lunar date approximation for display
    # In production this would use a proper lunar calendar library
    try:
        from lunarcalendar import Converter, Solar
        solar = Solar(d.year, d.month, d.day)
        lunar = Converter.Solar2Lunar(solar)
        month_str = LUNAR_MONTHS[lunar.month - 1]
        day_str = LUNAR_DAYS[lunar.day - 1]
        leap = "闰" if lunar.isleap else ""
        return f"农历{leap}{month_str}{day_str}"
    except Exception:
        return "农历-"


def generate_week(start_date):
    year = start_date.year
    year_gz, zodiac = get_year_gz(year)
    animal = ZODIAC[BRANCHES[(year - 4) % 60 % 12]]
    
    print(f"{year_gz}({animal}年)")
    print("| Date | Weekday | Nongli | 月天干地支 | 日天干地支 |")
    print("| ---- | ------- | ------ | ---------- | ---------- |")
    
    for i in range(7):
        d = start_date + timedelta(days=i)
        date_str = format_date(d)
        weekday_str = get_weekday(d)
        nongli_str = get_lunar_date(d)
        month_gz = get_month_gz(d.year, d.month)
        day_gz = get_day_gz(d)
        print(f"| {date_str} | {weekday_str} | {nongli_str} | {month_gz} | {day_gz} |")


if __name__ == "__main__":
    today = date.today()
    # Find the Monday of the current week
    start = today - timedelta(days=today.weekday())
    generate_week(start)
'''

(workspace / "scripts" / "calendar.py").write_text(calendar_script, encoding="utf-8")

# Create a SKILL.md reference file
skill_md = '''\
---
name: chinese-calendar
description: Calculate Chinese lunar calendar dates with Heavenly Stems (天干) and Earthly Branches (地支). Use when generating Chinese calendar tables, checking 黄历, or converting Gregorian dates to 干支 (stem-branch) dates for year/month/day.
---

# Chinese Calendar Calculator

## Usage

Run the script to generate weekly calendar:

```bash
python3 scripts/calendar.py
```

Output format:
```
丙午(马年) 🐎
| Date | Weekday | Nongli | 月天干地支 | 日天干地支 |
| ---- | ------- | ------ | ---------- | ---------- |
| 3月6日 | 周五 | 农历正月十八 | 辛卯月 | 己卯日 |
```

## Calculation Method

### Reference Date
- **1983-02-05 = 甲子日** (calibrated against verified sources)
- Day stem-branch: `(days since reference) % 60` → stem = pos % 10, branch = pos % 12

### Day Calculation
```
delta = (date - 1983-02-05).days
stem_idx = delta % 10
branch_idx = delta % 12
day_stem_branch = STEMS[stem_idx] + BRANCHES[branch_idx]
```

### Month Calculation
Month branches: 正月=寅, 二月=卯, 三月=辰...
```
month_branch_idx = (month + 1) % 12
month_stem_idx = (year_stem_idx * 2 + month) % 10
month_stem_branch = STEMS[month_stem_idx] + BRANCHES[month_branch_idx]
```

### Year Calculation
```
cycle_pos = (year - 4) % 60
year_stem_idx = cycle_pos % 10
year_branch_idx = cycle_pos % 12
year_stem_branch = STEMS[year_stem_idx] + BRANCHES[year_branch_idx]
```

## Constants

```python
STEMS = [\'甲\', \'乙\', \'丙\', \'丁\', \'戊\', \'己\', \'庚\', \'辛\', \'壬\', \'癸\']
BRANCHES = [\'子\', \'丑\', \'寅\', \'卯\', \'辰\', \'巳\', \'午\', \'未\', \'申\', \'酉\', \'戌\', \'亥\']
ZODIAC = {
    \'子\': \'鼠\', \'丑\': \'牛\', \'寅\': \'虎\', \'卯\': \'兔\',
    \'辰\': \'龙\', \'巳\': \'蛇\', \'午\': \'马\', \'未\': \'羊\',
    \'申\': \'猴\', \'酉\': \'鸡\', \'戌\': \'狗\', \'亥\': \'猪\'
}
```
'''

(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")