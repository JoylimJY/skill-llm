#!/usr/bin/env python3
"""
Evaluation script for market-sentiment-radar task.
Usage: python3 eval.py /workspace
"""
import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Search for market_health_report.md anywhere under workspace."""
    candidates = list(workspace.rglob("market_health_report.md"))
    if candidates:
        return candidates[0]
    return None

def evaluate(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_weight = 0.0
    weighted_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_weight, weighted_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        total_weight += weight
        if passed:
            weighted_score += weight

    # ── 1. File existence ───────────────────────────────────────────────────
    report_path = find_report(workspace)
    file_exists = report_path is not None
    add_check(
        "report_file_exists",
        file_exists,
        f"Found at {report_path}" if file_exists else "market_health_report.md not found anywhere in workspace",
        weight=2.0
    )

    if not file_exists:
        score = 0.0
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("report_readable", False, f"Cannot read file: {e}", weight=2.0)
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False, indent=2))
        return

    add_check("report_readable", True, f"File readable, {len(content)} chars", weight=1.0)

    # ── 2. All four sections present with emoji markers ─────────────────────
    section_patterns = [
        ("section_thermometer", r"🌡️|大盘温湿度|情绪周期", "Section 1: 大盘温湿度与情绪周期 (🌡️)"),
        ("section_sector_flow", r"🌊|板块轮动|资金暗流", "Section 2: 资金暗流与板块轮动 (🌊)"),
        ("section_cross_market", r"🌍|跨市场联动|宏观映射", "Section 3: 跨市场联动与宏观映射 (🌍)"),
        ("section_strategy", r"⚔️|战术指导|仓位建议|Actionable", "Section 4: 战术指导与仓位建议 (⚔️)"),
    ]
    for check_name, pattern, desc in section_patterns:
        found = bool(re.search(pattern, content))
        add_check(check_name, found, f"{desc} {'found' if found else 'MISSING'}", weight=1.5)

    # ── 3. Correct emotion cycle classification ─────────────────────────────
    # Data: volume=7500亿(<8000亿 萎缩), 涨跌比480:3210(<1:3), 连板高度2板(<3板), 
    # 跌停87家(>50 风险级), 溢价-2.3%(<0% 差)
    # → Should be 退潮期 OR 混沌期 (both valid given the data pattern)
    correct_cycles = ["退潮期", "混沌期", "退潮", "混沌"]
    # Must NOT say 主升 or 冰点 (not extreme enough for 冰点, clearly not 主升)
    wrong_cycles_positive = ["主升", "高潮期", "高潮"]
    
    has_correct_cycle = any(c in content for c in correct_cycles)
    has_wrong_positive = any(c in content for c in wrong_cycles_positive)
    
    # Also accept 冰点期 as marginally valid (87 limit-downs is <100 threshold)
    # but prefer 退潮/混沌
    cycle_detail = f"Searched for {correct_cycles}. Found correct: {has_correct_cycle}. Found wrong positive: {has_wrong_positive}"
    add_check(
        "correct_emotion_cycle",
        has_correct_cycle and not has_wrong_positive,
        cycle_detail,
        weight=3.0
    )

    # ── 4. Volume data mentioned ────────────────────────────────────────────
    # Script outputs 7500亿, report should mention it (possibly as 0.75万亿 or 7500亿)
    volume_pattern = r"7[,，]?500|7500|0\.75\s*万亿|7\.5\s*千亿"
    has_volume = bool(re.search(volume_pattern, content))
    # Also accept approximate range mentions
    volume_context = r"缩量|萎缩|8000\s*亿|不足.*万亿|低于.*8000"
    has_volume_context = bool(re.search(volume_context, content))
    add_check(
        "volume_data_mentioned",
        has_volume or has_volume_context,
        f"Volume (7500亿/萎缩) {'found' if (has_volume or has_volume_context) else 'MISSING'}",
        weight=2.0
    )

    # ── 5. Advance/decline ratio mentioned ─────────────────────────────────
    ad_pattern = r"480|3210|亏钱效应|涨跌.*[Rr]atio|跌.*家.*涨.*家|赚钱效应.*差|跌多涨少"
    has_ad = bool(re.search(ad_pattern, content))
    add_check(
        "advance_decline_ratio",
        has_ad,
        f"Advance/decline ratio or market breadth {'found' if has_ad else 'MISSING'}",
        weight=1.5
    )

    # ── 6. Conservative position recommendation ─────────────────────────────
    # Given mixed/retreating market: should recommend 空仓, 轻仓, or ≤20%
    conservative_position = r"空仓|轻仓|20%?\s*以?下|20%?\s*试错|极轻|不建议.*仓|观望|0%"
    has_conservative = bool(re.search(conservative_position, content))
    # Must NOT recommend heavy position in such bad market
    heavy_position = r"80%?\s*重仓|重拳出击|满仓|70%?\s*|60%?"
    has_heavy = bool(re.search(heavy_position, content))
    add_check(
        "conservative_position_recommended",
        has_conservative and not has_heavy,
        f"Conservative position: {has_conservative}, Heavy position (bad): {has_heavy}",
        weight=3.0
    )

    # ── 7. Sector rotation "电风扇" pattern mentioned ───────────────────────
    sector_pattern = r"电风扇|快速轮动|无主线|没有主线|板块.*轮动|轮动.*频繁"
    has_sector = bool(re.search(sector_pattern, content))
    add_check(
        "sector_rotation_pattern",
        has_sector,
        f"Sector rotation pattern (电风扇/快速轮动) {'found' if has_sector else 'MISSING'}",
        weight=2.0
    )

    # ── 8. Cross-market: US stock decline mentioned ─────────────────────────
    us_pattern = r"纳斯达克|美股.*跌|跌.*美股|NASDAQ|nasdaq|科技股.*跌|英伟达"
    has_us = bool(re.search(us_pattern, content, re.IGNORECASE))
    add_check(
        "us_market_decline_mentioned",
        has_us,
        f"US market decline (纳斯达克跌) {'found' if has_us else 'MISSING'}",
        weight=1.5
    )

    # ── 9. Currency/USD pressure mentioned ──────────────────────────────────
    fx_pattern = r"美元.*上涨|人民币.*贬值|贬值|外资.*流出|北向.*流出|汇率"
    has_fx = bool(re.search(fx_pattern, content))
    add_check(
        "currency_pressure_mentioned",
        has_fx,
        f"Currency/capital outflow pressure {'found' if has_fx else 'MISSING'}",
        weight=1.5
    )

    # ── 10. Tool call suggestion appropriate to market phase ────────────────
    # In 退潮/混沌: should mention Position Risk Manager or 空仓/观望, NOT Vegas T Trading as primary
    tool_pattern = r"Position Risk Manager|止损|空仓观望|管住手|混沌.*不操作|退潮.*止损"
    has_tool = bool(re.search(tool_pattern, content))
    add_check(
        "appropriate_tool_recommendation",
        has_tool,
        f"Defensive tool recommendation (stop-loss/空仓) {'found' if has_tool else 'MISSING'}",
        weight=2.0
    )

    # ── 11. Report title / header present ───────────────────────────────────
    title_pattern = r"市场环境体检报告|大盘.*体检|Market Health Report|Market.*Report"
    has_title = bool(re.search(title_pattern, content))
    add_check(
        "report_title_present",
        has_title,
        f"Report title {'found' if has_title else 'MISSING'}",
        weight=1.0
    )

    # ── 12. Date 2026-03-15 referenced ─────────────────────────────────────
    date_pattern = r"2026-03-15|2026年3月15日|3月15日"
    has_date = bool(re.search(date_pattern, content))
    add_check(
        "correct_date_referenced",
        has_date,
        f"Date 2026-03-15 {'found' if has_date else 'MISSING'}",
        weight=1.0
    )

    # ── Final scoring ───────────────────────────────────────────────────────
    score = round(weighted_score / total_weight, 4) if total_weight > 0 else 0.0
    passed = score >= 0.70 and all(
        c["passed"] for c in checks if c["name"] in [
            "report_file_exists",
            "correct_emotion_cycle",
            "conservative_position_recommended",
        ]
    )

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    evaluate(sys.argv[1])