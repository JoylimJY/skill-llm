import sys
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path

def load_json_report(workspace):
    matches = list(Path(workspace).rglob("momentum_signals.json"))
    if not matches:
        return None, "momentum_signals.json not found anywhere in workspace"
    return json.loads(matches[0].read_text()), str(matches[0])

# ─────────────────────────────────────────────────────────────────────────────
# Reference computation (mirrors SKILL.md scoring table exactly)
# ─────────────────────────────────────────────────────────────────────────────
def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(close, fast=12, slow=26, signal=9):
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def compute_obv(close, volume):
    direction = np.sign(close.diff().fillna(0))
    obv = (direction * volume).cumsum()
    return obv

def compute_bb(close, period=20):
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    bb_pct = (close - lower) / (upper - lower)
    return bb_pct

def check_rsi_divergence(close, rsi, lookback=5):
    """Simple divergence: last close higher but RSI lower → bearish div; opposite → bullish."""
    price_change = close.iloc[-1] - close.iloc[-1 - lookback]
    rsi_change = rsi.iloc[-1] - rsi.iloc[-1 - lookback]
    if price_change > 0 and rsi_change < 0:
        return "bearish"
    if price_change < 0 and rsi_change > 0:
        return "bullish"
    return "none"

def check_obv_divergence(close, obv, lookback=5):
    price_change = close.iloc[-1] - close.iloc[-1 - lookback]
    obv_change = obv.iloc[-1] - obv.iloc[-1 - lookback]
    if price_change > 0 and obv_change < 0:
        return "bearish"
    if price_change < 0 and obv_change > 0:
        return "bullish"
    return "none"

def score_asset(df):
    close = df["close"]
    volume = df["volume"]

    rsi = compute_rsi(close)
    rsi_val = rsi.iloc[-1]

    macd_line, signal_line, histogram = compute_macd(close)
    macd_hist_val = histogram.iloc[-1]
    macd_hist_prev = histogram.iloc[-2]
    macd_line_val = macd_line.iloc[-1]
    signal_line_val = signal_line.iloc[-1]
    macd_line_prev = macd_line.iloc[-2]
    signal_line_prev = signal_line.iloc[-2]

    ema20 = compute_ema(close, 20)
    ema50 = compute_ema(close, 50)
    ema200 = compute_ema(close, 200)

    bb_pct_series = compute_bb(close)
    bb_pct_val = bb_pct_series.iloc[-1]

    obv = compute_obv(close, volume)
    obv_val = obv.iloc[-1]
    obv_prev = obv.iloc[-6]

    avg_vol = volume.iloc[-20:].mean()
    last_vol = volume.iloc[-1]

    rsi_div = check_rsi_divergence(close, rsi)
    obv_div = check_obv_divergence(close, obv)

    score = 0
    details = {}

    # RSI ±1
    if rsi_val < 40:
        score += 1; details["rsi"] = +1
    elif rsi_val > 70:
        score -= 1; details["rsi"] = -1
    else:
        details["rsi"] = 0

    # RSI divergence ±2
    if rsi_div == "bullish":
        score += 2; details["rsi_div"] = +2
    elif rsi_div == "bearish":
        score -= 2; details["rsi_div"] = -2
    else:
        details["rsi_div"] = 0

    # MACD cross ±1  (cross = line crossed signal in last candle)
    bullish_cross = (macd_line_prev <= signal_line_prev) and (macd_line_val > signal_line_val)
    bearish_cross = (macd_line_prev >= signal_line_prev) and (macd_line_val < signal_line_val)
    if bullish_cross:
        score += 1; details["macd_cross"] = +1
    elif bearish_cross:
        score -= 1; details["macd_cross"] = -1
    else:
        details["macd_cross"] = 0

    # MACD histogram ±1
    if macd_hist_val > macd_hist_prev:
        score += 1; details["macd_hist"] = +1
    else:
        score -= 1; details["macd_hist"] = -1

    # EMA cross ±1
    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 1; details["ema_cross"] = +1
    else:
        score -= 1; details["ema_cross"] = -1

    # EMA200 ±1
    if close.iloc[-1] > ema200.iloc[-1]:
        score += 1; details["ema200"] = +1
    else:
        score -= 1; details["ema200"] = -1

    # Bollinger ±1
    if bb_pct_val < 0.2:
        score += 1; details["bb"] = +1
    elif bb_pct_val > 0.8:
        score -= 1; details["bb"] = -1
    else:
        details["bb"] = 0

    # OBV trend ±1
    if obv_val > obv_prev:
        score += 1; details["obv_trend"] = +1
    else:
        score -= 1; details["obv_trend"] = -1

    # OBV divergence ±2
    if obv_div == "bullish":
        score += 2; details["obv_div"] = +2
    elif obv_div == "bearish":
        score -= 2; details["obv_div"] = -2
    else:
        details["obv_div"] = 0

    # Volume ±1
    if last_vol > avg_vol * 1.5:
        score += 1; details["volume"] = +1
    else:
        score -= 1; details["volume"] = -1

    rsi_status = "oversold" if rsi_val < 40 else "overbought" if rsi_val > 70 else "neutral"
    macd_direction = "rising" if macd_hist_val > macd_hist_prev else "falling"
    obv_trend = "rising" if obv_val > obv_prev else "falling"
    ema_cross_str = "bullish" if ema20.iloc[-1] > ema50.iloc[-1] else "bearish"
    bias = "BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL"
    our_prob = 0.50 + (score * 0.05)
    confidence_pct = round(our_prob * 100, 1)

    return {
        "score": score,
        "rsi": round(rsi_val, 2),
        "rsi_status": rsi_status,
        "macd_hist": round(macd_hist_val, 4),
        "macd_direction": macd_direction,
        "obv_trend": obv_trend,
        "bb_pct": round(bb_pct_val, 4),
        "ema_cross": ema_cross_str,
        "bias": bias,
        "confidence_pct": confidence_pct,
        "our_prob": our_prob,
        "_details": details,
    }

def evaluate(workspace):
    checks = []
    workspace = Path(workspace)

    # ── Load agent output ──────────────────────────────────────────────────
    report, msg = load_json_report(workspace)
    if report is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": msg})
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append({"name": "output_file_exists", "passed": True, "detail": msg})

    # ── Compute reference scores ───────────────────────────────────────────
    candle_dir = workspace / "data" / "raw" / "candles"
    odds_path = workspace / "data" / "raw" / "polymarket_odds.json"
    polymarket = json.loads(odds_path.read_text())

    ref = {}
    for symbol in ["SOL", "XRP", "ATOM"]:
        df = pd.read_csv(candle_dir / f"{symbol}_1h_candles.csv")
        ref[symbol] = score_asset(df)
        odds = polymarket[symbol]
        our_p = ref[symbol]["our_prob"]
        edge = our_p - odds["market_up"]
        ref[symbol]["market_up"] = odds["market_up"]
        ref[symbol]["edge"] = round(edge, 4)
        ref[symbol]["direction"] = "UP" if edge > 0 else "DOWN"
        sc = ref[symbol]["score"]
        age = odds["age_minutes"]
        abs_edge = abs(edge)
        bet_valid = abs(sc) >= 3 and abs_edge >= 0.10 and age < 30
        # counter-consensus L023
        counter = (sc >= 3 and odds["market_down"] > 0.70) or (sc <= -3 and odds["market_up"] > 0.70)
        ref[symbol]["bet_valid"] = bet_valid
        ref[symbol]["counter_consensus"] = counter
        ref[symbol]["bet_recommend"] = bet_valid and counter

    # ── Normalize agent output to a dict keyed by asset ───────────────────
    # Accept either list or dict at top level
    if isinstance(report, list):
        agent_assets = {entry.get("asset", "").upper(): entry for entry in report
                        if isinstance(entry, dict)}
    elif isinstance(report, dict):
        # Top-level might be {"assets": [...], "bets": [...]}
        # Or {"SOL": {...}, "XRP": {...}} 
        if "assets" in report:
            agent_assets = {e.get("asset","").upper(): e for e in report["assets"]}
        else:
            # Try treating keys as asset names
            agent_assets = {}
            for k, v in report.items():
                if k.upper() in ["SOL","XRP","ATOM"] and isinstance(v, dict):
                    v["asset"] = k.upper()
                    agent_assets[k.upper()] = v
    else:
        agent_assets = {}

    # ── Per-asset checks ───────────────────────────────────────────────────
    total_score_checks = 0
    passed_score_checks = 0

    for symbol in ["SOL", "XRP", "ATOM"]:
        r = ref[symbol]
        a = agent_assets.get(symbol, {})

        has_entry = bool(a)
        checks.append({
            "name": f"{symbol}_entry_present",
            "passed": has_entry,
            "detail": f"Agent has entry for {symbol}: {has_entry}"
        })
        if not has_entry:
            continue

        # Score check (allow ±1 tolerance due to minor indicator impl differences)
        agent_score = a.get("score", None)
        ref_score = r["score"]
        score_ok = agent_score is not None and abs(int(agent_score) - ref_score) <= 1
        total_score_checks += 1
        if score_ok:
            passed_score_checks += 1
        checks.append({
            "name": f"{symbol}_momentum_score",
            "passed": score_ok,
            "detail": f"ref={ref_score}, agent={agent_score} (tolerance ±1)"
        })

        # Bias check
        agent_bias = str(a.get("bias", "")).upper()
        # Use agent's own score to determine expected bias
        if agent_score is not None:
            expected_bias = "BULLISH" if int(agent_score) > 0 else "BEARISH" if int(agent_score) < 0 else "NEUTRAL"
            bias_ok = agent_bias == expected_bias
        else:
            bias_ok = agent_bias == r["bias"]
        checks.append({
            "name": f"{symbol}_bias",
            "passed": bias_ok,
            "detail": f"ref={r['bias']}, agent={agent_bias}"
        })

        # confidence_pct = our_prob * 100 = (0.50 + score*0.05)*100
        agent_conf = a.get("confidence_pct", None)
        if agent_conf is not None and agent_score is not None:
            expected_conf = (0.50 + int(agent_score) * 0.05) * 100
            conf_ok = abs(float(agent_conf) - expected_conf) <= 2.0
        else:
            conf_ok = False
        checks.append({
            "name": f"{symbol}_confidence_pct",
            "passed": conf_ok,
            "detail": f"expected≈{(0.50 + ref_score*0.05)*100}, agent={agent_conf}"
        })

        # polymarket_edge sub-object
        pe = None
        if "polymarket_edge" in a:
            pe_val = a["polymarket_edge"]
            if isinstance(pe_val, dict):
                # Could be nested: {"sol_4pm_et": {...}} or flat
                if any(k in pe_val for k in ["market_up", "our_p", "edge", "direction"]):
                    pe = pe_val
                else:
                    # nested
                    for v in pe_val.values():
                        if isinstance(v, dict):
                            pe = v
                            break

        if pe is None:
            checks.append({
                "name": f"{symbol}_polymarket_edge_present",
                "passed": False,
                "detail": "polymarket_edge sub-object missing or malformed"
            })
        else:
            checks.append({
                "name": f"{symbol}_polymarket_edge_present",
                "passed": True,
                "detail": "polymarket_edge sub-object found"
            })
            # edge value check
            agent_edge = pe.get("edge", None)
            if agent_edge is not None and agent_score is not None:
                expected_our_p = 0.50 + int(agent_score) * 0.05
                expected_edge = expected_our_p - r["market_up"]
                edge_ok = abs(float(agent_edge) - expected_edge) <= 0.06
            else:
                edge_ok = False
            checks.append({
                "name": f"{symbol}_edge_value",
                "passed": edge_ok,
                "detail": f"ref_edge≈{r['edge']:.4f}, agent_edge={agent_edge}"
            })
            # direction check
            agent_dir = str(pe.get("direction", "")).upper()
            exp_dir = "UP" if r["edge"] > 0 else "DOWN"
            # If agent's score is different but consistent, use their own edge
            if agent_edge is not None:
                exp_dir_agent = "UP" if float(agent_edge) > 0 else "DOWN"
            else:
                exp_dir_agent = exp_dir
            dir_ok = agent_dir == exp_dir_agent
            checks.append({
                "name": f"{symbol}_edge_direction",
                "passed": dir_ok,
                "detail": f"expected={exp_dir_agent}, agent={agent_dir}"
            })

    # ── Bets list check ────────────────────────────────────────────────────
    # Only assets with valid bet AND counter-consensus should appear
    if isinstance(report, dict):
        bets_list = report.get("bets", None)
    else:
        bets_list = None
        # Try to find a "bets" key in any top-level dict
    
    bets_present = bets_list is not None and isinstance(bets_list, list)
    checks.append({
        "name": "bets_list_present",
        "passed": bets_present,
        "detail": f"Top-level 'bets' list present: {bets_present}"
    })

    if bets_present:
        # Determine which assets SHOULD be in bets (bet_valid AND counter_consensus)
        expected_bet_assets = {s for s in ["SOL", "XRP", "ATOM"] if ref[s]["bet_recommend"]}
        agent_bet_assets = set()
        for b in bets_list:
            if isinstance(b, dict):
                a_name = b.get("asset", "").upper()
                if a_name:
                    agent_bet_assets.add(a_name)
            elif isinstance(b, str):
                agent_bet_assets.add(b.upper())

        # Must include SOL (the designed counter-consensus winner)
        sol_in_bets = "SOL" in agent_bet_assets
        checks.append({
            "name": "bets_contains_SOL_counter_consensus",
            "passed": sol_in_bets,
            "detail": f"SOL (score>=+3, market DOWN 80%) must be in bets. agent_bets={agent_bet_assets}"
        })

        # XRP should NOT be in bets (edge may qualify but NOT counter-consensus: market_up=0.65 < 70%)
        xrp_not_in_bets = "XRP" not in agent_bet_assets
        checks.append({
            "name": "bets_excludes_XRP_non_counter",
            "passed": xrp_not_in_bets,
            "detail": f"XRP market_up=0.65 (<70%) → not counter-consensus → NOT in bets. agent_bets={agent_bet_assets}"
        })

        # ATOM should NOT be in bets (abs(score)<3)
        atom_not_in_bets = "ATOM" not in agent_bet_assets
        checks.append({
            "name": "bets_excludes_ATOM_low_score",
            "passed": atom_not_in_bets,
            "detail": f"ATOM abs(score)<3 → no valid bet. agent_bets={agent_bet_assets}"
        })

    # ── Aggregate scoring ──────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    final_score = round(passed_count / total, 4) if total > 0 else 0.0

    # Must pass at minimum: file exists, SOL score, SOL bias, SOL edge direction, bets SOL present
    critical = [
        "output_file_exists",
        "SOL_entry_present",
        "SOL_momentum_score",
        "SOL_bias",
        "SOL_polymarket_edge_present",
        "SOL_edge_direction",
        "bets_list_present",
        "bets_contains_SOL_counter_consensus",
        "bets_excludes_XRP_non_counter",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    passed = critical_passed and final_score >= 0.60

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = evaluate(workspace)
    except Exception as ex:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(ex)}]
        }
    print(json.dumps(result, indent=2))