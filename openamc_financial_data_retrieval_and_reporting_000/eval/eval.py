#!/usr/bin/env python3
"""
Evaluation script for the Global Macro Morning Brief task.
Checks that the agent correctly:
1. Used equity_price_historical with provider=akshare for A-share 600036
2. Used economy_fred_series with provider=fred and symbol=DFEDTARU
3. Used currency_price_historical with symbol=EURUSD=X and provider=yfinance
4. Wrote a valid morning_brief.json with all required fields
"""

import sys
import json
import os
from pathlib import Path

def main():
    workspace = sys.argv[1] if len(args := sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0
    
    # --- Find morning_brief.json ---
    found_files = list(Path(workspace).rglob("morning_brief.json"))
    # Exclude the template/archive files that are part of setup
    found_files = [f for f in found_files if "archive" not in str(f) and "drafts" not in str(f)]
    
    if not found_files:
        score = add_check("file_exists", False, "morning_brief.json not found in workspace (excluding archive/drafts directories)")
        final = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(final, indent=2))
        return
    
    # Use the first valid file found
    brief_path = found_files[0]
    score = add_check("file_exists", True, f"Found morning_brief.json at {brief_path}", 0.5)
    
    # --- Load and parse JSON ---
    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except Exception as e:
        score += add_check("file_parseable", False, f"Failed to parse morning_brief.json as JSON: {e}", 1.0)
        final = {"passed": False, "score": score / 6.0, "checks": checks}
        print(json.dumps(final, indent=2))
        return
    
    score += add_check("file_parseable", True, "morning_brief.json is valid JSON", 0.5)
    
    # --- Convert to string for full-text search ---
    brief_str = json.dumps(brief).lower()
    brief_str_orig = json.dumps(brief)
    
    # === CHECK 1: A-share data (600036 with akshare) ===
    
    # Check that 600036 symbol is present
    has_600036 = "600036" in brief_str_orig
    score += add_check(
        "astock_symbol_present",
        has_600036,
        "Symbol '600036' (CMB A-share) found in output" if has_600036 else "Symbol '600036' not found in morning_brief.json"
    )
    
    # Check that akshare provider was used (not yfinance for A-shares)
    has_akshare = "akshare" in brief_str
    # Check that there's actual price data for 600036 (data array not empty, no error)
    astock_data_valid = False
    astock_error = ""
    try:
        # Search recursively for data associated with 600036
        brief_raw = json.dumps(brief)
        # The data should contain close prices and dates
        if "akshare" in brief_raw.lower() and "600036" in brief_raw:
            # Check no error field associated with astock
            # Look for actual numeric close price data
            import re
            # Find any object containing 600036 and akshare
            if re.search(r'600036', brief_raw) and re.search(r'akshare', brief_raw.lower()):
                # Check that data isn't empty/null and no provider error
                if '"data": null' not in brief_raw and '"data":null' not in brief_raw:
                    # Make sure it's not an error response about wrong provider
                    if 'not supported for a-share' not in brief_raw.lower():
                        astock_data_valid = True
    except Exception as e:
        astock_error = str(e)
    
    score += add_check(
        "astock_akshare_provider_correct",
        has_akshare and astock_data_valid,
        ("A-share 600036 queried with akshare provider and returned valid data" 
         if (has_akshare and astock_data_valid) 
         else f"A-share data issue: akshare_present={has_akshare}, data_valid={astock_data_valid}, error={astock_error}")
    )
    
    # === CHECK 2: FRED DFEDTARU data ===
    has_dfedtaru = "DFEDTARU" in brief_str_orig or "dfedtaru" in brief_str
    has_fred = "fred" in brief_str
    
    fred_data_valid = False
    fred_error = ""
    try:
        if has_dfedtaru and has_fred:
            brief_raw = json.dumps(brief)
            # Check no error and data present
            if '"data": null' not in brief_raw and '"data":null' not in brief_raw:
                if 'not valid for fred' not in brief_raw.lower():
                    # Check that actual rate values exist (4.5 is expected)
                    if "4.5" in brief_raw or "4.50" in brief_raw:
                        fred_data_valid = True
    except Exception as e:
        fred_error = str(e)
    
    score += add_check(
        "fred_dfedtaru_symbol_present",
        has_dfedtaru,
        "FRED series 'DFEDTARU' found in output" if has_dfedtaru else "FRED series 'DFEDTARU' not found in morning_brief.json"
    )
    
    score += add_check(
        "fred_dfedtaru_data_valid",
        fred_data_valid,
        ("DFEDTARU series queried via economy_fred_series with fred provider, valid data present"
         if fred_data_valid
         else f"FRED data issue: dfedtaru_present={has_dfedtaru}, fred_present={has_fred}, data_valid={fred_data_valid}, error={fred_error}")
    )
    
    # === CHECK 3: Forex EURUSD=X data ===
    # The proprietary trap: must use EURUSD=X format, NOT EUR/USD or EURUSD
    has_eurusd_x = "EURUSD=X" in brief_str_orig
    has_eurusd_wrong = ("eur/usd" in brief_str and "EURUSD=X" not in brief_str_orig)
    
    forex_data_valid = False
    forex_error = ""
    try:
        brief_raw = json.dumps(brief)
        if "EURUSD=X" in brief_raw and "yfinance" in brief_raw.lower():
            if '"data": null' not in brief_raw and '"data":null' not in brief_raw:
                if 'invalid forex symbol' not in brief_raw.lower():
                    # Data should contain forex close prices around 1.08x
                    if "1.08" in brief_raw or "1.09" in brief_raw or "forex" in brief_raw.lower() or "FOREX" in brief_raw:
                        forex_data_valid = True
    except Exception as e:
        forex_error = str(e)
    
    score += add_check(
        "forex_symbol_format_correct",
        has_eurusd_x,
        ("Forex symbol 'EURUSD=X' (correct yfinance format) found in output"
         if has_eurusd_x
         else f"Forex symbol 'EURUSD=X' not found. Used wrong format? has_eur_usd_slash={has_eurusd_wrong}. Output snippet: {brief_str_orig[:300]}")
    )
    
    score += add_check(
        "forex_eurusd_data_valid",
        forex_data_valid,
        ("EURUSD=X forex data queried with yfinance provider and valid data returned"
         if forex_data_valid
         else f"Forex data issue: eurusd_x_present={has_eurusd_x}, data_valid={forex_data_valid}, error={forex_error}")
    )
    
    # === CHECK 4: Commands used are documented ===
    # The brief must include the actual mcp commands used
    has_commands = ("mcp" in brief_str and "openamc" in brief_str)
    score += add_check(
        "mcp_commands_recorded",
        has_commands,
        ("mcp call openamc commands recorded in output"
         if has_commands
         else "No mcp/openamc command references found in morning_brief.json")
    )
    
    # === CHECK 5: Timestamp present ===
    has_timestamp = any(k in brief_str for k in ["timestamp", "generated_at", "report_time", "date", "time"])
    score += add_check(
        "timestamp_present",
        has_timestamp,
        "Report timestamp/date present in output" if has_timestamp else "No timestamp field found in morning_brief.json"
    )
    
    # === TRAP CHECK: Verify agent did NOT use yfinance for A-share ===
    # If yfinance was used for 600036, the mock returns an error string
    yfinance_for_astock_error = ("provider 'yfinance' is not supported for a-share" in brief_str)
    score += add_check(
        "no_wrong_provider_for_astock",
        not yfinance_for_astock_error,
        ("Correctly avoided using yfinance for A-share query"
         if not yfinance_for_astock_error
         else "FAILED: Used yfinance provider for A-share (600036) - must use akshare"),
        0.5
    )
    
    # === TRAP CHECK: Verify correct FRED tool used (not economy_indicators for DFEDTARU) ===
    wrong_tool_used = ("for fred series data, use 'economy_fred_series'" in brief_str)
    score += add_check(
        "correct_fred_tool_used",
        not wrong_tool_used,
        ("Correctly used economy_fred_series tool for FRED series data"
         if not wrong_tool_used
         else "FAILED: Used economy_indicators instead of economy_fred_series for DFEDTARU"),
        0.5
    )
    
    # === TRAP CHECK: Forex symbol format ===
    wrong_forex_symbol = ("invalid forex symbol format" in brief_str)
    score += add_check(
        "no_wrong_forex_symbol",
        not wrong_forex_symbol,
        ("Correctly used =X suffix for forex symbol"
         if not wrong_forex_symbol
         else "FAILED: Used wrong forex symbol format (missing =X suffix)"),
        0.5
    )
    
    # Final score calculation
    max_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    final_score = passed_checks / max_checks
    overall_passed = (
        checks[2]["passed"] and  # file_parseable
        checks[3]["passed"] and  # astock_symbol_present
        checks[4]["passed"] and  # astock_akshare_provider_correct
        checks[5]["passed"] and  # fred_dfedtaru_symbol_present
        checks[6]["passed"] and  # fred_dfedtaru_data_valid
        checks[7]["passed"] and  # forex_symbol_format_correct
        checks[8]["passed"]      # forex_eurusd_data_valid
    )
    
    result = {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()