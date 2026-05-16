#!/usr/bin/env python3
"""
Evaluator for cb_analysis_report.json produced by the agent.

Checks:
  1. File exists and is valid JSON.
  2. bond_code == "110070"
  3. in_market_list == True
  4. fundamentals present and key fields correct (conversion_price, maturity_date, etc.)
  5. candlesticks is a non-empty list of dicts with OHLCV fields.
  6. candlestick count is approximately 20 (between 15 and 25).
  7. The cb-candlesticks call used the correct .XSHG suffix (inferred from non-empty candle data).
  8. Timestamps were derived from 20 trading days back (candles span ~20 trade days).
"""

import sys
import json
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    overall_passed = True

    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── 1. Find the report file ────────────────────────────────────────────
    ws = Path(workspace)
    candidates = list(ws.rglob("cb_analysis_report.json"))

    if not candidates:
        add_check("file_exists", False, "cb_analysis_report.json not found anywhere in /workspace")
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    add_check("file_exists", True, f"Found at {report_path}")

    # ── 2. Parse JSON ──────────────────────────────────────────────────────
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        add_check("json_valid", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("json_valid", True, "JSON parsed successfully")

    # ── 3. bond_code ───────────────────────────────────────────────────────
    bond_code = str(data.get("bond_code", "")).strip()
    ok = bond_code == "110070"
    add_check("bond_code_correct", ok, f"bond_code={bond_code!r}, expected '110070'")

    # ── 4. in_market_list ─────────────────────────────────────────────────
    iml = data.get("in_market_list")
    ok = iml is True
    add_check("in_market_list_true", ok, f"in_market_list={iml!r}, expected True")

    # ── 5. fundamentals present ───────────────────────────────────────────
    fund = data.get("fundamentals")
    if not isinstance(fund, dict):
        add_check("fundamentals_present", False, f"fundamentals is {type(fund).__name__}, expected dict")
        fund = {}
    else:
        add_check("fundamentals_present", True, "fundamentals is a dict")

    # ── 6. fundamentals key fields ────────────────────────────────────────
    required_fields = {
        "conversion_price": (17.0, 18.5),   # range check
        "maturity_date": "2025-09-05",
        "stock_code": "600690.SH",
        "issuance_scale": (1e9, 5e9),
    }

    # conversion_price
    try:
        cp = float(fund.get("conversion_price", 0))
        ok = 17.0 <= cp <= 18.5
        add_check("fund_conversion_price", ok, f"conversion_price={cp}, expected ~17.59")
    except Exception as e:
        add_check("fund_conversion_price", False, f"Error reading conversion_price: {e}")

    # maturity_date
    md = str(fund.get("maturity_date", "")).strip()
    ok = md == "2025-09-05"
    add_check("fund_maturity_date", ok, f"maturity_date={md!r}, expected '2025-09-05'")

    # stock_code
    sc = str(fund.get("stock_code", "")).strip()
    ok = sc == "600690.SH"
    add_check("fund_stock_code", ok, f"stock_code={sc!r}, expected '600690.SH'")

    # issuance_scale
    try:
        isc = float(fund.get("issuance_scale", 0))
        ok = 1e9 <= isc <= 5e9
        add_check("fund_issuance_scale", ok, f"issuance_scale={isc:.0f}, expected ~2300000000")
    except Exception as e:
        add_check("fund_issuance_scale", False, f"Error reading issuance_scale: {e}")

    # short_name / full_name presence
    sn = fund.get("short_name", "")
    fn = fund.get("full_name", "")
    add_check("fund_names_present", bool(sn) and bool(fn),
              f"short_name={sn!r}, full_name={fn!r}")

    # conversion_value and premium_rate presence
    cv = fund.get("conversion_value")
    pr = fund.get("conversion_premium_rate")
    add_check("fund_conv_value_premium", cv is not None and pr is not None,
              f"conversion_value={cv}, conversion_premium_rate={pr}")

    # ── 7. candlesticks array ─────────────────────────────────────────────
    candles = data.get("candlesticks")
    if not isinstance(candles, list):
        add_check("candlesticks_is_list", False, f"candlesticks is {type(candles).__name__}, expected list")
        candles = []
    else:
        add_check("candlesticks_is_list", True, f"candlesticks is a list with {len(candles)} entries")

    # ── 8. Candlestick count (should be ~20 trading days) ─────────────────
    n = len(candles)
    ok = 15 <= n <= 25
    add_check("candlesticks_count_approx_20", ok,
              f"Got {n} candles, expected 15-25 (approx 20 trading days)")

    # ── 9. Candlestick structure ───────────────────────────────────────────
    if candles:
        sample = candles[0]
        required_candle_fields = {"open", "high", "low", "close", "volume"}
        missing = required_candle_fields - set(sample.keys())
        ok = len(missing) == 0
        add_check("candlestick_ohlcv_fields", ok,
                  f"Sample candle keys: {set(sample.keys())}. Missing: {missing}")

        # All closes should be positive numbers
        try:
            closes = [float(c["close"]) for c in candles]
            all_positive = all(v > 0 for v in closes)
            add_check("candlestick_closes_positive", all_positive,
                      f"Min close={min(closes):.2f}, Max close={max(closes):.2f}")
        except Exception as e:
            add_check("candlestick_closes_positive", False, f"Error reading closes: {e}")
    else:
        add_check("candlestick_ohlcv_fields", False, "No candles to inspect")
        add_check("candlestick_closes_positive", False, "No candles to inspect")

    # ── 10. Correct symbol suffix used (XSHG, not SH) ─────────────────────
    # We infer this by checking that candles are non-empty: mock returns 400 for wrong suffix
    correct_suffix_inferred = len(candles) >= 15
    add_check("used_correct_xshg_suffix",
              correct_suffix_inferred,
              "Inferred from non-empty candlestick array (mock returns empty for .SH suffix)")

    # ── Score ─────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: eval.py <workspace_dir>"}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))