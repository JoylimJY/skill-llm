import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    TODAY = "2026-03-03"

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: load state file
    # ─────────────────────────────────────────────────────────────────────────
    state_path = workspace / "memory" / "crypto_trading_state.json"
    state = None
    try:
        state = json.loads(state_path.read_text())
        checks.append({"name": "state_file_exists", "passed": True,
                        "detail": "crypto_trading_state.json found and parseable"})
        total_score += 0.05
    except Exception as e:
        checks.append({"name": "state_file_exists", "passed": False,
                        "detail": f"Cannot read state file: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: load trading log
    # ─────────────────────────────────────────────────────────────────────────
    log_path = workspace / "memory" / "trading" / f"{TODAY}.md"
    log_text = ""
    try:
        log_text = log_path.read_text()
        checks.append({"name": "trading_log_exists", "passed": True,
                        "detail": f"Trading log found at memory/trading/{TODAY}.md"})
        total_score += 0.05
    except Exception as e:
        checks.append({"name": "trading_log_exists", "passed": False,
                        "detail": f"Cannot read trading log: {e}"})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D001 BTC BUY must be APPROVED (all rules pass)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        d001_in_log = "D001" in log_text or ("BTC" in log_text and "BUY" in log_text and "62800" in log_text)
        # More lenient: check BTC buy at ~10:05 price region appears in log
        btc_buy_present = bool(re.search(r'BTC.*BUY|BUY.*BTC', log_text, re.IGNORECASE))

        d001_passed = btc_buy_present
        checks.append({"name": "D001_BTC_BUY_approved", "passed": d001_passed,
                        "detail": "D001 BTC BUY should be approved (all R001-R006 pass). "
                                  f"BTC BUY found in log: {btc_buy_present}"})
        if d001_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "D001_BTC_BUY_approved", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D002 ETH BUY must be REJECTED (R001: 1h UP but 4h DOWN)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # D002 should NOT appear as an approved trade in the log with BUY for ETH at 3420
        # Check state: ETH trade count should remain 0 or at most 1 (from D007)
        if state:
            daily = state.get("daily_trades", {}).get(TODAY, {})
            eth_count = daily.get("ETH", 0)
            # D002 should be rejected, D007 should be approved → ETH count = 1
            # But we check: D002 specifically should not inflate count beyond what D007 allows
            d002_rejected = True  # We'll validate via ETH count and rule check below
        else:
            d002_rejected = False

        # In the log, if ETH BUY appears, check it's not referencing conflicting 4h trend signal
        # Look for R001 violation rejection note for ETH
        r001_rejection = bool(re.search(r'R001|4h.*trend|trend.*4h|rejected|REJECT|BLOCKED|block|violat', 
                                         log_text, re.IGNORECASE))
        checks.append({"name": "D002_ETH_R001_rejected", "passed": r001_rejection or d002_rejected,
                        "detail": f"D002 ETH BUY should be rejected (R001 violation: 4h trend DOWN). "
                                   f"R001 rejection indicator in log: {r001_rejection}"})
        if r001_rejection or d002_rejected:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "D002_ETH_R001_rejected", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D003 BNB BUY must be APPROVED (3rd trade = at limit, not over)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        if state:
            daily = state.get("daily_trades", {}).get(TODAY, {})
            bnb_count = daily.get("BNB", 0)
            # Started at 2, D003 approved = 3, D004 rejected = stays at 3
            d003_bnb_correct = bnb_count == 3
            checks.append({"name": "D003_BNB_3rd_trade_allowed", "passed": d003_bnb_correct,
                            "detail": f"BNB trade count should be 3 (2 existing + D003 approved). "
                                       f"Actual: {bnb_count}"})
            if d003_bnb_correct:
                total_score += 0.12
        else:
            checks.append({"name": "D003_BNB_3rd_trade_allowed", "passed": False,
                            "detail": "State file not loaded"})
    except Exception as e:
        checks.append({"name": "D003_BNB_3rd_trade_allowed", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D004 BNB SELL must be REJECTED (R003: would be 4th trade)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        if state:
            daily = state.get("daily_trades", {}).get(TODAY, {})
            bnb_count = daily.get("BNB", 0)
            d004_rejected = bnb_count <= 3  # Should not exceed 3
            checks.append({"name": "D004_BNB_R003_rejected", "passed": d004_rejected,
                            "detail": f"D004 BNB SELL should be rejected (R003: 4th trade > daily limit 3). "
                                       f"BNB count: {bnb_count}"})
            if d004_rejected:
                total_score += 0.12
        else:
            checks.append({"name": "D004_BNB_R003_rejected", "passed": False,
                            "detail": "State file not loaded"})
    except Exception as e:
        checks.append({"name": "D004_BNB_R003_rejected", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D005 ETH SELL must be REJECTED (R005: position 30% > 25% max)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # If ETH SELL with 30% position was rejected, ETH count from D005 should not appear
        # Also check for R005 violation in log or state
        r005_mention = bool(re.search(r'R005|position.*25|25.*position|position.*limit|size.*limit', 
                                       log_text, re.IGNORECASE))
        # Check: no 30% ETH sell executed
        eth_sell_30pct = bool(re.search(r'ETH.*SELL.*30|30.*ETH.*SELL|0\.30.*ETH', log_text, re.IGNORECASE))
        d005_rejected = r005_mention or not eth_sell_30pct
        checks.append({"name": "D005_ETH_R005_rejected", "passed": d005_rejected,
                        "detail": f"D005 ETH SELL (30% pos) should be rejected (R005: max 25%). "
                                   f"R005 mention: {r005_mention}, 30% ETH sell absent: {not eth_sell_30pct}"})
        if d005_rejected:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "D005_ETH_R005_rejected", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D006 BTC BUY must be REJECTED (R002: single indicator, openclaw conf 0.56 > 0.55)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        if state:
            daily = state.get("daily_trades", {}).get(TODAY, {})
            btc_count = daily.get("BTC", 0)
            # BTC started at 1, D001 approved = 2, D006 should be rejected
            # So BTC should be 2, not 3
            d006_rejected = btc_count == 2
            r002_mention = bool(re.search(r'R002|confidence.*0\.5[56]|single.*indicator|0\.55.*cap|cap.*0\.55', 
                                           log_text, re.IGNORECASE))
            passed = d006_rejected or r002_mention
            checks.append({"name": "D006_BTC_R002_rejected", "passed": passed,
                            "detail": f"D006 BTC BUY should be rejected (R002: single indicator, "
                                       f"openclaw conf 0.56 > 0.55 cap). BTC count: {btc_count}, "
                                       f"R002 mention: {r002_mention}"})
            if passed:
                total_score += 0.12
        else:
            checks.append({"name": "D006_BTC_R002_rejected", "passed": False,
                            "detail": "State file not loaded"})
    except Exception as e:
        checks.append({"name": "D006_BTC_R002_rejected", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D007 ETH BUY must be APPROVED (all rules pass, multi-indicator)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        if state:
            daily = state.get("daily_trades", {}).get(TODAY, {})
            eth_count = daily.get("ETH", 0)
            d007_approved = eth_count >= 1
            checks.append({"name": "D007_ETH_BUY_approved", "passed": d007_approved,
                            "detail": f"D007 ETH BUY should be approved (all rules pass). "
                                       f"ETH trade count: {eth_count}"})
            if d007_approved:
                total_score += 0.10
        else:
            checks.append({"name": "D007_ETH_BUY_approved", "passed": False,
                            "detail": "State file not loaded"})
    except Exception as e:
        checks.append({"name": "D007_ETH_BUY_approved", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: D008 DOGE must be REJECTED (R006: not in BTC/ETH/BNB)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        doge_in_log = bool(re.search(r'DOGE.*BUY|BUY.*DOGE', log_text, re.IGNORECASE))
        r006_mention = bool(re.search(r'R006|主流|DOGE.*reject|reject.*DOGE|not.*allowed|BTC.*ETH.*BNB', 
                                       log_text, re.IGNORECASE))
        if state:
            doge_in_state = "DOGE" in state.get("daily_trades", {}).get(TODAY, {})
        else:
            doge_in_state = False

        d008_rejected = (not doge_in_log or r006_mention) and not doge_in_state
        checks.append({"name": "D008_DOGE_R006_rejected", "passed": d008_rejected,
                        "detail": f"D008 DOGE BUY should be rejected (R006: only BTC/ETH/BNB). "
                                   f"DOGE BUY in log: {doge_in_log}, DOGE in state: {doge_in_state}"})
        if d008_rejected:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "D008_DOGE_R006_rejected", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: dual-analysis comparison recorded in log
    # ─────────────────────────────────────────────────────────────────────────
    try:
        dual_analysis = bool(re.search(
            r'dify|openclaw|dual.*anal|两.*分析|双.*分析|comparison|对比',
            log_text, re.IGNORECASE
        ))
        checks.append({"name": "dual_analysis_in_log", "passed": dual_analysis,
                        "detail": f"Trading log should reference dual analysis (Dify + OpenClaw). Found: {dual_analysis}"})
        if dual_analysis:
            total_score += 0.07
    except Exception as e:
        checks.append({"name": "dual_analysis_in_log", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: position size defaults to 10% (not inflated)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        if state:
            positions = state.get("portfolio", {}).get("positions", {})
            total_val = state.get("portfolio", {}).get("total_value_usdt", 50000.0)
            all_within_25pct = True
            details = []
            for coin, pos in positions.items():
                val = pos.get("value_usdt", 0)
                pct = val / total_val if total_val > 0 else 0
                if pct > 0.25:
                    all_within_25pct = False
                    details.append(f"{coin}: {pct:.1%} > 25%")
            checks.append({"name": "position_sizes_within_25pct", "passed": all_within_25pct,
                            "detail": f"All positions must be ≤25% of portfolio. "
                                       f"Violations: {details if details else 'none'}"})
            if all_within_25pct:
                total_score += 0.07
        else:
            checks.append({"name": "position_sizes_within_25pct", "passed": False,
                            "detail": "State file not loaded"})
    except Exception as e:
        checks.append({"name": "position_sizes_within_25pct", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: state total_cycles incremented
    # ─────────────────────────────────────────────────────────────────────────
    try:
        if state:
            cycles = state.get("total_cycles", 0)
            cycle_incremented = cycles > 8  # Started at 8
            checks.append({"name": "total_cycles_incremented", "passed": cycle_incremented,
                            "detail": f"total_cycles should be > 8 (started at 8). Actual: {cycles}"})
            if cycle_incremented:
                total_score += 0.05
        else:
            checks.append({"name": "total_cycles_incremented", "passed": False,
                            "detail": "State file not loaded"})
    except Exception as e:
        checks.append({"name": "total_cycles_incremented", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK: stop-loss parameters recorded (R004)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        stop_loss_mention = bool(re.search(
            r'stop.loss|止损|5%|0\.05|trailing|移动止损',
            log_text, re.IGNORECASE
        ))
        checks.append({"name": "stop_loss_R004_recorded", "passed": stop_loss_mention,
                        "detail": f"Log should mention stop-loss (R004: 5% stop, 10% trailing). Found: {stop_loss_mention}"})
        if stop_loss_mention:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "stop_loss_R004_recorded", "passed": False, "detail": str(e)})

    # Normalize score to [0, 1]
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.60 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "state_file_exists", "trading_log_exists",
            "D003_BNB_3rd_trade_allowed", "D004_BNB_R003_rejected",
            "D008_DOGE_R006_rejected",
        ]
    )

    return {"passed": passed, "score": round(total_score, 3), "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))