import os
import json
import random
from pathlib import Path

random.seed(42)

# Root workspace
workspace = Path("/workspace")

# ── Skill directory structure ──────────────────────────────────────────────
skill_root = workspace / "skills" / "china-holidays"
assets_dir = skill_root / "assets"
scripts_dir = skill_root / "scripts"
assets_dir.mkdir(parents=True, exist_ok=True)
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── The real fetch script (simulated as a wrapper that reads local assets or
#    fetches from gov.cn).  We create a MOCK version that:
#    - Returns canned good data for 2026 from cache (assets/2026.md exists)
#    - Returns STALE/WRONG data from cache for 2025 (assets/2025.md exists but
#      contains fabricated wrong content)
#    - When --force is supplied, returns the CORRECT authoritative data for
#      both years regardless of cache.
# ──────────────────────────────────────────────────────────────────────────

# Correct 2025 holiday notice text (authoritative)
CORRECT_2025 = """国务院办公厅关于2025年部分节假日安排的通知

各省、自治区、直辖市人民政府，国务院各部委、各直属机构：

经国务院批准，现将2025年元旦、春节、清明节、劳动节、端午节、中秋节和国庆节放假调休日期的具体安排通知如下。

一、元旦：1月1日（周三）放假，共1天。

二、春节：1月28日（农历除夕、周二）至2月4日（农历正月初七、周二）放假调休，共8天。1月26日（周日）、2月8日（周六）上班。

三、清明节：4月4日（周五）至6日（周日）放假，共3天。

四、劳动节：5月1日（周四）至5日（周一）放假调休，共5天。4月27日（周日）上班。

五、端午节：5月31日（周六）至6月2日（周一）放假，共3天。

六、中秋节：10月6日（周一）放假，调休1天，共1天。

七、国庆节：10月1日（周三）至7日（周二）放假调休，共7天。9月28日（周日）、10月11日（周六）上班。
"""

# STALE/WRONG 2025 cache — intentionally wrong spring festival data
STALE_2025 = """国务院办公厅关于2025年部分节假日安排的通知（草案，未经核实）

注意：此文件为早期草案，数据可能有误。

一、元旦：1月1日放假，共1天。

二、春节：1月29日（农历正月初一、周三）至2月3日（农历正月初六、周一）放假，共6天。（错误草案数据）

三、清明节：4月5日放假，共1天。

四、劳动节：5月1日至3日放假，共3天。

五、端午节：6月1日放假，共1天。

六、中秋节：10月6日放假，共1天。

七、国庆节：10月1日至6日放假，共6天。
"""

# Correct 2026 holiday notice text (authoritative)
CORRECT_2026 = """国务院办公厅关于2026年部分节假日安排的通知

各省、自治区、直辖市人民政府，国务院各部委、各直属机构：

经国务院批准，现将2026年元旦、春节、清明节、劳动节、端午节、中秋节和国庆节放假调休日期的具体安排通知如下。

一、元旦：1月1日（周四）至3日（周六）放假调休，共3天。1月4日（周日）上班。

二、春节：2月15日（农历腊月二十八、周日）至23日（农历正月初七、周一）放假调休，共9天。2月14日（周六）、2月28日（周六）上班。

三、清明节：4月4日（周六）至6日（周一）放假，共3天。

四、劳动节：5月1日（周五）至5日（周二）放假调休，共5天。5月9日（周六）上班。

五、端午节：6月19日（周五）至21日（周日）放假，共3天。

六、中秋节：9月25日（周五）至27日（周日）放假，共3天。

七、国庆节：10月1日（周四）至7日（周三）放假调休，共7天。9月20日（周六）、10月10日（周六）上班。
"""

# ── Write the STALE cache for 2025 (this is the trap: agent must --force for 2025)
(assets_dir / "2025.md").write_text(STALE_2025, encoding="utf-8")

# ── Write the correct cache for 2026 (agent should NOT force-refresh this)
(assets_dir / "2026.md").write_text(CORRECT_2026, encoding="utf-8")

# ── Write the mock fetch_holidays.py script ────────────────────────────────
mock_script = r'''#!/usr/bin/env python3
"""
Mock fetch_holidays.py — simulates cache-first strategy with --force support.
"""
import argparse
import sys
from pathlib import Path

# Authoritative data (what you get from the network)
NETWORK_DATA = {
    2025: """国务院办公厅关于2025年部分节假日安排的通知

各省、自治区、直辖市人民政府，国务院各部委、各直属机构：

经国务院批准，现将2025年元旦、春节、清明节、劳动节、端午节、中秋节和国庆节放假调休日期的具体安排通知如下。

一、元旦：1月1日（周三）放假，共1天。

二、春节：1月28日（农历除夕、周二）至2月4日（农历正月初七、周二）放假调休，共8天。1月26日（周日）、2月8日（周六）上班。

三、清明节：4月4日（周五）至6日（周日）放假，共3天。

四、劳动节：5月1日（周四）至5日（周一）放假调休，共5天。4月27日（周日）上班。

五、端午节：5月31日（周六）至6月2日（周一）放假，共3天。

六、中秋节：10月6日（周一）放假，调休1天，共1天。

七、国庆节：10月1日（周三）至7日（周二）放假调休，共7天。9月28日（周日）、10月11日（周六）上班。
""",
    2026: """国务院办公厅关于2026年部分节假日安排的通知

各省、自治区、直辖市人民政府，国务院各部委、各直属机构：

经国务院批准，现将2026年元旦、春节、清明节、劳动节、端午节、中秋节和国庆节放假调休日期的具体安排通知如下。

一、元旦：1月1日（周四）至3日（周六）放假调休，共3天。1月4日（周日）上班。

二、春节：2月15日（农历腊月二十八、周日）至23日（农历正月初七、周一）放假调休，共9天。2月14日（周六）、2月28日（周六）上班。

三、清明节：4月4日（周六）至6日（周一）放假，共3天。

四、劳动节：5月1日（周五）至5日（周二）放假调休，共5天。5月9日（周六）上班。

五、端午节：6月19日（周五）至21日（周日）放假，共3天。

六、中秋节：9月25日（周五）至27日（周日）放假，共3天。

七、国庆节：10月1日（周四）至7日（周三）放假调休，共7天。9月20日（周六）、10月10日（周六）上班。
""",
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--force", action="store_true", default=False)
    args = parser.parse_args()

    # Resolve assets directory relative to this script
    script_dir = Path(__file__).parent
    assets_dir = script_dir.parent / "assets"
    cache_file = assets_dir / f"{args.year}.md"

    if args.force:
        print(f"正在从网络获取 {args.year} 年节假日数据...")
        if args.year not in NETWORK_DATA:
            print(f"未找到相关节假日通知：{args.year} 年数据暂未发布")
            sys.exit(1)
        content = NETWORK_DATA[args.year]
        assets_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(content, encoding="utf-8")
        print(f"已缓存到：skills/china-holidays/assets/{args.year}.md")
        print(content)
    else:
        if cache_file.exists():
            content = cache_file.read_text(encoding="utf-8")
            print(content)
        else:
            print(f"正在从网络获取 {args.year} 年节假日数据...")
            if args.year not in NETWORK_DATA:
                print(f"未找到相关节假日通知：{args.year} 年数据暂未发布")
                sys.exit(1)
            content = NETWORK_DATA[args.year]
            assets_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(content, encoding="utf-8")
            print(f"已缓存到：skills/china-holidays/assets/{args.year}.md")
            print(content)

if __name__ == "__main__":
    main()
'''

(scripts_dir / "fetch_holidays.py").write_text(mock_script, encoding="utf-8")

# ── Distractor files to simulate a realistic workspace ─────────────────────
distractor_dirs = [
    workspace / "skills" / "weather-query" / "scripts",
    workspace / "skills" / "weather-query" / "assets",
    workspace / "skills" / "stock-price" / "scripts",
    workspace / "skills" / "currency-converter" / "assets",
    workspace / "skills" / "china-holidays" / "tests",
    workspace / "config",
    workspace / "logs",
    workspace / "docs" / "internal",
    workspace / "tmp" / "scratch",
    workspace / "skills" / "china-holidays" / "archive",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "skills" / "weather-query" / "scripts" / "fetch_weather.py":
        "# placeholder weather script\nprint('weather data')\n",
    workspace / "skills" / "weather-query" / "assets" / "2025.json":
        '{"city": "Beijing", "temp": 12}\n',
    workspace / "skills" / "stock-price" / "scripts" / "fetch_stock.py":
        "# stock fetch script\n",
    workspace / "skills" / "currency-converter" / "assets" / "rates.json":
        '{"USD": 7.23, "EUR": 7.89}\n',
    workspace / "skills" / "china-holidays" / "tests" / "test_fetch.py":
        "# unit tests placeholder\nimport unittest\n",
    workspace / "skills" / "china-holidays" / "archive" / "2024.md":
        "# 2024年节假日安排（已归档）\n春节：2月10日至17日，共8天\n",
    workspace / "config" / "agent_config.yaml":
        "model: gpt-4\ntemperature: 0.7\nmax_tokens: 2000\n",
    workspace / "config" / "skills_registry.json":
        '{"skills": ["china-holidays", "weather-query", "stock-price"]}\n',
    workspace / "logs" / "agent_run_20250101.log":
        "[INFO] Agent started\n[INFO] Skill loaded: china-holidays\n[WARN] Cache miss for 2025\n",
    workspace / "logs" / "agent_run_20250615.log":
        "[INFO] Query: 2025年春节\n[INFO] Cache hit: assets/2025.md\n[INFO] Returned stale data\n",
    workspace / "docs" / "internal" / "holiday_policy.txt":
        "公司假期政策：员工需按国家法定节假日安排休假。\n请参考最新官方通知。\n",
    workspace / "tmp" / "scratch" / "notes.txt":
        "TODO: 更新2025年春节数据\n可能存在草案缓存问题\n",
}

for path, content in distractor_files.items():
    path.write_text(content, encoding="utf-8")

# ── Write a skill.md stub (not the real one, just a distractor reference) ──
(skill_root / "SKILL.md").write_text(
    "# china-holidays skill\nSee scripts/fetch_holidays.py for usage.\n",
    encoding="utf-8"
)

print("Workspace initialized.")
print(f"  Stale 2025 cache written to: {assets_dir / '2025.md'}")
print(f"  Correct 2026 cache written to: {assets_dir / '2026.md'}")
print(f"  Mock script written to: {scripts_dir / 'fetch_holidays.py'}")