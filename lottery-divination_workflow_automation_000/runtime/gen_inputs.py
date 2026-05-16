import os
import json
import stat
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "app/routes",
    "app/templates",
    "app/static/css",
    "app/static/js",
    "app/models",
    "config",
    "tests",
    "docs",
    "output",
    "logs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "app/routes/lottery.py": """\
# Route handlers for lottery recommendation API
from flask import Blueprint, jsonify
bp = Blueprint('lottery', __name__)

@bp.route('/recommend/<ltype>')
def recommend(ltype):
    # TODO: integrate divination engine
    return jsonify({"status": "not_implemented"})
""",
    "app/routes/user.py": """\
from flask import Blueprint
bp = Blueprint('user', __name__)
""",
    "app/models/prediction.py": """\
class Prediction:
    def __init__(self, lottery_type, numbers, hexagram):
        self.lottery_type = lottery_type
        self.numbers = numbers
        self.hexagram = hexagram
""",
    "app/templates/result.html": """\
<!DOCTYPE html>
<html><body>
<h1>{{ title }}</h1>
<p>{{ numbers }}</p>
</body></html>
""",
    "app/static/css/style.css": "body { font-family: sans-serif; }",
    "app/static/js/app.js": "console.log('lottery app loaded');",
    "config/settings.py": """\
DEBUG = True
LOTTERY_TYPES = ['ssq', 'dlt']
DEFAULT_TYPE = 'ssq'
TIMEZONE = 'Asia/Shanghai'
""",
    "config/logging.conf": """\
[loggers]
keys=root

[handlers]
keys=consoleHandler

[formatters]
keys=simpleFormatter
""",
    "tests/test_divination.py": """\
# Unit tests for divination module
import subprocess, json

def test_ssq_output_keys():
    result = subprocess.run(
        ['python3', 'scripts/divination.py', 'ssq', '2025-06-15-14'],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    assert 'divination' in data
    assert 'lottery' in data

def test_dlt_output_keys():
    result = subprocess.run(
        ['python3', 'scripts/divination.py', 'dlt', '2025-06-15-14'],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    assert 'lottery' in data
""",
    "tests/test_routes.py": """\
# Placeholder route tests
def test_placeholder():
    assert True
""",
    "docs/api_spec.md": """\
# Lottery Divination API

## Endpoints

### GET /recommend/:type
Returns a lottery recommendation based on current time.

Parameters:
- type: 'ssq' or 'dlt'

Response: JSON with hexagram and lottery data
""",
    "logs/app.log": """\
2025-06-15 10:00:01 INFO  App started
2025-06-15 10:00:02 INFO  Routes registered
2025-06-15 14:22:10 WARN  divination.py not found, skipping
""",
    "output/.gitkeep": "",
}

for rel_path, content in distractors.items():
    p = WORKSPACE / rel_path
    p.write_text(content, encoding="utf-8")

# ── THE KEY ARTIFACT: divination.py ─────────────────────────────────────────
# This script already "exists in the workspace" per skill.md.
# We create it here as the real implementation.

DIVINATION_SCRIPT = r'''#!/usr/bin/env python3
"""
梅花易数起卦脚本 - 时间起卦法
Usage: python3 divination.py <type> <YYYY-MM-DD-HH>
  type: ssq | dlt
  YYYY-MM-DD-HH: e.g. 2026-03-22-15
"""
import sys
import json
import hashlib

# 64 hexagrams lookup table (index 0-63)
HEXAGRAMS = [
    ("坤为地",  "☷☷", "土", "土"),
    ("地雷复",  "☷☳", "土", "木"),
    ("地泽临",  "☷☱", "土", "金"),
    ("地天泰",  "☷☰", "土", "金"),
    ("地火明夷","☷☲", "土", "火"),
    ("地风升",  "☷☴", "土", "木"),
    ("地水师",  "☷☵", "土", "水"),
    ("地山谦",  "☷☶", "土", "土"),
    ("雷地豫",  "☳☷", "木", "土"),
    ("震为雷",  "☳☳", "木", "木"),
    ("雷泽归妹","☳☱", "木", "金"),
    ("雷天大壮","☳☰", "木", "金"),
    ("雷火丰",  "☳☲", "木", "火"),
    ("雷风恒",  "☳☴", "木", "木"),
    ("雷水解",  "☳☵", "木", "水"),
    ("雷山小过","☳☶", "木", "土"),
    ("泽地萃",  "☱☷", "金", "土"),
    ("泽雷随",  "☱☳", "金", "木"),
    ("兑为泽",  "☱☱", "金", "金"),
    ("泽天夬",  "☱☰", "金", "金"),
    ("泽火革",  "☱☲", "金", "火"),
    ("泽风大过","☱☴", "金", "木"),
    ("泽水困",  "☱☵", "金", "水"),
    ("泽山咸",  "☱☶", "金", "土"),
    ("乾为天",  "☰☰", "金", "金"),
    ("天地否",  "☰☷", "金", "土"),
    ("天雷无妄","☰☳", "金", "木"),
    ("天泽履",  "☰☱", "金", "金"),
    ("天火同人","☰☲", "金", "火"),
    ("天风姤",  "☰☴", "金", "木"),
    ("天水讼",  "☰☵", "金", "水"),
    ("天山遁",  "☰☶", "金", "土"),
    ("火地晋",  "☲☷", "火", "土"),
    ("火雷噬嗑","☲☳", "火", "木"),
    ("火泽睽",  "☲☱", "火", "金"),
    ("火天大有","☲☰", "火", "金"),
    ("离为火",  "☲☲", "火", "火"),
    ("火风鼎",  "☲☴", "火", "木"),
    ("火水未济","☲☵", "火", "水"),
    ("火山旅",  "☲☶", "火", "土"),
    ("风地观",  "☴☷", "木", "土"),
    ("风雷益",  "☴☳", "木", "木"),
    ("风泽中孚","☴☱", "木", "金"),
    ("风天小畜","☴☰", "木", "金"),
    ("风火家人","☴☲", "木", "火"),
    ("巽为风",  "☴☴", "木", "木"),
    ("风水涣",  "☴☵", "木", "水"),
    ("风山渐",  "☴☶", "木", "土"),
    ("水地比",  "☵☷", "水", "土"),
    ("水雷屯",  "☵☳", "水", "木"),
    ("水泽节",  "☵☱", "水", "金"),
    ("水天需",  "☵☰", "水", "金"),
    ("水火既济","☵☲", "水", "火"),
    ("水风井",  "☵☴", "水", "木"),
    ("坎为水",  "☵☵", "水", "水"),
    ("水山蹇",  "☵☶", "水", "土"),
    ("山地剥",  "☶☷", "土", "土"),
    ("山雷颐",  "☶☳", "土", "木"),
    ("山泽损",  "☶☱", "土", "金"),
    ("山天大畜","☶☰", "土", "金"),
    ("山火贲",  "☶☲", "土", "火"),
    ("山风蛊",  "☶☴", "土", "木"),
    ("山水蒙",  "☶☵", "土", "水"),
    ("艮为山",  "☶☶", "土", "土"),
]

STEMS_CN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES_CN = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
HOUR_NAMES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
HOUR_MAP = {0:0,1:0,2:1,3:1,4:2,5:2,6:3,7:3,8:4,9:4,10:5,11:5,
            12:6,13:6,14:7,15:7,16:8,17:8,18:9,19:9,20:10,21:10,22:11,23:11}

def parse_args():
    if len(sys.argv) != 3:
        print("Usage: divination.py <ssq|dlt> <YYYY-MM-DD-HH>", file=sys.stderr)
        sys.exit(1)
    ltype = sys.argv[1].lower()
    if ltype not in ("ssq", "dlt"):
        print("type must be ssq or dlt", file=sys.stderr)
        sys.exit(1)
    ts = sys.argv[2]
    parts = ts.split("-")
    if len(parts) != 4:
        print("timestamp must be YYYY-MM-DD-HH", file=sys.stderr)
        sys.exit(1)
    year, month, day, hour = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    return ltype, year, month, day, hour

def year_num(year):
    # 天干地支年数：(year - 4) % 10 +1 for stem; use branch for num
    branch_idx = (year - 4) % 12
    return branch_idx + 1  # 1-12

def time_num(hour):
    return HOUR_MAP[hour] + 1  # 1-12

def get_stem_branch(year, month, day, hour):
    # Simplified: year stem/branch
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    hour_branch = HOUR_MAP[hour]
    return (STEMS_CN[stem_idx] + BRANCHES_CN[branch_idx] + "年",
            BRANCHES_CN[hour_branch] + "时")

def derive_hexagrams(year, month, day, hour):
    yn = year_num(year)
    mn = month
    dn = day
    hn = time_num(hour)

    upper_num = (yn + mn + dn) % 8
    if upper_num == 0:
        upper_num = 8
    lower_num = (yn + mn + dn + hn) % 8
    if lower_num == 0:
        lower_num = 8
    moving_yao = (yn + mn + dn + hn) % 6
    if moving_yao == 0:
        moving_yao = 6

    # Encode upper/lower trigram (1-8) as hexagram index
    # upper_num and lower_num map to trigrams 1=坤2=震3=坎4=艮5=坤...
    # Use a simple encoding: (upper-1)*8 + (lower-1)
    hex_idx = ((upper_num - 1) * 8 + (lower_num - 1)) % 64
    
    # 互卦: take lines 2-4 as lower, 3-5 as upper
    # simplified: rotate hex_idx deterministically
    mutual_idx = (hex_idx + 13) % 64
    
    # 变卦: flip the moving yao
    changed_idx = (hex_idx + moving_yao * 7) % 64

    return {
        "year_num": yn,
        "month_num": mn,
        "day_num": dn,
        "hour_num": hn,
        "main": hex_idx,
        "mutual": mutual_idx,
        "changed": changed_idx,
        "moving_yao": moving_yao,
    }

def seed_from_hexagrams(h, ltype):
    key = f"{ltype}-{h['main']}-{h['mutual']}-{h['changed']}-{h['moving_yao']}"
    return int(hashlib.sha256(key.encode()).hexdigest(), 16)

def lcg(seed, n, lo, hi):
    """Simple LCG to pick n unique numbers in [lo, hi]."""
    pool = list(range(lo, hi + 1))
    result = []
    s = seed
    while len(result) < n:
        s = (s * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        idx = s % len(pool)
        result.append(pool.pop(idx))
    return sorted(result)

def generate_lottery(h, ltype):
    seed = seed_from_hexagrams(h, ltype)
    if ltype == "ssq":
        reds = lcg(seed, 6, 1, 33)
        blue = lcg(seed ^ 0xDEADBEEF, 1, 1, 16)
        fmt = "红球: " + " ".join(f"{n:02d}" for n in reds) + "  |  蓝球: " + f"{blue[0]:02d}"
        return {"type": "双色球", "red": reds, "blue": blue[0], "format": fmt}
    else:
        front = lcg(seed, 5, 1, 35)
        back = lcg(seed ^ 0xCAFEBABE, 2, 1, 12)
        fmt = "前区: " + " ".join(f"{n:02d}" for n in front) + "  |  后区: " + " ".join(f"{n:02d}" for n in back)
        return {"type": "大乐透", "front": front, "back": back, "format": fmt}

def main():
    ltype, year, month, day, hour = parse_args()
    h = derive_hexagrams(year, month, day, hour)
    stem_year, hour_name = get_stem_branch(year, month, day, hour)
    
    main_hex = HEXAGRAMS[h["main"]]
    mutual_hex = HEXAGRAMS[h["mutual"]]
    changed_hex = HEXAGRAMS[h["changed"]]
    lottery = generate_lottery(h, ltype)

    YAO_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    moving_name = YAO_NAMES[h["moving_yao"] - 1]

    result = {
        "divination": {
            "time": f"{year:04d}-{month:02d}-{day:02d}-{hour:02d}",
            "stem_branch": f"{stem_year}·{hour_name}",
            "year_num": h["year_num"],
            "month_num": h["month_num"],
            "day_num": h["day_num"],
            "hour_num": h["hour_num"],
            "main_hexagram": {
                "name": main_hex[0],
                "symbol": main_hex[1],
                "upper_element": main_hex[2],
                "lower_element": main_hex[3],
            },
            "mutual_hexagram": {
                "name": mutual_hex[0],
                "symbol": mutual_hex[1],
            },
            "changed_hexagram": {
                "name": changed_hex[0],
                "symbol": changed_hex[1],
                "moving_yao": moving_name,
            },
        },
        "lottery": lottery,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

script_path = WORKSPACE / "scripts" / "divination.py"
script_path.write_text(DIVINATION_SCRIPT, encoding="utf-8")
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── task specification file ──────────────────────────────────────────────────
# The task file contains the business request (timestamp + lottery type)
# This is what the agent will read to know WHAT to generate
task_spec = {
    "request_id": "QA-2026-001",
    "client": "FortuneLottery Inc.",
    "description": "Generate a sample prediction report for QA validation",
    "lottery_type": "dlt",
    "target_datetime": "2026-07-18-20",
    "output_filename": "prediction_report.txt",
    "purpose": "We need a formatted prediction report for the given date/time to validate our rendering pipeline."
}
(WORKSPACE / "config" / "qa_task.json").write_text(
    json.dumps(task_spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── a misleading/partial sample that shows wrong format ──────────────────────
bad_sample = """\
=== SAMPLE REPORT (OUTDATED FORMAT - DO NOT USE) ===

Date: 2025-01-01 12:00
Numbers: 3 8 15 22 27 + 9

This is an old format. The new format requires hexagram display.
"""
(WORKSPACE / "docs" / "sample_report_OUTDATED.txt").write_text(bad_sample, encoding="utf-8")

# ── another distractor: a half-baked formatter script ───────────────────────
(WORKSPACE / "app" / "formatter.py").write_text("""\
# Abandoned formatter - do not use
def format_numbers(numbers):
    return ' '.join(str(n) for n in numbers)

def format_report(data):
    # TODO: incomplete implementation
    raise NotImplementedError("Use divination.py output directly")
""", encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Task spec: {WORKSPACE}/config/qa_task.json")
print(f"Divination script: {WORKSPACE}/scripts/divination.py")