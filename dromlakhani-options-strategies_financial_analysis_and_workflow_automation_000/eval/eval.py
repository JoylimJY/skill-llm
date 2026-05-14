import sys
import json
import math
from pathlib import Path

def load_report(workspace):
    """Find strategy_report.json anywhere in the workspace."""
    matches = list(Path(workspace).rglob("strategy_report.json"))
    if not matches:
        return None, "File strategy_report.json not found anywhere in workspace"
    return matches[0], None

def approx_equal(a, b, tol=0.05):
    """Within 5 cents / 5% tolerance for financial values."""
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False

def run_eval(workspace):
    checks = []
    score = 0.0

    report_path, err = load_report(workspace)
    if report_path is None:
        checks.append({"name": "file_exists", "passed": False, "detail": err})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_exists", "passed": True, "detail": str(report_path)})
    score += 0.05

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return

    checks.append({"name": "valid_json", "passed": True, "detail": "Parsed successfully"})
    score += 0.05

    # Must be a list of 3 analyses
    if not isinstance(report, list) or len(report) < 3:
        checks.append({"name": "three_analyses", "passed": False,
                        "detail": f"Expected list of 3, got {type(report).__name__} len={len(report) if isinstance(report, list) else 'N/A'}"})
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return
    checks.append({"name": "three_analyses", "passed": True, "detail": "3 strategy analyses present"})
    score += 0.05

    def find_trade(trade_id):
        for item in report:
            item_str = json.dumps(item).upper()
            if trade_id.upper() in item_str:
                return item
        return None

    # ── TRADE-001: Bull Put Spread (XOM) ────────────────────────────────────
    t1 = find_trade("TRADE-001")
    if t1 is None:
        checks.append({"name": "trade001_present", "passed": False, "detail": "TRADE-001 not found"})
    else:
        checks.append({"name": "trade001_present", "passed": True, "detail": "TRADE-001 found"})
        score += 0.05

        # Strategy name must reference "bull put spread" or "bull put" (credit spread, bullish)
        t1_str = json.dumps(t1).lower()
        strategy_ok = "bull put" in t1_str
        checks.append({
            "name": "trade001_strategy_name",
            "passed": strategy_ok,
            "detail": f"Expected 'bull put spread' in analysis, found: {t1_str[:200]}"
        })
        if strategy_ok:
            score += 0.05

        # Net credit = 2.85 - 1.10 = 1.75
        net_credit = 2.85 - 1.10  # 1.75
        # Max Profit = net credit = 1.75
        max_profit_ok = False
        max_loss_ok = False
        breakeven_ok = False

        t1_str_full = json.dumps(t1)
        # Look for max profit value ~1.75
        for candidate in ["1.75", "175"]:  # 1.75 per share or $175 per contract
            if candidate in t1_str_full:
                max_profit_ok = True
                break
        checks.append({
            "name": "trade001_max_profit",
            "passed": max_profit_ok,
            "detail": f"Expected max profit ~1.75 (per share) or 175 (per contract). Report excerpt: {t1_str_full[:300]}"
        })
        if max_profit_ok:
            score += 0.08

        # Max Loss = Width - net credit = (100 - 95) - 1.75 = 3.25
        max_loss_val = 5.0 - 1.75  # 3.25
        for candidate in ["3.25", "325"]:
            if candidate in t1_str_full:
                max_loss_ok = True
                break
        checks.append({
            "name": "trade001_max_loss",
            "passed": max_loss_ok,
            "detail": f"Expected max loss ~3.25 (per share) or 325 (per contract). Report excerpt: {t1_str_full[:300]}"
        })
        if max_loss_ok:
            score += 0.08

        # Breakeven for Bull Put Spread = Higher strike - net credit = 100 - 1.75 = 98.25
        breakeven_val = 100.0 - 1.75  # 98.25
        if "98.25" in t1_str_full:
            breakeven_ok = True
        checks.append({
            "name": "trade001_breakeven",
            "passed": breakeven_ok,
            "detail": f"Expected breakeven = 98.25 (higher strike 100 - net credit 1.75). This is the proprietary formula. Report: {t1_str_full[:400]}"
        })
        if breakeven_ok:
            score += 0.10

        # IV Rank 46 → should be in 40-60 range → credit spreads/iron condors appropriate
        iv_alignment_ok = any(kw in t1_str.lower() for kw in ["credit", "iv rank", "40", "46", "premium selling"])
        checks.append({
            "name": "trade001_iv_alignment",
            "passed": iv_alignment_ok,
            "detail": "IV rank 46 should be noted as suitable for credit spread (40-60 range)"
        })
        if iv_alignment_ok:
            score += 0.05

    # ── TRADE-002: Iron Condor (SPY) — IV RANK MISMATCH ─────────────────────
    t2 = find_trade("TRADE-002")
    if t2 is None:
        checks.append({"name": "trade002_present", "passed": False, "detail": "TRADE-002 not found"})
    else:
        checks.append({"name": "trade002_present", "passed": True, "detail": "TRADE-002 found"})
        score += 0.05

        t2_str = json.dumps(t2).lower()

        # Strategy name: iron condor
        condor_ok = "iron condor" in t2_str
        checks.append({
            "name": "trade002_strategy_name",
            "passed": condor_ok,
            "detail": f"Expected 'iron condor'. Got: {t2_str[:200]}"
        })
        if condor_ok:
            score += 0.05

        # Net credit: (1.20 - 0.55) + (1.35 - 0.70) = 0.65 + 0.65 = 1.30
        net_credit_condor = (1.20 - 0.55) + (1.35 - 0.70)  # 1.30
        credit_ok = any(c in json.dumps(t2) for c in ["1.30", "1.3 ", "130"])
        checks.append({
            "name": "trade002_net_credit",
            "passed": credit_ok,
            "detail": f"Expected total net credit ~1.30. Report: {json.dumps(t2)[:300]}"
        })
        if credit_ok:
            score += 0.06

        # Max Loss for Iron Condor = Width of wider wing - total credit
        # Call wing: 495 - 490 = 5, Put wing: 455 - 450 = 5, both equal = 5
        # Max Loss = 5 - 1.30 = 3.70 (or $370 per contract)
        max_loss_condor = 5.0 - net_credit_condor  # 3.70
        max_loss_ok2 = any(c in json.dumps(t2) for c in ["3.70", "3.7 ", "370"])
        checks.append({
            "name": "trade002_max_loss",
            "passed": max_loss_ok2,
            "detail": f"Expected max loss = 3.70 (wider wing 5 - credit 1.30). Report: {json.dumps(t2)[:300]}"
        })
        if max_loss_ok2:
            score += 0.08

        # CRITICAL: IV rank is 12.5 → < 20 → should BUY premium, NOT sell iron condor
        # Agent MUST flag this as misaligned / suboptimal
        iv_warning_ok = any(kw in t2_str for kw in [
            "misalign", "not recommended", "suboptimal", "low iv", "iv rank", "buy premium",
            "not ideal", "warning", "caution", "ill-suited", "inappropriate", "conflict",
            "12.5", "below 20", "< 20", "under 20", "long premium"
        ])
        checks.append({
            "name": "trade002_iv_rank_warning",
            "passed": iv_warning_ok,
            "detail": (
                "IV rank 12.5 is < 20 (buy premium zone). "
                "Iron condor is a premium-SELLING strategy. "
                "Agent MUST flag this mismatch. "
                f"Got: {t2_str[:400]}"
            )
        })
        if iv_warning_ok:
            score += 0.10

        # Breakevens: Upper = call short strike + net credit = 490 + 1.30 = 491.30
        #             Lower = put short strike - net credit = 455 - 1.30 = 453.70
        upper_be = 490.0 + net_credit_condor  # 491.30
        lower_be = 455.0 - net_credit_condor  # 453.70
        upper_ok = "491.30" in json.dumps(t2) or "491.3" in json.dumps(t2)
        lower_ok = "453.70" in json.dumps(t2) or "453.7" in json.dumps(t2)
        be2_ok = upper_ok and lower_ok
        checks.append({
            "name": "trade002_breakevens",
            "passed": be2_ok,
            "detail": f"Expected upper BE=491.30, lower BE=453.70. Upper found:{upper_ok}, Lower found:{lower_ok}"
        })
        if be2_ok:
            score += 0.08

    # ── TRADE-003: Long Straddle (TSLA) ──────────────────────────────────────
    t3 = find_trade("TRADE-003")
    if t3 is None:
        checks.append({"name": "trade003_present", "passed": False, "detail": "TRADE-003 not found"})
    else:
        checks.append({"name": "trade003_present", "passed": True, "detail": "TRADE-003 found"})
        score += 0.05

        t3_str = json.dumps(t3).lower()
        t3_full = json.dumps(t3)

        # Strategy: Long Straddle
        straddle_ok = "long straddle" in t3_str or ("straddle" in t3_str and "long" in t3_str)
        checks.append({
            "name": "trade003_strategy_name",
            "passed": straddle_ok,
            "detail": f"Expected 'long straddle'. Got: {t3_str[:200]}"
        })
        if straddle_ok:
            score += 0.05

        # Total premium = 6.80 + 6.40 = 13.20
        total_premium = 6.80 + 6.40  # 13.20
        # Max Loss = total premium = 13.20
        max_loss_ok3 = any(c in t3_full for c in ["13.20", "13.2 ", "1320"])
        checks.append({
            "name": "trade003_max_loss_total_premium",
            "passed": max_loss_ok3,
            "detail": f"Expected max loss = 13.20 (total premium paid). Report: {t3_full[:300]}"
        })
        if max_loss_ok3:
            score += 0.07

        # Breakevens: Strike ± total premium = 215 + 13.20 = 228.20, 215 - 13.20 = 201.80
        upper_be3 = 215.0 + total_premium  # 228.20
        lower_be3 = 215.0 - total_premium  # 201.80
        upper_ok3 = "228.20" in t3_full or "228.2" in t3_full
        lower_ok3 = "201.80" in t3_full or "201.8" in t3_full
        be3_ok = upper_ok3 and lower_ok3
        checks.append({
            "name": "trade003_breakevens",
            "passed": be3_ok,
            "detail": f"Expected upper BE=228.20, lower BE=201.80. Upper:{upper_ok3}, Lower:{lower_ok3}"
        })
        if be3_ok:
            score += 0.08

        # Earnings play → DTE = 7 → skill says earnings plays: 1-7 DTE → should be flagged as valid
        dte_ok = any(kw in t3_str for kw in ["earnings", "1-7", "7 dte", "event", "1–7", "short-term"])
        checks.append({
            "name": "trade003_dte_earnings_context",
            "passed": dte_ok,
            "detail": "Agent should note 7 DTE is appropriate for earnings plays per optimal DTE table"
        })
        if dte_ok:
            score += 0.05

        # Greeks: +Vega (strong), -Theta (strong), near-zero Delta
        greeks_ok = any(kw in t3_str for kw in ["vega", "+vega", "theta", "-theta", "delta"])
        checks.append({
            "name": "trade003_greeks",
            "passed": greeks_ok,
            "detail": "Expected Greek references (+Vega, -Theta) for long straddle"
        })
        if greeks_ok:
            score += 0.04

    # ── Output Format: Adjustment Ideas must be present in ALL 3 ─────────────
    adj_count = 0
    for i, item in enumerate(report[:3]):
        item_str = json.dumps(item).lower()
        has_adj = any(kw in item_str for kw in [
            "adjustment", "adjust", "roll", "hedge", "convert", "close one leg",
            "if trade goes wrong", "remediation", "mitigation"
        ])
        if has_adj:
            adj_count += 1
    adj_ok = adj_count >= 2
    checks.append({
        "name": "adjustment_ideas_present",
        "passed": adj_ok,
        "detail": f"Adjustment Ideas required in at least 2/3 analyses. Found in {adj_count}/3."
    })
    if adj_ok:
        score += 0.06

    # ── Risk/Reward Ratio present ─────────────────────────────────────────────
    rr_count = 0
    for item in report[:3]:
        item_str = json.dumps(item).lower()
        if any(kw in item_str for kw in ["risk/reward", "risk reward", "r/r", "reward/risk", "rr ratio"]):
            rr_count += 1
    rr_ok = rr_count >= 2
    checks.append({
        "name": "risk_reward_ratio_present",
        "passed": rr_ok,
        "detail": f"Risk/Reward Ratio required in at least 2/3 analyses. Found in {rr_count}/3."
    })
    if rr_ok:
        score += 0.04

    score = min(round(score, 3), 1.0)
    passed = score >= 0.65

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)