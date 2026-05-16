import sys
import json
import re
import os
from pathlib import Path

def find_report(workspace):
    """Search for the valuation memo file anywhere in workspace."""
    for pattern in ["HPG_valuation_memo.md", "HPG_valuation_memo.json", "HPG_valuation_memo.txt"]:
        found = list(Path(workspace).rglob(pattern))
        if found:
            return found[0], pattern.split(".")[-1]
    # Fallback: any file with 'HPG' and 'memo' or 'valuation' in name
    for f in Path(workspace).rglob("*"):
        name = f.name.lower()
        if "hpg" in name and ("memo" in name or "valuation" in name) and f.suffix in [".md", ".txt", ".json"]:
            return f, f.suffix.lstrip(".")
    return None, None

def read_report(workspace):
    path, fmt = find_report(workspace)
    if path is None:
        return None, None, "Report file not found"
    try:
        content = path.read_text(encoding="utf-8")
        return content, fmt, None
    except Exception as e:
        return None, None, str(e)

def check_section_order(content):
    """Verify all 9 required sections appear in the correct order."""
    required_sections = [
        r"executive\s+summary",
        r"what\s+data\s+was\s+used",
        r"core\s+thesis",
        r"valuation\s+work",
        r"business\s+quality\s+assessment",
        r"risk\s+register",
        r"fair\s+value\s+and\s+safety\s+zone",
        r"confidence\s+and\s+gaps",
        r"disclaimer",
    ]
    positions = []
    for pat in required_sections:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            positions.append((pat, m.start()))
        else:
            positions.append((pat, -1))
    missing = [p for p, pos in positions if pos == -1]
    out_of_order = False
    valid_positions = [pos for _, pos in positions if pos != -1]
    if valid_positions != sorted(valid_positions):
        out_of_order = True
    return missing, out_of_order, positions

def check_confidence_tier(content):
    """Must be Medium (not High) due to missing CFO and minor BS inconsistency."""
    c = content.lower()
    # Accept 'medium' confidence explicitly stated
    has_medium = bool(re.search(r'\bmedium\b', c))
    has_high_only = bool(re.search(r'\bhigh\s+confidence\b', c)) and not has_medium
    # Should NOT claim High confidence as the overall tier
    wrongly_high = bool(re.search(r'confidence[^.:\n]*:\s*high', c, re.IGNORECASE))
    return has_medium, wrongly_high

def check_cyclical_adaptation(content):
    """Must use normalized margin (not peak), and cycle-risk as first-class risk item."""
    c = content.lower()
    normalized = bool(re.search(r'normaliz', c))
    cycle_risk = bool(re.search(r'cycl', c))
    not_peak = bool(re.search(r'peak\s+margin', c))  # mentioning to reject it is ok
    # Check that peak margin is NOT used uncritically as the base assumption
    peak_as_assumption = bool(re.search(r'(use|using|based on|assume|assumption)[^.\n]*peak\s+margin', c, re.IGNORECASE))
    return normalized, cycle_risk, not peak_as_assumption

def check_scenarios(content):
    """Must have Bull, Base, Bear scenarios."""
    c = content.lower()
    has_bull = bool(re.search(r'\bbull\b', c))
    has_base = bool(re.search(r'\bbase\b', c))
    has_bear = bool(re.search(r'\bbear\b', c))
    return has_bull, has_base, has_bear

def check_margin_of_safety_language(content):
    """Must not say 'buy' or 'sell' as direct commands; must use approved language."""
    c = content.lower()
    # Check for approved terms
    approved = bool(re.search(r'(appears\s+undervalued|appears\s+fairly\s+valued|appears\s+stretched|margin.of.safety)', c))
    # Check for banned direct commands
    banned = bool(re.search(r'\b(buy\s+this|sell\s+this|recommend\s+buying|recommend\s+selling|strong\s+buy|strong\s+sell)\b', c))
    return approved, not banned

def check_conditional_action_framing(content):
    """Must include trigger to add risk, trigger to reduce risk, invalidation, horizon."""
    c = content.lower()
    has_add_trigger = bool(re.search(r'trigger\s+to\s+add|add\s+risk', c))
    has_reduce_trigger = bool(re.search(r'trigger\s+to\s+reduce|reduce\s+risk', c))
    has_invalidation = bool(re.search(r'invalidat', c))
    has_horizon = bool(re.search(r'\bhorizon\b', c))
    return has_add_trigger, has_reduce_trigger, has_invalidation, has_horizon

def check_conclusion_label(content):
    """Must use Attractive, Watchlist, or Caution."""
    c = content.lower()
    labels = ["attractive", "watchlist", "caution"]
    found = [l for l in labels if re.search(r'\b' + l + r'\b', c)]
    return len(found) > 0, found

def check_data_quality_flags(content):
    """Must flag: missing CFO, BS inconsistency, stale date."""
    c = content.lower()
    cfo_flagged = bool(re.search(r'(cash\s+flow|cfo|operating\s+cash)', c))
    inconsistency_flagged = bool(re.search(r'(inconsisten|balance\s+sheet|assets?\s*[=!≠]|delta|discrepan)', c))
    staleness_flagged = bool(re.search(r'(stale|fresh|cutoff|cut.off|data\s+as\s+of|2024.03)', c))
    return cfo_flagged, inconsistency_flagged, staleness_flagged

def check_multiples_table(content):
    """Must have a multiples comparison (current vs peer vs implied)."""
    c = content.lower()
    has_pe = bool(re.search(r'p/?e', c))
    has_pb = bool(re.search(r'p/?b', c))
    has_ev_ebitda = bool(re.search(r'ev/?ebitda|ev\s*/\s*ebitda', c))
    has_peer_comparison = bool(re.search(r'(peer|sector\s+median|hsg|nkg|tlh)', c))
    return has_pe, has_pb, has_ev_ebitda, has_peer_comparison

def check_sensitivity_grid(content):
    """DCF sensitivity: WACC ±100bps, terminal growth ±50bps OR clearly stated DCF was skipped with reason."""
    c = content.lower()
    dcf_present = bool(re.search(r'\bdcf\b', c))
    sensitivity = bool(re.search(r'(sensitivit|wacc.*±|±.*wacc|terminal.*growth|±.*bps|bps.*±)', c))
    dcf_skipped = bool(re.search(r'(dcf\s+skipped|skip.*dcf|not\s+run.*dcf|dcf.*not\s+run|dcf.*fragile|fragile.*dcf|dcf.*excluded|excluded.*dcf)', c))
    # Pass if sensitivity present OR dcf explicitly skipped with reason
    return dcf_present, sensitivity, dcf_skipped

def check_business_quality_checklist(content):
    """Must assess: moat, governance, earnings quality, balance-sheet risk, cyclicality, execution."""
    c = content.lower()
    items = {
        "moat/pricing_power": bool(re.search(r'(moat|pricing\s+power)', c)),
        "governance": bool(re.search(r'governance', c)),
        "earnings_quality": bool(re.search(r'(earnings\s+quality|cash\s+conversion|accrual)', c)),
        "balance_sheet_risk": bool(re.search(r'(balance.sheet\s+risk|leverage|debt)', c)),
        "cyclicality": bool(re.search(r'cyclic', c)),
        "execution": bool(re.search(r'execution', c)),
    }
    return items

def check_disclaimer(content):
    """Must have educational/not personalized investment advice disclaimer."""
    c = content.lower()
    return bool(re.search(r'(educational|not\s+personalized|not\s+investment\s+advice|for\s+informational)', c))

def run_eval(workspace):
    checks = []
    total_weight = 0
    total_score = 0

    content, fmt, err = read_report(workspace)

    # ── Check 0: File exists ────────────────────────────────────────────────
    file_exists = content is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_exists,
        "detail": err if not file_exists else f"Found report file ({fmt})"
    })
    if not file_exists:
        output = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(output))
        return

    # ── Check 1: All 9 sections present and in correct order ───────────────
    missing_sections, out_of_order, _ = check_section_order(content)
    sections_ok = len(missing_sections) == 0 and not out_of_order
    detail = ""
    if missing_sections:
        detail += f"Missing sections: {missing_sections}. "
    if out_of_order:
        detail += "Sections are out of the required order."
    if sections_ok:
        detail = "All 9 sections present and in correct order."
    checks.append({"name": "nine_sections_in_order", "passed": sections_ok, "detail": detail})

    # ── Check 2: Confidence tier is Medium (not High) ──────────────────────
    has_medium, wrongly_high = check_confidence_tier(content)
    conf_ok = has_medium and not wrongly_high
    checks.append({
        "name": "confidence_tier_medium",
        "passed": conf_ok,
        "detail": (
            f"medium_stated={has_medium}, wrongly_claimed_high={wrongly_high}. "
            "Missing CFO + BS inconsistency must yield Medium confidence."
        )
    })

    # ── Check 3: Data quality flags (CFO missing, BS inconsistency, staleness)
    cfo_f, bs_f, stale_f = check_data_quality_flags(content)
    dq_ok = cfo_f and bs_f and stale_f
    checks.append({
        "name": "data_quality_flags",
        "passed": dq_ok,
        "detail": f"cfo_flagged={cfo_f}, bs_inconsistency_flagged={bs_f}, staleness_flagged={stale_f}"
    })

    # ── Check 4: Cyclical sector adaptation ────────────────────────────────
    normalized, cycle_risk, no_peak_assumption = check_cyclical_adaptation(content)
    cyclical_ok = normalized and cycle_risk and no_peak_assumption
    checks.append({
        "name": "cyclical_sector_adaptation",
        "passed": cyclical_ok,
        "detail": (
            f"normalized_margin_mentioned={normalized}, cycle_risk_flagged={cycle_risk}, "
            f"peak_margin_not_used_uncritically={no_peak_assumption}"
        )
    })

    # ── Check 5: Three scenarios present ───────────────────────────────────
    h_bull, h_base, h_bear = check_scenarios(content)
    scenarios_ok = h_bull and h_base and h_bear
    checks.append({
        "name": "three_scenarios_present",
        "passed": scenarios_ok,
        "detail": f"bull={h_bull}, base={h_base}, bear={h_bear}"
    })

    # ── Check 6: Multiples table with peer comparison ──────────────────────
    has_pe, has_pb, has_ev_ev, has_peer = check_multiples_table(content)
    multiples_ok = has_pe and has_pb and has_ev_ev and has_peer
    checks.append({
        "name": "multiples_table_with_peers",
        "passed": multiples_ok,
        "detail": f"P/E={has_pe}, P/B={has_pb}, EV/EBITDA={has_ev_ev}, peer_comparison={has_peer}"
    })

    # ── Check 7: Sensitivity grid OR explicit DCF skip with reason ─────────
    dcf_present, sensitivity, dcf_skipped = check_sensitivity_grid(content)
    sensitivity_ok = (dcf_present and sensitivity) or dcf_skipped
    checks.append({
        "name": "dcf_sensitivity_or_skip_with_reason",
        "passed": sensitivity_ok,
        "detail": (
            f"dcf_mentioned={dcf_present}, sensitivity_grid={sensitivity}, "
            f"dcf_explicitly_skipped={dcf_skipped}"
        )
    })

    # ── Check 8: Business quality checklist ────────────────────────────────
    bq_items = check_business_quality_checklist(content)
    bq_count = sum(bq_items.values())
    bq_ok = bq_count >= 5
    checks.append({
        "name": "business_quality_checklist",
        "passed": bq_ok,
        "detail": f"Items covered ({bq_count}/6): {bq_items}"
    })

    # ── Check 9: Margin of safety language ─────────────────────────────────
    mos_approved, no_buy_sell = check_margin_of_safety_language(content)
    mos_ok = mos_approved and no_buy_sell
    checks.append({
        "name": "margin_of_safety_language",
        "passed": mos_ok,
        "detail": f"approved_language={mos_approved}, no_direct_buy_sell_commands={no_buy_sell}"
    })

    # ── Check 10: Conditional action framing ───────────────────────────────
    add_t, reduce_t, inval, horizon = check_conditional_action_framing(content)
    action_ok = add_t and reduce_t and inval and horizon
    checks.append({
        "name": "conditional_action_framing",
        "passed": action_ok,
        "detail": (
            f"trigger_add={add_t}, trigger_reduce={reduce_t}, "
            f"invalidation={inval}, horizon={horizon}"
        )
    })

    # ── Check 11: Conclusion label ─────────────────────────────────────────
    label_ok, labels = check_conclusion_label(content)
    checks.append({
        "name": "conclusion_label",
        "passed": label_ok,
        "detail": f"Found labels: {labels}. Must be one of: Attractive, Watchlist, Caution."
    })

    # ── Check 12: Disclaimer ───────────────────────────────────────────────
    disc_ok = check_disclaimer(content)
    checks.append({
        "name": "disclaimer_present",
        "passed": disc_ok,
        "detail": "Must state educational/not personalized investment advice."
    })

    # ── Scoring ────────────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 1,
        "nine_sections_in_order": 2,
        "confidence_tier_medium": 2,
        "data_quality_flags": 2,
        "cyclical_sector_adaptation": 2,
        "three_scenarios_present": 1,
        "multiples_table_with_peers": 2,
        "dcf_sensitivity_or_skip_with_reason": 1,
        "business_quality_checklist": 1,
        "margin_of_safety_language": 1,
        "conditional_action_framing": 1,
        "conclusion_label": 1,
        "disclaimer_present": 1,
    }

    total_weight = sum(weights.values())
    total_score = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(total_score / total_weight, 3)
    passed = score >= 0.75

    output = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)