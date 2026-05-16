import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    workspace = Path(workspace_dir)
    
    # Find the report file
    report_files = list(workspace.rglob('gold_analysis_report.md'))
    
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_exists", "passed": False, "detail": "gold_analysis_report.md not found anywhere in workspace"}]
        }
    
    report_path = report_files[0]
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_readable", "passed": False, "detail": f"Could not read report: {e}"}]
        }
    
    # ---- CHECK 1: Module 1 - 实时行情 section present ----
    try:
        has_realtime = bool(re.search(r'黄金实时行情|📊', content))
        has_xauusd_table = bool(re.search(r'XAUUSD|国际金价', content, re.IGNORECASE))
        has_au9999_table = bool(re.search(r'Au9999|au9999|AU9999|国内金价', content))
        module1_pass = has_realtime and has_xauusd_table and has_au9999_table
        checks.append({
            "name": "module1_realtime_market",
            "passed": module1_pass,
            "detail": f"实时行情模块: section={has_realtime}, xauusd={has_xauusd_table}, au9999={has_au9999_table}"
        })
        if module1_pass:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "module1_realtime_market", "passed": False, "detail": str(e)})

    # ---- CHECK 2: International price data present (3520 range) ----
    try:
        # Looking for the price 3520 or similar value
        has_intl_price = bool(re.search(r'3[,.]?5[0-9]{2}', content))
        has_usd_oz = bool(re.search(r'USD|美元|盎司|\$', content))
        price_check_pass = has_intl_price and has_usd_oz
        checks.append({
            "name": "module1_international_price_value",
            "passed": price_check_pass,
            "detail": f"International price ~3520: found={has_intl_price}, unit_present={has_usd_oz}"
        })
        if price_check_pass:
            total_score += 0.08
    except Exception as e:
        checks.append({"name": "module1_international_price_value", "passed": False, "detail": str(e)})

    # ---- CHECK 3: Domestic price data present (808 range) ----
    try:
        has_domestic_price = bool(re.search(r'80[0-9]\.[0-9]|8[0-1][0-9]', content))
        has_cny_g = bool(re.search(r'元.{0,5}克|CNY|人民币|克', content))
        domestic_check_pass = has_domestic_price and has_cny_g
        checks.append({
            "name": "module1_domestic_price_value",
            "passed": domestic_check_pass,
            "detail": f"Domestic Au9999 price ~808: found={has_domestic_price}, cny_unit={has_cny_g}"
        })
        if domestic_check_pass:
            total_score += 0.08
    except Exception as e:
        checks.append({"name": "module1_domestic_price_value", "passed": False, "detail": str(e)})

    # ---- CHECK 4: Module 2 - 历史价格走势 with ASCII chart ----
    try:
        has_history_section = bool(re.search(r'历史价格走势|📉', content))
        # ASCII chart should use box-drawing characters
        has_ascii_chart = bool(re.search(r'[┤┼╭╰─│]', content))
        has_price_axis = bool(re.search(r'\$[23][,\d]+|\d{4}[,\s]', content))
        has_3month_label = bool(re.search(r'3个月|3月前|month', content, re.IGNORECASE))
        module2_pass = has_history_section and has_ascii_chart
        checks.append({
            "name": "module2_history_ascii_chart",
            "passed": module2_pass,
            "detail": f"历史走势模块: section={has_history_section}, ascii_chart={has_ascii_chart}, price_axis={has_price_axis}, 3month={has_3month_label}"
        })
        if module2_pass:
            total_score += 0.12
    except Exception as e:
        checks.append({"name": "module2_history_ascii_chart", "passed": False, "detail": str(e)})

    # ---- CHECK 5: Key price levels in history section ----
    try:
        has_high = bool(re.search(r'最高价|高点|high', content, re.IGNORECASE))
        has_low = bool(re.search(r'最低价|低点|low', content, re.IGNORECASE))
        has_support = bool(re.search(r'支撑位|support', content, re.IGNORECASE))
        has_resistance = bool(re.search(r'压力位|resistance', content, re.IGNORECASE))
        keylevels_pass = has_high and has_low and has_support and has_resistance
        checks.append({
            "name": "module2_key_price_levels",
            "passed": keylevels_pass,
            "detail": f"Key levels: high={has_high}, low={has_low}, support={has_support}, resistance={has_resistance}"
        })
        if keylevels_pass:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "module2_key_price_levels", "passed": False, "detail": str(e)})

    # ---- CHECK 6: Module 3 - 趋势分析 with all 5 macro drivers ----
    try:
        has_trend_section = bool(re.search(r'趋势分析|📈', content))
        has_fed = bool(re.search(r'美联储|Fed|Federal Reserve', content, re.IGNORECASE))
        has_dxy = bool(re.search(r'美元指数|DXY', content))
        has_geopolitics = bool(re.search(r'地缘政治|geopolit', content, re.IGNORECASE))
        has_inflation = bool(re.search(r'通胀|CPI|PCE|inflation', content, re.IGNORECASE))
        has_fund_flow = bool(re.search(r'资金流向|ETF持仓|fund flow', content, re.IGNORECASE))
        drivers_count = sum([has_fed, has_dxy, has_geopolitics, has_inflation, has_fund_flow])
        module3_pass = has_trend_section and drivers_count >= 4
        checks.append({
            "name": "module3_trend_analysis_5_drivers",
            "passed": module3_pass,
            "detail": f"趋势分析: section={has_trend_section}, drivers_found={drivers_count}/5 (fed={has_fed}, dxy={has_dxy}, geo={has_geopolitics}, inflation={has_inflation}, fundflow={has_fund_flow})"
        })
        if module3_pass:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "module3_trend_analysis_5_drivers", "passed": False, "detail": str(e)})

    # ---- CHECK 7: DXY value 106.3 mentioned correctly ----
    try:
        has_dxy_value = bool(re.search(r'106[.\s]?[3-9]?|dxy.*106|106.*dxy', content, re.IGNORECASE))
        checks.append({
            "name": "module3_dxy_value_106",
            "passed": has_dxy_value,
            "detail": f"DXY value ~106.3 present in analysis: {has_dxy_value}"
        })
        if has_dxy_value:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "module3_dxy_value_106", "passed": False, "detail": str(e)})

    # ---- CHECK 8: Module 4 - 买入建议 with correct 🔴 暂缓买入 recommendation ----
    try:
        has_buyrec_section = bool(re.search(r'买入建议|💡', content))
        # Based on market data: DXY=106.3 (>104), 1-month change=9.7% (>8%), ETF outflow, high real rates
        # This MUST trigger 🔴 暂缓买入
        has_red_signal = bool(re.search(r'🔴|暂缓买入|暂缓', content))
        no_green_signal = not bool(re.search(r'🟢\s*建议买入', content))
        
        buyrec_pass = has_buyrec_section and has_red_signal
        checks.append({
            "name": "module4_buy_recommendation_red",
            "passed": buyrec_pass,
            "detail": f"买入建议模块: section={has_buyrec_section}, red_signal={has_red_signal}, no_incorrect_green={no_green_signal}. Market conditions (DXY=106.3>104, 1M-gain=9.7%>8%) require 🔴"
        })
        if buyrec_pass:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "module4_buy_recommendation_red", "passed": False, "detail": str(e)})

    # ---- CHECK 9: Buy recommendation has 3-row operation table ----
    try:
        has_longterm = bool(re.search(r'长期配置', content))
        has_midterm = bool(re.search(r'中期持有', content))
        has_shortterm = bool(re.search(r'短期交易', content))
        has_key_levels = bool(re.search(r'建议买入区间|目标价位|止损', content))
        op_table_pass = has_longterm and has_midterm and has_shortterm and has_key_levels
        checks.append({
            "name": "module4_operation_table_and_keylevels",
            "passed": op_table_pass,
            "detail": f"操作策略表: 长期={has_longterm}, 中期={has_midterm}, 短期={has_shortterm}, key_levels={has_key_levels}"
        })
        if op_table_pass:
            total_score += 0.07
    except Exception as e:
        checks.append({"name": "module4_operation_table_and_keylevels", "passed": False, "detail": str(e)})

    # ---- CHECK 10: Module 5 - ETF推荐 with correct fund codes ----
    try:
        has_etf_section = bool(re.search(r'ETF|黄金.*基金', content))
        has_code_518880 = bool(re.search(r'518880', content))
        has_code_159937 = bool(re.search(r'159937', content))
        has_code_159934 = bool(re.search(r'159934', content))
        has_code_518800 = bool(re.search(r'518800', content))
        codes_found = sum([has_code_518880, has_code_159937, has_code_159934, has_code_518800])
        etf_codes_pass = has_etf_section and codes_found >= 3
        checks.append({
            "name": "module5_etf_domestic_codes",
            "passed": etf_codes_pass,
            "detail": f"国内ETF代码: 518880={has_code_518880}, 159937={has_code_159937}, 159934={has_code_159934}, 518800={has_code_518800} ({codes_found}/4 found)"
        })
        if etf_codes_pass:
            total_score += 0.08
    except Exception as e:
        checks.append({"name": "module5_etf_domestic_codes", "passed": False, "detail": str(e)})

    # ---- CHECK 11: ETF fund names present ----
    try:
        has_huaan = bool(re.search(r'华安黄金|华安.*ETF', content))
        has_boshi = bool(re.search(r'博时黄金|博时.*ETF', content))
        has_yfd = bool(re.search(r'易方达黄金|易方达.*ETF', content))
        has_guotai = bool(re.search(r'国泰黄金|国泰.*ETF', content))
        names_count = sum([has_huaan, has_boshi, has_yfd, has_guotai])
        etf_names_pass = names_count >= 3
        checks.append({
            "name": "module5_etf_fund_names",
            "passed": etf_names_pass,
            "detail": f"ETF基金名称: 华安={has_huaan}, 博时={has_boshi}, 易方达={has_yfd}, 国泰={has_guotai} ({names_count}/4)"
        })
        if etf_names_pass:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "module5_etf_fund_names", "passed": False, "detail": str(e)})

    # ---- CHECK 12: Overseas ETF mentioned (GLD/IAU/SGOL) ----
    try:
        has_gld = bool(re.search(r'GLD|SPDR黄金', content))
        has_iau = bool(re.search(r'IAU|iShares', content))
        has_sgol = bool(re.search(r'SGOL|Aberdeen', content))
        overseas_count = sum([has_gld, has_iau, has_sgol])
        overseas_pass = overseas_count >= 2
        checks.append({
            "name": "module5_etf_overseas",
            "passed": overseas_pass,
            "detail": f"境外ETF: GLD={has_gld}, IAU={has_iau}, SGOL={has_sgol} ({overseas_count}/3)"
        })
        if overseas_pass:
            total_score += 0.04
    except Exception as e:
        checks.append({"name": "module5_etf_overseas", "passed": False, "detail": str(e)})

    # ---- CHECK 13: ETF NAV values from market_data.json filled in ----
    try:
        # NAV: 7.2341, 7.1856, 5.8923, 7.1102
        has_nav_7234 = bool(re.search(r'7\.23[0-9]', content))
        has_nav_7185 = bool(re.search(r'7\.18[0-9]', content))
        has_nav_5892 = bool(re.search(r'5\.89[0-9]', content))
        navs_found = sum([has_nav_7234, has_nav_7185, has_nav_5892])
        etf_nav_pass = navs_found >= 2
        checks.append({
            "name": "module5_etf_nav_values",
            "passed": etf_nav_pass,
            "detail": f"ETF净值填入: 7.234x={has_nav_7234}, 7.185x={has_nav_7185}, 5.892x={has_nav_5892} ({navs_found}/3 NAVs from market_data.json)"
        })
        if etf_nav_pass:
            total_score += 0.04
    except Exception as e:
        checks.append({"name": "module5_etf_nav_values", "passed": False, "detail": str(e)})

    # ---- CHECK 14: Investment method comparison table ----
    try:
        has_comp_table = bool(re.search(r'投资方式.*对比|黄金ETF.*场内|实物金|银行黄金|期货', content))
        has_gate_criteria = bool(re.search(r'流动性|门槛|费用', content))
        comp_pass = has_comp_table and has_gate_criteria
        checks.append({
            "name": "module5_investment_comparison_table",
            "passed": comp_pass,
            "detail": f"投资方式对比表: table_present={has_comp_table}, criteria_present={has_gate_criteria}"
        })
        if comp_pass:
            total_score += 0.04
    except Exception as e:
        checks.append({"name": "module5_investment_comparison_table", "passed": False, "detail": str(e)})

    # ---- CHECK 15: Module 6 - Risk disclaimer ----
    try:
        has_risk = bool(re.search(r'风险提示|⚠️|仅供参考|不构成.*投资建议|投资决策', content))
        risk_pass = has_risk
        checks.append({
            "name": "module6_risk_disclaimer",
            "passed": risk_pass,
            "detail": f"风险提示模块: {has_risk}"
        })
        if risk_pass:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "module6_risk_disclaimer", "passed": False, "detail": str(e)})

    # ---- CHECK 16: All 6 emoji section headers present ----
    try:
        emojis = ['📊', '📉', '📈', '💡', '🏦', '⚠️']
        found_emojis = [e for e in emojis if e in content]
        # Also allow text alternatives
        alt_sections = [
            bool(re.search(r'黄金实时行情|实时行情', content)),
            bool(re.search(r'历史价格走势', content)),
            bool(re.search(r'趋势分析', content)),
            bool(re.search(r'买入建议', content)),
            bool(re.search(r'黄金.{0,5}ETF.{0,5}推荐|ETF推荐', content)),
            bool(re.search(r'风险提示', content))
        ]
        sections_present = sum(alt_sections)
        emoji_count = len(found_emojis)
        all_6_pass = sections_present >= 5 and emoji_count >= 4
        checks.append({
            "name": "all_6_modules_present",
            "passed": all_6_pass,
            "detail": f"6个模块: {sections_present}/6 sections, {emoji_count}/6 emojis found: {found_emojis}"
        })
        if all_6_pass:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "all_6_modules_present", "passed": False, "detail": str(e)})

    # ---- Final scoring ----
    total_score = min(total_score, 1.0)
    num_passed = sum(1 for c in checks if c["passed"])
    passed_overall = num_passed >= 10 and total_score >= 0.65

    return {
        "passed": passed_overall,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))