#!/usr/bin/env python3
"""
Generate the sandbox workspace for the Bazi analysis task.
Creates a realistic consultancy directory structure with distractor files
and the actual skill directory with the bazi_chart.py script.
"""

import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/bazi-analysis/scripts",
    "skills/bazi-analysis/references",
    "clients/intake_forms",
    "clients/archived_reports/2023",
    "clients/archived_reports/2024",
    "config/templates",
    "config/locales",
    "reports/pending",
    "reports/delivered",
    "internal/qa",
    "internal/billing",
    "logs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "clients/intake_forms/client_007_intake.txt": (
        "Name: Zhang Wei\nDOB: 1985-03-22\nGender: Male\nNotes: Prefers evening consultation\n"
    ),
    "clients/intake_forms/client_008_intake.txt": (
        "Name: Liu Mei\nDOB: 1992-07-14\nGender: Female\nNotes: Interested in career outlook\n"
    ),
    "clients/archived_reports/2023/report_client_001.md": (
        "# Bazi Report – Client 001\n\nDate: 1978-06-15\n\n*Archived report from 2023 consultation cycle.*\n"
    ),
    "clients/archived_reports/2024/report_client_005.json": json.dumps(
        {"client_id": "005", "date": "1990-11-03", "status": "delivered"}, indent=2
    ),
    "config/templates/report_template.md": (
        "# {{client_name}} – Bazi Consultation\n\n## Chart Facts\n{{chart_facts}}\n\n## Interpretation\n{{interpretation}}\n"
    ),
    "config/templates/json_schema.json": json.dumps(
        {
            "type": "object",
            "properties": {
                "pillars": {"type": "array"},
                "day_master": {"type": "string"},
                "luck_cycles": {"type": "array"},
            },
        },
        indent=2,
    ),
    "config/locales/zh_CN.json": json.dumps(
        {"greeting": "欢迎", "report_title": "八字命盘报告"}, indent=2
    ),
    "internal/qa/checklist.md": (
        "# QA Checklist\n\n- [ ] Verify four pillars\n- [ ] Check day master\n- [ ] Confirm luck cycle start year\n"
    ),
    "internal/billing/invoice_2024_q3.csv": (
        "client_id,amount,status\n001,500,paid\n002,500,pending\n003,750,paid\n"
    ),
    "logs/app.log": (
        "[2024-12-01 09:00:01] INFO: Script started\n"
        "[2024-12-01 09:00:02] INFO: Chart generated for client 003\n"
        "[2024-12-01 09:00:03] WARN: Birth time near boundary – recommend adjacent chart check\n"
    ),
    "reports/delivered/client_003_final.md": (
        "# Final Report – Client 003\n\nDelivered on 2024-12-01.\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── references/notes.md ─────────────────────────────────────────────────────
(WORKSPACE / "skills/bazi-analysis/references/notes.md").write_text(
    "# Bazi Analysis Notes\n\n"
    "## School Differences\n"
    "- Sect 1 uses solar calendar exclusively for hour branch.\n"
    "- Sect 2 (default) applies additional corrections for night birth.\n\n"
    "## Boundary Times\n"
    "Times within 5 minutes of a full hour may shift the hour pillar.\n\n"
    "## Yearly Outlook\n"
    "Use `--from-year` to anchor the start year for annual flow analysis.\n",
    encoding="utf-8",
)

# ── The actual bazi_chart.py script ─────────────────────────────────────────
bazi_chart_script = r'''#!/usr/bin/env python3
"""
Bazi Chart Generator – skills/bazi-analysis/scripts/bazi_chart.py
Generates a Four Pillars (Bazi) consultation report.
"""

import argparse
import json
import sys
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Minimal self-contained Bazi calculation (no external dependency required)
# ---------------------------------------------------------------------------

HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
NAYIN = [
    "海中金","炉中火","大林木","路旁土","剑锋金","山头火",
    "涧下水","城头土","白蜡金","杨柳木","泉中水","屋上土",
    "霹雳火","松柏木","长流水","沙中金","山下火","平地木",
    "壁上土","金箔金","覆灯火","天河水","大驿土","钗钏金",
    "桑柘木","大溪水","沙中土","天上火","石榴木","大海水"
]
ELEMENTS = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
            "己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
BRANCH_ELEMENTS = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土",
                   "巳":"火","午":"火","未":"土","申":"金","酉":"金",
                   "戌":"土","亥":"水"}
HIDDEN_STEMS = {
    "子":["癸"],"丑":["己","癸","辛"],"寅":["甲","丙","戊"],
    "卯":["乙"],"辰":["戊","乙","癸"],"巳":["丙","庚","戊"],
    "午":["丁","己"],"未":["己","丁","乙"],"申":["庚","壬","戊"],
    "酉":["辛"],"戌":["戊","辛","丁"],"亥":["壬","甲"]
}
TEN_GODS_TABLE = {
    ("甲","甲"):"比肩",("甲","乙"):"劫财",("甲","丙"):"食神",("甲","丁"):"伤官",
    ("甲","戊"):"偏财",("甲","己"):"正财",("甲","庚"):"七杀",("甲","辛"):"正官",
    ("甲","壬"):"偏印",("甲","癸"):"正印",
    ("乙","甲"):"劫财",("乙","乙"):"比肩",("乙","丙"):"伤官",("乙","丁"):"食神",
    ("乙","戊"):"正财",("乙","己"):"偏财",("乙","庚"):"正官",("乙","辛"):"七杀",
    ("乙","壬"):"正印",("乙","癸"):"偏印",
    ("丙","甲"):"偏印",("丙","乙"):"正印",("丙","丙"):"比肩",("丙","丁"):"劫财",
    ("丙","戊"):"食神",("丙","己"):"伤官",("丙","庚"):"偏财",("丙","辛"):"正财",
    ("丙","壬"):"七杀",("丙","癸"):"正官",
    ("丁","甲"):"正印",("丁","乙"):"偏印",("丁","丙"):"劫财",("丁","丁"):"比肩",
    ("丁","戊"):"伤官",("丁","己"):"食神",("丁","庚"):"正财",("丁","辛"):"偏财",
    ("丁","壬"):"正官",("丁","癸"):"七杀",
    ("戊","甲"):"七杀",("戊","乙"):"正官",("戊","丙"):"偏印",("戊","丁"):"正印",
    ("戊","戊"):"比肩",("戊","己"):"劫财",("戊","庚"):"食神",("戊","辛"):"伤官",
    ("戊","壬"):"偏财",("戊","癸"):"正财",
    ("己","甲"):"正官",("己","乙"):"七杀",("己","丙"):"正印",("己","丁"):"偏印",
    ("己","戊"):"劫财",("己","己"):"比肩",("己","庚"):"伤官",("己","辛"):"食神",
    ("己","壬"):"正财",("己","癸"):"偏财",
    ("庚","甲"):"偏财",("庚","乙"):"正财",("庚","丙"):"七杀",("庚","丁"):"正官",
    ("庚","戊"):"偏印",("庚","己"):"正印",("庚","庚"):"比肩",("庚","辛"):"劫财",
    ("庚","壬"):"食神",("庚","癸"):"伤官",
    ("辛","甲"):"正财",("辛","乙"):"偏财",("辛","丙"):"正官",("辛","丁"):"七杀",
    ("辛","戊"):"正印",("辛","己"):"偏印",("辛","庚"):"劫财",("辛","辛"):"比肩",
    ("辛","壬"):"伤官",("辛","癸"):"食神",
    ("壬","甲"):"食神",("壬","乙"):"伤官",("壬","丙"):"偏财",("壬","丁"):"正财",
    ("壬","戊"):"七杀",("壬","己"):"正官",("壬","庚"):"偏印",("壬","辛"):"正印",
    ("壬","壬"):"比肩",("壬","癸"):"劫财",
    ("癸","甲"):"伤官",("癸","乙"):"食神",("癸","丙"):"正财",("癸","丁"):"偏财",
    ("癸","戊"):"正官",("癸","己"):"七杀",("癸","庚"):"正印",("癸","辛"):"偏印",
    ("癸","壬"):"劫财",("癸","癸"):"比肩",
}

def _year_pillar(year):
    s = (year - 4) % 10
    b = (year - 4) % 12
    return HEAVENLY_STEMS[s], EARTHLY_BRANCHES[b]

def _month_pillar(year, month, sect=2):
    # simplified: month branch is month-1 offset from 寅(index 2)
    branch_idx = (month + 1) % 12
    # year stem drives month stem cycle
    year_stem_idx = (year - 4) % 10
    base = (year_stem_idx % 5) * 2
    stem_idx = (base + month - 1) % 10
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx]

def _day_pillar(year, month, day):
    # Zeller-inspired simplified day pillar
    d = date(year, month, day)
    base = date(1900, 1, 1)
    delta = (d - base).days
    stem_idx = (delta + 6) % 10
    branch_idx = (delta + 6) % 12
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx]

def _hour_pillar(hour, day_stem, sect=2):
    # Each 2-hour block = one branch
    branch_idx = (hour // 2) % 12
    day_stem_idx = HEAVENLY_STEMS.index(day_stem)
    base = (day_stem_idx % 5) * 2
    stem_idx = (base + branch_idx) % 10
    # sect 2: if hour is between 23:00-00:00, shift branch
    if sect == 2 and hour == 23:
        branch_idx = 0
        stem_idx = (base + 0) % 10
    return HEAVENLY_STEMS[stem_idx], EARTHLY_BRANCHES[branch_idx]

def _nayin(stem, branch):
    s = HEAVENLY_STEMS.index(stem)
    b = EARTHLY_BRANCHES.index(branch)
    idx = (s * 6 + b) // 2 % 30
    return NAYIN[idx]

def _luck_cycles(year_stem, year_branch, month_stem, month_branch, gender, birth_year, birth_month, sect=2):
    """Generate 8 luck pillars starting from approximate age."""
    # Simplified: start age based on forward/reverse count
    is_yang_year = HEAVENLY_STEMS.index(year_stem) % 2 == 0
    forward = (is_yang_year and gender in ("male","男")) or \
              (not is_yang_year and gender in ("female","女"))
    # start age ~ 3-8, simplified to 5 for this implementation
    start_age = 5 if sect == 1 else 4
    cycles = []
    ms_idx = HEAVENLY_STEMS.index(month_stem)
    mb_idx = EARTHLY_BRANCHES.index(month_branch)
    for i in range(8):
        if forward:
            si = (ms_idx + i + 1) % 10
            bi = (mb_idx + i + 1) % 12
        else:
            si = (ms_idx - i - 1) % 10
            bi = (mb_idx - i - 1) % 12
        cycles.append({
            "age": start_age + i * 10,
            "stem": HEAVENLY_STEMS[si],
            "branch": EARTHLY_BRANCHES[bi],
            "element": ELEMENTS[HEAVENLY_STEMS[si]]
        })
    return cycles

def _yearly_outlook(day_stem, from_year, years):
    outlooks = []
    for y in range(from_year, from_year + years):
        ys, yb = _year_pillar(y)
        ten_god = TEN_GODS_TABLE.get((day_stem, ys), "未知")
        elem = ELEMENTS[ys]
        outlooks.append({
            "year": y,
            "year_pillar": f"{ys}{yb}",
            "element": elem,
            "ten_god_to_day_master": ten_god
        })
    return outlooks

def _five_element_balance(pillars, sect=2):
    counts = {"木":0,"火":0,"土":0,"金":0,"水":0}
    for stem, branch in pillars:
        counts[ELEMENTS[stem]] += 1
        counts[BRANCH_ELEMENTS[branch]] += 1
        for hs in HIDDEN_STEMS.get(branch, []):
            counts[ELEMENTS[hs]] += 0.5
    total = sum(counts.values())
    return {k: round(v/total*100, 1) for k,v in counts.items()}

def build_chart(date_str, time_str, gender, sect=2, from_year=None, years=10):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    Y, M, D, H = dt.year, dt.month, dt.day, dt.hour

    ys, yb = _year_pillar(Y)
    ms, mb = _month_pillar(Y, M, sect=sect)
    ds, db = _day_pillar(Y, M, D)
    hs_stem, hb = _hour_pillar(H, ds, sect=sect)

    pillars = [(ys, yb), (ms, mb), (ds, db), (hs_stem, hb)]
    pillar_labels = ["年柱", "月柱", "日柱", "时柱"]

    luck = _luck_cycles(ys, yb, ms, mb, gender, Y, M, sect=sect)
    balance = _five_element_balance(pillars, sect=sect)

    # Near-boundary check
    minute = dt.minute
    near_boundary = (minute >= 55 or minute <= 5)

    chart = {
        "meta": {
            "birth_date": date_str,
            "birth_time": time_str,
            "gender": gender,
            "sect": sect,
            "near_hour_boundary": near_boundary
        },
        "pillars": [
            {
                "label": pillar_labels[i],
                "stem": pillars[i][0],
                "branch": pillars[i][1],
                "nayin": _nayin(pillars[i][0], pillars[i][1]),
                "hidden_stems": HIDDEN_STEMS.get(pillars[i][1], []),
                "ten_god": TEN_GODS_TABLE.get((ds, pillars[i][0]), "比肩") if i != 2 else "—"
            }
            for i in range(4)
        ],
        "day_master": {"stem": ds, "element": ELEMENTS[ds]},
        "five_element_balance": balance,
        "luck_cycles": luck,
    }

    if from_year:
        chart["yearly_outlook"] = _yearly_outlook(ds, from_year, years)

    return chart

def render_markdown(chart):
    meta = chart["meta"]
    dm = chart["day_master"]
    lines = []
    lines.append(f"# 八字命盘报告")
    lines.append(f"\n**出生信息**: {meta['birth_date']} {meta['birth_time']} | 性别: {meta['gender']} | 流派: Sect {meta['sect']}\n")
    lines.append("## 四柱")
    lines.append("| 柱 | 天干 | 地支 | 纳音 | 藏干 | 十神 |")
    lines.append("|---|---|---|---|---|---|")
    for p in chart["pillars"]:
        lines.append(f"| {p['label']} | {p['stem']} | {p['branch']} | {p['nayin']} | {'、'.join(p['hidden_stems'])} | {p['ten_god']} |")
    lines.append(f"\n## 日主\n**{dm['stem']}** ({dm['element']})\n")
    lines.append("## 五行平衡")
    for elem, pct in chart["five_element_balance"].items():
        lines.append(f"- {elem}: {pct}%")
    lines.append("\n## 大运")
    lines.append("| 起运年龄 | 天干 | 地支 | 五行 |")
    lines.append("|---|---|---|---|")
    for lc in chart["luck_cycles"]:
        lines.append(f"| {lc['age']} | {lc['stem']} | {lc['branch']} | {lc['element']} |")
    if "yearly_outlook" in chart:
        lines.append("\n## 流年展望")
        lines.append("| 年份 | 年柱 | 五行 | 对日主十神 |")
        lines.append("|---|---|---|---|")
        for yo in chart["yearly_outlook"]:
            lines.append(f"| {yo['year']} | {yo['year_pillar']} | {yo['element']} | {yo['ten_god_to_day_master']} |")
    if meta.get("near_hour_boundary"):
        lines.append(
            "\n> ⚠️ **时辰边界提示**: 出生时间接近整点，建议同时参考相邻时辰的命盘进行比对。"
        )
    lines.append("\n## 诠释\n")
    lines.append("**优势与压力点**: 根据日主与五行格局，建议关注用神与忌神的运程走向。")
    lines.append("\n**事业/财运/感情/健康**: 请结合流年大运具体分析，本报告以事实图表为准，解读仅供参考，不作为医疗、法律或投资建议。\n")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Bazi Chart Generator")
    parser.add_argument("--date", required=True, help="Birth date YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="Birth time HH:MM")
    parser.add_argument("--gender", required=True, choices=["male","female","男","女"])
    parser.add_argument("--format", choices=["markdown","json"], default="markdown")
    parser.add_argument("--sect", type=int, choices=[1,2], default=2)
    parser.add_argument("--from-year", type=int, default=None)
    parser.add_argument("--years", type=int, default=10)
    args = parser.parse_args()

    chart = build_chart(
        args.date, args.time, args.gender,
        sect=args.sect,
        from_year=args.from_year,
        years=args.years
    )
    if args.format == "json":
        print(json.dumps(chart, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(chart))

if __name__ == "__main__":
    main()
'''

script_path = WORKSPACE / "skills/bazi-analysis/scripts/bazi_chart.py"
script_path.write_text(bazi_chart_script, encoding="utf-8")

# ── Client intake to process ─────────────────────────────────────────────────
# The actual task subject: birth near an hour boundary, requires both sects
client_brief = {
    "client_id": "009",
    "name": "Chen Jing",
    "birth_date": "1993-08-23",
    "birth_time": "10:58",
    "gender": "female",
    "consultation_request": (
        "Full chart report with 10-year yearly outlook starting from 2026. "
        "Client requests comparison between both major calculation schools."
    ),
    "assigned_consultant": "Senior Analyst",
    "priority": "high",
}
(WORKSPACE / "clients/intake_forms/client_009_intake.json").write_text(
    json.dumps(client_brief, indent=2), encoding="utf-8"
)

# ── reports/pending placeholder ──────────────────────────────────────────────
(WORKSPACE / "reports/pending/.gitkeep").write_text("", encoding="utf-8")

print("Workspace generated successfully.")
print(f"Key files:")
print(f"  {WORKSPACE}/skills/bazi-analysis/scripts/bazi_chart.py")
print(f"  {WORKSPACE}/clients/intake_forms/client_009_intake.json")