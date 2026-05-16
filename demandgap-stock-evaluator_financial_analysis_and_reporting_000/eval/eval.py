import sys
import json
import math
from pathlib import Path

def find_output_file(workspace):
    """Find the agent's output JSON file."""
    candidates = list(Path(workspace).rglob("NSLG_analysis_report.json"))
    if candidates:
        return candidates[0]
    return None

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def approx_equal(val, expected, tolerance=0.15):
    """Check if val is within tolerance% of expected."""
    if expected == 0:
        return abs(val) < 0.01
    return abs(val - expected) / abs(expected) <= tolerance

def run_checks(workspace):
    checks = []

    # --- Find and load the output file ---
    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "NSLG_analysis_report.json not found anywhere in workspace"})
        return checks
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})

    data, err = load_json_safe(output_file)
    if data is None:
        checks.append({"name": "output_file_valid_json", "passed": False, "detail": f"Could not parse JSON: {err}"})
        return checks
    checks.append({"name": "output_file_valid_json", "passed": True, "detail": "File is valid JSON"})

    # =====================================================================
    # CHECK 1: Currency - ALL monetary values must be in EUR (€), not USD ($)
    # =====================================================================
    try:
        currency = str(data.get("currency", data.get("metrics", {}).get("currency", ""))).upper()
        price_val = str(data.get("metrics", {}).get("price", data.get("price", "")))
        market_cap_val = str(data.get("metrics", {}).get("market_cap", data.get("market_cap", "")))
        
        # Check that currency is EUR and price values use €
        uses_eur = (
            "EUR" in currency or "€" in currency or
            "€" in price_val or
            "€" in market_cap_val or
            data.get("currency") == "EUR"
        )
        # Check price does NOT show "$" prefix (USD)
        uses_usd = "$" in price_val or "USD" in currency
        
        passed = uses_eur and not uses_usd
        checks.append({
            "name": "currency_is_euro",
            "passed": passed,
            "detail": f"currency='{currency}', price='{price_val}'. Must use EUR/€, not USD/$"
        })
    except Exception as e:
        checks.append({"name": "currency_is_euro", "passed": False, "detail": f"Error checking currency: {e}"})

    # =====================================================================
    # CHECK 2: Piotroski F-Score calculation
    # Expected: Let's calculate manually
    # ROA FY2024 = 289.2M / 5610M = 5.15% > 0 → +1
    # Operating CF FY2024 = 521.4M > 0 → +1
    # ROA FY2024 (5.15%) vs ROA FY2023 (4.6%) → improving → +1
    # OCF (521.4M) > Net Income (289.2M) → +1
    # Long-term debt: FY2024=1540M < FY2023=1620M → decreasing → +1
    # Current ratio: FY2024=1.5003 vs FY2023=1.4674 → improving → +1
    # No new shares: FY2024=79.8M == FY2023=79.8M → no dilution → +1
    # Gross margin: FY2024=31.0% > FY2023=29.8% → improving → +1
    # Asset turnover: FY2024=0.859 < FY2023=0.878 → NOT improving → 0
    # TOTAL F-SCORE = 8
    # =====================================================================
    try:
        metrics = data.get("metrics", data)
        f_score_raw = metrics.get("f_score", metrics.get("piotroski_f", metrics.get("fScore", None)))
        if f_score_raw is None:
            # Try top level
            f_score_raw = data.get("f_score", data.get("piotroski_f_score", None))
        
        f_score = int(float(f_score_raw)) if f_score_raw is not None else None
        expected_f = 8
        passed = f_score == expected_f
        checks.append({
            "name": "piotroski_f_score_correct",
            "passed": passed,
            "detail": f"Got F-Score={f_score}, expected={expected_f}. Breakdown: ROA>0(+1), OCF>0(+1), ROA improving(+1), OCF>NetIncome(+1), LTDebt decreasing(+1), CurrRatio improving(+1), No dilution(+1), GrossMargin improving(+1), AssetTurnover NOT improving(0)=8"
        })
    except Exception as e:
        checks.append({"name": "piotroski_f_score_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 3: Altman Z-Score calculation
    # Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MarketCap/TotalLiabilities) + 1.0*(Sales/TA)
    # WC = 561M, TA = 5610M, RE = 1890M, EBIT = 434.88M
    # MarketCap = 3420M, TotalLiabilities = 3220M, Sales = 4820M
    # A = 561/5610 = 0.10000
    # B = 1890/5610 = 0.33690
    # C = 434.88/5610 = 0.07751
    # D = 3420/3220 = 1.06211
    # E = 4820/5610 = 0.85918
    # Z = 1.2*0.100 + 1.4*0.3369 + 3.3*0.07751 + 0.6*1.06211 + 1.0*0.85918
    # Z = 0.120 + 0.47167 + 0.25578 + 0.63727 + 0.85918 = 2.3439
    # Expected Z ≈ 2.34 (Grey Zone: 1.81-2.99)
    # =====================================================================
    try:
        z_score_raw = metrics.get("z_score", metrics.get("altman_z", metrics.get("zScore", None)))
        if z_score_raw is None:
            z_score_raw = data.get("z_score", data.get("altman_z_score", None))
        z_score = float(z_score_raw) if z_score_raw is not None else None
        
        expected_z = 2.344  # ±15% tolerance
        passed = z_score is not None and approx_equal(z_score, expected_z, 0.15)
        
        # Also check zone classification
        z_zone = str(metrics.get("z_zone", metrics.get("altman_zone", data.get("z_zone", "")))).lower()
        zone_correct = "grey" in z_zone or "gray" in z_zone or "moderate" in z_zone or "1.81" in z_zone or "2.99" in z_zone
        
        checks.append({
            "name": "altman_z_score_correct",
            "passed": passed,
            "detail": f"Got Z-Score={z_score}, expected≈{expected_z} (Grey Zone). Formula: 1.2*(WC/TA)+1.4*(RE/TA)+3.3*(EBIT/TA)+0.6*(MktCap/TotLiab)+1.0*(Sales/TA)"
        })
        checks.append({
            "name": "altman_z_zone_grey",
            "passed": zone_correct or (z_score is not None and 1.81 <= z_score <= 2.99),
            "detail": f"Z-Score should be in Grey Zone (1.81-2.99), zone='{z_zone}', z={z_score}"
        })
    except Exception as e:
        checks.append({"name": "altman_z_score_correct", "passed": False, "detail": f"Error: {e}"})
        checks.append({"name": "altman_z_zone_grey", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 4: Beneish M-Score
    # M = -4.84 + (-0.920*1.04) + (0.528*0.96) + (0.404*1.08) + (0.892*1.021) + (0.115*0.97) + (-0.172*1.02) + (4.679*0.038) + (-0.327*0.95)
    # = -4.84 + (-0.9568) + (0.50688) + (0.43632) + (0.91075) + (0.11155) + (-0.17544) + (0.17780) + (-0.31065)
    # = -4.84 - 0.9568 + 0.50688 + 0.43632 + 0.91075 + 0.11155 - 0.17544 + 0.17780 - 0.31065
    # = -4.84 + 0.66321 = -4.1368 ≈ -4.14
    # Expected M-Score ≈ -4.14 (< -1.78 → Clean, unlikely manipulator)
    # =====================================================================
    try:
        m_score_raw = metrics.get("m_score", metrics.get("beneish_m", metrics.get("mScore", None)))
        if m_score_raw is None:
            m_score_raw = data.get("m_score", data.get("beneish_m_score", None))
        m_score = float(m_score_raw) if m_score_raw is not None else None
        
        expected_m = -4.137
        passed = m_score is not None and approx_equal(m_score, expected_m, 0.20)
        
        checks.append({
            "name": "beneish_m_score_correct",
            "passed": passed,
            "detail": f"Got M-Score={m_score}, expected≈{expected_m}. Must use formula: M=-4.84+(-0.920*DSRI)+(0.528*GMI)+(0.404*AQI)+(0.892*SGI)+(0.115*DEPI)+(-0.172*SGAI)+(4.679*TATA)+(-0.327*LVGI)"
        })
        
        # Check that M-Score is correctly classified as "clean" (< -1.78)
        m_clean = str(metrics.get("m_interpretation", metrics.get("earnings_quality", data.get("m_clean", "")))).lower()
        m_clean_correct = (
            "clean" in m_clean or "unlikely" in m_clean or "high" in m_clean or
            (m_score is not None and m_score < -1.78)
        )
        checks.append({
            "name": "beneish_m_classified_clean",
            "passed": m_clean_correct,
            "detail": f"M-Score={m_score} should be classified as Clean/High earnings quality (< -1.78 threshold). Got: '{m_clean}'"
        })
    except Exception as e:
        checks.append({"name": "beneish_m_score_correct", "passed": False, "detail": f"Error: {e}"})
        checks.append({"name": "beneish_m_classified_clean", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 5: Max Drawdown (5-Year)
    # Peak = 61.40, Trough after peak... looking at data:
    # Peak in series is 61.40 (from peak_5y). Subsequent trough = 28.90 (from trough_5y)
    # But for 5-year (2020-2025), peak=55.30 (2022), trough=29.40 (2020)... 
    # Actually using the provided peak_5y=61.40 and trough_5y=28.90:
    # MaxDrawdown = (28.90 - 61.40) / 61.40 = -52.93%
    # Expected ≈ -52.9% (High volatility category)
    # =====================================================================
    try:
        dd_raw = metrics.get("max_drawdown", metrics.get("maxDrawdown", metrics.get("max_drawdown_5y", None)))
        if dd_raw is None:
            dd_raw = data.get("max_drawdown", data.get("max_drawdown_5y", None))
        dd = float(str(dd_raw).replace("%", "")) if dd_raw is not None else None
        
        expected_dd = -52.93
        passed = dd is not None and approx_equal(dd, expected_dd, 0.10)
        
        checks.append({
            "name": "max_drawdown_correct",
            "passed": passed,
            "detail": f"Got MaxDrawdown={dd}%, expected≈{expected_dd}%. Formula: (trough-peak)/peak*100 = (28.90-61.40)/61.40*100"
        })
    except Exception as e:
        checks.append({"name": "max_drawdown_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 6: Value Trap Score - must be calculated correctly
    # Price momentum: 12m change = (42.85-51.30)/51.30 = -16.5% → underperforming, ADD 15 points
    # 6m change = (42.85-37.50)/37.50 = +14.3% → positive, ADD 0
    # Combined momentum ≈ 10-15 points
    # Earnings quality: Net income FY2024(289.2M) > FY2023(261.8M) improving → 0 penalty
    # Revenue FY2024(4820M) > FY2023(4721M) → growing → 0 penalty
    # Gross margin improving (31.0% vs 29.8%) → 0 penalty
    # Balance sheet: LT debt decreasing (1540 < 1620) → 0; OCF positive and growing → 0
    # Current ratio 1.50 → healthy → 0
    # Valuation context: P/E = 42.85/3.62 = 11.84, low but improving earnings → partial
    # Expected range: 15-30 (Probably Genuine to Genuine)
    # =====================================================================
    try:
        vt_raw = metrics.get("value_trap_score", metrics.get("valueTrapScore", metrics.get("value_trap", None)))
        if vt_raw is None:
            vt_raw = data.get("value_trap_score", data.get("value_trap", None))
        vt_score = int(float(str(vt_raw).split("(")[0].strip())) if vt_raw is not None else None
        
        # Should be in range 0-39 (Genuine or Probably Genuine)
        # Given improving fundamentals but 12m price decline, expect 10-35
        in_range = vt_score is not None and 0 <= vt_score <= 45
        label_raw = str(metrics.get("value_trap_label", metrics.get("valueTrapLabel", data.get("value_trap_label", "")))).lower()
        label_ok = "genuine" in label_raw or "caution" in label_raw or (vt_score is not None and vt_score < 60)
        
        # Critical: LOWER score = more genuine (not a trap). Check the agent understood this correctly.
        checks.append({
            "name": "value_trap_score_in_range",
            "passed": in_range,
            "detail": f"Value Trap Score={vt_score}. Expected 0-45 (improving fundamentals, mixed momentum). LOWER=genuine, HIGHER=trap."
        })
        checks.append({
            "name": "value_trap_score_direction_correct",
            "passed": label_ok,
            "detail": f"Label='{label_raw}'. Score {vt_score} should be labeled Genuine/Probably Genuine (LOWER=genuine is the correct convention)"
        })
    except Exception as e:
        checks.append({"name": "value_trap_score_in_range", "passed": False, "detail": f"Error: {e}"})
        checks.append({"name": "value_trap_score_direction_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 7: Operative Margin label (NOT "Operating Margin")
    # This is one of the most important proprietary constraints
    # =====================================================================
    try:
        raw_text = json.dumps(data).lower()
        has_operative = "operative" in raw_text
        # Also check in dashboard/metrics section specifically
        metrics_str = json.dumps(metrics).lower() if isinstance(metrics, dict) else raw_text
        has_operative_in_metrics = "operative" in metrics_str
        
        # Check it does NOT use "operating_margin" as the label (it should be operative_margin)
        op_margin_label = metrics.get("operative_margin", metrics.get("operative_margin_label", 
                          metrics.get("opMargin", metrics.get("operating_margin", None))))
        
        # The label must be "operative" not just "operating"
        label_key_check = "operative_margin" in metrics or "operative" in str(metrics.get("op_margin_label", "")).lower()
        
        checks.append({
            "name": "operative_margin_label_used",
            "passed": has_operative,
            "detail": f"Must use 'Operative Margin' label (NOT 'Operating Margin'). Found 'operative' in output: {has_operative}. This is a proprietary label convention."
        })
    except Exception as e:
        checks.append({"name": "operative_margin_label_used", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 8: Operative Margin VALUE correct
    # Operating Income / Revenue = 434,880,000 / 4,820,000,000 = 9.02%
    # =====================================================================
    try:
        op_margin = (
            metrics.get("operative_margin") or
            metrics.get("opMargin") or
            metrics.get("operating_margin") or
            data.get("operative_margin")
        )
        op_val = float(str(op_margin).replace("%", "")) if op_margin is not None else None
        expected_op = 9.02
        passed = op_val is not None and approx_equal(op_val, expected_op, 0.05)
        checks.append({
            "name": "operative_margin_value_correct",
            "passed": passed,
            "detail": f"Got Operative Margin={op_val}%, expected≈{expected_op}%. EBIT(434.88M)/Revenue(4820M)*100"
        })
    except Exception as e:
        checks.append({"name": "operative_margin_value_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 9: Investor Persona Scores - all 8 must be present and in 0-10 range
    # =====================================================================
    persona_keys = [
        ("buffett", ["buffettScore", "buffett_score", "warren_buffett"]),
        ("munger", ["mungerScore", "munger_score", "charlie_munger"]),
        ("dalio", ["dalioScore", "dalio_score", "ray_dalio"]),
        ("lynch", ["lynchScore", "lynch_score", "peter_lynch"]),
        ("graham", ["grahamScore", "graham_score", "benjamin_graham"]),
        ("greenblatt", ["greenblattScore", "greenblatt_score", "joel_greenblatt"]),
        ("templeton", ["templetonScore", "templeton_score", "john_templeton"]),
        ("soros", ["sorosScore", "soros_score", "george_soros"]),
    ]
    
    persona_data = metrics.get("investor_personas", metrics.get("personas", data.get("investor_personas", metrics)))
    
    personas_found = 0
    personas_valid = 0
    persona_details = []
    
    for persona_name, keys in persona_keys:
        found_val = None
        for key in keys:
            val = persona_data.get(key) if isinstance(persona_data, dict) else None
            if val is None and isinstance(metrics, dict):
                val = metrics.get(key)
            if val is not None:
                found_val = val
                break
        
        if found_val is not None:
            personas_found += 1
            try:
                score = float(found_val)
                if 0 <= score <= 10:
                    personas_valid += 1
                    persona_details.append(f"{persona_name}={score}✓")
                else:
                    persona_details.append(f"{persona_name}={score}(OUT OF RANGE)")
            except:
                persona_details.append(f"{persona_name}=INVALID({found_val})")
        else:
            persona_details.append(f"{persona_name}=MISSING")
    
    checks.append({
        "name": "all_8_investor_personas_present",
        "passed": personas_found >= 8,
        "detail": f"Found {personas_found}/8 personas: {', '.join(persona_details)}"
    })
    checks.append({
        "name": "investor_persona_scores_valid_range",
        "passed": personas_valid >= 7,
        "detail": f"Valid scores (0-10): {personas_valid}/8. Details: {', '.join(persona_details)}"
    })

    # =====================================================================
    # CHECK 10: Peter Lynch Score specifically
    # PEG = P/E / Growth Rate
    # P/E = 42.85 / 3.62 = 11.84
    # Revenue growth (reported YoY) = (4820-4721)/4721 = 2.10%
    # Earnings growth (reported YoY) = (289.2-261.8)/261.8 = 10.47%
    # For Lynch, use earnings growth: PEG = 11.84 / 10.47 = 1.131
    # PEG 1.0-1.5 → 6 points base
    # +1 if earnings growing consistently (yes, revenue grew) → +1
    # +1 if business easy to understand (logistics = yes) → +1
    # Lynch score = 6+1+1 = 8 (but reasonable range 5-8 given data)
    # =====================================================================
    try:
        lynch_score = None
        for key in ["lynchScore", "lynch_score", "peter_lynch"]:
            v = metrics.get(key) or (persona_data.get(key) if isinstance(persona_data, dict) else None)
            if v is not None:
                lynch_score = float(v)
                break
        
        passed = lynch_score is not None and 4 <= lynch_score <= 9
        checks.append({
            "name": "lynch_score_plausible",
            "passed": passed,
            "detail": f"Lynch Score={lynch_score}. Expected 4-9 based on PEG≈1.13 (P/E=11.84, EPS growth=10.47%). PEG 1.0-1.5→6 base pts."
        })
    except Exception as e:
        checks.append({"name": "lynch_score_plausible", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 11: Graham Score
    # P/E = 11.84 < 15 → +2
    # P/B = 1.43 < 1.5 → +2
    # Current ratio FY2024 = 1682/1121 = 1.50 < 2 → 0 (NOT > 2)
    # Positive earnings 10 years → only 7 years given → 0
    # Dividend paid 20+ years → only 8 years → 0
    # Graham score = 4/10
    # =====================================================================
    try:
        graham_score = None
        for key in ["grahamScore", "graham_score", "benjamin_graham"]:
            v = metrics.get(key) or (persona_data.get(key) if isinstance(persona_data, dict) else None)
            if v is not None:
                graham_score = float(v)
                break
        
        passed = graham_score is not None and 2 <= graham_score <= 6
        checks.append({
            "name": "graham_score_plausible",
            "passed": passed,
            "detail": f"Graham Score={graham_score}. Expected 2-6. P/E<15(+2), P/B<1.5(+2), CurrentRatio 1.5 NOT>2(0), Earnings<10yrs(0), Dividends<20yrs(0)=4"
        })
    except Exception as e:
        checks.append({"name": "graham_score_plausible", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 12: Reported Revenue Growth (must use REPORTED, not organic/underlying)
    # Revenue FY2024=4820M, FY2023=4721M
    # YoY reported growth = (4820-4721)/4721 = 2.097% ≈ 2.1%
    # =====================================================================
    try:
        rev_growth = (
            metrics.get("rev_growth") or
            metrics.get("revGrowth") or
            metrics.get("revenue_growth") or
            data.get("revenue_growth_yoy")
        )
        rv = float(str(rev_growth).replace("%", "")) if rev_growth is not None else None
        expected_rv = 2.097
        passed = rv is not None and approx_equal(rv, expected_rv, 0.15)
        checks.append({
            "name": "reported_revenue_growth_correct",
            "passed": passed,
            "detail": f"Got RevGrowth={rv}%, expected≈{expected_rv}%. Must use REPORTED growth: (4820M-4721M)/4721M*100. NOT organic/underlying."
        })
    except Exception as e:
        checks.append({"name": "reported_revenue_growth_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 13: Reported Earnings Growth
    # Net Income FY2024=289.2M, FY2023=261.8M
    # Growth = (289.2-261.8)/261.8 = 10.47%
    # =====================================================================
    try:
        earn_growth = (
            metrics.get("earn_growth") or
            metrics.get("earnGrowth") or
            metrics.get("earnings_growth") or
            data.get("earnings_growth_yoy")
        )
        eg = float(str(earn_growth).replace("%", "")) if earn_growth is not None else None
        expected_eg = 10.47
        passed = eg is not None and approx_equal(eg, expected_eg, 0.15)
        checks.append({
            "name": "reported_earnings_growth_correct",
            "passed": passed,
            "detail": f"Got EarningsGrowth={eg}%, expected≈{expected_eg}%. Must use REPORTED: (289.2M-261.8M)/261.8M*100"
        })
    except Exception as e:
        checks.append({"name": "reported_earnings_growth_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 14: FCF Margin = FCF/Revenue × 100
    # FCF = 323.4M, Revenue = 4820M
    # FCF Margin = 323.4/4820 * 100 = 6.71%
    # =====================================================================
    try:
        fcf_margin = (
            metrics.get("fcf_margin") or
            metrics.get("fcfMargin") or
            data.get("fcf_margin")
        )
        fm = float(str(fcf_margin).replace("%", "")) if fcf_margin is not None else None
        expected_fm = 6.71
        passed = fm is not None and approx_equal(fm, expected_fm, 0.10)
        checks.append({
            "name": "fcf_margin_correct",
            "passed": passed,
            "detail": f"Got FCF Margin={fm}%, expected≈{expected_fm}%. Formula: FCF(323.4M)/Revenue(4820M)*100"
        })
    except Exception as e:
        checks.append({"name": "fcf_margin_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 15: PEG Ratio (1Y)
    # P/E = 42.85 / 3.62 = 11.84
    # Use reported earnings growth for PEG: 10.47%
    # PEG (1Y) = 11.84 / 10.47 = 1.131
    # =====================================================================
    try:
        peg = (
            metrics.get("peg1Y") or
            metrics.get("peg_1y") or
            metrics.get("peg") or
            data.get("peg_ratio")
        )
        pg = float(peg) if peg is not None else None
        expected_peg = 1.131
        passed = pg is not None and approx_equal(pg, expected_peg, 0.25)
        checks.append({
            "name": "peg_ratio_correct",
            "passed": passed,
            "detail": f"Got PEG={pg}, expected≈{expected_peg}. P/E(11.84)/EarningsGrowth(10.47%)=1.13"
        })
    except Exception as e:
        checks.append({"name": "peg_ratio_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 16: Recommendation must be BUY, HOLD, or SELL (present and explicit)
    # Given Z-score in grey zone, F-score=8 (excellent), M-score clean,
    # P/E=11.84 (cheap), margin of safety present, logistics company...
    # Reasonable to expect HOLD or BUY (not SELL)
    # =====================================================================
    try:
        rec = str(
            data.get("recommendation") or
            data.get("verdict") or
            metrics.get("recommendation") or
            ""
        ).upper().strip()
        
        valid_rec = any(r in rec for r in ["BUY", "HOLD", "SELL", "AVOID", "STRONG BUY"])
        not_sell_without_alts = True
        
        if "SELL" in rec or "AVOID" in rec:
            # If SELL, must provide alternatives
            alts = data.get("alternatives", data.get("alternative_candidates", []))
            not_sell_without_alts = len(alts) >= 3
        
        checks.append({
            "name": "clear_recommendation_present",
            "passed": valid_rec,
            "detail": f"Recommendation='{rec}'. Must be one of: BUY/HOLD/SELL/AVOID/STRONG BUY"
        })
        checks.append({
            "name": "sell_includes_alternatives",
            "passed": not_sell_without_alts,
            "detail": f"If SELL/AVOID: must provide 3-5 alternative candidates. rec='{rec}'"
        })
    except Exception as e:
        checks.append({"name": "clear_recommendation_present", "passed": False, "detail": f"Error: {e}"})
        checks.append({"name": "sell_includes_alternatives", "passed": True, "detail": f"Error checking: {e}"})

    # =====================================================================
    # CHECK 17: Conviction rating must be present
    # =====================================================================
    try:
        conviction = str(
            data.get("conviction") or
            metrics.get("conviction") or
            ""
        ).lower()
        valid_conv = any(c in conviction for c in ["strong buy", "buy", "hold", "avoid", "strong"])
        checks.append({
            "name": "conviction_rating_present",
            "passed": valid_conv,
            "detail": f"Conviction='{conviction}'. Must be: Strong Buy/Buy/Hold/Avoid"
        })
    except Exception as e:
        checks.append({"name": "conviction_rating_present", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 18: Greenblatt Magic Formula metrics present (EY and ROC)
    # EY = EBIT/EV; EV ≈ MarketCap + TotalDebt - Cash = 3420+1870-412 = 4878M
    # EY = 434.88/4878 = 8.92%
    # ROC = EBIT/(Net Fixed Assets + Working Capital)
    # Net Fixed Assets ≈ Total Assets - Current Assets = 5610-1682 = 3928M
    # ROC = 434.88/(3928+561) = 434.88/4489 = 9.69%
    # =====================================================================
    try:
        ey = (
            metrics.get("greenblattEY") or
            metrics.get("greenblatt_ey") or
            metrics.get("earnings_yield") or
            data.get("greenblatt_earnings_yield")
        )
        roc = (
            metrics.get("greenblattROC") or
            metrics.get("greenblatt_roc") or
            metrics.get("return_on_capital") or
            data.get("greenblatt_roc")
        )
        
        ey_val = float(str(ey).replace("%", "")) if ey is not None else None
        roc_val = float(str(roc).replace("%", "")) if roc is not None else None
        
        ey_ok = ey_val is not None and approx_equal(ey_val, 8.92, 0.20)
        roc_ok = roc_val is not None and approx_equal(roc_val, 9.69, 0.25)
        
        checks.append({
            "name": "greenblatt_ey_correct",
            "passed": ey_ok,
            "detail": f"Got EY={ey_val}%, expected≈8.92%. EY=EBIT(434.88M)/EV(MktCap+Debt-Cash=4878M)*100"
        })
        checks.append({
            "name": "greenblatt_roc_correct",
            "passed": roc_ok,
            "detail": f"Got ROC={roc_val}%, expected≈9.69%. ROC=EBIT(434.88M)/(NetFixedAssets(3928M)+WC(561M))*100"
        })
    except Exception as e:
        checks.append({"name": "greenblatt_ey_correct", "passed": False, "detail": f"Error: {e}"})
        checks.append({"name": "greenblatt_roc_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 19: FCF Growth 5Y (smoothed/CAGR)
    # FCF: 2020=198M, 2021=260M, 2022=285M, 2023=301.5M, 2024=323.4M
    # CAGR = (323.4/198)^(1/4) - 1 = (1.6333)^0.25 - 1 = 1.1314 - 1 = 13.14%
    # =====================================================================
    try:
        fcf_g = (
            metrics.get("fcfGrowth5Y") or
            metrics.get("fcf_growth_5y") or
            metrics.get("fcf_growth") or
            data.get("fcf_growth_5y")
        )
        fcg = float(str(fcf_g).replace("%", "")) if fcf_g is not None else None
        expected_fcg = 13.14
        passed = fcg is not None and approx_equal(fcg, expected_fcg, 0.25)
        checks.append({
            "name": "fcf_growth_5y_correct",
            "passed": passed,
            "detail": f"Got FCFGrowth5Y={fcg}%, expected≈{expected_fcg}%. CAGR from FCF(2020=198M) to FCF(2024=323.4M) over 4 years"
        })
    except Exception as e:
        checks.append({"name": "fcf_growth_5y_correct", "passed": False, "detail": f"Error: {e}"})

    # =====================================================================
    # CHECK 20: ROA FY2024 correctly calculated
    # ROA = Net Income / Total Assets = 289.2M / 5610M = 5.155%
    # (Note: provided derived_ratios_raw has roa_fy2023 = 4.6%, but agent must compute FY2024)
    # =====================================================================
    try:
        roa = (
            metrics.get("roa") or
            metrics.get("ROA") or
            data.get("roa")
        )
        roa_val = float(str(roa).replace("%", "")) if roa is not None else None
        expected_roa = 5.155
        passed = roa_val is not None and approx_equal(roa_val, expected_roa, 0.10)
        checks.append({
            "name": "roa_fy2024_correct",
            "passed": passed,
            "detail": f"Got ROA={roa_val}%, expected≈{expected_roa}%. NetIncome(289.2M)/TotalAssets(5610M)*100. Note: don't use the pre-provided FY2023 ROA=4.6%"
        })
    except Exception as e:
        checks.append({"name": "roa_fy2024_correct", "passed": False, "detail": f"Error: {e}"})

    return checks


def main():
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]

    checks = run_checks(workspace)

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0

    # Hard gates: certain critical checks must pass
    critical_checks = [
        "output_file_exists",
        "output_file_valid_json",
        "piotroski_f_score_correct",
        "altman_z_score_correct",
        "operative_margin_label_used",
        "all_8_investor_personas_present",
        "clear_recommendation_present",
        "currency_is_euro",
    ]
    critical_passed = all(
        any(c["name"] == ck and c["passed"] for c in checks)
        for ck in critical_checks
    )

    result = {
        "passed": critical_passed and score >= 0.70,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()