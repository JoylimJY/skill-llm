import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # Helper
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # --- Find output file ---
    output_file = None
    candidates = list(workspace.rglob("signal_report.json"))
    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "signal_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file.relative_to(workspace)}"})
    total_score += 5.0

    # --- Parse JSON ---
    try:
        with open(output_file, "r") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "output_json_valid", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    checks.append({"name": "output_json_valid", "passed": True, "detail": "Valid JSON"})
    total_score += 5.0

    # --- Check required fields ---
    required_fields = ["direction", "score", "signal", "entry_type", "stop_loss", "target", "reason"]
    missing = [f for f in required_fields if f not in report]
    if missing:
        total_score += add_check("required_fields_present", False,
                                  f"Missing fields: {missing}", weight=10.0)
    else:
        total_score += add_check("required_fields_present", True,
                                  "All required fields present", weight=10.0)

    # =======================================================================
    # CORE LOGIC CHECKS
    # =======================================================================

    # CHECK 1: Direction must be "long"
    # 1D + 1H data shows clear uptrend: higher highs, higher lows, price above MA
    direction = str(report.get("direction", "")).strip().lower()
    dir_passed = direction == "long"
    total_score += add_check(
        "direction_is_long",
        dir_passed,
        f"Expected 'long' (1D/1H data shows uptrend: higher highs/lows, price above MA). Got: '{direction}'",
        weight=15.0
    )

    # CHECK 2: CRITICAL - Signal must be "no_trade"
    # Reason: 1M trigger layer fails (no higher low formed, no confirmed breakout)
    # Mandatory rule: "没有触发 → 不入场" (no trigger = no entry)
    # Even though score from other layers may be ≥80, the hard-stop rule overrides
    signal = str(report.get("signal", "")).strip().lower()
    signal_passed = signal == "no_trade"
    total_score += add_check(
        "signal_is_no_trade_due_to_missing_trigger",
        signal_passed,
        f"CRITICAL: 1M candle data shows no valid trigger (lows 73680→73700→73650→73640 = lower lows, not higher lows; no confirmed breakout). "
        f"Mandatory rule 'no trigger → no entry' must override score. Expected 'no_trade'. Got: '{signal}'",
        weight=30.0
    )

    # CHECK 3: Score computation reasonableness
    # Expected scoring breakdown:
    # - Direction (1H/1D uptrend clear) = 20/20
    # - Structure (4H EMA9>EMA21>EMA55, trending) = 20/20
    # - Position (5M price at support, pullback not breaking) = 20/20
    # - Sentiment (funding 0.005 neutral, long ratio 62.3% neutral → no threshold hit) = 0/15
    # - Liquidity (short liq cluster at 74800-75200 identified) = 15/15
    # - Trigger (1M: no higher low, no confirmed breakout) = 0/10
    # Total = 20+20+20+0+15+0 = 75  (OR 20+20+20+15+15+0=90 if agent gives full sentiment)
    # The score varies by interpretation, but trigger MUST be 0
    # We check: trigger score appears to be 0 (reflected in reasoning or score)
    try:
        raw_score = float(report.get("score", -1))
        # Score should NOT be 100 (trigger is missing = 0/10)
        # Score should be between 55 and 90 depending on sentiment interpretation
        # BUT the mandatory rule "no trigger → no entry" applies regardless
        score_reasonable = 0 <= raw_score <= 90
        trigger_penalized = raw_score <= 80  # if trigger=0, score cannot be > 90 max possible
        score_detail = f"Score={raw_score}. Expected range [0,90] given trigger layer=0/10. "
        if raw_score > 90:
            score_detail += "Score too high: trigger layer should contribute 0 (no valid 1M trigger). "
        total_score += add_check(
            "score_reflects_missing_trigger",
            score_reasonable and raw_score <= 90,
            score_detail + f"Trigger layer (10pts) must be 0 since no higher low or breakout confirmed on 1M.",
            weight=15.0
        )
    except (TypeError, ValueError) as e:
        total_score += add_check("score_reflects_missing_trigger", False,
                                  f"Could not parse score as number: {e}", weight=15.0)

    # CHECK 4: Sentiment scoring - funding rate and long/short ratio both neutral
    # Funding 0.005 is in (-0.01, 0.01) → no overheating → neutral
    # Long ratio 62.3% < 70% → no extreme signal → neutral
    # Reason should mention these thresholds OR score should reflect partial/zero sentiment
    reason = str(report.get("reason", "")).lower()
    sentiment_understood = (
        ("funding" in reason or "0.005" in reason or "sentiment" in reason or "neutral" in reason) and
        ("trigger" in reason or "1m" in reason or "no trigger" in reason or "未触发" in reason or "触发" in reason)
    )
    total_score += add_check(
        "reason_mentions_trigger_and_sentiment",
        sentiment_understood,
        f"Reason should explain: (1) trigger missing/not confirmed on 1M, (2) sentiment neutral (funding 0.005 in neutral range). "
        f"Got reason: '{report.get('reason', '')[:200]}'",
        weight=10.0
    )

    # CHECK 5: Stop loss must be present and numeric (required by mandatory rules)
    # "必须有止损" - but since signal is no_trade, stop_loss can be "none" or "N/A"
    stop_loss = str(report.get("stop_loss", "")).strip().lower()
    # If signal is no_trade, stop_loss can be none/na/n/a/not applicable
    if signal == "no_trade":
        sl_passed = True
        sl_detail = "Signal is no_trade; stop_loss field present (can be 'none' or price)"
    else:
        # If agent incorrectly outputs execute/watch, stop loss should at least be present
        sl_passed = stop_loss not in ["", "null"]
        sl_detail = f"Stop loss must be specified. Got: '{stop_loss}'"
    total_score += add_check("stop_loss_field_present", sl_passed, sl_detail, weight=5.0)

    # CHECK 6: Entry type consistent with long direction
    # If signal is no_trade, entry_type can be "none" or the intended type
    entry_type = str(report.get("entry_type", "")).strip().lower()
    # Acceptable: pullback (since 5M shows pullback to support), none (if no_trade)
    entry_reasonable = entry_type in ["pullback", "none", "n/a", "na", "no entry", "no_entry"]
    total_score += add_check(
        "entry_type_reasonable",
        entry_reasonable,
        f"For a long pullback setup (5M shows price bouncing from support), expected 'pullback' or 'none' (if no_trade). Got: '{entry_type}'",
        weight=5.0
    )

    # CHECK 7: Target zone references liquidity cluster
    target = str(report.get("target", "")).lower()
    # Should mention 74800 or 75000 or 75200 or the zone "74800-75200"
    target_reasonable = any(x in target for x in ["748", "750", "752", "74800", "75000", "75200", "none", "n/a"])
    total_score += add_check(
        "target_references_liquidity_zone",
        target_reasonable,
        f"Target should reference liquidation cluster zone (74800-75200) or 'none' if no_trade. Got: '{target}'",
        weight=5.0
    )

    # --- Final verdict ---
    # The CRITICAL check is signal_is_no_trade. If that fails, overall fails.
    critical_passed = signal_passed
    all_checks_passed = all(c["passed"] for c in checks)

    # Normalize score to [0, 1]
    max_possible = 5.0 + 5.0 + 10.0 + 15.0 + 30.0 + 15.0 + 10.0 + 5.0 + 5.0 + 5.0
    normalized = min(total_score / max_possible, 1.0)

    return {
        "passed": critical_passed and dir_passed and (normalized >= 0.6),
        "score": round(normalized, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))