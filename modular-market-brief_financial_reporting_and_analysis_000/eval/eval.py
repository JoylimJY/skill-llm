import sys
import json
import re
from pathlib import Path

def find_brief(workspace: Path) -> Path | None:
    """Find pm_brief.md anywhere under workspace/reports/"""
    candidates = list((workspace / "reports").rglob("pm_brief.md"))
    if candidates:
        return candidates[0]
    # Also search workspace root just in case
    root_candidates = list(workspace.rglob("pm_brief.md"))
    return root_candidates[0] if root_candidates else None

def check_section_present(content: str, pattern: str, flags=re.IGNORECASE) -> bool:
    return bool(re.search(pattern, content, flags))

def eval_main(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    score = 0.0

    # ── CHECK 0: File exists ──────────────────────────────────────────────────
    try:
        brief_path = find_brief(workspace)
        exists = brief_path is not None and brief_path.exists()
        checks.append({
            "name": "pm_brief.md exists under reports/",
            "passed": exists,
            "detail": str(brief_path) if exists else "File not found anywhere under workspace"
        })
        if not exists:
            return {"passed": False, "score": 0.0, "checks": checks}
        content = brief_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "pm_brief.md exists under reports/", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 1: PM framing (not AM) ──────────────────────────────────────────
    try:
        # Must indicate PM session, afternoon, or end-of-day context
        pm_pattern = r'\b(PM|afternoon|pm brief|pm session|end.?of.?day|EOD|wrap.?up)\b'
        has_pm = check_section_present(content, pm_pattern)
        checks.append({
            "name": "Report framed as PM/afternoon session",
            "passed": has_pm,
            "detail": "Found PM framing" if has_pm else "No PM/afternoon framing found in content"
        })
    except Exception as e:
        checks.append({"name": "Report framed as PM/afternoon session", "passed": False, "detail": str(e)})

    # ── CHECK 2: TL;DR section with 3–6 bullets ───────────────────────────────
    try:
        tldr_match = re.search(r'TL[;:\s]?DR.{0,200}', content, re.IGNORECASE | re.DOTALL)
        if tldr_match:
            tldr_block = content[tldr_match.start():tldr_match.start()+600]
            bullets = re.findall(r'^\s*[-•*]\s+.+', tldr_block, re.MULTILINE)
            bullet_count = len(bullets)
            has_tldr = 3 <= bullet_count <= 6
            detail = f"Found {bullet_count} bullets in TL;DR block"
        else:
            has_tldr = False
            detail = "TL;DR section not found"
        checks.append({"name": "TL;DR section with 3-6 bullets", "passed": has_tldr, "detail": detail})
    except Exception as e:
        checks.append({"name": "TL;DR section with 3-6 bullets", "passed": False, "detail": str(e)})

    # ── CHECK 3: Equities section covering required tickers ───────────────────
    try:
        required_equity = ["SPY", "QQQ", "IWM", "EWZ", "FXI"]
        missing = [t for t in required_equity if t not in content.upper() and t not in content]
        # Case-insensitive check
        missing = [t for t in required_equity if not re.search(re.escape(t), content, re.IGNORECASE)]
        has_equities = len(missing) == 0
        checks.append({
            "name": "Equities section: all required tickers present (SPY,QQQ,IWM,EWZ,FXI)",
            "passed": has_equities,
            "detail": f"Missing tickers: {missing}" if missing else "All equity tickers present"
        })
    except Exception as e:
        checks.append({"name": "Equities section: all required tickers present", "passed": False, "detail": str(e)})

    # ── CHECK 4: Rates section ────────────────────────────────────────────────
    try:
        # Must reference 10Y treasury and 3M/short-end rates
        has_10y = bool(re.search(r'10[Yy]|TNX|10-[Yy]ear', content))
        has_short = bool(re.search(r'3[Mm]\s*(bill|T-bill|IRX)|2[Yy]|short.?end', content, re.IGNORECASE))
        has_rates = has_10y and has_short
        checks.append({
            "name": "Rates section: 10Y and short-end rates referenced",
            "passed": has_rates,
            "detail": f"10Y found: {has_10y}, short-end found: {has_short}"
        })
    except Exception as e:
        checks.append({"name": "Rates section: 10Y and short-end rates referenced", "passed": False, "detail": str(e)})

    # ── CHECK 5: FX section ───────────────────────────────────────────────────
    try:
        required_fx = ["DXY", "EURUSD", "USDJPY"]
        fx_aliases = {"DXY": ["DXY", "DX-Y", "dollar index", "USD index"],
                      "EURUSD": ["EURUSD", "EUR/USD", "EUR-USD"],
                      "USDJPY": ["USDJPY", "USD/JPY", "USD-JPY"]}
        fx_found = {}
        for key, aliases in fx_aliases.items():
            fx_found[key] = any(re.search(re.escape(a), content, re.IGNORECASE) for a in aliases)
        has_fx = all(fx_found.values())
        checks.append({
            "name": "FX section: DXY, EURUSD, USDJPY present",
            "passed": has_fx,
            "detail": str(fx_found)
        })
    except Exception as e:
        checks.append({"name": "FX section: DXY, EURUSD, USDJPY present", "passed": False, "detail": str(e)})

    # ── CHECK 6: Commodities section ──────────────────────────────────────────
    try:
        commodity_patterns = {
            "WTI/Oil": [r'\bWTI\b', r'\bcrude\b', r'\bCL=F\b', r'\bBrent\b'],
            "Gold": [r'\bGold\b', r'\bGC=F\b', r'\bXAU\b'],
            "Copper": [r'\bCopper\b', r'\bHG=F\b']
        }
        commod_found = {}
        for name, pats in commodity_patterns.items():
            commod_found[name] = any(re.search(p, content, re.IGNORECASE) for p in pats)
        has_commodities = all(commod_found.values())
        checks.append({
            "name": "Commodities section: WTI, Gold, Copper present",
            "passed": has_commodities,
            "detail": str(commod_found)
        })
    except Exception as e:
        checks.append({"name": "Commodities section: WTI, Gold, Copper present", "passed": False, "detail": str(e)})

    # ── CHECK 7: Crypto section ───────────────────────────────────────────────
    try:
        has_btc = bool(re.search(r'\bBTC\b|\bBitcoin\b', content, re.IGNORECASE))
        has_eth = bool(re.search(r'\bETH\b|\bEthereum\b', content, re.IGNORECASE))
        has_crypto = has_btc and has_eth
        checks.append({
            "name": "Crypto section: BTC and ETH present",
            "passed": has_crypto,
            "detail": f"BTC: {has_btc}, ETH: {has_eth}"
        })
    except Exception as e:
        checks.append({"name": "Crypto section: BTC and ETH present", "passed": False, "detail": str(e)})

    # ── CHECK 8: Top Movers section with gainers AND losers ───────────────────
    try:
        has_movers_section = bool(re.search(r'top\s*mover|gainer|loser', content, re.IGNORECASE))
        # Must have both gainers and losers
        has_gainers = bool(re.search(r'gainer', content, re.IGNORECASE))
        has_losers = bool(re.search(r'loser', content, re.IGNORECASE))
        # Count movers mentioned (should have at least 3 per side or 6 total symbols)
        movers_ok = has_movers_section and has_gainers and has_losers
        checks.append({
            "name": "Top Movers section: gainers and losers both present",
            "passed": movers_ok,
            "detail": f"Section: {has_movers_section}, Gainers: {has_gainers}, Losers: {has_losers}"
        })
    except Exception as e:
        checks.append({"name": "Top Movers section: gainers and losers present", "passed": False, "detail": str(e)})

    # ── CHECK 9: Trend / Pattern box with BUY/SELL/WAIT labels ───────────────
    try:
        has_trend_section = bool(re.search(r'pattern|trend\s*box|trend\s*label|signal', content, re.IGNORECASE))
        has_buy = bool(re.search(r'\bBUY\b', content))
        has_sell = bool(re.search(r'\bSELL\b', content))
        has_wait = bool(re.search(r'\bWAIT\b', content))
        # Must have at least two of the three labels (real data will produce varied results)
        label_count = sum([has_buy, has_sell, has_wait])
        has_trend = has_trend_section and label_count >= 2
        checks.append({
            "name": "Patterns/Trend Box: BUY/SELL/WAIT labels present (>=2 distinct labels)",
            "passed": has_trend,
            "detail": f"Trend section: {has_trend_section}, BUY: {has_buy}, SELL: {has_sell}, WAIT: {has_wait}, distinct labels: {label_count}"
        })
    except Exception as e:
        checks.append({"name": "Patterns/Trend Box with BUY/SELL/WAIT labels", "passed": False, "detail": str(e)})

    # ── CHECK 10: Trend label rationale (MA + RSI mention) ───────────────────
    try:
        # The skill mandates a one-line rationale referencing MA/RSI logic
        has_ma = bool(re.search(r'\bMA\d{0,3}\b|moving\s*average|MA20|MA50', content, re.IGNORECASE))
        has_rsi = bool(re.search(r'\bRSI\b', content, re.IGNORECASE))
        has_rationale = has_ma and has_rsi
        checks.append({
            "name": "Trend labels include MA and RSI rationale",
            "passed": has_rationale,
            "detail": f"MA mention: {has_ma}, RSI mention: {has_rsi}"
        })
    except Exception as e:
        checks.append({"name": "Trend labels include MA and RSI rationale", "passed": False, "detail": str(e)})

    # ── CHECK 11: One Best Idea with invalidation scenario ───────────────────
    try:
        has_best_idea = bool(re.search(r'best\s*idea|top\s*idea|conviction|best.?trade', content, re.IGNORECASE))
        # CRITICAL: must include invalidation
        has_invalidation = bool(re.search(r'invalidat|stop.?loss|stops?\s+at|risk\s+scenario|if\s+.{0,40}breaks?|downside\s+risk|exit\s+if', content, re.IGNORECASE))
        best_idea_ok = has_best_idea and has_invalidation
        checks.append({
            "name": "One Best Idea section with explicit invalidation scenario",
            "passed": best_idea_ok,
            "detail": f"Best idea found: {has_best_idea}, Invalidation found: {has_invalidation}"
        })
    except Exception as e:
        checks.append({"name": "One Best Idea with invalidation scenario", "passed": False, "detail": str(e)})

    # ── CHECK 12: Aggressive risk framing (not conservative language) ─────────
    try:
        # Aggressive framing: should NOT be dominated by purely conservative language
        # Should have conviction language — "strong", "momentum", "upside", "target", "aggressive"
        aggressive_terms = r'\baggressive\b|\bstrong\b|\bmomentum\b|\bupside\b|\btarget\b|\bbullish\b|\bbearish\b|\bhigh conviction\b'
        conservative_only = bool(re.search(r'\bconservative\b', content, re.IGNORECASE))
        has_aggressive = bool(re.search(aggressive_terms, content, re.IGNORECASE))
        # Pass if aggressive framing present (conservative alone = wrong risk profile)
        risk_ok = has_aggressive
        checks.append({
            "name": "Report uses aggressive risk framing (conviction language present)",
            "passed": risk_ok,
            "detail": f"Aggressive framing found: {has_aggressive}"
        })
    except Exception as e:
        checks.append({"name": "Aggressive risk framing", "passed": False, "detail": str(e)})

    # ── CHECK 13: Section ordering (structural integrity) ─────────────────────
    try:
        section_patterns = [
            ("TL;DR",       r'TL[;:\s]?DR'),
            ("Equities",    r'##\s*Equities|###\s*Equities|\*\*Equities'),
            ("Rates",       r'##\s*Rates|###\s*Rates|\*\*Rates'),
            ("FX",          r'##\s*FX|###\s*FX|\*\*FX'),
            ("Commodities", r'##\s*Commodit|###\s*Commodit|\*\*Commodit'),
            ("Crypto",      r'##\s*Crypto|###\s*Crypto|\*\*Crypto'),
            ("Movers",      r'##\s*Top\s*Mover|###\s*Top\s*Mover|\*\*Top\s*Mover'),
            ("Trends",      r'##\s*Pattern|###\s*Pattern|##\s*Trend|###\s*Trend|\*\*Pattern|\*\*Trend'),
            ("Best Idea",   r'##\s*One\s*Best|###\s*One\s*Best|##\s*Best\s*Idea|\*\*Best\s*Idea|\*\*One\s*Best'),
        ]
        positions = {}
        for name, pattern in section_patterns:
            m = re.search(pattern, content, re.IGNORECASE)
            positions[name] = m.start() if m else None

        found_sections = {k: v for k, v in positions.items() if v is not None}
        # At least 7 of 9 sections must be present and in correct relative order
        ordered_found = sorted(found_sections.items(), key=lambda x: x[1])
        expected_order = [s[0] for s in section_patterns]
        actual_order = [s[0] for s in ordered_found]

        # Check if the actual order is a subsequence of expected order
        exp_idx = 0
        in_order = 0
        for sec in actual_order:
            while exp_idx < len(expected_order) and expected_order[exp_idx] != sec:
                exp_idx += 1
            if exp_idx < len(expected_order):
                in_order += 1
                exp_idx += 1

        sections_ok = len(found_sections) >= 7 and in_order == len(actual_order)
        checks.append({
            "name": "Report has >= 7 of 9 required sections in correct order",
            "passed": sections_ok,
            "detail": f"Found {len(found_sections)} sections, {in_order} in correct order. Actual: {actual_order}"
        })
    except Exception as e:
        checks.append({"name": "Section ordering check", "passed": False, "detail": str(e)})

    # ── CHECK 14: No certainty language (finance guardrails) ──────────────────
    try:
        certainty_patterns = [
            r'\bwill definitely\b',
            r'\bguaranteed\b',
            r'\bcertain(ly)? to\b',
            r'\b100%\s+(sure|certain|confident)\b',
            r'\bno risk\b',
        ]
        certainty_hits = [p for p in certainty_patterns if re.search(p, content, re.IGNORECASE)]
        no_certainty = len(certainty_hits) == 0
        checks.append({
            "name": "Finance guardrail: no absolute certainty language",
            "passed": no_certainty,
            "detail": f"Certainty phrases found: {certainty_hits}" if certainty_hits else "Clean — no certainty language detected"
        })
    except Exception as e:
        checks.append({"name": "Finance guardrail check", "passed": False, "detail": str(e)})

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weighted scoring: critical checks get higher weight
    weights = {
        0: 0.05,   # file exists
        1: 0.05,   # PM framing
        2: 0.07,   # TL;DR bullets
        3: 0.08,   # equity tickers
        4: 0.06,   # rates
        5: 0.06,   # fx
        6: 0.06,   # commodities
        7: 0.06,   # crypto
        8: 0.07,   # movers
        9: 0.10,   # trend labels (PROPRIETARY)
        10: 0.08,  # MA/RSI rationale (PROPRIETARY)
        11: 0.10,  # best idea + invalidation (PROPRIETARY)
        12: 0.05,  # aggressive framing
        13: 0.08,  # section ordering
        14: 0.03,  # guardrails
    }
    total_weight = sum(weights.values())
    score = sum(weights[i] for i, c in enumerate(checks) if c["passed"]) / total_weight

    # Must pass the three proprietary checks (9, 10, 11) to pass overall
    proprietary_passed = all(checks[i]["passed"] for i in [9, 10, 11] if i < len(checks))
    # Must also have file and at least 9/15 checks passing
    check_pass_count = sum(1 for c in checks if c["passed"])
    overall_passed = (
        checks[0]["passed"] and          # file exists
        proprietary_passed and           # proprietary logic correct
        check_pass_count >= 9            # broad coverage
    )

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = eval_main(sys.argv[1])
    print(json.dumps(result, indent=2))