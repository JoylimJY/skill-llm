import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Find market_analysis_report.json anywhere in workspace."""
    candidates = list(workspace.rglob("market_analysis_report.json"))
    if candidates:
        return candidates[0]
    return None

def score_check(name, condition, detail_pass, detail_fail):
    passed = bool(condition)
    return {"name": name, "passed": passed, "detail": detail_pass if passed else detail_fail}

def run_evaluation(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    
    # =========================================================================
    # CHECK 0: File exists
    # =========================================================================
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append(score_check(
        "report_file_exists",
        file_exists,
        f"Found market_analysis_report.json at {report_path}",
        "market_analysis_report.json not found anywhere in workspace"
    ))
    
    if not file_exists:
        final_score = 0.0
        return {"passed": False, "score": final_score, "checks": checks}
    
    # =========================================================================
    # Load the report
    # =========================================================================
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        report = json.loads(content)
    except json.JSONDecodeError as e:
        checks.append({"name": "report_parseable_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.05, "checks": checks}
    except Exception as e:
        checks.append({"name": "report_parseable_json", "passed": False, "detail": f"File read error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "report_parseable_json", "passed": True, "detail": "Report is valid JSON"})
    
    # Helper: search report text recursively for a keyword
    report_text = content.lower()
    
    def contains_any(keywords, text=None):
        t = (text or report_text).lower()
        return any(k.lower() in t for k in keywords)
    
    def get_nested(d, *keys, default=None):
        for k in keys:
            if isinstance(d, dict):
                # case-insensitive key search
                found = None
                for dk in d:
                    if dk.lower() == k.lower():
                        found = dk
                        break
                if found is None:
                    return default
                d = d[found]
            elif isinstance(d, list):
                try:
                    d = d[k]
                except:
                    return default
            else:
                return default
        return d
    
    # =========================================================================
    # CHECK 1: Layer 1 - RHD markets eliminated
    # Ethiopia (ETH) and Vietnam (VNM) are both RHD and MUST be eliminated
    # =========================================================================
    try:
        eth_eliminated = True
        vnm_eliminated = True
        
        # Look for layer 1 filtering section
        report_str_lower = json.dumps(report).lower()
        
        # Check if Ethiopia is explicitly eliminated/excluded
        eth_in_final = False
        vnm_in_final = False
        
        # Check layer_1 or funnel_layer_1 or similar
        layer1_data = None
        for key in report:
            if "layer" in key.lower() and "1" in key:
                layer1_data = report[key]
                break
            if "funnel" in key.lower():
                layer1_data = report[key]
                break
            if "macro" in key.lower() or "screening" in key.lower() or "filter" in key.lower():
                layer1_data = report[key]
                break
        
        # More robust: look for eliminated markets list
        eliminated_section_text = ""
        for key in report:
            val_str = json.dumps(report[key]).lower()
            if "eliminat" in val_str or "filter" in val_str or "excluded" in val_str or "layer_1" in key.lower() or "layer1" in key.lower():
                eliminated_section_text += val_str
        
        # Check if Ethiopia (ETH/Ethiopia) appears as eliminated due to RHD
        eth_eliminated_mentioned = (
            ("ethiopia" in eliminated_section_text and ("right" in eliminated_section_text or "rh" in eliminated_section_text or "eliminat" in eliminated_section_text))
            or
            ("eth" in eliminated_section_text and ("right" in eliminated_section_text or "eliminat" in eliminated_section_text))
        )
        
        # Vietnam - note: Vietnam is actually LHD (drives on right side of road but cars are LHD)
        # Per the data we set drive_side = "Right" for Vietnam
        # The SKILL.md says: filter out right-hand drive markets
        # The data clearly states Vietnam drive_side = "Right" 
        # Let's check if Vietnam is eliminated
        vnm_eliminated_mentioned = (
            ("vietnam" in eliminated_section_text and ("right" in eliminated_section_text or "eliminat" in eliminated_section_text or "excluded" in eliminated_section_text))
            or
            ("vnm" in eliminated_section_text and ("right" in eliminated_section_text or "eliminat" in eliminated_section_text))
        )
        
        # Also check that the final recommended markets do NOT include ETH or VNM
        final_markets_text = ""
        for key in report:
            if any(w in key.lower() for w in ["final", "recommend", "priorit", "roadmap", "phase", "result", "output"]):
                final_markets_text += json.dumps(report[key]).lower()
        
        # If Ethiopia appears in final recommendations (as positive entry), that's wrong
        eth_in_positive_final = (
            "ethiopia" in final_markets_text and 
            any(w in final_markets_text for w in ["enter", "phase 1", "phase 2", "priority", "recommend enter"])
        )
        vnm_in_positive_final = (
            "vietnam" in final_markets_text and 
            any(w in final_markets_text for w in ["enter", "phase 1", "phase 2", "priority", "recommend enter"])
        )
        
        eth_check_pass = eth_eliminated_mentioned or not eth_in_positive_final
        vnm_check_pass = vnm_eliminated_mentioned or not vnm_in_positive_final
        
        checks.append(score_check(
            "layer1_rhd_elimination_ethiopia",
            eth_eliminated_mentioned,
            "Ethiopia correctly eliminated at Layer 1 due to right-hand drive",
            "Ethiopia (RHD market) not explicitly eliminated at Layer 1 filter"
        ))
        checks.append(score_check(
            "layer1_rhd_elimination_vietnam",
            vnm_eliminated_mentioned,
            "Vietnam correctly eliminated at Layer 1 due to right-hand drive configuration",
            "Vietnam (RHD configuration per data) not explicitly eliminated at Layer 1 filter"
        ))
    except Exception as e:
        checks.append({"name": "layer1_rhd_elimination", "passed": False, "detail": f"Error checking Layer 1 elimination: {e}"})
    
    # =========================================================================
    # CHECK 2: Colombia boundary tariff (exactly 15%) - must PASS Layer 1 filter
    # The rule is ≤15%, so 15% is allowed
    # =========================================================================
    try:
        colombia_text = ""
        for key in report:
            val = json.dumps(report[key]).lower()
            if "colombia" in val or "col" in val:
                colombia_text += val
        
        colombia_not_eliminated_tariff = not (
            "colombia" in colombia_text and 
            ("eliminat" in colombia_text or "excluded" in colombia_text) and
            "tariff" in colombia_text and
            # Only fail if tariff is the reason, not other reasons
            "15" in colombia_text
        )
        
        # More specifically: Colombia should appear in passing Layer 1 candidates
        colombia_passes_l1 = (
            "colombia" in report_text and
            not (
                "colombia" in colombia_text and 
                any(f in colombia_text for f in ["fail layer 1", "eliminated at layer 1", "disqualified", "excluded from layer 1"])
                and "tariff" in colombia_text
            )
        )
        
        checks.append(score_check(
            "layer1_colombia_boundary_tariff_passes",
            colombia_passes_l1,
            "Colombia with exactly 15% tariff correctly passes Layer 1 filter (≤15% rule)",
            "Colombia incorrectly eliminated at Layer 1 despite 15% tariff meeting the ≤15% threshold"
        ))
    except Exception as e:
        checks.append({"name": "layer1_colombia_boundary_tariff", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 3: Weighted Scoring System - correct weights used
    # The SKILL.md specifies: Market Size 15%, Growth 20%, Policy 20%, 
    # Certification 15%, Competition 15%, Payment 10%, Logistics 5%
    # MUST NOT use the deprecated weights (25/25/20/10/10/5/5)
    # =========================================================================
    try:
        scoring_text = report_text
        
        # Look for the correct weights
        has_15pct_market_size = bool(re.search(r'market.{0,30}(size|scale|规模).{0,30}(15%|0\.15)', scoring_text))
        has_20pct_growth = bool(re.search(r'(growth|增速|增长).{0,30}(20%|0\.20)', scoring_text))
        has_20pct_policy = bool(re.search(r'(policy|政策|红利).{0,30}(20%|0\.20)', scoring_text))
        has_15pct_cert = bool(re.search(r'(certif|认证).{0,30}(15%|0\.15)', scoring_text))
        has_15pct_competition = bool(re.search(r'(compet|竞争).{0,30}(15%|0\.15)', scoring_text))
        has_10pct_payment = bool(re.search(r'(payment|pay|付款|外汇).{0,30}(10%|0\.10)', scoring_text))
        has_5pct_logistics = bool(re.search(r'(logistic|物流|港口).{0,30}(5%|0\.05)', scoring_text))
        
        # Also check for deprecated wrong weights - 25% for market size or growth would be wrong
        uses_deprecated_weights = bool(re.search(r'market.{0,30}size.{0,30}25%|25%.{0,30}market.{0,30}size', scoring_text))
        
        correct_weights_count = sum([
            has_15pct_market_size, has_20pct_growth, has_20pct_policy,
            has_15pct_cert, has_15pct_competition, has_10pct_payment, has_5pct_logistics
        ])
        
        weights_mostly_correct = correct_weights_count >= 4 and not uses_deprecated_weights
        
        checks.append(score_check(
            "scorecard_correct_weights_applied",
            weights_mostly_correct,
            f"Correct SKILL.md weights detected ({correct_weights_count}/7 explicit weight references found)",
            f"Correct weights not found (only {correct_weights_count}/7 detected). May be using deprecated weights or generic scoring."
        ))
        
        # Check threshold: must be >4.0, not 3.5 (deprecated)
        uses_correct_threshold = "4" in report_text and not (
            re.search(r'threshold.{0,20}3\.5|3\.5.{0,20}threshold', report_text)
        )
        checks.append(score_check(
            "scorecard_correct_threshold_4point0",
            uses_correct_threshold,
            "Correct threshold (>4.0) referenced, not deprecated 3.5",
            "Uses deprecated threshold (3.5) or missing correct threshold (>4.0)"
        ))
    except Exception as e:
        checks.append({"name": "scorecard_weights_check", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 4: Powertrain recommendations based on SKILL.md rules
    # Kyrgyzstan: cheap fuel (0.55) + cold winters + no charging → ICE or EREV/HEV
    # Uzbekistan: cheap fuel (0.65) + some policy + limited charging → PHEV
    # Colombia: partial subsidy + low charging → PHEV recommended
    # Georgia: temperate + partial subsidy + charging score 3 → could be EV or PHEV
    # =========================================================================
    try:
        powertrain_text = report_text
        
        # Kyrgyzstan: cheap fuel + cold winters + poor charging → ICE or EREV (NOT pure EV)
        kgz_not_pure_ev = not bool(re.search(
            r'kyrgyz.{0,100}(pure.?ev|bev|battery.?electric|纯电)',
            powertrain_text
        ))
        
        # Uzbekistan: cheap fuel + policy partial → PHEV/EREV recommended
        uzb_phev_or_erev = bool(re.search(
            r'uzbek.{0,200}(phev|plug.?in|hybrid|erev|extended.?range|混动|插混)',
            powertrain_text
        ))
        
        checks.append(score_check(
            "powertrain_kyrgyzstan_not_pure_ev",
            kgz_not_pure_ev,
            "Kyrgyzstan correctly avoids pure EV recommendation (cheap fuel + cold + no charging per SKILL.md rules)",
            "Kyrgyzstan incorrectly recommended pure EV despite cheap fuel, cold climate, and lacking charging infra"
        ))
        checks.append(score_check(
            "powertrain_uzbekistan_hybrid_recommended",
            uzb_phev_or_erev,
            "Uzbekistan correctly recommended PHEV/EREV/hybrid (cheap fuel + partial policy + limited charging)",
            "Uzbekistan did not receive PHEV/hybrid/EREV recommendation per SKILL.md powertrain rules"
        ))
    except Exception as e:
        checks.append({"name": "powertrain_recommendations", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 5: Opportunity type classification (Blue Ocean / Growth / Red Ocean)
    # per SKILL.md Layer 2
    # Uzbekistan: 4 Chinese brands, 28% top competitor → Growth Market (not saturated but active)
    # Kyrgyzstan: 2 Chinese brands, 12% share → Blue Ocean or Growth
    # Georgia: 2 Chinese brands, 10% share → Blue Ocean
    # Colombia: 3 Chinese brands → Growth Market
    # =========================================================================
    try:
        opp_text = report_text
        
        has_blue_ocean = contains_any(["blue ocean", "蓝海", "blue-ocean"])
        has_growth_market = contains_any(["growth market", "成长市场", "growing market", "growth opportunity"])
        has_red_ocean = contains_any(["red ocean", "红海", "saturated"])
        
        # Uzbekistan should be classified as Growth (not Blue Ocean, not Red Ocean)
        uzb_growth = bool(re.search(
            r'uzbek.{0,300}(growth market|成长市场|growing|not.{0,20}saturated)',
            opp_text
        ))
        
        # Georgia should be Blue Ocean (small market, 2 Chinese brands, low share)
        geo_blue_ocean = bool(re.search(
            r'georgia.{0,300}(blue.?ocean|蓝海|low.{0,20}competition|pioneer|first.?mover)',
            opp_text
        ))
        
        opportunity_classification_present = has_blue_ocean or has_growth_market
        
        checks.append(score_check(
            "layer2_opportunity_classification_present",
            opportunity_classification_present,
            "Blue Ocean/Growth Market/Red Ocean classification framework applied",
            "No opportunity type classification (Blue Ocean/Growth/Red Ocean) found in report"
        ))
        checks.append(score_check(
            "layer2_uzbekistan_growth_market",
            uzb_growth or ("uzbek" in opp_text and "growth" in opp_text),
            "Uzbekistan classified as Growth Market (Chinese brands present but market unsaturated)",
            "Uzbekistan not classified as Growth Market per Layer 2 competitive analysis rules"
        ))
    except Exception as e:
        checks.append({"name": "layer2_opportunity_classification", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 6: Phased execution roadmap
    # Must follow SKILL.md structure:
    # Phase 1 (1-2 months): Khorgos inventory liquidation → Central Asia + Caucasus
    # Phase 2 (2-4 months): New global markets
    # Phase 3 (4-6 months): Field penetration
    # =========================================================================
    try:
        roadmap_text = report_text
        
        has_phase_structure = bool(re.search(r'phase.{0,10}(1|one|i\b|first)', roadmap_text))
        has_inventory_urgency = contains_any(["inventory", "khorgos", "liquidat", "库存", "霍尔果斯"])
        has_central_asia_phase1 = bool(re.search(
            r'phase.{0,5}1.{0,300}(uzbek|kyrgyz|georgia|central.?asia|caucasus|tbilisi|bishkek|tashkent)',
            roadmap_text
        ))
        
        # Phase 1 should prioritize Uzbekistan, Kyrgyzstan, or Georgia (Khorgos rail markets)
        rail_markets_in_phase1 = bool(re.search(
            r'(phase.{0,5}1|first.{0,10}phase|month.{0,5}[12]).{0,400}(uzbek|kyrgyz|georgia)',
            roadmap_text
        ))
        
        checks.append(score_check(
            "roadmap_phase_structure_present",
            has_phase_structure and has_inventory_urgency,
            "Phased execution roadmap with inventory liquidation priority found",
            "No phased roadmap structure found, or Khorgos inventory urgency not addressed"
        ))
        checks.append(score_check(
            "roadmap_phase1_khorgos_rail_markets",
            rail_markets_in_phase1 or (has_central_asia_phase1),
            "Phase 1 correctly prioritizes Khorgos-adjacent rail markets (Uzbekistan/Kyrgyzstan/Georgia)",
            "Phase 1 does not prioritize rail-accessible Central Asia/Caucasus markets per SKILL.md Phase 1 logic"
        ))
    except Exception as e:
        checks.append({"name": "roadmap_phase_structure", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 7: Risk register with SKILL.md required categories
    # Must cover: Policy risk, FX risk, Competition risk, Inventory risk
    # Must include specific monitoring tools (GoodsFox for competition, IMF/WB for FX)
    # =========================================================================
    try:
        risk_text = report_text
        
        has_policy_risk = contains_any(["policy risk", "政策风险", "tariff risk", "regulatory risk", "关税"])
        has_fx_risk = contains_any(["fx risk", "foreign exchange", "currency risk", "外汇", "exchange rate"])
        has_competition_risk = contains_any(["competition risk", "competitive risk", "竞争风险"])
        has_inventory_risk = contains_any(["inventory risk", "库存风险", "stock risk", "overstock"])
        
        risk_categories_count = sum([has_policy_risk, has_fx_risk, has_competition_risk, has_inventory_risk])
        
        # GoodsFox specifically mentioned for competition monitoring (not SEMrush/SimilarWeb for this purpose)
        has_goodsfox = contains_any(["goodsfox"])
        
        checks.append(score_check(
            "risk_register_four_categories",
            risk_categories_count >= 3,
            f"Risk register covers required categories ({risk_categories_count}/4: policy={has_policy_risk}, FX={has_fx_risk}, competition={has_competition_risk}, inventory={has_inventory_risk})",
            f"Risk register missing required categories (only {risk_categories_count}/4 found)"
        ))
        checks.append(score_check(
            "risk_goodsfox_monitoring_tool",
            has_goodsfox,
            "GoodsFox correctly specified as competition monitoring tool per SKILL.md",
            "GoodsFox not mentioned - SKILL.md specifically requires GoodsFox for quarterly competitive ad intelligence"
        ))
    except Exception as e:
        checks.append({"name": "risk_register", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 8: Final market priority list - must reflect 4 passing markets max
    # (ETH and VNM eliminated, leaving UZB, KGZ, COL, GEO)
    # Report should recommend a subset of these 4
    # =========================================================================
    try:
        final_text = report_text
        
        # Check that the report contains all 4 surviving markets
        uzb_present = "uzbekistan" in final_text or "uzb" in final_text
        kgz_present = "kyrgyzstan" in final_text or "kgz" in final_text or "kyrgyz" in final_text
        col_present = "colombia" in final_text or "col" in final_text
        geo_present = "georgia" in final_text or "geo" in final_text
        
        surviving_markets_count = sum([uzb_present, kgz_present, col_present, geo_present])
        
        checks.append(score_check(
            "final_markets_correct_pool",
            surviving_markets_count >= 3,
            f"Final analysis covers correct pool of Layer-1-surviving markets ({surviving_markets_count}/4 present: UZB={uzb_present}, KGZ={kgz_present}, COL={col_present}, GEO={geo_present})",
            f"Final market pool incomplete: only {surviving_markets_count}/4 surviving markets analyzed"
        ))
        
        # Uzbekistan should score highest (largest market with rail access and 0% tariff and partial policy)
        # Georgia should be high too (0% tariff, rail, FX free, high GDP/capita)
        # Check that at least UZB or GEO appears in top recommendations
        top_recommendations = bool(re.search(
            r'(top|priority|recommended|phase.{0,5}1|first).{0,300}(uzbek|georgia)',
            final_text
        ))
        checks.append(score_check(
            "final_uzbekistan_or_georgia_top_priority",
            top_recommendations,
            "Uzbekistan or Georgia appears in top priority recommendations (0% tariff + rail logistics from Khorgos)",
            "Neither Uzbekistan nor Georgia prioritized despite both having 0% tariff and direct rail access from Khorgos"
        ))
    except Exception as e:
        checks.append({"name": "final_market_priorities", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # CHECK 9: Report structure completeness 
    # Must have sections covering all major areas
    # =========================================================================
    try:
        has_layer1_section = contains_any(["layer 1", "layer_1", "layer1", "第一层", "macro", "macroeconomic", "first layer", "funnel"])
        has_layer2_section = contains_any(["layer 2", "layer_2", "layer2", "第二层", "competitive", "competition analysis", "industry", "second layer"])
        has_scorecard_section = contains_any(["scorecard", "score card", "weighted score", "评分", "scoring"])
        has_roadmap_section = contains_any(["roadmap", "execution", "phase", "timeline", "路线图"])
        has_risk_section = contains_any(["risk", "风险"])
        
        sections_count = sum([has_layer1_section, has_layer2_section, has_scorecard_section, has_roadmap_section, has_risk_section])
        
        checks.append(score_check(
            "report_structure_completeness",
            sections_count >= 4,
            f"Report covers required structural sections ({sections_count}/5: L1={has_layer1_section}, L2={has_layer2_section}, scorecard={has_scorecard_section}, roadmap={has_roadmap_section}, risk={has_risk_section})",
            f"Report missing key sections (only {sections_count}/5 found)"
        ))
    except Exception as e:
        checks.append({"name": "report_structure", "passed": False, "detail": f"Error: {e}"})
    
    # =========================================================================
    # FINAL SCORING
    # =========================================================================
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    
    # Weight critical checks more heavily
    critical_checks = {
        "report_file_exists": 0.10,
        "report_parseable_json": 0.05,
        "layer1_rhd_elimination_ethiopia": 0.10,
        "layer1_rhd_elimination_vietnam": 0.08,
        "layer1_colombia_boundary_tariff_passes": 0.07,
        "scorecard_correct_weights_applied": 0.12,
        "scorecard_correct_threshold_4point0": 0.05,
        "powertrain_kyrgyzstan_not_pure_ev": 0.06,
        "powertrain_uzbekistan_hybrid_recommended": 0.06,
        "layer2_opportunity_classification_present": 0.05,
        "layer2_uzbekistan_growth_market": 0.04,
        "roadmap_phase_structure_present": 0.05,
        "roadmap_phase1_khorgos_rail_markets": 0.05,
        "risk_register_four_categories": 0.04,
        "risk_goodsfox_monitoring_tool": 0.04,
        "final_markets_correct_pool": 0.04,
        "final_uzbekistan_or_georgia_top_priority": 0.04,
        "report_structure_completeness": 0.06,
    }
    
    weighted_score = 0.0
    for check in checks:
        weight = critical_checks.get(check["name"], 0.03)
        if check["passed"]:
            weighted_score += weight
    
    # Normalize to ensure max is 1.0
    max_possible = sum(critical_checks.values())
    normalized_score = min(1.0, weighted_score / max_possible)
    
    overall_passed = (
        checks[0]["passed"] and  # file exists
        checks[1]["passed"] and  # valid JSON
        normalized_score >= 0.60  # at least 60% weighted score
    )
    
    return {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = run_evaluation(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))