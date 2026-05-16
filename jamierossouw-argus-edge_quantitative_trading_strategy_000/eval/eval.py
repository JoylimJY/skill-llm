import sys
import json
import math
from pathlib import Path

def find_output(workspace):
    candidates = list(Path(workspace).rglob("betting_recommendations.json"))
    if not candidates:
        return None
    return candidates[0]

def argus_compute(market):
    """
    Replicate the Argus edge logic for evaluation.
    Returns dict with: action, reason, our_p_win, edge, kelly_stake
    """
    asset = market["asset"]
    ta_score = market["ta_score"]
    ta_dir = market["ta_direction"]
    age = market["market_age_minutes"]
    market_prob_up = market["market_implied_prob_up"]
    consensus_pct = market["market_consensus_pct"]
    bankroll = market["bankroll"]
    odds = market["decimal_odds"]

    # Asset calibration table
    calibration = {
        "BTC": {"reliability": 0.75, "bias": 0.0,  "min_score": 3},
        "ETH": {"reliability": 0.80, "bias": 0.05, "min_score": 2},  # bias is UP bias
        "SOL": {"reliability": 0.90, "bias": 0.05, "min_score": 1},
        "XRP": {"reliability": 0.70, "bias": 0.08, "min_score": 2},
    }

    cal = calibration[asset]
    min_score = cal["min_score"]
    reliability = cal["reliability"]

    # Consensus guard: skip if > 92%
    if consensus_pct > 92:
        return {"action": "SKIP", "reason": "consensus_guard", "our_p_win": None, "edge": None, "kelly_stake": None}

    # Freshness guard: skip if age > 30 min (not fresh)
    if age > 30:
        return {"action": "SKIP", "reason": "not_fresh", "our_p_win": None, "edge": None, "kelly_stake": None}

    # TA score threshold check (use absolute value for DOWN direction)
    abs_ta = abs(ta_score)
    if abs_ta < min_score:
        return {"action": "SKIP", "reason": "ta_score_below_min", "our_p_win": None, "edge": None, "kelly_stake": None}

    # Determine our_P(win):
    # Base probability from TA reliability: 0.5 + (reliability * normalized_signal)
    # The TA score is a signal; we interpret the probability as:
    # For UP bet: our_P(UP) = reliability (as stated: reliability is how reliable the TA signal is)
    # Plus UP bias if direction is UP
    # For DOWN bet: our_P(DOWN) = reliability (no UP bias applies)
    # The bias is an "UP bias" - added when betting UP

    if ta_dir == "UP":
        our_p_win = reliability + cal["bias"]
    else:  # DOWN
        our_p_win = reliability  # no UP bias for DOWN bets

    # Market implied probability for our bet direction
    if ta_dir == "UP":
        market_p = market_prob_up
    else:
        market_p = 1.0 - market_prob_up

    edge = our_p_win - market_p

    # Counter-Consensus Rule L023:
    # TA score >= +1 AND market DOWN > 80% (market_implied_prob_up < 0.20 means DOWN > 80%)
    # AND >= 20 min remaining (age <= 40, i.e., if we assume 60-min markets: remaining = 60 - age >= 20 → age <= 40)
    # → bet UP regardless
    market_down_heavy = (1.0 - market_prob_up) > 0.80  # DOWN side > 80%
    minutes_remaining = 60 - age  # assume 60-min market
    counter_consensus_trigger = (ta_score >= 1 and market_down_heavy and minutes_remaining >= 20)

    if counter_consensus_trigger:
        # Override: bet UP
        our_p_win_cc = reliability + cal["bias"]  # UP bet with bias
        market_p_cc = market_prob_up
        edge_cc = our_p_win_cc - market_p_cc
        kelly = (edge_cc * bankroll) / odds
        return {
            "action": "BET_UP",
            "reason": "counter_consensus_L023",
            "our_p_win": round(our_p_win_cc, 4),
            "edge": round(edge_cc, 4),
            "kelly_stake": round(kelly, 4)
        }

    # Edge guard: edge must be >= 10% (0.10)
    if edge < 0.10:
        return {"action": "SKIP", "reason": "edge_too_small", "our_p_win": round(our_p_win, 4), "edge": round(edge, 4), "kelly_stake": None}

    # Kelly stake: (edge × bankroll) / odds  [Argus formula, NOT standard Kelly]
    kelly = (edge * bankroll) / odds

    action = f"BET_{ta_dir}"
    return {
        "action": action,
        "reason": "edge_sufficient",
        "our_p_win": round(our_p_win, 4),
        "edge": round(edge, 4),
        "kelly_stake": round(kelly, 4)
    }

def run_eval(workspace):
    checks = []

    output_path = find_output(workspace)
    if output_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "betting_recommendations.json not found anywhere in workspace"}]
        }

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {output_path}"})

    try:
        with open(output_path) as f:
            result = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.05,
            "checks": checks + [{"name": "json_parseable", "passed": False, "detail": str(e)}]
        }

    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})

    # Load input markets
    input_path = Path(workspace) / "market_data/raw/opportunity_batch.json"
    with open(input_path) as f:
        batch = json.load(f)
    markets = {m["id"]: m for m in batch["markets"]}

    # Compute expected results
    expected = {mid: argus_compute(m) for mid, m in markets.items()}

    # The result should be a list of recommendations or a dict keyed by market id
    # Normalize: support both list and dict
    if isinstance(result, list):
        recs = {r.get("id") or r.get("market_id"): r for r in result}
    elif isinstance(result, dict):
        # Could be {"recommendations": [...]} or {"MKT-001": {...}, ...}
        if "recommendations" in result:
            recs = {r.get("id") or r.get("market_id"): r for r in result["recommendations"]}
        elif "markets" in result:
            recs = {r.get("id") or r.get("market_id"): r for r in result["markets"]}
        else:
            recs = result
    else:
        checks.append({"name": "output_structure", "passed": False, "detail": "Unexpected output type"})
        return {"passed": False, "score": 0.1, "checks": checks}

    checks.append({"name": "output_structure", "passed": True, "detail": f"Parsed {len(recs)} recommendations"})

    # ─── Per-market checks ───────────────────────────────────────────────────

    TOLERANCE = 0.02  # 2% tolerance for float comparisons

    def get_action(rec):
        """Normalize action field."""
        if isinstance(rec, dict):
            return str(rec.get("action", rec.get("recommendation", rec.get("decision", "")))).upper()
        return ""

    def get_val(rec, *keys):
        if isinstance(rec, dict):
            for k in keys:
                if k in rec:
                    return rec[k]
        return None

    market_checks = []

    # MKT-001: BTC, ta_score=3>=3, fresh (22min), consensus 88%<92%, ETH no bias
    # our_P = 0.75 (BTC reliability, no bias), market_P = 0.52, edge = 0.23 >= 0.10 → BET_UP
    # kelly = (0.23 * 1000) / 1.92 = 119.79
    e001 = expected["MKT-001"]
    r001 = recs.get("MKT-001", {})
    a001_ok = "BET" in get_action(r001) and "UP" in get_action(r001)
    e_val = get_val(r001, "edge", "expected_value", "ev")
    k_val = get_val(r001, "kelly_stake", "kelly", "stake", "bet_size")
    e001_edge_ok = e_val is not None and abs(float(e_val) - e001["edge"]) < TOLERANCE
    e001_kelly_ok = k_val is not None and abs(float(k_val) - e001["kelly_stake"]) < TOLERANCE
    market_checks.append({"name": "MKT-001_action_BET_UP", "passed": a001_ok,
                           "detail": f"Expected BET_UP, got {get_action(r001)}"})
    market_checks.append({"name": "MKT-001_edge_value", "passed": e001_edge_ok,
                           "detail": f"Expected edge≈{e001['edge']}, got {e_val}"})
    market_checks.append({"name": "MKT-001_kelly_stake", "passed": e001_kelly_ok,
                           "detail": f"Expected kelly≈{e001['kelly_stake']}, got {k_val}"})

    # MKT-002: ETH, ta_score=2>=2, fresh (15min), consensus 75%<92%
    # our_P = 0.80 + 0.05 = 0.85 (ETH reliability + UP bias), market_P = 0.60, edge = 0.25 >= 0.10 → BET_UP
    # kelly = (0.25 * 1000) / 1.67 = 149.70
    e002 = expected["MKT-002"]
    r002 = recs.get("MKT-002", {})
    a002_ok = "BET" in get_action(r002) and "UP" in get_action(r002)
    e_val2 = get_val(r002, "edge", "expected_value", "ev")
    k_val2 = get_val(r002, "kelly_stake", "kelly", "stake", "bet_size")
    e002_edge_ok = e_val2 is not None and abs(float(e_val2) - e002["edge"]) < TOLERANCE
    e002_kelly_ok = k_val2 is not None and abs(float(k_val2) - e002["kelly_stake"]) < TOLERANCE
    market_checks.append({"name": "MKT-002_action_BET_UP_ETH_bias", "passed": a002_ok,
                           "detail": f"Expected BET_UP (ETH UP bias applied), got {get_action(r002)}"})
    market_checks.append({"name": "MKT-002_edge_with_ETH_bias", "passed": e002_edge_ok,
                           "detail": f"Expected edge≈{e002['edge']} (ETH bias 0.05 included), got {e_val2}"})
    market_checks.append({"name": "MKT-002_kelly_stake", "passed": e002_kelly_ok,
                           "detail": f"Expected kelly≈{e002['kelly_stake']}, got {k_val2}"})

    # MKT-003: BTC, ta_score=2 < BTC min 3 → SKIP
    r003 = recs.get("MKT-003", {})
    a003_raw = get_action(r003)
    a003_ok = "SKIP" in a003_raw or ("BET" not in a003_raw and r003 != {})
    # Also acceptable if MKT-003 simply absent from output
    if not recs.get("MKT-003"):
        a003_ok = True
    market_checks.append({"name": "MKT-003_skip_btc_ta_below_min", "passed": a003_ok,
                           "detail": f"BTC ta_score=2 < min 3 → must SKIP. Got: {a003_raw}"})

    # MKT-004: SOL, ta_score=1>=1 (SOL min), fresh (10min), consensus 70%<92%
    # our_P = 0.90 + 0.05 = 0.95 (SOL reliability + UP bias), market_P = 0.55, edge = 0.40 >= 0.10 → BET_UP
    # kelly = (0.40 * 1000) / 1.82 = 219.78
    e004 = expected["MKT-004"]
    r004 = recs.get("MKT-004", {})
    a004_ok = "BET" in get_action(r004) and "UP" in get_action(r004)
    e_val4 = get_val(r004, "edge", "expected_value", "ev")
    k_val4 = get_val(r004, "kelly_stake", "kelly", "stake", "bet_size")
    e004_edge_ok = e_val4 is not None and abs(float(e_val4) - e004["edge"]) < TOLERANCE
    e004_kelly_ok = k_val4 is not None and abs(float(k_val4) - e004["kelly_stake"]) < TOLERANCE
    market_checks.append({"name": "MKT-004_action_BET_UP_SOL_min1", "passed": a004_ok,
                           "detail": f"SOL min_score=1, ta=1, should BET_UP. Got: {get_action(r004)}"})
    market_checks.append({"name": "MKT-004_edge_SOL_bias", "passed": e004_edge_ok,
                           "detail": f"Expected edge≈{e004['edge']} (SOL bias 0.05), got {e_val4}"})
    market_checks.append({"name": "MKT-004_kelly_stake", "passed": e004_kelly_ok,
                           "detail": f"Expected kelly≈{e004['kelly_stake']}, got {k_val4}"})

    # MKT-005: XRP, consensus=93% > 92% → SKIP
    r005 = recs.get("MKT-005", {})
    a005_raw = get_action(r005)
    a005_ok = "SKIP" in a005_raw or "BET" not in a005_raw
    if not recs.get("MKT-005"):
        a005_ok = True
    market_checks.append({"name": "MKT-005_skip_consensus_guard", "passed": a005_ok,
                           "detail": f"Consensus 93%>92% → SKIP. Got: {a005_raw}"})

    # MKT-006: ETH, age=45 > 30 → not fresh → SKIP
    r006 = recs.get("MKT-006", {})
    a006_raw = get_action(r006)
    a006_ok = "SKIP" in a006_raw or "BET" not in a006_raw
    if not recs.get("MKT-006"):
        a006_ok = True
    market_checks.append({"name": "MKT-006_skip_stale_market", "passed": a006_ok,
                           "detail": f"Age 45min>30min → SKIP. Got: {a006_raw}"})

    # MKT-007: SOL, ta_score=2>=1(SOL min), age=18min, counter-consensus L023
    # market_prob_up=0.15, DOWN=0.85>80%, remaining=60-18=42>=20 → BET_UP (counter-consensus)
    # our_P_UP = 0.90+0.05=0.95, market_P_UP=0.15, edge=0.80, kelly=(0.80*1000)/6.67=119.94
    e007 = expected["MKT-007"]
    r007 = recs.get("MKT-007", {})
    a007_ok = "BET" in get_action(r007) and "UP" in get_action(r007)
    e_val7 = get_val(r007, "edge", "expected_value", "ev")
    k_val7 = get_val(r007, "kelly_stake", "kelly", "stake", "bet_size")
    e007_edge_ok = e_val7 is not None and abs(float(e_val7) - e007["edge"]) < TOLERANCE
    e007_kelly_ok = k_val7 is not None and abs(float(k_val7) - e007["kelly_stake"]) < TOLERANCE
    # Check reason mentions counter-consensus
    reason7 = str(get_val(r007, "reason", "rationale", "note") or "").lower()
    cc_reason_ok = "counter" in reason7 or "l023" in reason7 or "consensus" in reason7
    market_checks.append({"name": "MKT-007_counter_consensus_L023_action", "passed": a007_ok,
                           "detail": f"Counter-consensus L023 → BET_UP. Got: {get_action(r007)}"})
    market_checks.append({"name": "MKT-007_counter_consensus_reason", "passed": cc_reason_ok,
                           "detail": f"Reason should mention counter-consensus/L023. Got: {reason7}"})
    market_checks.append({"name": "MKT-007_edge_counter_consensus", "passed": e007_edge_ok,
                           "detail": f"Expected edge≈{e007['edge']}, got {e_val7}"})
    market_checks.append({"name": "MKT-007_kelly_stake", "passed": e007_kelly_ok,
                           "detail": f"Expected kelly≈{e007['kelly_stake']}, got {k_val7}"})

    # MKT-008: XRP, ta_score=2>=2(XRP min), fresh (28min), consensus 76%<92%
    # XRP UP bias=0.08: our_P = 0.70 + 0.08 = 0.78, market_P = 0.45, edge = 0.33 >= 0.10 → BET_UP
    # kelly = (0.33 * 1000) / 2.22 = 148.65
    e008 = expected["MKT-008"]
    r008 = recs.get("MKT-008", {})
    a008_ok = "BET" in get_action(r008) and "UP" in get_action(r008)
    e_val8 = get_val(r008, "edge", "expected_value", "ev")
    k_val8 = get_val(r008, "kelly_stake", "kelly", "stake", "bet_size")
    e008_edge_ok = e_val8 is not None and abs(float(e_val8) - e008["edge"]) < TOLERANCE
    e008_kelly_ok = k_val8 is not None and abs(float(k_val8) - e008["kelly_stake"]) < TOLERANCE
    market_checks.append({"name": "MKT-008_action_BET_UP_XRP_bias", "passed": a008_ok,
                           "detail": f"XRP UP bias=0.08 applied. Expected BET_UP. Got: {get_action(r008)}"})
    market_checks.append({"name": "MKT-008_edge_XRP_bias", "passed": e008_edge_ok,
                           "detail": f"Expected edge≈{e008['edge']} (XRP bias 0.08), got {e_val8}"})
    market_checks.append({"name": "MKT-008_kelly_stake", "passed": e008_kelly_ok,
                           "detail": f"Expected kelly≈{e008['kelly_stake']}, got {k_val8}"})

    # MKT-009: BTC, ta_score=4>=3, fresh (5min), consensus 80%<92%
    # our_P = 0.75 (BTC, no bias), market_P = 0.80, edge = 0.75-0.80 = -0.05 < 0.10 → SKIP (edge too small)
    r009 = recs.get("MKT-009", {})
    a009_raw = get_action(r009)
    a009_ok = "SKIP" in a009_raw or "BET" not in a009_raw
    if not recs.get("MKT-009"):
        a009_ok = True
    market_checks.append({"name": "MKT-009_skip_edge_too_small", "passed": a009_ok,
                           "detail": f"Edge=-0.05<0.10 → SKIP. Got: {a009_raw}"})

    # MKT-010: SOL DOWN, ta_score=-2 abs=2>=1(SOL min), fresh (8min), consensus 65%<92%
    # DOWN bet: our_P = 0.90 (no UP bias for DOWN), market_P_down = 1-0.65=0.35, edge=0.90-0.35=0.55 → BET_DOWN
    # kelly = (0.55 * 1000) / 1.54 = 357.14
    e010 = expected["MKT-010"]
    r010 = recs.get("MKT-010", {})
    a010_ok = "BET" in get_action(r010) and "DOWN" in get_action(r010)
    e_val10 = get_val(r010, "edge", "expected_value", "ev")
    k_val10 = get_val(r010, "kelly_stake", "kelly", "stake", "bet_size")
    e010_edge_ok = e_val10 is not None and abs(float(e_val10) - e010["edge"]) < TOLERANCE
    e010_kelly_ok = k_val10 is not None and abs(float(k_val10) - e010["kelly_stake"]) < TOLERANCE
    market_checks.append({"name": "MKT-010_action_BET_DOWN_no_bias", "passed": a010_ok,
                           "detail": f"SOL DOWN: no UP bias. Expected BET_DOWN. Got: {get_action(r010)}"})
    market_checks.append({"name": "MKT-010_edge_no_UP_bias_for_DOWN", "passed": e010_edge_ok,
                           "detail": f"Expected edge≈{e010['edge']} (no bias for DOWN), got {e_val10}"})
    market_checks.append({"name": "MKT-010_kelly_stake", "passed": e010_kelly_ok,
                           "detail": f"Expected kelly≈{e010['kelly_stake']}, got {k_val10}"})

    checks.extend(market_checks)

    # ─── Scoring ─────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Must pass ALL critical action checks to be considered passing
    critical = [
        "MKT-001_action_BET_UP",
        "MKT-002_action_BET_UP_ETH_bias",
        "MKT-003_skip_btc_ta_below_min",
        "MKT-004_action_BET_UP_SOL_min1",
        "MKT-005_skip_consensus_guard",
        "MKT-006_skip_stale_market",
        "MKT-007_counter_consensus_L023_action",
        "MKT-008_action_BET_UP_XRP_bias",
        "MKT-009_skip_edge_too_small",
        "MKT-010_action_BET_DOWN_no_bias",
    ]
    critical_check_map = {c["name"]: c["passed"] for c in checks}
    all_critical_passed = all(critical_check_map.get(k, False) for k in critical)

    passed = all_critical_passed and score >= 0.75

    return {"passed": passed, "score": round(score, 4), "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))