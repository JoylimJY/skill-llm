#!/usr/bin/env python3
"""
Evaluation script for A-share semiconductor sector analysis task.
Checks:
1. Output file exists and is valid JSON
2. The report covers all 5 semiconductor sector constituent stocks
3. Historical price data was fetched with correct parameters (daily, qfq, 2024)
4. Financial data was included with indicator="按报告期"
5. Each stock entry has required computed fields (avg_close, max_close, min_close, net_profit_latest)
6. The agent used stock_board_industry_cons_em to discover stocks (not hardcoded partial list)
"""

import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0

    EXPECTED_STOCKS = {"300750", "688981", "002371", "603501", "002049"}
    EXPECTED_STOCK_NAMES = {"宁德时代", "中芯国际", "北方华创", "韦尔股份", "紫光国微"}

    # ---- Check 1: Output file exists ----
    report_files = list(workspace.rglob("sector_analysis_report.json"))
    if not report_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "sector_analysis_report.json not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {report_path.relative_to(workspace)}"
    })
    total_score += 0.1

    # ---- Check 2: Valid JSON ----
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "JSON parsed successfully"})
        total_score += 0.1
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    # ---- Check 3: Sector field present and correct ----
    sector = report.get("sector", "")
    sector_ok = "半导体" in str(sector)
    checks.append({
        "name": "sector_field_correct",
        "passed": sector_ok,
        "detail": f"sector='{sector}'" if sector_ok else f"Expected '半导体' in sector, got '{sector}'"
    })
    if sector_ok:
        total_score += 0.05

    # ---- Check 4: All 5 constituent stocks present ----
    stocks_data = report.get("stocks", [])
    if not isinstance(stocks_data, list):
        checks.append({"name": "stocks_list_present", "passed": False, "detail": "stocks field is not a list"})
        return {"passed": False, "score": total_score, "checks": checks}

    found_symbols = set()
    for s in stocks_data:
        if isinstance(s, dict):
            sym = str(s.get("symbol", s.get("代码", s.get("code", ""))))
            found_symbols.add(sym.strip())

    all_stocks_present = EXPECTED_STOCKS.issubset(found_symbols)
    checks.append({
        "name": "all_5_constituent_stocks_present",
        "passed": all_stocks_present,
        "detail": f"Found symbols: {sorted(found_symbols)}. Expected all of: {sorted(EXPECTED_STOCKS)}"
    })
    if all_stocks_present:
        total_score += 0.2
    elif len(found_symbols & EXPECTED_STOCKS) >= 3:
        total_score += 0.1  # partial credit

    # ---- Check 5: Historical price data computed fields present (avg_close or similar) ----
    hist_fields_found = 0
    for s in stocks_data:
        if not isinstance(s, dict):
            continue
        # Accept various reasonable field names for price statistics
        has_avg = any(k in s for k in ["avg_close", "平均收盘价", "average_close", "mean_close", "avg_price"])
        has_max = any(k in s for k in ["max_close", "最高收盘价", "max_price", "highest_close", "period_high"])
        has_min = any(k in s for k in ["min_close", "最低收盘价", "min_price", "lowest_close", "period_low"])
        if has_avg or has_max or has_min:
            hist_fields_found += 1

    hist_coverage = hist_fields_found / max(len(stocks_data), 1)
    hist_ok = hist_fields_found >= 4  # at least 4 of 5 stocks have price stats
    checks.append({
        "name": "historical_price_stats_present",
        "passed": hist_ok,
        "detail": f"{hist_fields_found}/{len(stocks_data)} stocks have historical price statistics"
    })
    if hist_ok:
        total_score += 0.2

    # ---- Check 6: Financial data present per stock ----
    fin_fields_found = 0
    for s in stocks_data:
        if not isinstance(s, dict):
            continue
        has_fin = any(k in s for k in [
            "net_profit", "净利润", "financial_data", "financials",
            "net_profit_latest", "latest_net_profit", "revenue", "营业总收入",
            "roe", "净资产收益率", "eps", "基本每股收益"
        ])
        if has_fin:
            fin_fields_found += 1

    fin_ok = fin_fields_found >= 4
    checks.append({
        "name": "financial_data_present",
        "passed": fin_ok,
        "detail": f"{fin_fields_found}/{len(stocks_data)} stocks have financial data"
    })
    if fin_ok:
        total_score += 0.2

    # ---- Check 7: Verify the analysis script used correct AkShare parameters ----
    # Look for the agent's Python script and check it used correct parameters
    agent_scripts = list(workspace.rglob("*.py"))
    # Exclude mock and legacy files
    agent_scripts = [s for s in agent_scripts if
                     "mock_akshare" not in str(s) and
                     "legacy_code" not in str(s) and
                     "tools/scrapers" not in str(s) and
                     "__pycache__" not in str(s)]

    qfq_found = False
    period_daily_found = False
    indicator_correct = False
    board_cons_used = False
    financial_abs_used = False

    for script_path in agent_scripts:
        try:
            content = script_path.read_text(encoding="utf-8", errors="ignore")
            if 'adjust' in content and 'qfq' in content:
                qfq_found = True
            if 'period' in content and 'daily' in content:
                period_daily_found = True
            if '按报告期' in content:
                indicator_correct = True
            if 'stock_board_industry_cons_em' in content:
                board_cons_used = True
            if 'stock_financial_abstract_ths' in content:
                financial_abs_used = True
        except Exception:
            pass

    checks.append({
        "name": "used_qfq_adjust_parameter",
        "passed": qfq_found,
        "detail": "Found adjust='qfq' in agent script(s)" if qfq_found else "Did not find adjust='qfq' — must use forward-adjusted prices per SKILL.md"
    })
    if qfq_found:
        total_score += 0.05

    checks.append({
        "name": "used_daily_period_parameter",
        "passed": period_daily_found,
        "detail": "Found period='daily' in agent script(s)" if period_daily_found else "Did not find period='daily' in script"
    })
    if period_daily_found:
        total_score += 0.025

    checks.append({
        "name": "used_correct_financial_indicator",
        "passed": indicator_correct,
        "detail": "Found indicator='按报告期' in agent script(s)" if indicator_correct else "Missing indicator='按报告期' — proprietary Chinese parameter required"
    })
    if indicator_correct:
        total_score += 0.05

    checks.append({
        "name": "used_board_industry_cons_em",
        "passed": board_cons_used,
        "detail": "Found stock_board_industry_cons_em() call in agent script(s)" if board_cons_used else "Did not call stock_board_industry_cons_em() to discover sector constituents"
    })
    if board_cons_used:
        total_score += 0.025

    checks.append({
        "name": "used_financial_abstract_ths",
        "passed": financial_abs_used,
        "detail": "Found stock_financial_abstract_ths() call in agent script(s)" if financial_abs_used else "Did not call stock_financial_abstract_ths() for financial data"
    })
    if financial_abs_used:
        total_score += 0.025

    # ---- Check 8: Date range 2024 in report ----
    report_str = json.dumps(report, ensure_ascii=False)
    date_range_ok = "2024" in report_str
    checks.append({
        "name": "date_range_2024_present",
        "passed": date_range_ok,
        "detail": "Report contains 2024 date range" if date_range_ok else "No 2024 date reference found in report"
    })
    if date_range_ok:
        total_score += 0.025

    # ---- Final pass/fail ----
    critical_checks = [
        "output_file_exists",
        "valid_json",
        "all_5_constituent_stocks_present",
        "historical_price_stats_present",
        "financial_data_present",
        "used_qfq_adjust_parameter",
        "used_correct_financial_indicator",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    final_score = min(round(total_score, 3), 1.0)
    passed = critical_passed and final_score >= 0.7

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))