#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation script for lucky-day task.
Checks that the agent:
  1. Found and created lucky_report.txt anywhere in workspace
  2. Invoked the tool with the correct zodiac argument (马)
  3. Output contains the correct 【需求】 and 【属相】 headers
  4. Contains all three medal emojis (🥇🥈🥉)
  5. Contains the 冲煞 field with 不冲马 annotation (since 马 zodiac should be respected)
  6. Contains the 【建议】 section
  7. Contains the exact footer ※ 黄历仅供参考 ※
  8. Contains 干支 field for at least one date
  9. Contains 吉神 field for at least one date
  10. The recommended dates are NOT ones that conflict with 马 (冲马 dates excluded)
"""

import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta
import hashlib

def get_ganzhi(offset_from_epoch):
    TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    DIZHI   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    tg_idx = offset_from_epoch % 10
    dz_idx = offset_from_epoch % 12
    return TIANGAN[tg_idx] + DIZHI[dz_idx]

def pseudo_random(seed_str, n):
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return h % n

LIUCHONG = {
    "子":"午","午":"子","丑":"未","未":"丑",
    "寅":"申","申":"寅","卯":"酉","酉":"卯",
    "辰":"戌","戌":"辰","巳":"亥","亥":"巳"
}
DIZHI_TO_SHUXIANG = {
    "子":"鼠","丑":"牛","寅":"虎","卯":"兔","辰":"龙","巳":"蛇",
    "午":"马","未":"羊","申":"猴","酉":"鸡","戌":"狗","亥":"猪"
}

def chong_shuxiang_for_date(d):
    epoch = date(2024, 1, 1)
    offset = (d - epoch).days
    gz = get_ganzhi(offset)
    dizhi_day = gz[1]
    chong_dz = LIUCHONG.get(dizhi_day, "子")
    return DIZHI_TO_SHUXIANG.get(chong_dz, "鼠")

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ── Check 1: File exists ─────────────────────────────────────────────────
    report_files = list(workspace.rglob("lucky_report.txt"))
    file_found = len(report_files) > 0
    checks.append({
        "name": "lucky_report.txt exists",
        "passed": file_found,
        "detail": f"Found {len(report_files)} file(s)" if file_found else "lucky_report.txt not found anywhere in workspace"
    })
    
    if not file_found:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    # ── Check 2: Header emoji ────────────────────────────────────────────────
    has_header = "🗓️ 择吉选日" in content
    checks.append({
        "name": "Report header 🗓️ 择吉选日",
        "passed": has_header,
        "detail": "Found header" if has_header else "Missing '🗓️ 择吉选日' header"
    })

    # ── Check 3: 【需求】 field shows 嫁娶 ───────────────────────────────────
    has_xiqiu = bool(re.search(r"【需求】.*嫁娶", content))
    checks.append({
        "name": "【需求】：嫁娶",
        "passed": has_xiqiu,
        "detail": "Found" if has_xiqiu else "Missing '【需求】：嫁娶'"
    })

    # ── Check 4: 【属相】 field shows 马 ────────────────────────────────────
    has_zodiac = bool(re.search(r"【您的属相】.*马", content))
    checks.append({
        "name": "【您的属相】：马",
        "passed": has_zodiac,
        "detail": "Found" if has_zodiac else "Missing '【您的属相】：马' — agent may have omitted zodiac argument"
    })

    # ── Check 5: Three medal emojis ──────────────────────────────────────────
    has_gold   = "🥇" in content
    has_silver = "🥈" in content
    has_bronze = "🥉" in content
    all_medals = has_gold and has_silver and has_bronze
    checks.append({
        "name": "Three medal rankings 🥇🥈🥉",
        "passed": all_medals,
        "detail": f"🥇:{has_gold} 🥈:{has_silver} 🥉:{has_bronze}"
    })

    # ── Check 6: 干支 field present ──────────────────────────────────────────
    has_ganzhi = bool(re.search(r"干支[：:]", content))
    checks.append({
        "name": "干支 field present",
        "passed": has_ganzhi,
        "detail": "Found '干支：' field" if has_ganzhi else "Missing 干支 field"
    })

    # ── Check 7: 冲煞 field with 不冲马 annotation ───────────────────────────
    has_buchong_ma = "不冲马" in content
    checks.append({
        "name": "冲煞 field shows 不冲马",
        "passed": has_buchong_ma,
        "detail": "Found '不冲马' annotation" if has_buchong_ma else "Missing '不冲马' — zodiac collision check not applied"
    })

    # ── Check 8: 吉神 field present ──────────────────────────────────────────
    has_jishen = bool(re.search(r"吉神[：:]", content))
    checks.append({
        "name": "吉神 field present",
        "passed": has_jishen,
        "detail": "Found" if has_jishen else "Missing 吉神 field"
    })

    # ── Check 9: 【建议】 section ────────────────────────────────────────────
    has_suggest = "【建议】" in content
    has_shouxuan = "首选" in content
    checks.append({
        "name": "【建议】 section with 首选",
        "passed": has_suggest and has_shouxuan,
        "detail": f"【建议】:{has_suggest}, 首选:{has_shouxuan}"
    })

    # ── Check 10: Exact footer ───────────────────────────────────────────────
    has_footer = "※ 黄历仅供参考 ※" in content
    checks.append({
        "name": "Footer ※ 黄历仅供参考 ※",
        "passed": has_footer,
        "detail": "Found" if has_footer else "Missing exact footer '※ 黄历仅供参考 ※'"
    })

    # ── Check 11: No 冲马 dates in recommendations ───────────────────────────
    # Extract dates mentioned in report and verify none clash with 马
    date_pattern = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
    found_dates = date_pattern.findall(content)
    clashing = []
    for (y, m, d) in found_dates:
        try:
            dt = date(int(y), int(m), int(d))
            if chong_shuxiang_for_date(dt) == "马":
                clashing.append(f"{y}-{m}-{d}")
        except Exception:
            pass
    no_clashing = len(clashing) == 0
    checks.append({
        "name": "No 冲马 dates recommended",
        "passed": no_clashing,
        "detail": f"No clashing dates found" if no_clashing else f"Dates clashing with 马 zodiac found: {clashing}"
    })

    # ── Check 12: 宜 field present ───────────────────────────────────────────
    has_yi = bool(re.search(r"\s+宜[：:]", content))
    checks.append({
        "name": "宜 field present in day entries",
        "passed": has_yi,
        "detail": "Found" if has_yi else "Missing 宜 field"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Must pass critical checks to overall pass
    critical = [
        "lucky_report.txt exists",
        "【需求】：嫁娶",
        "【您的属相】：马",
        "Three medal rankings 🥇🥈🥉",
        "冲煞 field shows 不冲马",
        "Footer ※ 黄历仅供参考 ※",
        "No 冲马 dates recommended",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical
    )

    result = {
        "passed": critical_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()