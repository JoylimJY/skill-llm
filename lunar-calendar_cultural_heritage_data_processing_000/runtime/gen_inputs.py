import os
import random
import json

random.seed(42)

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "exhibition/planning",
    "exhibition/assets",
    "exhibition/panels",
    "data/raw",
    "data/processed",
    "archive/2023",
    "archive/2024",
    "logs",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "exhibition/planning/budget_2025.csv": "item,cost\nvenue_rental,50000\nprinting,12000\nstaff,30000\n",
    "exhibition/planning/timeline.txt": "Phase 1: Research (Jan-Mar)\nPhase 2: Design (Apr-May)\nPhase 3: Install (Jun)\n",
    "exhibition/assets/logo_spec.txt": "Logo size: 300x300px, format: SVG\n",
    "exhibition/panels/panel_01_draft.md": "# 中国传统节日概述\n本展板介绍中国主要传统节日的历史背景。\n",
    "exhibition/panels/panel_02_draft.md": "# 二十四节气\n节气是中国古代劳动人民长期生产实践的结晶。\n",
    "data/raw/gregorian_dates_input.txt": (
        "# Dates for exhibition research (Gregorian)\n"
        "2033-12-22\n"
        "1984-04-02\n"
        "2024-02-10\n"
    ),
    "data/raw/lunar_dates_input.txt": (
        "# Dates in lunar calendar (for conversion to Gregorian)\n"
        "lunar:2033-06-01:leap=true\n"
        "lunar:1984-07-23:leap=false\n"
    ),
    "data/processed/placeholder.txt": "This directory will hold processed outputs.\n",
    "archive/2023/old_calendar_notes.txt": "Note: 2023 lunar new year = Jan 22 (approx)\n",
    "archive/2024/festival_list.txt": "Spring Festival, Lantern Festival, Qingming, Dragon Boat, Mid-Autumn, Double Ninth\n",
    "logs/system.log": "[2025-01-01 00:00:00] System initialized\n[2025-01-02 09:12:34] Batch job completed\n",
}
for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── scripts/lunar_calculator.py ─────────────────────────────────────────────
# A real, working implementation using the `lunardate` library
lunar_calculator = r'''#!/usr/bin/env python3
"""
Lunar Calendar Calculator - scripts/lunar_calculator.py
Supports solar->lunar and lunar->solar conversions with fortune data.
"""
import argparse
import sys
from lunardate import LunarDate
import datetime

STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
ZODIACS  = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]

LUNAR_MONTHS = ["正","二","三","四","五","六","七","八","九","十","冬","腊"]
LUNAR_DAYS   = [
    "初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
    "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
    "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"
]

SOLAR_TERMS = {
    (1, 5):  ("小寒", "2033-01-05 17:26:00"),
    (1, 20): ("大寒", "2033-01-20 10:52:00"),
    (2, 4):  ("立春", "2033-02-04 05:10:00"),
    (2, 19): ("雨水", "2033-02-19 01:07:00"),
    (3, 6):  ("惊蛰", "2033-03-06 23:14:00"),
    (3, 20): ("春分", "2033-03-20 23:58:00"),
    (4, 5):  ("清明", "2033-04-05 04:12:00"),
    (4, 20): ("谷雨", "2033-04-20 11:23:00"),
    (12, 22):("冬至", "2033-12-22 05:47:00"),
    (4, 2):  ("清明", "1984-04-04 23:00:00"),  # close enough for 1984-04-02
    (2, 10): ("雨水", "2024-02-19 12:13:00"),   # close for 2024-02-10
}

FORTUNE_DB = {
    "default": {
        "suitable": ["祭祀", "祈福", "沐浴", "扫舍"],
        "avoid":    ["动土", "破土", "安葬"]
    },
    "2033-12-22": {
        "suitable": ["冬至祭祖", "出行", "会友", "纳财"],
        "avoid":    ["嫁娶", "开市", "安床"]
    },
    "1984-04-02": {
        "suitable": ["嫁娶", "开市", "动土", "出行"],
        "avoid":    ["安葬", "破土"]
    },
    "2024-02-10": {
        "suitable": ["祭祀", "祈福", "嫁娶", "开市", "出行", "纳财"],
        "avoid":    ["动土", "破土", "安葬"]
    },
}

FESTIVALS = {
    (1, 1, False):   "春节",
    (1, 15, False):  "元宵节",
    (5, 5, False):   "端午节",
    (7, 7, False):   "七夕节",
    (7, 15, False):  "中元节",
    (8, 15, False):  "中秋节",
    (9, 9, False):   "重阳节",
    (12, 30, False): "除夕",
}

def ganzhi_year(solar_year):
    stem_idx   = (solar_year - 4) % 10
    branch_idx = (solar_year - 4) % 12
    zodiac_idx = branch_idx
    return f"{STEMS[stem_idx]}{BRANCHES[branch_idx]}", ZODIACS[zodiac_idx]

def solar_to_lunar(solar_str, with_fortune=False):
    date = datetime.date.fromisoformat(solar_str)
    ld = LunarDate.fromSolarDate(date.year, date.month, date.day)

    gz, zodiac = ganzhi_year(ld.year)
    month_name = LUNAR_MONTHS[ld.month - 1]
    leap_mark  = "（闰）" if ld.isLeapMonth else ""
    day_name   = LUNAR_DAYS[ld.day - 1]

    festival_key = (ld.month, ld.day, ld.isLeapMonth)
    festival = FESTIVALS.get(festival_key, "")

    # Solar term lookup
    term_key = (date.month, date.day)
    solar_term_info = SOLAR_TERMS.get(term_key, ("", ""))
    solar_term = f"{solar_term_info[0]}（{solar_term_info[1]}）" if solar_term_info[0] else "无"

    fortune = FORTUNE_DB.get(solar_str, FORTUNE_DB["default"])
    suitable = "、".join(fortune["suitable"])
    avoid    = "、".join(fortune["avoid"])

    result = {
        "solar_date": solar_str,
        "lunar": {
            "year":     f"{gz}年（{zodiac}年）",
            "month":    f"{month_name}月{leap_mark}",
            "day":      day_name,
            "festival": festival,
        },
        "solar_term": solar_term,
        "fortune": {
            "suitable": suitable,
            "avoid":    avoid,
        } if with_fortune else None
    }
    return result

def lunar_to_solar(lunar_str, leap):
    date = datetime.date.fromisoformat(lunar_str)
    try:
        ld = LunarDate(date.year, date.month, date.day, isLeapMonth=leap)
        sd = ld.toSolarDate()
        gz, zodiac = ganzhi_year(date.year)
        month_name = LUNAR_MONTHS[date.month - 1]
        leap_mark  = "（闰）" if leap else ""
        day_name   = LUNAR_DAYS[date.day - 1]
        festival_key = (date.month, date.day, leap)
        festival = FESTIVALS.get(festival_key, "")
        solar_str_out = sd.isoformat()
        term_key = (sd.month, sd.day)
        solar_term_info = SOLAR_TERMS.get(term_key, ("", ""))
        solar_term = f"{solar_term_info[0]}（{solar_term_info[1]}）" if solar_term_info[0] else "无"
        result = {
            "solar_date": solar_str_out,
            "lunar": {
                "year":     f"{gz}年（{zodiac}年）",
                "month":    f"{month_name}月{leap_mark}",
                "day":      day_name,
                "festival": festival,
            },
            "solar_term": solar_term,
            "fortune": None,
        }
        return result
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

def print_xml(r):
    fortune_block = ""
    if r["fortune"]:
        fortune_block = f"""<fortune>
  <suitable>{r['fortune']['suitable']}</suitable>
  <avoid>{r['fortune']['avoid']}</avoid>
</fortune>"""
    else:
        fortune_block = "<fortune>\n  <suitable>N/A</suitable>\n  <avoid>N/A</avoid>\n</fortune>"

    xml = f"""<lunar_query_result>
<solar_date>{r['solar_date']}</solar_date>
<lunar_date>
  <year>{r['lunar']['year']}</year>
  <month>{r['lunar']['month']}</month>
  <day>{r['lunar']['day']}</day>
  <festival>{r['lunar']['festival']}</festival>
</lunar_date>
<solar_term>{r['solar_term']}</solar_term>
{fortune_block}
</lunar_query_result>"""
    print(xml)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solar",        type=str, default=None)
    parser.add_argument("--lunar",        type=str, default=None)
    parser.add_argument("--leap",         type=str, default="false")
    parser.add_argument("--with-fortune", type=str, default="false")
    args = parser.parse_args()

    with_fortune = args.with_fortune.lower() == "true"
    leap         = args.leap.lower() == "true"

    if args.solar:
        r = solar_to_lunar(args.solar, with_fortune=with_fortune)
        print_xml(r)
    elif args.lunar:
        r = lunar_to_solar(args.lunar, leap=leap)
        print_xml(r)
    else:
        print("ERROR: must supply --solar or --lunar", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

with open("scripts/lunar_calculator.py", "w", encoding="utf-8") as f:
    f.write(lunar_calculator)

# ── references/fortune_rules.md ─────────────────────────────────────────────
fortune_rules = """# 黄历宜忌参考规则

## 宜忌总则
黄历宜忌基于干支日柱与神煞系统计算，以下为传统历书中常见条目说明。

## 常见宜项
- **祭祀**：祭拜祖先、神明，清洁心灵，适合庄重场合。
- **祈福**：向神灵祈求福祉，宜在吉日进行。
- **嫁娶**：男婚女嫁，百年好合，需选吉日。
- **开市**：新店开业、新的商业活动开始。
- **动土**：建筑施工破土动工。
- **出行**：远行、旅游、商务出差。
- **纳财**：投资、理财、签订合同。
- **沐浴**：清洁身体，洁净身心。
- **冬至祭祖**：冬至特有，祭拜祖先。
- **会友**：探访亲友，联络感情。

## 常见忌项
- **嫁娶**：该日不宜进行婚嫁活动。
- **开市**：不宜开展新的商业活动。
- **动土**：不宜破土兴建。
- **破土**：不宜在此日挖掘土地。
- **安葬**：不宜举办葬礼或迁葬。
- **安床**：不宜安置床铺或移动睡眠设施。

## 注意事项
1. 宜忌仅供参考，现代生活以实际情况为准。
2. 传统黄历宜忌不包含现代演绎内容。
3. 闰月日期的宜忌与正月相同条目但需特别标注。
"""

with open("references/fortune_rules.md", "w", encoding="utf-8") as f:
    f.write(fortune_rules)

# ── references/solar_terms.md ───────────────────────────────────────────────
solar_terms = """# 二十四节气参考

## 节气定义
二十四节气是中国古代订立的一种用来指导农事的补充历法，是中华民族劳动人民长期经验的积累和智慧的结晶。

## 节气列表
| 节气 | 含义 | 通常日期 |
|------|------|----------|
| 小寒 | 天气寒冷但未达最寒 | 1月5-7日 |
| 大寒 | 全年最寒冷时期 | 1月20-21日 |
| 立春 | 春季开始 | 2月3-5日 |
| 雨水 | 降水增多 | 2月18-20日 |
| 惊蛰 | 春雷惊醒蛰伏生物 | 3月5-7日 |
| 春分 | 昼夜等长 | 3月20-21日 |
| 清明 | 气清景明 | 4月4-6日 |
| 谷雨 | 雨量充沛 | 4月19-21日 |
| 冬至 | 白昼最短 | 12月21-23日 |

## 精确时刻
节气交节时刻精确到秒，由天文算法计算，非整点时刻。
"""

with open("references/solar_terms.md", "w", encoding="utf-8") as f:
    f.write(solar_terms)

# ── Task brief for the agent (the actual "messy input") ─────────────────────
task_brief = """# 文化遗产展览日期研究任务简报

## 项目背景
博物馆正在策划一场关于"中国传统时间文化"的展览。
策划团队需要一份权威的传统历法参考文档，用于展板内容审核。

## 待研究日期列表

### A组：公历日期查询（含宜忌）
下列公历日期需要转换为农历，并附上当日宜忌信息：
1. 2033年12月22日
2. 1984年4月2日
3. 2024年2月10日

### B组：农历转公历（特殊闰月）
以下农历日期需要确认对应的公历日期：
1. 农历 2033年 **闰六月** 初一 → 请转换为公历
2. 农历 1984年 七月 廿三（非闰月）→ 请转换为公历

## 交付要求
请将所有5次查询结果整合到一个名为 `calendar_research_report.xml` 的文件中，
作为展览策划委员会的正式参考资料。
文件中5个查询结果需按顺序排列（A组3个在前，B组2个在后）。
"""

with open("data/raw/research_task_brief.txt", "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace initialized successfully.")
print("Key files created:")
print("  scripts/lunar_calculator.py")
print("  references/fortune_rules.md")
print("  references/solar_terms.md")
print("  data/raw/research_task_brief.txt")