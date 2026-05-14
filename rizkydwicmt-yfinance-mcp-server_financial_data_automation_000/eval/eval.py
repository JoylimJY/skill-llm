#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
checks = []

def find_report(workspace):
    """Find healthcare_value_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("healthcare_value_report.json"))
    return matches[0] if matches else None

def load_tool_calls(workspace):
    log_path = Path(workspace) / "logs" / "tool_calls.jsonl"
    calls = []
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        calls.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return calls

# ---- Check 1: Report file exists ----
report_path = find_report(workspace)
check1 = {
    "name": "report_file_exists",
    "passed": report_path is not None,
    "detail": f"Found at {report_path}" if report_path else "healthcare_value_report.json not found anywhere in workspace"
}
checks.append(check1)

report_data = None
if report_path:
    try:
        with open(report_path) as f:
            report_data = json.load(f)
    except Exception as e:
        report_data = None
        checks.append({
            "name": "report_json_valid",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })

# ---- Check 2: Report has required top-level sections ----
required_sections = ["screened_stocks", "financials", "comparison"]
if report_data is not None:
    missing = [s for s in required_sections if s not in report_data]
    checks.append({
        "name": "report_has_required_sections",
        "passed": len(missing) == 0,
        "detail": f"Missing sections: {missing}" if missing else f"All required sections present: {required_sections}"
    })
else:
    checks.append({
        "name": "report_has_required_sections",
        "passed": False,
        "detail": "Cannot check sections — report not loaded"
    })

# ---- Check 3: Screened stocks includes expected symbols ----
expected_symbols = {"JNJ", "ABT", "BMY"}
if report_data is not None:
    try:
        screened = report_data.get("screened_stocks", [])
        found_symbols = set()
        if isinstance(screened, list):
            for item in screened:
                if isinstance(item, dict):
                    sym = item.get("symbol", "")
                    if sym:
                        found_symbols.add(sym)
                elif isinstance(item, str):
                    found_symbols.add(item)
        elif isinstance(screened, dict):
            found_symbols = set(screened.keys())
        
        has_all = expected_symbols.issubset(found_symbols)
        checks.append({
            "name": "screened_stocks_correct_symbols",
            "passed": has_all,
            "detail": f"Found symbols: {found_symbols}, expected: {expected_symbols}"
        })
    except Exception as e:
        checks.append({
            "name": "screened_stocks_correct_symbols",
            "passed": False,
            "detail": f"Error checking screened stocks: {e}"
        })
else:
    checks.append({
        "name": "screened_stocks_correct_symbols",
        "passed": False,
        "detail": "Report not loaded"
    })

# ---- Check 4: Financials present for all screened symbols with all 3 statement types ----
if report_data is not None:
    try:
        financials = report_data.get("financials", {})
        all_financials_ok = True
        detail_parts = []
        
        for sym in expected_symbols:
            sym_fin = None
            if isinstance(financials, dict):
                sym_fin = financials.get(sym)
            
            if sym_fin is None:
                all_financials_ok = False
                detail_parts.append(f"{sym}: missing")
                continue
            
            # Check that all three statement types are present
            has_income = "income" in sym_fin
            has_balance = "balance_sheet" in sym_fin
            has_cashflow = "cash_flow" in sym_fin
            
            if has_income and has_balance and has_cashflow:
                detail_parts.append(f"{sym}: all 3 statements present")
            else:
                all_financials_ok = False
                missing_stmts = []
                if not has_income: missing_stmts.append("income")
                if not has_balance: missing_stmts.append("balance_sheet")
                if not has_cashflow: missing_stmts.append("cash_flow")
                detail_parts.append(f"{sym}: missing {missing_stmts}")
        
        checks.append({
            "name": "financials_all_statements_all_symbols",
            "passed": all_financials_ok,
            "detail": "; ".join(detail_parts)
        })
    except Exception as e:
        checks.append({
            "name": "financials_all_statements_all_symbols",
            "passed": False,
            "detail": f"Error: {e}"
        })
else:
    checks.append({
        "name": "financials_all_statements_all_symbols",
        "passed": False,
        "detail": "Report not loaded"
    })

# ---- Check 5: Comparison section has data for all 3 symbols ----
if report_data is not None:
    try:
        comparison = report_data.get("comparison", {})
        comp_symbols = set()
        
        if isinstance(comparison, list):
            for item in comparison:
                if isinstance(item, dict):
                    sym = item.get("symbol", "")
                    if sym:
                        comp_symbols.add(sym)
        elif isinstance(comparison, dict):
            comp_symbols = set(comparison.keys())
        
        comp_ok = expected_symbols.issubset(comp_symbols)
        checks.append({
            "name": "comparison_includes_all_symbols",
            "passed": comp_ok,
            "detail": f"Comparison symbols: {comp_symbols}, expected: {expected_symbols}"
        })
    except Exception as e:
        checks.append({
            "name": "comparison_includes_all_symbols",
            "passed": False,
            "detail": f"Error: {e}"
        })
else:
    checks.append({
        "name": "comparison_includes_all_symbols",
        "passed": False,
        "detail": "Report not loaded"
    })

# ---- Check 6: Tool calls log — screen_stocks was called with correct params ----
tool_calls = load_tool_calls(workspace)

screen_calls = [c for c in tool_calls if c.get("tool") == "tool_screen_stocks"]
screen_call_ok = False
screen_detail = "tool_screen_stocks was never called"

if screen_calls:
    for call in screen_calls:
        params = call.get("params", {})
        sector_ok = params.get("sector") == "Healthcare"
        # min_dividend_yield must be decimal (< 1.0), not percentage (e.g. 2.5)
        div_yield = params.get("min_dividend_yield")
        div_yield_ok = div_yield is not None and isinstance(div_yield, (int, float)) and div_yield < 1.0
        # min_market_cap must be a large integer (billions)
        mktcap = params.get("min_market_cap")
        mktcap_ok = mktcap is not None and isinstance(mktcap, (int, float)) and mktcap >= 1_000_000_000
        # max_pe_ratio should be present
        pe = params.get("max_pe_ratio")
        pe_ok = pe is not None
        
        if sector_ok and div_yield_ok and mktcap_ok and pe_ok:
            screen_call_ok = True
            screen_detail = (
                f"Valid screen call: sector={params.get('sector')}, "
                f"min_dividend_yield={div_yield} (decimal ✓), "
                f"min_market_cap={mktcap}, max_pe_ratio={pe}"
            )
            break
        else:
            issues = []
            if not sector_ok: issues.append(f"sector={params.get('sector')} (expected 'Healthcare')")
            if not div_yield_ok: issues.append(f"min_dividend_yield={div_yield} (must be decimal < 1.0, e.g. 0.02)")
            if not mktcap_ok: issues.append(f"min_market_cap={mktcap} (must be >= 1B)")
            if not pe_ok: issues.append("max_pe_ratio missing")
            screen_detail = f"Screen call found but issues: {'; '.join(issues)}"

checks.append({
    "name": "screen_stocks_correct_params_decimal_dividend",
    "passed": screen_call_ok,
    "detail": screen_detail
})

# ---- Check 7: tool_get_financials called with statement_type=all and quarterly=true ----
fin_calls = [c for c in tool_calls if c.get("tool") == "tool_get_financials"]
fin_all_quarterly_ok = False
fin_detail = "tool_get_financials never called with statement_type=all and quarterly=true"

symbols_with_all_quarterly = set()
for call in fin_calls:
    params = call.get("params", {})
    stmt = params.get("statement_type")
    quarterly = params.get("quarterly")
    sym = params.get("symbol", "")
    if stmt == "all" and quarterly is True:
        symbols_with_all_quarterly.add(sym)

if expected_symbols.issubset(symbols_with_all_quarterly):
    fin_all_quarterly_ok = True
    fin_detail = f"All symbols called with statement_type=all, quarterly=true: {symbols_with_all_quarterly}"
elif symbols_with_all_quarterly:
    fin_detail = f"Only these symbols had statement_type=all + quarterly=true: {symbols_with_all_quarterly}, missing: {expected_symbols - symbols_with_all_quarterly}"
else:
    fin_detail = "No tool_get_financials calls used statement_type='all' with quarterly=true"

checks.append({
    "name": "financials_called_with_all_and_quarterly",
    "passed": fin_all_quarterly_ok,
    "detail": fin_detail
})

# ---- Check 8: tool_compare_stocks called with all 3 symbols ----
compare_calls = [c for c in tool_calls if c.get("tool") == "tool_compare_stocks"]
compare_ok = False
compare_detail = "tool_compare_stocks was never called"

if compare_calls:
    for call in compare_calls:
        params = call.get("params", {})
        symbols_param = params.get("symbols", "")
        if isinstance(symbols_param, str):
            # Accept comma or space separated
            import re
            found = set(re.split(r'[,\s]+', symbols_param.strip()))
            found = {s for s in found if s}
            if expected_symbols.issubset(found):
                compare_ok = True
                compare_detail = f"compare_stocks called with symbols: {symbols_param!r}"
                break
            else:
                compare_detail = f"compare_stocks called but symbols {found} don't include all of {expected_symbols}"

checks.append({
    "name": "compare_stocks_called_with_all_symbols",
    "passed": compare_ok,
    "detail": compare_detail
})

# ---- Scoring ----
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = all(c["passed"] for c in checks)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))