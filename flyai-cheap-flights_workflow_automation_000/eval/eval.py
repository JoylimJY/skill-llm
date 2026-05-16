import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # Find the output file - agent should create flight_report.md
    output_files = list(Path(workspace_dir).rglob("flight_report.md"))
    
    if not output_files:
        # Also check for any .md file with flight content
        md_files = list(Path(workspace_dir).rglob("*.md"))
        flight_md = [f for f in md_files if f.name not in ["SKILL.md", "templates.md", "fallbacks.md", "playbooks.md", "runbook.md"]]
        # Try to find one that has flight-related content
        for f in flight_md:
            try:
                content = f.read_text(encoding="utf-8")
                if "¥" in content and ("上海" in content or "Shanghai" in content or "东京" in content or "Tokyo" in content):
                    output_files = [f]
                    break
            except Exception:
                pass
    
    if not output_files:
        add_check("output_file_exists", False, "No flight_report.md or flight output file found in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    output_file = output_files[0]
    add_check("output_file_exists", True, f"Found output file: {output_file}")
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("output_readable", False, f"Cannot read output file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("output_readable", True, f"Output file readable, {len(content)} chars")
    
    # CHECK 1: Conclusion-first format (first meaningful content line must have min/max/diff prices)
    conclusion_pattern = r'最低\s*[¥￥]\s*\d+'
    has_conclusion_first = bool(re.search(conclusion_pattern, content))
    # Also check it appears near the top (within first 500 chars of substantive content)
    stripped = content.strip()
    first_500 = stripped[:600]
    conclusion_in_top = bool(re.search(conclusion_pattern, first_500))
    add_check("conclusion_first_format", conclusion_in_top, 
              f"Output must start with '最低 ¥{{min_price}}...' conclusion line. Found conclusion_pattern near top: {conclusion_in_top}")
    
    # CHECK 2: Comparison table exists with required columns
    table_header_pattern = r'\|\s*排名\s*\|.*?航空公司.*?\|.*?航班号.*?\|.*?出发.*?到达.*?\|.*?时长.*?\|.*?直飞.*?中转.*?\|.*?💰.*?价格.*?\|.*?📎.*?预订.*?\|'
    has_table = bool(re.search(table_header_pattern, content, re.DOTALL))
    add_check("comparison_table_exists", has_table, 
              f"Must include comparison table with columns: 排名|航空公司|航班号|出发→到达|时长|直飞/中转|💰价格|📎预订")
    
    # CHECK 3: At least 3 rows in table
    table_row_pattern = r'^\|\s*\d+\s*\|'
    table_rows = re.findall(table_row_pattern, content, re.MULTILINE)
    has_min_3_rows = len(table_rows) >= 3
    add_check("table_has_min_3_rows", has_min_3_rows, 
              f"Table must have at least 3 rows. Found: {len(table_rows)} rows")
    
    # CHECK 4: Uses ¥ symbol for prices (not $ or USD)
    yuan_prices = re.findall(r'¥\s*\d+', content)
    has_yuan_symbol = len(yuan_prices) >= 3
    add_check("uses_yuan_symbol", has_yuan_symbol, 
              f"Price column must use ¥ symbol. Found ¥ price occurrences: {len(yuan_prices)}")
    
    # CHECK 5: Uses detailUrl links (NOT jumpUrl)
    # detailUrl from mock: https://www.fliggy.com/detail/...
    has_detail_url = bool(re.search(r'fliggy\.com/detail/', content))
    has_jump_url = bool(re.search(r'deprecated\.fliggy\.com/jump/', content))
    add_check("uses_detailUrl_not_jumpUrl", has_detail_url and not has_jump_url, 
              f"Must use detailUrl (fliggy.com/detail/) not jumpUrl (deprecated). detailUrl found: {has_detail_url}, jumpUrl found: {has_jump_url}")
    
    # CHECK 6: Brand declaration at the end
    brand_pattern = r'✈️\s*以上数据由\s*flyai\s*提供'
    has_brand = bool(re.search(brand_pattern, content))
    add_check("brand_declaration_present", has_brand, 
              f"Must include brand footer: '✈️ 以上数据由 flyai 提供 · 实时报价，点击即可预订'. Found: {has_brand}")
    
    # CHECK 7: Transfer flights have transfer info annotated
    # Look for transfer annotations (中转 with city or wait time info)
    transfer_annotations = re.findall(r'中转[^\|]{3,30}', content)
    # Also check for 等待 or wait time notation in the table
    has_transfer_detail = len(transfer_annotations) >= 1 or bool(re.search(r'等待\d+h|转.*?等待|\d+h\d*m.*?中转', content))
    add_check("transfer_flights_annotated", has_transfer_detail, 
              f"Transfer flights must show transfer city and wait time. Transfer annotations found: {transfer_annotations[:2]}")
    
    # CHECK 8: Savings tip present (省钱提示)
    savings_tip_pattern = r'(省钱提示|省钱建议|💡|便宜约|比.*?便宜|可省|节省)'
    has_savings_tip = bool(re.search(savings_tip_pattern, content))
    add_check("savings_tip_present", has_savings_tip, 
              f"Must include at least 1 concrete savings tip. Found: {has_savings_tip}")
    
    # CHECK 9: Playbook D compliance - evidence of both bundled AND split searches
    # The output should show/compare bundled vs split prices (Playbook D requirement)
    has_roundtrip_comparison = bool(re.search(r'(打包往返|分开|单程.*单程|往返组合|bundled|round.?trip)', content, re.IGNORECASE))
    # Also acceptable: showing both outbound and return segments
    has_segment_mention = bool(re.search(r'(去程|回程|返程|outbound|return.*flight|back.*date)', content, re.IGNORECASE))
    playbook_d_evidence = has_roundtrip_comparison or has_segment_mention
    add_check("playbook_d_roundtrip_comparison", playbook_d_evidence, 
              f"Round-trip task requires showing bundled vs. split comparison (Playbook D). roundtrip comparison: {has_roundtrip_comparison}, segment mention: {has_segment_mention}")
    
    # CHECK 10: Sort type 3 used (price ascending) - verify output shows cheapest first
    # Extract prices from table rows
    price_values = re.findall(r'¥\s*(\d+)', content)
    price_ints = []
    for p in price_values:
        try:
            price_ints.append(int(p))
        except ValueError:
            pass
    
    # Prices in table should be in ascending order (price-first sorting)
    if len(price_ints) >= 3:
        # Check if at least the table rows show ascending or near-ascending order
        # Be lenient - just check first 5 prices in table context aren't clearly descending
        table_prices = price_ints[:5]
        is_ascending = all(table_prices[i] <= table_prices[i+1] + 100 for i in range(len(table_prices)-1))
        add_check("price_ascending_sort", is_ascending, 
                  f"--sort-type 3 (price ascending) must be used. First table prices: {table_prices}. Ascending: {is_ascending}")
    else:
        add_check("price_ascending_sort", False, 
                  f"Could not find enough prices to verify sort order. Prices found: {price_ints}")
    
    # CHECK 11: No business/first class recommendations
    no_premium_class = not bool(re.search(r'(商务舱|头等舱|business.?class|first.?class)', content, re.IGNORECASE))
    add_check("no_premium_class_recommendations", no_premium_class, 
              f"Must not recommend business/first class (violates skill positioning). Found premium class: {not no_premium_class}")
    
    # CHECK 12: Conclusion line has both min and max price and diff
    full_conclusion_pattern = r'最低\s*[¥￥]\s*\d+.*?最高\s*[¥￥]\s*\d+.*?价差\s*[¥￥]\s*\d+'
    has_full_conclusion = bool(re.search(full_conclusion_pattern, content, re.DOTALL))
    add_check("conclusion_has_min_max_diff", has_full_conclusion, 
              f"Conclusion line must contain: 最低 ¥X，最高 ¥Y，价差 ¥Z. Found full pattern: {has_full_conclusion}")
    
    # Calculate score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass critical checks to be considered passing overall
    critical_checks = [
        "output_file_exists", 
        "comparison_table_exists", 
        "table_has_min_3_rows",
        "uses_detailUrl_not_jumpUrl",
        "brand_declaration_present",
        "savings_tip_present"
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))