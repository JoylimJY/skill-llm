import sys
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Locate research_report.json ───────────────────────────────────────────
    report_files = list(workspace.rglob("research_report.json"))
    
    if not report_files:
        checks.append({
            "name": "file_exists",
            "passed": False,
            "detail": "research_report.json not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = report_files[0]
    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })
    
    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # ── Check 1: hk-view data present ─────────────────────────────────────────
    # The report must contain view/basic info fields for 02318.HK
    try:
        report_str = json.dumps(report)
        
        # Look for view data — sector should be "金融", listing_status "正常上市"
        has_sector = False
        has_listing_status = False
        has_market_cap = False
        has_total_shares = False
        has_a_share_code = False
        
        def search_recursive(obj, key, value=None):
            """Recursively search for a key (and optionally matching value) in nested dict/list."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == key:
                        if value is None:
                            return True, v
                        if str(v) == str(value):
                            return True, v
                    found, val = search_recursive(v, key, value)
                    if found:
                        return found, val
            elif isinstance(obj, list):
                for item in obj:
                    found, val = search_recursive(item, key, value)
                    if found:
                        return found, val
            return False, None
        
        found_sector, sector_val = search_recursive(report, 'sector')
        has_sector = found_sector and sector_val == '金融'
        
        found_ls, ls_val = search_recursive(report, 'listing_status')
        has_listing_status = found_ls and ls_val == '正常上市'
        
        found_mc, mc_val = search_recursive(report, 'market_cap')
        has_market_cap = found_mc and mc_val == 868000000000
        
        found_ts, ts_val = search_recursive(report, 'total_shares')
        has_total_shares = found_ts and ts_val == 18210000000
        
        found_asc, asc_val = search_recursive(report, 'a_share_code')
        has_a_share_code = found_asc and asc_val == '601318.SH'
        
        view_passed = has_sector and has_listing_status and has_market_cap and has_total_shares
        checks.append({
            "name": "hk_view_data_present",
            "passed": view_passed,
            "detail": (
                f"sector={'金融' if has_sector else 'MISSING'}, "
                f"listing_status={'正常上市' if has_listing_status else 'MISSING'}, "
                f"market_cap={mc_val if found_mc else 'MISSING'}, "
                f"total_shares={ts_val if found_ts else 'MISSING'}, "
                f"a_share_code={asc_val if found_asc else 'MISSING'}"
            )
        })
    except Exception as e:
        checks.append({"name": "hk_view_data_present", "passed": False, "detail": f"Error: {e}"})

    # ── Check 2: Valuation data present ───────────────────────────────────────
    try:
        found_pe, pe_val = search_recursive(report, 'pe_ttm')
        found_pb, pb_val = search_recursive(report, 'pb')
        found_ps, ps_val = search_recursive(report, 'ps')
        found_dy, dy_val = search_recursive(report, 'dividend_yield')
        
        pe_ok = found_pe and abs(float(pe_val) - 9.87) < 0.01
        pb_ok = found_pb and abs(float(pb_val) - 1.23) < 0.01
        ps_ok = found_ps and abs(float(ps_val) - 0.87) < 0.01
        dy_ok = found_dy and abs(float(dy_val) - 5.12) < 0.01
        
        val_passed = pe_ok and pb_ok and ps_ok and dy_ok
        checks.append({
            "name": "valuation_data_present",
            "passed": val_passed,
            "detail": (
                f"pe_ttm={'9.87✓' if pe_ok else f'{pe_val}✗'}, "
                f"pb={'1.23✓' if pb_ok else f'{pb_val}✗'}, "
                f"ps={'0.87✓' if ps_ok else f'{ps_val}✗'}, "
                f"dividend_yield={'5.12✓' if dy_ok else f'{dy_val}✗'}"
            )
        })
    except Exception as e:
        checks.append({"name": "valuation_data_present", "passed": False, "detail": f"Error: {e}"})

    # ── Check 3: Candlestick data present with correct range ──────────────────
    try:
        # Find candlestick/kline data: look for list of OHLCV dicts with date fields
        candle_data = None
        
        def find_candle_data(obj):
            if isinstance(obj, list) and len(obj) > 0:
                item = obj[0]
                if isinstance(item, dict) and 'date' in item and 'open' in item and 'close' in item:
                    return obj
            if isinstance(obj, dict):
                for v in obj.values():
                    result = find_candle_data(v)
                    if result is not None:
                        return result
            if isinstance(obj, list):
                for item in obj:
                    result = find_candle_data(item)
                    if result is not None:
                        return result
            return None
        
        candle_data = find_candle_data(report)
        
        has_candle = candle_data is not None
        
        # Check date range: all dates should be >= 2026-03-01 and <= 2026-03-24
        dates_ok = False
        interval_day_ok = False
        candle_count_ok = False
        
        if has_candle:
            dates = [d['date'] for d in candle_data if 'date' in d]
            dates_ok = all(d >= '2026-03-01' and d <= '2026-03-24' for d in dates)
            candle_count_ok = len(candle_data) >= 10  # We expect ~20 trading days
            
            # Check interval_unit = day is recorded somewhere in report
            found_iu, iu_val = search_recursive(report, 'interval_unit')
            interval_day_ok = found_iu and iu_val == 'day'
            
            # Verify first candle: 2026-03-01 open=47.10, close=47.55
            first_candle = candle_data[0]
            first_date_ok = first_candle.get('date') == '2026-03-01'
            first_close_ok = abs(float(first_candle.get('close', 0)) - 47.55) < 0.01
            
            # Verify last candle: 2026-03-24 close=54.30
            last_candle = candle_data[-1]
            last_date_ok = last_candle.get('date') == '2026-03-24'
            last_close_ok = abs(float(last_candle.get('close', 0)) - 54.30) < 0.01
        else:
            first_date_ok = False
            first_close_ok = False
            last_date_ok = False
            last_close_ok = False
        
        candle_passed = (has_candle and dates_ok and interval_day_ok and 
                         candle_count_ok and first_date_ok and last_date_ok)
        checks.append({
            "name": "candlestick_data_present",
            "passed": candle_passed,
            "detail": (
                f"has_candle_data={has_candle}, "
                f"date_range_ok={dates_ok}, "
                f"interval_unit_day={interval_day_ok}, "
                f"count_ge_10={candle_count_ok}({len(candle_data) if candle_data else 0}), "
                f"first_date={'2026-03-01✓' if first_date_ok else 'WRONG'}, "
                f"first_close={'47.55✓' if first_close_ok else 'WRONG'}, "
                f"last_date={'2026-03-24✓' if last_date_ok else 'WRONG'}, "
                f"last_close={'54.30✓' if last_close_ok else 'WRONG'}"
            )
        })
    except Exception as e:
        checks.append({"name": "candlestick_data_present", "passed": False, "detail": f"Error: {e}"})

    # ── Check 4: Stock code 02318.HK is referenced ───────────────────────────
    try:
        code_present = '02318.HK' in json.dumps(report)
        checks.append({
            "name": "correct_stock_code",
            "passed": code_present,
            "detail": f"02318.HK {'found' if code_present else 'NOT found'} in report"
        })
    except Exception as e:
        checks.append({"name": "correct_stock_code", "passed": False, "detail": f"Error: {e}"})

    # ── Check 5: All three sub-skill data sections present ────────────────────
    try:
        # hk-view: must have sector + market_cap
        # hk-valuatnanalyd: must have pe_ttm + dividend_yield
        # hk-candlesticks: must have OHLCV list
        all_three_passed = (
            checks[2]["passed"] and  # view
            checks[3]["passed"] and  # valuation
            checks[4]["passed"]      # candlesticks
        )
        checks.append({
            "name": "all_three_subskills_data_combined",
            "passed": all_three_passed,
            "detail": (
                f"hk_view={'✓' if checks[2]['passed'] else '✗'}, "
                f"valuation={'✓' if checks[3]['passed'] else '✗'}, "
                f"candlesticks={'✓' if checks[4]['passed'] else '✗'}"
            )
        })
    except Exception as e:
        checks.append({"name": "all_three_subskills_data_combined", "passed": False, "detail": f"Error: {e}"})

    # ── Final scoring ─────────────────────────────────────────────────────────
    weights = {
        "file_exists": 0.05,
        "json_parseable": 0.05,
        "hk_view_data_present": 0.25,
        "valuation_data_present": 0.25,
        "candlestick_data_present": 0.30,
        "correct_stock_code": 0.05,
        "all_three_subskills_data_combined": 0.05,
    }
    
    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w
    
    overall_passed = all(c["passed"] for c in checks)
    
    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == '__main__':
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))