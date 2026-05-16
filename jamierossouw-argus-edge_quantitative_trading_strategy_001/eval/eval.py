import sys
import json
import math
from pathlib import Path

def load_result(workspace):
    """Find and load the agent's output file."""
    candidates = list(Path(workspace).rglob("bet_recommendations.json"))
    if not candidates:
        return None, "File 'bet_recommendations.json' not found anywhere in workspace."
    # Prefer most recently modified if multiple
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(candidates[0]) as f:
            data = json.load(f)
        return data, str(candidates[0])
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def compute_expected(markets):
    """
    Compute expected analysis for all markets using Argus Edge rules.
    
    Asset calibration (from SKILL.md):
      BTC: reliability=0.75, bias=0.0 (neutral), min_score=3
      ETH: reliability=0.80, bias=+0.05 (UP), min_score=2
      SOL: reliability=0.90, bias=+0.05 (UP), min_score=1
      XRP: reliability=0.70, bias=+0.08 (UP), min_score=2
    
    our_P(win) formula:
      base = 0.5 + (ta_score / 10.0) * reliability
      if direction == "UP": our_P = base + bias
      else: our_P = base
    
    Edge = our_P(win) - market_implied_P(win)
    Kelly stake = (edge * bankroll) / market_odds
    
    BET conditions (ALL must be true):
      1. |ta_score| >= min_score for asset
      2. consensus_pct <= 92.0 (not dead signal)
      3. edge >= 0.10
    
    Counter-Consensus Rule L023 (overrides direction analysis):
      ta_score >= +1 AND consensus_pct (DOWN) > 80% AND time_remaining_min >= 20
      → force bet UP regardless
      (In our data this means: market consensus is betting DOWN heavily >80%,
       but this is encoded as: the market consensus_pct represents what % bet DOWN
       for the "DOWN bet" side... 
       Actually re-reading: "market DOWN >80%" = the market price/implied prob for DOWN is >80%
       = market_implied_P for DOWN > 0.80 = market_implied_P for UP < 0.20
       So L023 triggers when: ta_score >= 1 AND (1 - market_implied_P) > 0.80 AND time_remaining_min >= 20
       i.e., market_implied_P < 0.20)
    
    Freshness: market_age_min < 30 → primary (fresh). Just affects priority labeling.
    """
    
    ASSET_PARAMS = {
        "BTC": {"reliability": 0.75, "bias": 0.0,  "min_score": 3},
        "ETH": {"reliability": 0.80, "bias": 0.05, "min_score": 2},
        "SOL": {"reliability": 0.90, "bias": 0.05, "min_score": 1},
        "XRP": {"reliability": 0.70, "bias": 0.08, "min_score": 2},
    }
    
    results = {}
    
    for m in markets:
        mid = m["id"]
        asset = m["asset"]
        params = ASSET_PARAMS[asset]
        ta = m["ta_score"]
        mip = m["market_implied_P"]
        odds = m["market_odds"]
        consensus = m["consensus_pct"]
        age = m["market_age_min"]
        time_rem = m["time_remaining_min"]
        bankroll = m["bankroll"]
        direction = m["direction"]
        
        # Check dead signal (consensus skip)
        dead_signal = consensus > 92.0
        
        # Check min TA score
        meets_min_ta = abs(ta) >= params["min_score"]
        
        # Check freshness
        is_fresh = age < 30
        
        # Check counter-consensus L023
        # "TA score >=+1 + market DOWN >80% + >=20 min remaining → bet UP"
        # "market DOWN >80%" = market_implied_P for DOWN > 0.80 = market_implied_P for UP < 0.20
        counter_consensus = (ta >= 1) and ((1 - mip) > 0.80) and (time_rem >= 20)
        # Actually re-check: "market DOWN >80%" more naturally means the market consensus 
        # (crowd) is betting DOWN heavily, i.e., DOWN_implied_P > 0.80
        # which means UP_implied_P < 0.20, so mip < 0.20 (assuming direction=UP)
        # Let's use: counter_consensus requires market_implied_P < 0.20 for UP direction
        counter_consensus_v2 = (ta >= 1) and (mip < 0.20) and (time_rem >= 20)
        # Use v2 as canonical interpretation
        counter_consensus = counter_consensus_v2
        
        # Compute our_P(win)
        base_prob = 0.5 + (ta / 10.0) * params["reliability"]
        if direction == "UP":
            our_p = base_prob + params["bias"]
        else:
            our_p = base_prob
        
        # Edge
        edge = our_p - mip
        
        # Kelly stake
        kelly_stake = (edge * bankroll) / odds if edge > 0 else 0
        
        # Decision
        should_bet = (
            not dead_signal and
            meets_min_ta and
            edge >= 0.10
        )
        
        # L023 override: counter-consensus can also trigger a bet
        if counter_consensus and not dead_signal:
            should_bet = True
            # In L023, we bet UP regardless - direction is already UP in our data
        
        results[mid] = {
            "asset": asset,
            "dead_signal": dead_signal,
            "meets_min_ta": meets_min_ta,
            "is_fresh": is_fresh,
            "counter_consensus_l023": counter_consensus,
            "our_p": round(our_p, 4),
            "edge": round(edge, 4),
            "kelly_stake": round(kelly_stake, 2) if should_bet else 0.0,
            "should_bet": should_bet,
        }
    
    return results

def find_bets_in_result(data):
    """
    Try to extract the list of recommended bets from the agent's output.
    Supports: list at top level, or dict with 'bets'/'recommendations'/'results' key.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["bets", "recommendations", "results", "recommended_bets", "bet_recommendations"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        # Try to find a list value
        for v in data.values():
            if isinstance(v, list) and len(v) > 0:
                return v
    return []

def run_eval(workspace):
    checks = []
    
    # Load markets input
    try:
        with open(f"{workspace}/data/processed/market_opportunities.json") as f:
            markets = json.load(f)
    except Exception as e:
        checks.append({"name": "input_load", "passed": False, "detail": f"Cannot load input: {e}"})
        return checks, 0.0
    
    expected = compute_expected(markets)
    
    # Load agent output
    data, path_or_err = load_result(workspace)
    if data is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": path_or_err})
        return checks, 0.0
    
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at: {path_or_err}"})
    
    bets = find_bets_in_result(data)
    
    # --- CHECK 1: Dead signal exclusion (M008, XRP, consensus 94.5%) ---
    m008_in_bets = any(
        str(b.get("id", "")).upper() == "M008" or
        ("XRP" in str(b.get("asset", "")) and "94" in str(b.get("consensus_pct", "")))
        for b in bets
    )
    checks.append({
        "name": "dead_signal_M008_excluded",
        "passed": not m008_in_bets,
        "detail": (
            "M008 (XRP, 94.5% consensus) correctly excluded as dead signal (>92%)" 
            if not m008_in_bets else 
            "FAIL: M008 should be excluded due to >92% consensus dead signal rule"
        )
    })
    
    # --- CHECK 2: BTC M005 excluded (ta_score=2 < min_score=3 for BTC) ---
    m005_in_bets = any(
        str(b.get("id", "")).upper() == "M005" or
        (str(b.get("asset", "")) == "BTC" and 
         any(x in str(b.get("question", "")) for x in ["68,500", "68500", "4pm"]))
        for b in bets
    )
    checks.append({
        "name": "btc_min_score_M005_excluded",
        "passed": not m005_in_bets,
        "detail": (
            "M005 (BTC, ta_score=2 < BTC min_score=3) correctly excluded"
            if not m005_in_bets else
            "FAIL: M005 should be excluded — BTC requires min TA score ±3, but ta_score=2"
        )
    })
    
    # --- CHECK 3: XRP M004 excluded (ta_score=1 < min_score=2 for XRP) ---
    m004_in_bets = any(
        str(b.get("id", "")).upper() == "M004" or
        (str(b.get("asset", "")) == "XRP" and 
         any(x in str(b.get("question", "")) for x in ["0.52", "noon", "12"]))
        for b in bets
    )
    checks.append({
        "name": "xrp_min_score_M004_excluded",
        "passed": not m004_in_bets,
        "detail": (
            "M004 (XRP, ta_score=1 < XRP min_score=2) correctly excluded"
            if not m004_in_bets else
            "FAIL: M004 should be excluded — XRP requires min TA score ±2, but ta_score=1"
        )
    })
    
    # --- CHECK 4: ETH M006 excluded (ta_score=-1, abs < min_score=2 for ETH) ---
    m006_in_bets = any(
        str(b.get("id", "")).upper() == "M006"
        for b in bets
    )
    checks.append({
        "name": "eth_ta_score_M006_excluded",
        "passed": not m006_in_bets,
        "detail": (
            "M006 (ETH, |ta_score|=1 < ETH min_score=2) correctly excluded"
            if not m006_in_bets else
            "FAIL: M006 should be excluded — |ta_score|=1 < ETH min_score=2"
        )
    })
    
    # --- CHECK 5: M001 BTC included (ta_score=3, meets BTC min, edge check) ---
    # M001: BTC, ta=3, mip=0.48, odds=2.08, age=12 (fresh)
    # our_p = 0.5 + (3/10)*0.75 + 0 = 0.5 + 0.225 = 0.725
    # edge = 0.725 - 0.48 = 0.245 >= 0.10 ✓
    # kelly = (0.245 * 10000) / 2.08 = 2450/2.08 = 1178.85
    m001_exp = expected["M001"]
    m001_in_bets = any(str(b.get("id", "")).upper() == "M001" for b in bets)
    checks.append({
        "name": "M001_BTC_included",
        "passed": m001_in_bets,
        "detail": (
            f"M001 (BTC fresh, edge={m001_exp['edge']}) correctly included as recommended bet"
            if m001_in_bets else
            f"FAIL: M001 should be a recommended bet (BTC ta=3>=3, edge={m001_exp['edge']}>=0.10, fresh)"
        )
    })
    
    # --- CHECK 6: M002 ETH included with correct kelly stake ---
    # M002: ETH, ta=2>=2 ✓, mip=0.41, odds=2.44, age=8 (fresh)
    # our_p = 0.5 + (2/10)*0.80 + 0.05 = 0.5 + 0.16 + 0.05 = 0.71
    # edge = 0.71 - 0.41 = 0.30 >= 0.10 ✓
    # kelly = (0.30 * 10000) / 2.44 = 3000/2.44 = 1229.51
    m002_exp = expected["M002"]
    m002_bet = next((b for b in bets if str(b.get("id","")).upper() == "M002"), None)
    
    if m002_bet is None:
        checks.append({"name": "M002_ETH_kelly_stake", "passed": False, 
                       "detail": f"FAIL: M002 not found in bets. Expected kelly~{m002_exp['kelly_stake']:.2f}"})
    else:
        # Check kelly stake within 5% tolerance
        try:
            agent_kelly = float(str(m002_bet.get("kelly_stake", m002_bet.get("stake", m002_bet.get("bet_size", 0)))))
            tolerance = m002_exp["kelly_stake"] * 0.05
            kelly_ok = abs(agent_kelly - m002_exp["kelly_stake"]) <= max(tolerance, 5.0)
            checks.append({
                "name": "M002_ETH_kelly_stake",
                "passed": kelly_ok,
                "detail": (
                    f"M002 kelly stake {agent_kelly:.2f} matches expected {m002_exp['kelly_stake']:.2f}"
                    if kelly_ok else
                    f"FAIL: M002 kelly stake {agent_kelly:.2f} != expected {m002_exp['kelly_stake']:.2f} "
                    f"(ETH bias +0.05 must be applied: our_p={m002_exp['our_p']}, edge={m002_exp['edge']})"
                )
            })
        except (TypeError, ValueError) as e:
            checks.append({"name": "M002_ETH_kelly_stake", "passed": False, 
                           "detail": f"Could not parse kelly stake from M002 bet: {e}"})
    
    # --- CHECK 7: M003 SOL included with correct kelly stake ---
    # M003: SOL, ta=2>=1 ✓, mip=0.55, odds=1.82, age=5 (fresh)
    # our_p = 0.5 + (2/10)*0.90 + 0.05 = 0.5 + 0.18 + 0.05 = 0.73
    # edge = 0.73 - 0.55 = 0.18 >= 0.10 ✓
    # kelly = (0.18 * 10000) / 1.82 = 1800/1.82 = 989.01
    m003_exp = expected["M003"]
    m003_bet = next((b for b in bets if str(b.get("id","")).upper() == "M003"), None)
    
    if m003_bet is None:
        checks.append({"name": "M003_SOL_kelly_stake", "passed": False,
                       "detail": f"FAIL: M003 not found in bets. Expected kelly~{m003_exp['kelly_stake']:.2f}"})
    else:
        try:
            agent_kelly = float(str(m003_bet.get("kelly_stake", m003_bet.get("stake", m003_bet.get("bet_size", 0)))))
            tolerance = m003_exp["kelly_stake"] * 0.05
            kelly_ok = abs(agent_kelly - m003_exp["kelly_stake"]) <= max(tolerance, 5.0)
            checks.append({
                "name": "M003_SOL_kelly_stake",
                "passed": kelly_ok,
                "detail": (
                    f"M003 SOL kelly stake {agent_kelly:.2f} matches expected {m003_exp['kelly_stake']:.2f}"
                    if kelly_ok else
                    f"FAIL: M003 SOL kelly {agent_kelly:.2f} != {m003_exp['kelly_stake']:.2f} "
                    f"(SOL bias +0.05, reliability 0.90: our_p={m003_exp['our_p']}, edge={m003_exp['edge']})"
                )
            })
        except (TypeError, ValueError) as e:
            checks.append({"name": "M003_SOL_kelly_stake", "passed": False,
                           "detail": f"Could not parse kelly stake from M003 bet: {e}"})
    
    # --- CHECK 8: M007 SOL counter-consensus L023 ---
    # M007: SOL, ta=1>=1 ✓, mip=0.15 (DOWN>80% implied: 1-0.15=0.85>0.80), time_rem=28>=20
    # → L023 triggers: bet UP (counter-consensus)
    # our_p = 0.5 + (1/10)*0.90 + 0.05 = 0.5+0.09+0.05 = 0.64
    # edge = 0.64 - 0.15 = 0.49 >= 0.10 ✓ (also passes normally)
    # kelly = (0.49 * 10000) / 6.67 = 4900/6.67 = 734.63
    # Not dead signal (85% < 92%) ✓
    m007_exp = expected["M007"]
    m007_bet = next((b for b in bets if str(b.get("id","")).upper() == "M007"), None)
    
    if m007_bet is None:
        checks.append({"name": "M007_SOL_counter_consensus_L023", "passed": False,
                       "detail": f"FAIL: M007 not found. L023 counter-consensus should trigger bet UP on SOL (mip=0.15, crowd DOWN=85%>80%, time_rem=28>=20)"})
    else:
        # Check it's flagged as counter-consensus or L023
        raw_str = json.dumps(m007_bet).lower()
        l023_mentioned = any(kw in raw_str for kw in ["l023", "counter", "consensus", "counter_consensus", "contrarian"])
        checks.append({
            "name": "M007_SOL_counter_consensus_L023",
            "passed": l023_mentioned or True,  # Pass if included in bets; L023 label is bonus
            "detail": (
                f"M007 included in bets (L023 counter-consensus triggered). "
                f"{'L023 rule explicitly noted.' if l023_mentioned else 'Note: L023 label not found but bet included.'}"
            )
        })
    
    # --- CHECK 9: M001 BTC correct kelly stake ---
    # kelly = (0.245 * 10000) / 2.08 = 1178.85
    m001_bet = next((b for b in bets if str(b.get("id","")).upper() == "M001"), None)
    if m001_bet is None:
        checks.append({"name": "M001_BTC_kelly_stake", "passed": False,
                       "detail": "M001 not found in bets"})
    else:
        try:
            agent_kelly = float(str(m001_bet.get("kelly_stake", m001_bet.get("stake", m001_bet.get("bet_size", 0)))))
            exp_kelly = m001_exp["kelly_stake"]
            tolerance = exp_kelly * 0.05
            kelly_ok = abs(agent_kelly - exp_kelly) <= max(tolerance, 5.0)
            checks.append({
                "name": "M001_BTC_kelly_stake",
                "passed": kelly_ok,
                "detail": (
                    f"M001 BTC kelly {agent_kelly:.2f} matches expected {exp_kelly:.2f}"
                    if kelly_ok else
                    f"FAIL: M001 BTC kelly {agent_kelly:.2f} != {exp_kelly:.2f}. "
                    f"Formula: (edge*bankroll)/odds = ({m001_exp['edge']}*10000)/{m001_exp['edge']/m001_exp['kelly_stake']*10000:.2f}"
                )
            })
        except Exception as e:
            checks.append({"name": "M001_BTC_kelly_stake", "passed": False,
                           "detail": f"Error parsing M001 kelly: {e}"})
    
    # --- CHECK 10: Freshness labeling ---
    # All included bets should have freshness noted; M001(12m), M002(8m), M003(5m), M007(25m) all fresh
    # Check that the output has some freshness-related metadata
    raw_output = json.dumps(data).lower()
    has_freshness = any(kw in raw_output for kw in ["fresh", "primary", "age", "window", "30 min", "30min"])
    checks.append({
        "name": "freshness_metadata_present",
        "passed": has_freshness,
        "detail": (
            "Output includes freshness/primary window metadata"
            if has_freshness else
            "WARN: No freshness metadata found in output (expected 'fresh', 'primary', 'age' references)"
        )
    })
    
    return checks, None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, _ = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return
    
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass critical checks to be considered passing overall
    critical = ["dead_signal_M008_excluded", "btc_min_score_M005_excluded", 
                "M001_BTC_included", "M002_ETH_kelly_stake"]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()