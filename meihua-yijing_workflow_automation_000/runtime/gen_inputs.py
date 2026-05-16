import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# === Create the meihua.py script (the core tool referenced in SKILL.md) ===
meihua_script = r'''#!/usr/bin/env python3
"""
梅花易数起卦脚本
用法:
  python3 meihua.py time             # 时间起卦
  python3 meihua.py numbers n1 n2 n3 # 数字起卦
  python3 meihua.py direction dir h  # 方位起卦
"""

import sys
import datetime

# 先天八卦数序
BAGUA = {
    1: {"name": "乾", "symbol": "☰", "wuxing": "金", "nature": "天"},
    2: {"name": "兑", "symbol": "☱", "wuxing": "金", "nature": "泽"},
    3: {"name": "离", "symbol": "☲", "wuxing": "火", "nature": "火"},
    4: {"name": "震", "symbol": "☳", "wuxing": "木", "nature": "雷"},
    5: {"name": "巽", "symbol": "☴", "wuxing": "木", "nature": "风"},
    6: {"name": "坎", "symbol": "☵", "wuxing": "水", "nature": "水"},
    7: {"name": "艮", "symbol": "☶", "wuxing": "土", "nature": "山"},
    8: {"name": "坤", "symbol": "☷", "wuxing": "土", "nature": "地"},
}

HEXAGRAM_NAMES = {
    (1,1): "乾为天", (1,2): "天泽履", (1,3): "天火同人", (1,4): "天雷无妄",
    (1,5): "天风姤", (1,6): "天水讼", (1,7): "天山遯", (1,8): "天地否",
    (2,1): "泽天夬", (2,2): "兑为泽", (2,3): "泽火革", (2,4): "泽雷随",
    (2,5): "泽风大过", (2,6): "泽水困", (2,7): "泽山咸", (2,8): "泽地萃",
    (3,1): "火天大有", (3,2): "火泽睽", (3,3): "离为火", (3,4): "火雷噬嗑",
    (3,5): "火风鼎", (3,6): "火水未济", (3,7): "火山旅", (3,8): "火地晋",
    (4,1): "雷天大壮", (4,2): "雷泽归妹", (4,3): "雷火丰", (4,4): "震为雷",
    (4,5): "雷风恒", (4,6): "雷水解", (4,7): "雷山小过", (4,8): "雷地豫",
    (5,1): "风天小畜", (5,2): "风泽中孚", (5,3): "风火家人", (5,4): "风雷益",
    (5,5): "巽为风", (5,6): "风水涣", (5,7): "风山渐", (5,8): "风地观",
    (6,1): "水天需", (6,2): "水泽节", (6,3): "水火既济", (6,4): "水雷屯",
    (6,5): "水风井", (6,6): "坎为水", (6,7): "水山蹇", (6,8): "水地比",
    (7,1): "山天大畜", (7,2): "山泽损", (7,3): "山火贲", (7,4): "山雷颐",
    (7,5): "山风蛊", (7,6): "山水蒙", (7,7): "艮为山", (7,8): "山地剥",
    (8,1): "地天泰", (8,2): "地泽临", (8,3): "地火明夷", (8,4): "地雷复",
    (8,5): "地风升", (8,6): "地水师", (8,7): "地山谦", (8,8): "坤为地",
}

# 五行相生相克
WUXING_SHENG = {
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
}
WUXING_KE = {
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"
}

DIRECTION_MAP = {
    "东": 4, "南": 3, "西": 2, "北": 6,
    "东南": 5, "西南": 8, "西北": 1, "东北": 7,
}

def get_relation(ti_wuxing, yong_wuxing):
    if ti_wuxing == yong_wuxing:
        return "比和", "吉", "体用同属一行，比和则吉"
    if WUXING_SHENG.get(yong_wuxing) == ti_wuxing:
        return "用生体", "吉", "用卦生体卦，得助为吉"
    if WUXING_SHENG.get(ti_wuxing) == yong_wuxing:
        return "体生用", "平", "体卦生用卦，泄气为平"
    if WUXING_KE.get(yong_wuxing) == ti_wuxing:
        return "用克体", "凶", "用卦克体卦，受制为凶"
    if WUXING_KE.get(ti_wuxing) == yong_wuxing:
        return "体克用", "平", "体卦克用卦，制而为平"
    return "未知", "未知", "关系不明"

def get_hugua(shang, xia):
    """互卦：取本卦二三四爻为下互，三四五爻为上互"""
    # 简化实现：互卦上卦=本卦下卦数+1 mod 8+1, 下卦=本卦上卦数-1
    hu_shang = (xia % 8) + 1
    hu_xia = ((shang + 1) % 8) + 1
    return hu_shang, hu_xia

def format_output(method, info, shang_num, xia_num, dong_yao=None):
    shang = BAGUA[shang_num]
    xia = BAGUA[xia_num]
    bengua_name = HEXAGRAM_NAMES.get((shang_num, xia_num), f"{shang['name']}{xia['name']}卦")

    hu_shang_num, hu_xia_num = get_hugua(shang_num, xia_num)
    hu_shang = BAGUA[hu_shang_num]
    hu_xia = BAGUA[hu_xia_num]
    hugua_name = HEXAGRAM_NAMES.get((hu_shang_num, hu_xia_num), f"{hu_shang['name']}{hu_xia['name']}卦")

    # 变卦：若有动爻
    biangua_str = "无动爻，无变卦"
    if dong_yao is not None:
        yao_pos = dong_yao % 2
        if yao_pos == 0:
            bian_shang_num = (shang_num % 8) + 1
            bian_xia_num = xia_num
        else:
            bian_shang_num = shang_num
            bian_xia_num = (xia_num % 8) + 1
        bian_shang = BAGUA[bian_shang_num]
        bian_xia = BAGUA[bian_xia_num]
        biangua_name = HEXAGRAM_NAMES.get((bian_shang_num, bian_xia_num), f"{bian_shang['name']}{bian_xia['name']}卦")
        biangua_str = f"{bian_shang['symbol']} {bian_shang['name']}卦（上） + {bian_xia['symbol']} {bian_xia['name']}卦（下） = {biangua_name}"

    # 体用：上卦为用，下卦为体（梅花易数传统：内卦为体，外卦为用）
    ti_num = xia_num
    yong_num = shang_num
    ti = BAGUA[ti_num]
    yong = BAGUA[yong_num]

    relation, jixiong, detail = get_relation(ti["wuxing"], yong["wuxing"])

    if jixiong == "吉":
        advice = "事宜积极进取，顺势而为，当前形势有利，可大胆行动。"
    elif jixiong == "凶":
        advice = "事宜谨慎保守，暂缓行动，静待时机，避免冒进。"
    else:
        advice = "事宜平稳处置，不必过于担忧，也不可大意，随机应变。"

    output = f"""🎲 梅花易数占卜

【起卦方式】：{method}
【起卦信息】：{info}
【本卦】：{shang['symbol']} {shang['name']}卦（上） + {xia['symbol']} {xia['name']}卦（下） = {bengua_name}
【互卦】：{hu_shang['symbol']} {hu_shang['name']}卦（上） + {hu_xia['symbol']} {hu_xia['name']}卦（下） = {hugua_name}
【变卦】：{biangua_str}

【体用分析】
- 体卦：{xia['name']}卦（属{xia['name']}宫，五行{xia['wuxing']}）
- 用卦：{shang['name']}卦（属{shang['name']}宫，五行{shang['wuxing']}）
- 关系：{relation}（{detail}）

【吉凶判断】：{jixiong}

【建议】：{advice}
"""
    return output.strip()

def cast_time():
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    shang_num = ((year + month + day) % 8) + 1
    xia_num = ((year + month + day + hour) % 8) + 1
    dong_yao = (year + month + day + hour) % 6 + 1
    info = f"{year}年{month}月{day}日{hour}时"
    return format_output("时间起卦", info, shang_num, xia_num, dong_yao)

def cast_numbers(n1, n2, n3):
    shang_num = (n1 % 8) or 8
    xia_num = (n2 % 8) or 8
    dong_yao = (n3 % 6) or 6
    info = f"数字 {n1} {n2} {n3}"
    return format_output("数字起卦", info, shang_num, xia_num, dong_yao)

def cast_direction(direction, hour):
    dir_num = DIRECTION_MAP.get(direction, 1)
    shang_num = (dir_num % 8) or 8
    xia_num = ((dir_num + hour) % 8) or 8
    dong_yao = (hour % 6) or 6
    info = f"方位{direction}，时辰{hour}"
    return format_output("方位起卦", info, shang_num, xia_num, dong_yao)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 meihua.py [time|numbers|direction] [参数...]")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "time":
        print(cast_time())
    elif mode == "numbers":
        if len(sys.argv) < 5:
            print("数字起卦需要3个数字参数")
            sys.exit(1)
        n1, n2, n3 = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
        print(cast_numbers(n1, n2, n3))
    elif mode == "direction":
        if len(sys.argv) < 4:
            print("方位起卦需要方位和时辰参数")
            sys.exit(1)
        direction = sys.argv[2]
        hour = int(sys.argv[3])
        print(cast_direction(direction, hour))
    else:
        print(f"未知模式: {mode}")
        sys.exit(1)
'''

with open(workspace / "meihua.py", "w", encoding="utf-8") as f:
    f.write(meihua_script)

# === Create distractor directory structure ===

dirs = [
    "client_records/2024/Q1",
    "client_records/2024/Q2",
    "client_records/2024/Q3",
    "client_records/2024/Q4_pending",
    "client_records/archive",
    "templates/standard",
    "templates/premium",
    "tools/legacy",
    "tools/utils",
    "reports/monthly",
    "reports/annual",
    "config",
    "logs",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "client_records/2024/Q1/client_001.txt": "客户：张三\n咨询日期：2024-01-15\n问题：工作运势\n结果：待整理",
    "client_records/2024/Q1/client_002.txt": "客户：李四\n咨询日期：2024-01-22\n问题：婚姻\n结果：待整理",
    "client_records/2024/Q2/client_003.txt": "客户：王五\n咨询日期：2024-04-10\n问题：财运\n结果：待整理",
    "client_records/2024/Q3/client_004.txt": "客户：赵六\n咨询日期：2024-07-08\n问题：健康\n结果：待整理",
    "client_records/archive/old_format.txt": "旧格式记录：此文件格式已废弃",
    "templates/standard/report_template.txt": "标准报告模板\n[起卦信息]\n[卦象]\n[分析]\n[建议]",
    "templates/premium/premium_template.txt": "高级报告模板（VIP专用）\n详细分析版本",
    "tools/legacy/old_calculator.py": "# 旧版计算器 - 已废弃\n# 请使用新版 meihua.py",
    "tools/utils/date_converter.py": "# 日期转换工具\nimport datetime\n\ndef convert(y,m,d):\n    return datetime.date(y,m,d)",
    "reports/monthly/2024_06_summary.txt": "2024年6月报告\n共计咨询：45次\n满意度：92%",
    "reports/annual/2023_annual.txt": "2023年度报告\n总咨询：520次",
    "config/settings.json": json.dumps({"version": "2.1", "lang": "zh-CN", "output_dir": "reports"}, ensure_ascii=False, indent=2),
    "logs/app.log": "2024-10-01 09:00:00 INFO 系统启动\n2024-10-01 09:05:12 INFO 占卜请求处理完成\n",
    "tools/legacy/hexagram_table.txt": "旧版卦象表（已废弃，以meihua.py为准）\n乾=111111\n坤=000000",
}

for fpath, content in distractor_files.items():
    with open(workspace / fpath, "w", encoding="utf-8") as f:
        f.write(content)

# === Create the client request file ===
# This is the "messy input" the agent must process
client_request = """【客户咨询请求单】
编号：CR-20241115-007
客户姓名：陈美华
联系方式：138-XXXX-XXXX
咨询日期：2024年11月15日

【咨询内容】
客户希望就近期创业计划进行占卜咨询。
客户报出的起卦数字为：6、7、3

【特别备注】
客户要求使用"数字起卦"方式。
报告需存档备查，请将完整占卜报告保存为文件。

【经办人】：前台小王
"""

with open(workspace / "client_records/2024/Q4_pending/CR-20241115-007.txt", "w", encoding="utf-8") as f:
    f.write(client_request)

# === Create a SKILL.md reference for the agent ===
skill_md = """---
name: meihua-yijing
description: 梅花易数占卜，基于时间、数字、方位起卦，解读吉凶祸福
metadata:
  {
    "openclaw":
      {
        "emoji": "🔮",
        "requires": { "bins": ["python3"] }
      }
  }
---

你是"梅花易数"占卜专家。梅花易数是北宋邵雍所创的占卜术，以"先天八卦"数序为基础，通过"体用生克"判断吉凶。

# 核心概念

## 先天八卦数序
| 卦 | 乾 | 兑 | 离 | 震 | 巽 | 坎 | 艮 | 坤 |
|---|---|---|---|---|---|---|---|---|
| 数 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |

## 先天八卦方位
- 乾：西北 | 兑：西 | 离：南 | 震：东
- 巽：东南 | 坎：北 | 艮：东北 | 坤：西南

## 体用生克
- **体卦**：主卦、问事之人
- **用卦**：应卦、所占之事
- **生**：用生体吉，体生用泄
- **克**：用克体凶，体克用平
- **比和**：体用同属一体，吉

## 起卦方式

用户可以用以下方式起卦：

1. **时间起卦**：报出年月日时（阳历）
2. **数字起卦**：报出3个数字（1-9）
3. **方位出方位+时间起卦**：报

# 计算流程

调用脚本进行起卦和分析：
```bash
python3 "{baseDir}/meihua.py" time          # 时间起卦
python3 "{baseDir}/meihua.py" numbers 3 8 5  # 数字起卦
python3 "{baseDir}/meihua.py" direction 东 9  # 方位起卦
```

# 输出格式

```
🎲 梅花易数占卜

【起卦方式】：时间/数字/方位
【起卦信息】：xxx
【本卦】：☰ 乾卦（上） + ☵ 坎卦（下） = 水天需
【互卦】：xxx
【变卦】：xxx（若有）

【体用分析】
- 体卦：xxx（属xx宫，五行xx）
- 用卦：xxx（属xx宫，五行xx）
- 关系：xx（生/克/比和）

【吉凶判断】：xxx

【建议】：xxx
```

# 约束
- 必须调用脚本获取卦象
- 解释要清晰易懂，帮助用户理解
- 吉凶判断要客观，避免夸大
- 提醒：占卜仅供参考，不可尽信
"""

with open(workspace / "SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_md)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")