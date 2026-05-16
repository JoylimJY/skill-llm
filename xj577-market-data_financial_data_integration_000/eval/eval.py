import sys
import json
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # --- Find the output file ---
    candidates = list(workspace.rglob("morning_briefing.json"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "morning_briefing.json not found anywhere in workspace."}]
        }

    briefing_path = candidates[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {briefing_path}"})

    try:
        with open(briefing_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
    checks.append({"name": "file_parseable", "passed": True, "detail": "JSON is valid."})

    # --- CHECK 1: get_stock_price was called with correct parameters ---
    # Must use ticker='NVDA', timeframe='1wk', and period1/period2 covering ~3 months (Q1 2024 or similar)
    equity_ok = False
    equity_ticker_ok = False
    equity_timeframe_ok = False
    equity_dates_ok = False
    equity_has_data = False
    equity_detail = "No equity_data or stock section found."

    # Look for equity/stock section in the JSON (flexible key search)
    equity_section = None
    for key in ['equity_data', 'stock_data', 'nvda', 'NVDA', 'equities', 'stock']:
        if key in data:
            equity_section = data[key]
            break
    # Also search nested
    if equity_section is None:
        for v in data.values():
            if isinstance(v, dict):
                for key in ['equity_data', 'stock_data', 'nvda', 'NVDA', 'ticker', 'timeframe']:
                    if key in v:
                        equity_section = v
                        break
            if equity_section:
                break

    if equity_section is not None:
        section_str = json.dumps(equity_section).lower()
        raw_str = json.dumps(data).lower()

        # Check ticker = NVDA
        if 'nvda' in section_str or 'nvda' in raw_str:
            equity_ticker_ok = True

        # Check timeframe = '1wk' (the skill only supports '1d', '1wk', '1mo')
        if '1wk' in section_str or '1wk' in raw_str:
            equity_timeframe_ok = True

        # Check period covers roughly 3 months
        # Look for period1 in a reasonable 3-month window (2024)
        import re
        dates_found = re.findall(r'202[34]-\d{2}-\d{2}', json.dumps(data))
        if len(dates_found) >= 2:
            equity_dates_ok = True

        # Check data records exist
        records = None
        for rkey in ['data', 'records', 'ohlcv', 'bars', 'candles']:
            if rkey in equity_section:
                records = equity_section[rkey]
                break
        if records and isinstance(records, list) and len(records) > 0:
            equity_has_data = True

        equity_ok = equity_ticker_ok and equity_timeframe_ok
        equity_detail = (
            f"ticker_ok={equity_ticker_ok}, timeframe_1wk={equity_timeframe_ok}, "
            f"dates_present={equity_dates_ok}, has_records={equity_has_data}"
        )
    
    checks.append({
        "name": "equity_data_correct_params",
        "passed": equity_ok,
        "detail": equity_detail
    })
    checks.append({
        "name": "equity_data_has_records",
        "passed": equity_has_data,
        "detail": f"OHLCV records present: {equity_has_data}"
    })

    # --- CHECK 2: get_crypto_price was called with token='ethereum' (NOT 'ETH') and currency='eur' ---
    crypto_token_ok = False
    crypto_currency_ok = False
    crypto_price_ok = False
    crypto_detail = "No crypto section found."

    raw_str = json.dumps(data).lower()

    # Check that 'ethereum' appears (not just 'eth' standalone as a ticker)
    if 'ethereum' in raw_str:
        crypto_token_ok = True

    # Check that currency is EUR
    if 'eur' in raw_str:
        crypto_currency_ok = True

    # Check that a numeric price for ETH in EUR is present (should be ~2944 = 3200 * 0.92)
    import re
    numbers = re.findall(r'\b2[89]\d{2}\.?\d*\b|\b3[0-3]\d{2}\.?\d*\b', json.dumps(data))
    if numbers:
        crypto_price_ok = True

    crypto_ok = crypto_token_ok and crypto_currency_ok
    crypto_detail = f"token='ethereum'_found={crypto_token_ok}, currency='eur'_found={crypto_currency_ok}, price_in_range={crypto_price_ok}"

    checks.append({
        "name": "crypto_correct_token_name",
        "passed": crypto_token_ok,
        "detail": f"'ethereum' (full name, not 'ETH') found in output: {crypto_token_ok}"
    })
    checks.append({
        "name": "crypto_correct_currency_eur",
        "passed": crypto_currency_ok,
        "detail": f"EUR currency found: {crypto_currency_ok}"
    })
    checks.append({
        "name": "crypto_price_present",
        "passed": crypto_price_ok,
        "detail": f"Numeric ETH/EUR price in expected range found: {crypto_price_ok}"
    })

    # --- CHECK 3: fetch_economic_calendar called with importance='High' (exact casing) and currencies='USD' ---
    calendar_ok = False
    calendar_importance_ok = False
    calendar_currency_ok = False
    calendar_has_events = False

    # Look for calendar/macro section
    calendar_section = None
    for key in ['macro_events', 'economic_calendar', 'calendar', 'events', 'macro']:
        if key in data:
            calendar_section = data[key]
            break

    if calendar_section is not None:
        cal_str = json.dumps(calendar_section)

        # Check importance='High' was used (response will echo it back)
        if 'High' in cal_str:
            calendar_importance_ok = True

        # Check USD filter was applied
        if 'USD' in cal_str or 'usd' in cal_str.lower():
            calendar_currency_ok = True

        # Check events are present
        events = None
        if isinstance(calendar_section, dict):
            for ekey in ['events', 'data', 'items']:
                if ekey in calendar_section:
                    events = calendar_section[ekey]
                    break
        elif isinstance(calendar_section, list):
            events = calendar_section

        if events and isinstance(events, list) and len(events) > 0:
            calendar_has_events = True
            # Verify events are USD and High importance
            usd_high_count = sum(
                1 for e in events
                if isinstance(e, dict)
                and e.get('currency', '').upper() == 'USD'
                and e.get('importance', '') == 'High'
            )
            if usd_high_count > 0:
                calendar_importance_ok = True
                calendar_currency_ok = True

    calendar_ok = calendar_importance_ok and calendar_currency_ok and calendar_has_events
    checks.append({
        "name": "calendar_correct_importance_High",
        "passed": calendar_importance_ok,
        "detail": f"importance='High' (exact casing) confirmed via events: {calendar_importance_ok}"
    })
    checks.append({
        "name": "calendar_correct_currency_USD",
        "passed": calendar_currency_ok,
        "detail": f"USD currency filter applied: {calendar_currency_ok}"
    })
    checks.append({
        "name": "calendar_has_events",
        "passed": calendar_has_events,
        "detail": f"Economic events list present and non-empty: {calendar_has_events}"
    })

    # --- CHECK 4: All three data sources are present in one unified file ---
    all_present = equity_ok and crypto_ok and calendar_ok
    checks.append({
        "name": "unified_briefing_all_sources",
        "passed": all_present,
        "detail": f"All three data sources (NVDA weekly, ETH/EUR, USD High calendar) unified: {all_present}"
    })

    # --- Scoring ---
    passed_checks = [c for c in checks if c['passed']]
    total_checks = len(checks)
    score = round(len(passed_checks) / total_checks, 3)
    overall_passed = all_present and equity_has_data and crypto_price_ok

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))