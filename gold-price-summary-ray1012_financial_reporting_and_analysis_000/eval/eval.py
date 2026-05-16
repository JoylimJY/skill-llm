import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # Find the gold report file
    report_files = list(workspace.rglob("gold_daily_report*")) + \
                   list(workspace.rglob("gold_report*")) + \
                   list(workspace.rglob("今日金价*")) + \
                   list(workspace.rglob("金价日报*")) + \
                   list(workspace.rglob("gold_price_report*")) + \
                   list(workspace.rglob("daily_gold*"))
    
    # Also search for any .md, .txt files that look like the report
    candidate_files = []
    for ext in ["*.md", "*.txt", "*.report"]:
        for f in workspace.rglob(ext):
            try:
                content = f.read_text(encoding="utf-8")
                # Must contain gold price indicators
                if ("XAU" in content or "金价" in content) and ("盎司" in content or "投资建议" in content):
                    candidate_files.append(f)
            except Exception:
                pass
    
    all_candidates = list(set(report_files + candidate_files))
    
    if not all_candidates:
        add_check("report_file_exists", False, "No gold daily report file found in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Use the most recently modified candidate
    report_file = sorted(all_candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    
    try:
        content = report_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("report_file_readable", False, f"Could not read report file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("report_file_exists", True, f"Found report at: {report_file}")
    
    # CHECK 1: Emoji header for 今日金价速报 (📊)
    has_chart_emoji = "📊" in content
    has_title = "今日金价速报" in content or "金价速报" in content
    add_check(
        "header_emoji_and_title",
        has_chart_emoji and has_title,
        f"📊 emoji: {has_chart_emoji}, 今日金价速报 title: {has_title}"
    )
    
    # CHECK 2: International gold price section with XAU/USD
    has_international = "XAU/USD" in content or "国际金价" in content
    add_check("international_price_section", has_international,
              f"International gold section present: {has_international}")
    
    # CHECK 3: Price values - current price should be around 3344 (today's close from data)
    # Accept range 3330-3360 for the main price
    price_matches = re.findall(r'3[23]\d{2}(?:\.\d+)?', content)
    has_valid_price = any(3330 <= float(p) <= 3360 for p in price_matches)
    add_check(
        "international_price_value",
        has_valid_price,
        f"Found price values near 3344.65 (today's close): {price_matches[:5]}"
    )
    
    # CHECK 4: Change calculation - prev close was 3298.30, today close 3344.65
    # Change = +46.35, Pct = +1.41% approximately
    # Accept absolute change in range 40-55
    abs_change_matches = re.findall(r'[+\+]?\d{2}\.\d+', content)
    change_numbers = []
    for m in re.findall(r'[\+\-]?(\d+\.?\d*)', content):
        try:
            val = float(m)
            if 35 <= val <= 60:
                change_numbers.append(val)
        except:
            pass
    has_change_value = len(change_numbers) > 0
    
    # Check percentage change ~1.4%
    pct_matches = re.findall(r'(\d+\.\d+)\s*%', content)
    has_pct_change = any(1.0 <= float(p) <= 1.8 for p in pct_matches)
    
    add_check(
        "change_calculation",
        has_change_value and has_pct_change,
        f"Absolute change ~46 present: {has_change_value} {change_numbers[:3]}, Pct ~1.41% present: {has_pct_change} {pct_matches[:5]}"
    )
    
    # CHECK 5: OHLC fields present (开盘, 最高, 最低 or open/high/low)
    has_open = "开盘" in content or "open" in content.lower()
    has_high = "最高" in content or "high" in content.lower()
    has_low = "最低" in content or "low" in content.lower()
    add_check(
        "ohlc_fields_present",
        has_open and has_high and has_low,
        f"开盘: {has_open}, 最高: {has_high}, 最低: {has_low}"
    )
    
    # CHECK 6: Domestic gold price (国内金价) section with CNY/gram
    has_domestic = "国内金价" in content or "人民币" in content or "元/克" in content or "CNY" in content
    # Price should be around 782.50
    domestic_price_matches = re.findall(r'78[0-9]\.\d+|78[0-9](?!\d)', content)
    has_domestic_price = len(domestic_price_matches) > 0
    add_check(
        "domestic_price_section",
        has_domestic and has_domestic_price,
        f"Domestic section: {has_domestic}, Domestic price ~782.50: {has_domestic_price} {domestic_price_matches[:3]}"
    )
    
    # CHECK 7: Domestic price change (today 782.50 - yesterday 765.30 = +17.20)
    domestic_change = re.findall(r'1[5-9]\.\d+|17\.\d+', content)
    has_domestic_change = len(domestic_change) > 0
    add_check(
        "domestic_change_calculation",
        has_domestic_change,
        f"Domestic change ~17.20 CNY: {has_domestic_change} {domestic_change[:3]}"
    )
    
    # CHECK 8: 近期走势 (recent trend) section with 1-week/1-month/3-month data
    has_trend_section = "近期走势" in content or "trend" in content.lower()
    # 1-week data: 3265.40, 1-month: 3180.00
    has_1week = "3265" in content or "1周" in content or "1 周" in content or "一周" in content
    has_1month = "3180" in content or "1个月" in content or "1 个月" in content or "一个月" in content
    add_check(
        "trend_section_with_data",
        has_trend_section and (has_1week or has_1month),
        f"Trend section: {has_trend_section}, 1-week data: {has_1week}, 1-month data: {has_1month}"
    )
    
    # CHECK 9: Market factors section (📰 emoji)
    has_news_emoji = "📰" in content
    has_factors_section = "市场" in content and ("影响因素" in content or "因素" in content)
    # Should mention USD/dollar, interest rates, geopolitical
    has_usd = "美元" in content or "USD" in content or "DXY" in content
    has_rates = "利率" in content or "美联储" in content or "Fed" in content or "联储" in content
    has_geo = "地缘" in content or "geopolit" in content.lower() or "中东" in content
    add_check(
        "market_factors_section",
        has_news_emoji and has_factors_section,
        f"📰 emoji: {has_news_emoji}, Market factors section: {has_factors_section}"
    )
    add_check(
        "market_factors_content",
        has_usd and has_rates and has_geo,
        f"USD mention: {has_usd}, Interest rates: {has_rates}, Geopolitical: {has_geo}"
    )
    
    # CHECK 10: Investment advice section (💡 emoji) 
    has_bulb_emoji = "💡" in content
    has_advice_section = "投资建议" in content
    add_check(
        "investment_advice_section",
        has_bulb_emoji and has_advice_section,
        f"💡 emoji: {has_bulb_emoji}, 投资建议 section: {has_advice_section}"
    )
    
    # CHECK 11: Three risk tiers present (proprietary trap from SKILL.md)
    has_conservative = "保守" in content or "保守型" in content
    has_steady = "稳健" in content or "稳健型" in content
    has_aggressive = "激进" in content or "激进型" in content
    add_check(
        "three_risk_tiers",
        has_conservative and has_steady and has_aggressive,
        f"保守型: {has_conservative}, 稳健型: {has_steady}, 激进型: {has_aggressive}"
    )
    
    # CHECK 12: Specific percentage allocations from SKILL.md framework (10-20%, 20-30%)
    pct_10_20 = bool(re.search(r'10.{0,5}20\s*%|10%-?20%|10%.*?20%', content))
    pct_20_30 = bool(re.search(r'20.{0,5}30\s*%|20%-?30%|20%.*?30%', content))
    add_check(
        "risk_tier_allocations",
        pct_10_20 or pct_20_30,
        f"10-20% allocation: {pct_10_20}, 20-30% allocation: {pct_20_30}"
    )
    
    # CHECK 13: Mandatory disclaimer - 市场有风险，投资需谨慎
    has_disclaimer = "市场有风险" in content and "投资需谨慎" in content
    add_check(
        "mandatory_disclaimer",
        has_disclaimer,
        f"'市场有风险，投资需谨慎' disclaimer present: {has_disclaimer}"
    )
    
    # CHECK 14: Data source annotation (数据来源 or source mention)
    has_source = "数据来源" in content or "来源" in content or "kitco" in content.lower() or \
                 "中国黄金" in content or "source" in content.lower() or "上海黄金" in content
    has_time = "2025-07-08" in content or "2025年7月8日" in content or "07-08" in content
    add_check(
        "data_source_and_time_annotation",
        has_source and has_time,
        f"Data source mentioned: {has_source}, Date annotated: {has_time}"
    )
    
    # Compute score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "header_emoji_and_title",
        "three_risk_tiers",
        "mandatory_disclaimer",
        "investment_advice_section",
        "international_price_section",
        "domestic_price_section",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))