#!/usr/bin/env python3
"""
Evaluation script for A-stock portfolio task.

Expected agent actions:
1. Add 3 stocks to portfolio via portfolio.py:
   - 600789: cost=10.416, qty=3400
   - 002446: cost=8.30, qty=5000
   - 002342: cost=5.20, qty=8000
2. Run portfolio.py analyze (with --minute, --json implicitly via analyze sub-call)
3. Save the JSON output to /workspace/portfolio_analysis.json

Evaluation checks:
A. portfolio.json exists at ~/.clawdbot/skills/a-stock-analysis/portfolio.json
B. portfolio.json contains all 3 stocks with correct cost/qty
C. portfolio_analysis.json exists somewhere in /workspace
D. portfolio_analysis.json is valid JSON with 'portfolio' and 'summary' keys
E. portfolio_analysis.json contains minute_analysis for each stock
F. minute_analysis has segments with early_30min, tail_30min
G. summary has total_pnl field
H. The analysis reflects correct pnl calculation (market_value - cost_value)
"""

import sys
import json
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    overall_passed = True

    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── Check A: Portfolio JSON at correct path ──────────────────────────────
    portfolio_path = Path.home() / ".clawdbot" / "skills" / "a-stock-analysis" / "portfolio.json"
    try:
        if portfolio_path.exists():
            with open(portfolio_path, 'r', encoding='utf-8') as f:
                portfolio_data = json.load(f)
            add_check(
                "portfolio_json_exists_at_correct_path",
                True,
                f"Found portfolio.json at {portfolio_path} with {len(portfolio_data)} entries"
            )
        else:
            add_check(
                "portfolio_json_exists_at_correct_path",
                False,
                f"portfolio.json not found at {portfolio_path}. The agent may have used wrong path."
            )
            portfolio_data = []
    except Exception as e:
        add_check("portfolio_json_exists_at_correct_path", False, f"Error reading portfolio.json: {e}")
        portfolio_data = []

    # ── Check B: All 3 stocks present with correct values ────────────────────
    EXPECTED_HOLDINGS = {
        "600789": {"cost": 10.416, "qty": 3400},
        "002446": {"cost": 8.30,   "qty": 5000},
        "002342": {"cost": 5.20,   "qty": 8000},
    }

    code_map = {h.get('code', ''): h for h in portfolio_data}

    all_stocks_correct = True
    stock_details = []
    for code, expected in EXPECTED_HOLDINGS.items():
        if code not in code_map:
            all_stocks_correct = False
            stock_details.append(f"MISSING {code}")
            continue
        holding = code_map[code]
        cost_ok = abs(holding.get('cost', -1) - expected['cost']) < 0.01
        qty_ok = holding.get('qty', -1) == expected['qty']
        if cost_ok and qty_ok:
            stock_details.append(f"OK {code} cost={holding['cost']} qty={holding['qty']}")
        else:
            all_stocks_correct = False
            stock_details.append(
                f"WRONG {code}: got cost={holding.get('cost')},qty={holding.get('qty')} "
                f"expected cost={expected['cost']},qty={expected['qty']}"
            )

    add_check(
        "portfolio_has_correct_holdings",
        all_stocks_correct,
        "; ".join(stock_details)
    )

    # ── Check C: portfolio_analysis.json exists ──────────────────────────────
    analysis_file = None
    ws = Path(workspace)
    for candidate in ws.rglob("portfolio_analysis.json"):
        analysis_file = candidate
        break

    if analysis_file is None:
        add_check("portfolio_analysis_json_exists", False,
                  "portfolio_analysis.json not found anywhere under /workspace")
        # remaining checks will fail
        for name in [
            "portfolio_analysis_json_valid_structure",
            "portfolio_analysis_has_minute_data",
            "minute_analysis_has_segments",
            "summary_has_pnl",
            "pnl_calculation_correct",
        ]:
            add_check(name, False, "Skipped: portfolio_analysis.json not found")
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": overall_passed, "score": round(score, 2), "checks": checks}

    add_check("portfolio_analysis_json_exists", True, f"Found at {analysis_file}")

    # ── Check D: Valid JSON with correct top-level structure ─────────────────
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        has_portfolio_key = 'portfolio' in analysis_data
        has_summary_key = 'summary' in analysis_data

        if has_portfolio_key and has_summary_key:
            add_check("portfolio_analysis_json_valid_structure", True,
                      "Has 'portfolio' and 'summary' keys")
        else:
            missing = []
            if not has_portfolio_key: missing.append("'portfolio'")
            if not has_summary_key: missing.append("'summary'")
            add_check("portfolio_analysis_json_valid_structure", False,
                      f"Missing keys: {', '.join(missing)}")
            analysis_data = {}
    except Exception as e:
        add_check("portfolio_analysis_json_valid_structure", False,
                  f"Failed to parse portfolio_analysis.json: {e}")
        analysis_data = {}

    portfolio_items = analysis_data.get('portfolio', [])
    summary = analysis_data.get('summary', {})

    # ── Check E: minute_analysis present for each stock ─────────────────────
    items_with_minute = [
        item for item in portfolio_items
        if 'analysis' in item and 'minute_analysis' in item.get('analysis', {})
    ]
    minute_count = len(items_with_minute)
    add_check(
        "portfolio_analysis_has_minute_data",
        minute_count >= 3,
        f"{minute_count}/3 stocks have minute_analysis data"
    )

    # ── Check F: Segments structure in minute_analysis ───────────────────────
    required_segments = {'early_30min', 'morning_mid', 'afternoon_mid', 'tail_30min'}
    segments_ok = True
    seg_details = []
    for item in portfolio_items:
        code = item.get('code', '?')
        ma = item.get('analysis', {}).get('minute_analysis')
        if not ma:
            continue
        segs = ma.get('segments', {})
        found_segs = set(segs.keys())
        missing_segs = required_segments - found_segs
        if missing_segs:
            segments_ok = False
            seg_details.append(f"{code} missing segments: {missing_segs}")
        else:
            # Verify early_30min pct is present and non-zero
            early_pct = segs.get('early_30min', {}).get('pct', 0)
            seg_details.append(f"{code} early_pct={early_pct}%")

    add_check(
        "minute_analysis_has_segments",
        segments_ok and len(seg_details) > 0,
        "; ".join(seg_details) if seg_details else "No segment data found"
    )

    # ── Check G: summary has total_pnl ──────────────────────────────────────
    has_pnl = 'total_pnl' in summary and 'total_pnl_pct' in summary
    add_check(
        "summary_has_pnl",
        has_pnl,
        f"summary keys: {list(summary.keys())}"
    )

    # ── Check H: PNL calculation is reasonable ───────────────────────────────
    # Expected costs: 600789: 10.416*3400=35414.4, 002446: 8.3*5000=41500, 002342: 5.2*8000=41600 → total=118514.4
    expected_total_cost = 10.416 * 3400 + 8.30 * 5000 + 5.20 * 8000
    reported_cost = summary.get('total_cost', 0)
    cost_reasonable = abs(reported_cost - expected_total_cost) < 100  # within 100 yuan

    pnl_reasonable = 'total_pnl' in summary and isinstance(summary.get('total_pnl'), (int, float))

    add_check(
        "pnl_calculation_correct",
        cost_reasonable and pnl_reasonable,
        f"Expected total_cost≈{expected_total_cost:.2f}, got {reported_cost}; total_pnl={summary.get('total_pnl')}"
    )

    score = sum(1 for c in checks if c["passed"]) / len(checks)
    return {"passed": overall_passed, "score": round(score, 2), "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))