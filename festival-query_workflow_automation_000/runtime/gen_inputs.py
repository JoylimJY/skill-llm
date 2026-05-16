import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create realistic deeply nested directory structure for a travel agency
dirs = [
    "scripts",
    "agency/brochures/2024",
    "agency/brochures/2025/drafts",
    "agency/brochures/2025/final",
    "agency/tours/china",
    "agency/tours/europe",
    "agency/marketing/social_media",
    "agency/marketing/email_campaigns",
    "agency/clients/vip",
    "agency/clients/general",
    "agency/finance/invoices",
    "agency/finance/reports",
    "data/raw/scraped",
    "data/processed",
    "config",
    "logs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files with plausible-sounding but irrelevant content
distractor_files = {
    "agency/brochures/2024/china_tour_2024.pdf.txt": "Placeholder for 2024 China tour brochure. Contact marketing team.",
    "agency/brochures/2025/drafts/draft_v1.txt": "Draft v1: Tentative schedule for 2025 tours. Dates TBD pending cultural calendar confirmation.",
    "agency/brochures/2025/drafts/draft_v2.txt": "Draft v2: Added European routes. Chinese festival dates still unconfirmed.",
    "agency/tours/china/itinerary_template.txt": "Day 1: Arrival Beijing\nDay 2: Great Wall\nDay 3: [FESTIVAL_PLACEHOLDER]\nDay 4: Departure",
    "agency/tours/china/pricing_2025.csv": "tour_name,base_price,festival_surcharge\nSpring Festival Tour,2999,500\nMid-Autumn Tour,2499,300\nDragon Boat Tour,1999,200",
    "agency/tours/europe/xmas_markets.txt": "Christmas market tours: December dates TBD. Confirm with local operators.",
    "agency/marketing/social_media/content_calendar_template.xlsx.txt": "Q1: Spring Festival content\nQ2: Dragon Boat content\nQ3: Mid-Autumn content\nQ4: Christmas content",
    "agency/marketing/email_campaigns/campaign_brief.txt": "Subject: 2025 Cultural Festival Tours\nTarget: International travelers interested in Chinese culture\nKey dates: To be filled by research team",
    "agency/clients/vip/preferences.json": json.dumps({
        "client_001": {"name": "Smith Family", "interest": "Chinese traditional culture", "preferred_festivals": ["Spring Festival", "Mid-Autumn"]},
        "client_002": {"name": "Johnson Corp", "interest": "Team building during holidays", "preferred_festivals": ["Dragon Boat", "Christmas"]}
    }, indent=2),
    "agency/clients/general/survey_results.txt": "Survey: 68% of clients want festival-specific tours\n45% interested in Chinese New Year\n33% interested in Mid-Autumn Festival",
    "agency/finance/invoices/invoice_2024_festival_research.txt": "Invoice #2024-FR-001\nService: Festival date research for 2024 brochure\nAmount: $450\nStatus: Paid",
    "agency/finance/reports/q4_2024_summary.txt": "Q4 2024 Revenue: $1.2M\nFestival tours contributed 34% of revenue\n2025 projections pending calendar finalization",
    "data/raw/scraped/festival_dates_rough.txt": "NOTE: This data is UNVERIFIED and may be wrong. Do not use without cross-checking.\nSpring Festival 2025: possibly late January?\nMid-Autumn 2025: October?\nDragon Boat 2025: unknown",
    "data/raw/scraped/western_holidays_partial.txt": "Christmas: Dec 25 (always)\nNew Year: Jan 1 (always)\nValentine's Day: Feb 14 (always)\nEaster: varies each year - 2025 date unknown\nThanksgiving: varies - 4th Thursday of November",
    "data/processed/incomplete_calendar_2025.json": json.dumps({
        "year": 2025,
        "status": "INCOMPLETE - DO NOT USE",
        "festivals": {
            "spring_festival": "UNKNOWN",
            "dragon_boat": "UNKNOWN",
            "mid_autumn": "UNKNOWN",
            "christmas": "2025-12-25"
        },
        "note": "Lunar-based dates need proper calculation tool"
    }, indent=2),
    "config/agency_settings.json": json.dumps({
        "agency_name": "CulturalBridge Travel Agency",
        "output_format": "json",
        "brochure_year": 2025,
        "target_markets": ["USA", "UK", "Australia", "Canada"]
    }, indent=2),
    "logs/research_log.txt": "2024-11-15: Started 2025 cultural calendar research\n2024-11-16: Identified need for accurate lunar calendar data\n2024-11-17: Awaiting tool setup to query festival dates",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create the festival_query.py script in scripts/
festival_query_script = '''#!/usr/bin/env python3
"""节日查询工具 - 支持中国农历、传统节日、二十四节气、欧美节日"""

import argparse
import sys
from datetime import date, timedelta

try:
    from zhdate import ZhDate
except ImportError:
    print("请安装依赖: pip install zhdate", file=sys.stderr)
    sys.exit(1)

try:
    import holidays
except ImportError:
    print("请安装依赖: pip install holidays", file=sys.stderr)
    sys.exit(1)

# 二十四节气数据（2020-2030）精确日期
SOLAR_TERMS = {
    2025: {
        "小寒": "2025-01-05",
        "大寒": "2025-01-20",
        "立春": "2025-02-03",
        "雨水": "2025-02-18",
        "惊蛰": "2025-03-05",
        "春分": "2025-03-20",
        "清明": "2025-04-04",
        "谷雨": "2025-04-20",
        "立夏": "2025-05-05",
        "小满": "2025-05-21",
        "芒种": "2025-06-05",
        "夏至": "2025-06-21",
        "小暑": "2025-07-07",
        "大暑": "2025-07-22",
        "立秋": "2025-08-07",
        "处暑": "2025-08-22",
        "白露": "2025-09-07",
        "秋分": "2025-09-23",
        "寒露": "2025-10-08",
        "霜降": "2025-10-23",
        "立冬": "2025-11-07",
        "小雪": "2025-11-22",
        "大雪": "2025-12-07",
        "冬至": "2025-12-22",
    },
    2026: {
        "小寒": "2026-01-05",
        "大寒": "2026-01-20",
        "立春": "2026-02-04",
        "雨水": "2026-02-19",
        "惊蛰": "2026-03-06",
        "春分": "2026-03-21",
        "清明": "2026-04-05",
        "谷雨": "2026-04-20",
        "立夏": "2026-05-06",
        "小满": "2026-05-21",
        "芒种": "2026-06-06",
        "夏至": "2026-06-21",
        "小暑": "2026-07-07",
        "大暑": "2026-07-23",
        "立秋": "2026-08-07",
        "处暑": "2026-08-23",
        "白露": "2026-09-08",
        "秋分": "2026-09-23",
        "寒露": "2026-10-08",
        "霜降": "2026-10-23",
        "立冬": "2026-11-07",
        "小雪": "2026-11-22",
        "大雪": "2026-12-07",
        "冬至": "2026-12-22",
    },
}

# 天干地支
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

def get_ganzhi(year):
    tg = TIANGAN[(year - 4) % 10]
    dz = DIZHI[(year - 4) % 12]
    sx = SHENGXIAO[(year - 4) % 12]
    return f"{tg}{dz}年（{sx}年）"

def get_lunar_info(greg_date):
    try:
        zh = ZhDate.from_datetime(greg_date)
        lunar_month = zh.lunar_month
        lunar_day = zh.lunar_day
        lunar_year = zh.lunar_year
        
        month_names = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
        day_names = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                     "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                     "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]
        
        month_str = month_names[lunar_month - 1] + "月"
        day_str = day_names[lunar_day - 1]
        ganzhi = get_ganzhi(lunar_year)
        
        return {
            "lunar_year": lunar_year,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "lunar_month_name": month_str,
            "lunar_day_name": day_str,
            "ganzhi": ganzhi,
        }
    except Exception as e:
        return None

def get_chinese_festivals(greg_date):
    """通过农历日期匹配中国传统节日"""
    festivals = []
    lunar = get_lunar_info(greg_date)
    if not lunar:
        return festivals
    
    m = lunar["lunar_month"]
    d = lunar["lunar_day"]
    
    festival_map = {
        (1, 1): "春节",
        (1, 15): "元宵节",
        (2, 2): "龙抬头",
        (5, 5): "端午节",
        (7, 7): "七夕节",
        (7, 15): "中元节",
        (8, 15): "中秋节",
        (9, 9): "重阳节",
        (12, 8): "腊八节",
    }
    
    # 小年：腊月二十三（北方）
    if m == 12 and d == 23:
        festivals.append("小年（北方）")
    # 除夕：腊月最后一天（腊月三十或二十九）
    if m == 12 and d in [29, 30]:
        # Check if next day is Spring Festival
        next_day = greg_date + timedelta(days=1)
        next_lunar = get_lunar_info(next_day)
        if next_lunar and next_lunar["lunar_month"] == 1 and next_lunar["lunar_day"] == 1:
            festivals.append("除夕")
    
    if (m, d) in festival_map:
        festivals.append(festival_map[(m, d)])
    
    return festivals

def get_solar_term(greg_date, year):
    """获取节气"""
    if year not in SOLAR_TERMS:
        return None
    date_str = greg_date.strftime("%Y-%m-%d")
    for term, term_date in SOLAR_TERMS[year].items():
        if term_date == date_str:
            return term
    return None

def get_western_festivals(greg_date):
    """获取欧美/国际节日"""
    festivals = []
    y = greg_date.year
    m = greg_date.month
    d = greg_date.day
    
    # Fixed dates
    fixed = {
        (1, 1): "元旦（New Year\'s Day）",
        (2, 14): "情人节（Valentine\'s Day）",
        (4, 1): "愚人节（April Fools\' Day）",
        (5, 1): "国际劳动节（International Workers\' Day）",
        (10, 31): "万圣节（Halloween）",
        (12, 24): "平安夜（Christmas Eve）",
        (12, 25): "圣诞节（Christmas Day）",
        (12, 26): "节礼日（Boxing Day）",
    }
    if (m, d) in fixed:
        festivals.append(fixed[(m, d)])
    
    # Easter (using algorithm)
    easter_date = _easter(y)
    if greg_date == easter_date:
        festivals.append("复活节（Easter）")
    
    # Mother\'s Day: 2nd Sunday of May
    if m == 5:
        sundays = [date(y, 5, day) for day in range(1, 32) if date(y, 5, day).weekday() == 6]
        if len(sundays) >= 2 and greg_date == sundays[1]:
            festivals.append("母亲节（Mother\'s Day）")
    
    # Father\'s Day: 3rd Sunday of June
    if m == 6:
        sundays = [date(y, 6, day) for day in range(1, 31) if date(y, 6, day).weekday() == 6]
        if len(sundays) >= 3 and greg_date == sundays[2]:
            festivals.append("父亲节（Father\'s Day）")
    
    # Thanksgiving: 4th Thursday of November (US)
    if m == 11:
        thursdays = [date(y, 11, day) for day in range(1, 31) if date(y, 11, day).weekday() == 3]
        if len(thursdays) >= 4 and greg_date == thursdays[3]:
            festivals.append("感恩节（Thanksgiving Day）")
    
    return festivals

def _easter(year):
    """Anonymous Gregorian algorithm for Easter"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def query_date(date_str):
    """查询指定日期"""
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        print(f"日期格式错误: {date_str}，请使用 YYYY-MM-DD 格式")
        sys.exit(1)
    
    print(f"\\n=== 查询日期: {date_str} ({d.strftime(\'%A\')}) ===")
    
    lunar = get_lunar_info(d)
    if lunar:
        print(f"农历: {lunar[\'ganzhi\']} {lunar[\'lunar_month_name\']}{lunar[\'lunar_day_name\']}")
        print(f"农历年份: {lunar[\'lunar_year\']} 年")
        print(f"农历月: {lunar[\'lunar_month\']} 月 ({lunar[\'lunar_month_name\']})")
        print(f"农历日: {lunar[\'lunar_day\']} 日 ({lunar[\'lunar_day_name\']})")
    
    solar_term = get_solar_term(d, d.year)
    if solar_term:
        print(f"节气: {solar_term}")
    
    cn_festivals = get_chinese_festivals(d)
    if cn_festivals:
        print(f"中国传统节日: {\'、\'.join(cn_festivals)}")
    
    western = get_western_festivals(d)
    if western:
        print(f"欧美/国际节日: {\'、\'.join(western)}")
    
    if not solar_term and not cn_festivals and not western:
        print("今日无特殊节日或节气")

def query_year(year):
    """查询全年节日"""
    print(f"\\n=== {year} 年节日与节气总览 ===")
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    current = start
    while current <= end:
        events = []
        solar_term = get_solar_term(current, year)
        if solar_term:
            events.append(f"[节气] {solar_term}")
        cn_festivals = get_chinese_festivals(current)
        for f in cn_festivals:
            events.append(f"[中国节日] {f}")
        western = get_western_festivals(current)
        for f in western:
            events.append(f"[西方节日] {f}")
        if events:
            print(f"{current.strftime(\'%Y-%m-%d\')}: {\' | \'.join(events)}")
        current += timedelta(days=1)

def query_month(month_str):
    """查询指定月份节日"""
    try:
        parts = month_str.split("-")
        year = int(parts[0])
        month = int(parts[1])
        d = date(year, month, 1)
    except (ValueError, IndexError):
        print(f"月份格式错误: {month_str}，请使用 YYYY-MM 格式")
        sys.exit(1)
    
    print(f"\\n=== {month_str} 月节日与节气 ===")
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    
    current = d
    while current <= end:
        events = []
        solar_term = get_solar_term(current, year)
        if solar_term:
            events.append(f"[节气] {solar_term}")
        cn_festivals = get_chinese_festivals(current)
        for f in cn_festivals:
            events.append(f"[中国节日] {f}")
        western = get_western_festivals(current)
        for f in western:
            events.append(f"[西方节日] {f}")
        if events:
            print(f"{current.strftime(\'%Y-%m-%d\')}: {\' | \'.join(events)}")
        current += timedelta(days=1)

def query_terms(year):
    """查询全年二十四节气"""
    print(f"\\n=== {year} 年二十四节气 ===")
    if year not in SOLAR_TERMS:
        print(f"暂无 {year} 年节气数据")
        return
    terms = SOLAR_TERMS[year]
    order = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
             "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
             "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
    for term in order:
        if term in terms:
            print(f"{term}: {terms[term]}")

def main():
    parser = argparse.ArgumentParser(description="节日查询工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date", type=str, help="查询指定日期 (YYYY-MM-DD)")
    group.add_argument("--year", type=int, help="查询全年节日 (YYYY)")
    group.add_argument("--month", type=str, help="查询指定月份节日 (YYYY-MM)")
    group.add_argument("--terms", type=int, help="查看全年二十四节气 (YYYY)")
    
    args = parser.parse_args()
    
    if args.date:
        query_date(args.date)
    elif args.year:
        query_year(args.year)
    elif args.month:
        query_month(args.month)
    elif args.terms:
        query_terms(args.terms)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts/festival_query.py"), "w", encoding="utf-8") as f:
    f.write(festival_query_script)

# The task: Agent must produce agency/brochures/2025/final/cultural_calendar_2025.json
# with specific queried data from the tool

print("Workspace setup complete.")
print(f"Files created: {len(distractor_files) + 1}")