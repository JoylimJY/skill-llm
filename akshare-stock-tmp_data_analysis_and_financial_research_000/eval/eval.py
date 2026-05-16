#!/usr/bin/env python3
"""
Evaluation script for the stock screening task.
Usage: python eval_script.py /workspace
"""
import sys
import json
import subprocess
import traceback
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    passed_all = True

    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── Check 1: run_screening.py exists ──────────────────────────────────────
    script_path = None
    candidates = list(workspace.rglob("run_screening.py"))
    if candidates:
        script_path = candidates[0]
        add_check("run_screening.py exists", True, f"Found at {script_path}")
    else:
        add_check("run_screening.py exists", False, "File not found anywhere in workspace")
        # Cannot proceed further
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 2: Script uses qfq adjust parameter ──────────────────────────────
    try:
        script_content = script_path.read_text()
        uses_qfq = "qfq" in script_content
        add_check(
            "Script uses adjust='qfq' (前复权)",
            uses_qfq,
            "Found 'qfq' in script" if uses_qfq else "Missing 'qfq' — script will fail against mock akshare"
        )
    except Exception as e:
        add_check("Script uses adjust='qfq' (前复权)", False, f"Error reading script: {e}")

    # ── Check 3: Script uses correct financial indicator ──────────────────────
    try:
        uses_correct_indicator = "按报告期" in script_content
        uses_financial_fn = "stock_financial_abstract_ths" in script_content
        ok = uses_correct_indicator and uses_financial_fn
        add_check(
            "Script uses stock_financial_abstract_ths with '按报告期'",
            ok,
            f"stock_financial_abstract_ths present: {uses_financial_fn}, '按报告期' present: {uses_correct_indicator}"
        )
    except Exception as e:
        add_check("Script uses correct financial indicator", False, str(e))

    # ── Check 4: Execute the script ────────────────────────────────────────────
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(script_path.parent)
        )
        exec_ok = result.returncode == 0
        detail = f"returncode={result.returncode}"
        if result.stderr:
            detail += f"\nSTDERR: {result.stderr[:800]}"
        if result.stdout:
            detail += f"\nSTDOUT: {result.stdout[:400]}"
        add_check("Script executes without errors", exec_ok, detail)
        if not exec_ok:
            return {"passed": False, "score": max(0, len([c for c in checks if c["passed"]]) / 8), "checks": checks}
    except subprocess.TimeoutExpired:
        add_check("Script executes without errors", False, "Execution timed out (60s)")
        return {"passed": False, "score": 0.1, "checks": checks}
    except Exception as e:
        add_check("Script executes without errors", False, f"Exception: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 5: screening_result.json exists ─────────────────────────────────
    result_path = None
    result_candidates = list(workspace.rglob("screening_result.json"))
    if result_candidates:
        result_path = result_candidates[0]
        add_check("screening_result.json created", True, f"Found at {result_path}")
    else:
        add_check("screening_result.json created", False, "screening_result.json not found")
        return {"passed": False, "score": 3/8, "checks": checks}

    # ── Check 6: JSON structure is correct ────────────────────────────────────
    try:
        data = json.loads(result_path.read_text())
        has_stocks_key = "stocks" in data
        stocks_list = data.get("stocks", [])
        is_list = isinstance(stocks_list, list)
        has_three = len(stocks_list) == 3 if is_list else False

        structure_ok = has_stocks_key and is_list and has_three
        add_check(
            "JSON has correct structure (top-level 'stocks' list with 3 entries)",
            structure_ok,
            f"has_stocks_key={has_stocks_key}, is_list={is_list}, count={len(stocks_list) if is_list else 'N/A'}"
        )
        if not structure_ok:
            return {"passed": False, "score": 4/8, "checks": checks}
    except Exception as e:
        add_check("JSON has correct structure", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 3/8, "checks": checks}

    # ── Check 7: Required fields present and correctly typed ──────────────────
    required_fields = ["symbol", "last_date", "last_close", "ma20", "price_vs_ma20", "net_profit", "roe", "gross_margin"]
    required_symbols = {"000001", "600519", "300750"}

    try:
        field_errors = []
        symbols_found = set()
        for entry in stocks_list:
            sym = entry.get("symbol", "MISSING")
            symbols_found.add(sym)
            for field in required_fields:
                if field not in entry:
                    field_errors.append(f"{sym}: missing field '{field}'")
            # Type checks
            if "last_close" in entry and not isinstance(entry["last_close"], (int, float)):
                field_errors.append(f"{sym}: last_close must be numeric")
            if "ma20" in entry and not isinstance(entry["ma20"], (int, float)):
                field_errors.append(f"{sym}: ma20 must be numeric")
            if "price_vs_ma20" in entry and entry["price_vs_ma20"] not in ("above", "below"):
                field_errors.append(f"{sym}: price_vs_ma20 must be 'above' or 'below', got {entry['price_vs_ma20']!r}")
            if "last_date" in entry:
                # Must match YYYY-MM-DD
                import re
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(entry["last_date"])):
                    field_errors.append(f"{sym}: last_date format must be YYYY-MM-DD, got {entry['last_date']!r}")
        
        missing_symbols = required_symbols - symbols_found
        if missing_symbols:
            field_errors.append(f"Missing symbols: {missing_symbols}")

        fields_ok = len(field_errors) == 0
        add_check(
            "All required fields present with correct types and values",
            fields_ok,
            "All fields valid" if fields_ok else "; ".join(field_errors[:5])
        )
    except Exception as e:
        add_check("All required fields present", False, f"Exception: {traceback.format_exc()}")
        fields_ok = False

    # ── Check 8: Numeric correctness — MA20 computed correctly ────────────────
    try:
        import pandas as pd
        import numpy as np
        sys.path.insert(0, str(workspace / "mock_akshare_pkg"))
        import akshare as ak

        numeric_errors = []
        for entry in stocks_list:
            sym = entry.get("symbol")
            if sym not in required_symbols:
                continue
            try:
                df = ak.stock_zh_a_hist(symbol=sym, period="daily", start_date="20240101", end_date="20240630", adjust="qfq")
                df["收盘"] = pd.to_numeric(df["收盘"])
                df["ma20"] = df["收盘"].rolling(window=20).mean()
                
                expected_last_close = float(round(df["收盘"].iloc[-1], 2))
                expected_ma20 = float(round(df["ma20"].iloc[-1], 2))
                expected_last_date = df["日期"].iloc[-1] if isinstance(df["日期"].iloc[-1], str) else str(df["日期"].iloc[-1])
                expected_signal = "above" if expected_last_close > expected_ma20 else "below"

                actual_close = float(entry.get("last_close", -999))
                actual_ma20 = float(entry.get("ma20", -999))
                actual_signal = entry.get("price_vs_ma20", "")
                actual_date = entry.get("last_date", "")

                if abs(actual_close - expected_last_close) > 0.01:
                    numeric_errors.append(f"{sym}: last_close expected {expected_last_close}, got {actual_close}")
                if abs(actual_ma20 - expected_ma20) > 0.05:
                    numeric_errors.append(f"{sym}: ma20 expected {expected_ma20}, got {actual_ma20}")
                if actual_signal != expected_signal:
                    numeric_errors.append(f"{sym}: price_vs_ma20 expected '{expected_signal}', got '{actual_signal}'")
                if actual_date != expected_last_date:
                    numeric_errors.append(f"{sym}: last_date expected '{expected_last_date}', got '{actual_date}'")
            except Exception as e2:
                numeric_errors.append(f"{sym}: exception during validation: {e2}")

        numeric_ok = len(numeric_errors) == 0
        add_check(
            "MA20 and price signals computed correctly from qfq-adjusted data",
            numeric_ok,
            "All numeric values correct" if numeric_ok else "; ".join(numeric_errors)
        )
    except Exception as e:
        add_check("MA20 and price signals computed correctly", False, f"Eval error: {traceback.format_exc()}")

    # ── Final score ────────────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / len(checks), 4)
    final_pass = all(c["passed"] for c in checks)

    return {"passed": final_pass, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    output = run_checks(workspace)
    print(json.dumps(output, ensure_ascii=False, indent=2))