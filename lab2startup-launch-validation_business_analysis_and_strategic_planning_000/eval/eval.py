import sys
import json
import math
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # --- Find the output file ---
    output_file = None
    candidates = list(Path(workspace_dir).rglob("startup_assessment.json"))
    if candidates:
        output_file = candidates[0]

    add_check(
        "output_file_exists",
        output_file is not None,
        f"Found startup_assessment.json at: {output_file}" if output_file else "startup_assessment.json not found anywhere in workspace",
        weight=1.0
    )

    if output_file is None:
        final_score = 0.0
        return {"passed": False, "score": final_score, "checks": checks}

    # --- Load and parse the file ---
    data = None
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        add_check("output_is_valid_json", True, "File parsed as valid JSON.", weight=0.5)
    except Exception as e:
        add_check("output_is_valid_json", False, f"Failed to parse JSON: {e}", weight=0.5)
        final_score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": final_score, "checks": checks}

    # =============================================================
    # CHECK 1: Weighted Technology Commercialization Score
    # Weights from SKILL.md: 技术创新性 20%, 市场需求度 25%, 技术成熟度 20%,
    #                         竞争优势 15%, 团队匹配度 10%, 资源可获得性 10%
    # Raw scores: 9, 8, 7, 8, 6, 5
    # Weighted score = 9*0.20 + 8*0.25 + 7*0.20 + 8*0.15 + 6*0.10 + 5*0.10
    #                = 1.80 + 2.00 + 1.40 + 1.20 + 0.60 + 0.50 = 7.50
    # As 100-point scale: 7.50 * 10 = 75.0
    # Decision: > 70 -> "强烈推荐转化"
    # =============================================================
    EXPECTED_WEIGHTED_SCORE = 9*0.20 + 8*0.25 + 7*0.20 + 8*0.15 + 6*0.10 + 5*0.10  # = 7.50
    EXPECTED_SCORE_100 = EXPECTED_WEIGHTED_SCORE * 10  # = 75.0
    EXPECTED_RECOMMENDATION = "strongly_recommended"  # or equivalent Chinese: 强烈推荐转化

    # Find score in data structure (flexible key search)
    found_score = None
    found_recommendation = None
    score_section = None

    # Try common key names
    for key in ["commercialization_assessment", "technology_assessment", "scoring", "技术商业化评估", "assessment"]:
        if key in data:
            score_section = data[key]
            break

    if score_section is None:
        # Try top-level
        score_section = data

    for key in ["total_score", "weighted_score", "score", "总分", "加权总分"]:
        if key in score_section:
            try:
                found_score = float(score_section[key])
            except (TypeError, ValueError):
                pass
            break

    # Check if score is approximately correct (within 0.5 on 100-point scale)
    score_correct = False
    score_detail = "Score key not found in output"
    if found_score is not None:
        # Handle both 0-10 and 0-100 scale
        if abs(found_score - EXPECTED_SCORE_100) <= 0.5:
            score_correct = True
            score_detail = f"Correct score {found_score} ≈ {EXPECTED_SCORE_100} (100-point scale)"
        elif abs(found_score - EXPECTED_WEIGHTED_SCORE) <= 0.05:
            score_correct = True
            score_detail = f"Correct score {found_score} ≈ {EXPECTED_WEIGHTED_SCORE} (10-point scale)"
        else:
            score_detail = (
                f"Wrong score: got {found_score}, expected ~{EXPECTED_SCORE_100} (100-pt) "
                f"or ~{EXPECTED_WEIGHTED_SCORE} (10-pt). "
                f"Naive equal-weight average would be (9+8+7+8+6+5)/6*10=71.7 — that is WRONG."
            )

    add_check("correct_weighted_score", score_correct, score_detail, weight=2.5)

    # Check recommendation matches ">70 => 强烈推荐"
    recommendation_correct = False
    rec_detail = "Recommendation key not found"
    for key in ["recommendation", "decision", "建议", "推荐", "结论"]:
        if key in score_section:
            found_recommendation = str(score_section[key])
            break
    if found_recommendation is None:
        # try top level
        for key in ["recommendation", "decision", "建议", "推荐", "结论"]:
            if key in data:
                found_recommendation = str(data[key])
                break

    if found_recommendation is not None:
        val_lower = found_recommendation.lower()
        if any(kw in val_lower for kw in ["强烈推荐", "strongly", "strongly_recommend", "strong", "推荐转化"]):
            recommendation_correct = True
            rec_detail = f"Correct recommendation: '{found_recommendation}' (score >70 → 强烈推荐转化)"
        else:
            rec_detail = f"Wrong recommendation: '{found_recommendation}'. Score is 75 (>70), so should be '强烈推荐转化'."
    
    add_check("correct_recommendation_threshold", recommendation_correct, rec_detail, weight=1.5)

    # =============================================================
    # CHECK 2: Funding Calculation
    # Formula from SKILL.md: 资金需求 = 月度burn rate × 达到下一里程碑的月份 × 1.5
    # = 230000 × 8 × 1.5 = 2,760,000
    # Stage: 种子轮 (50万-300万) — NO, 276万 is in 种子轮? 
    # 种子轮: 50-300万; 天使轮: 300-1000万
    # 276万 is ABOVE 300万? 276 < 300, so it's seed round (种子轮) upper range
    # Actually 276万 = 2,760,000 yuan. 种子轮: 50-300万 (500,000-3,000,000). 276万 < 300万 YES => 种子轮
    # =============================================================
    EXPECTED_FUNDING = 230000 * 8 * 1.5  # = 2,760,000
    EXPECTED_STAGE = "seed"  # 种子轮 (50万-300万 = 500k-3M yuan)

    found_funding = None
    found_stage = None
    funding_section = None

    for key in ["funding", "financing", "融资规划", "funding_requirement", "资金需求"]:
        if key in data:
            funding_section = data[key]
            break

    if funding_section is None:
        funding_section = data

    for key in ["required_amount", "amount", "总需求", "资金需求金额", "funding_amount", "required_funding"]:
        if key in funding_section:
            try:
                found_funding = float(funding_section[key])
            except (TypeError, ValueError):
                pass
            break

    for key in ["stage", "funding_stage", "阶段", "融资阶段", "round"]:
        if key in funding_section:
            found_stage = str(funding_section[key])
            break

    funding_correct = False
    funding_detail = "Funding amount key not found"
    if found_funding is not None:
        if abs(found_funding - EXPECTED_FUNDING) <= 1000:
            funding_correct = True
            funding_detail = f"Correct funding amount: {found_funding} ≈ {EXPECTED_FUNDING} (burn_rate × months × 1.5)"
        else:
            funding_detail = (
                f"Wrong funding: got {found_funding}, expected {EXPECTED_FUNDING}. "
                f"Formula: 230000 × 8 × 1.5 = 2,760,000. "
                f"Missing the 1.5 safety factor gives 1,840,000 — that is WRONG."
            )

    add_check("correct_funding_formula_with_safety_factor", funding_correct, funding_detail, weight=2.5)

    # Check stage classification
    stage_correct = False
    stage_detail = "Stage key not found"
    if found_stage is not None:
        s_lower = found_stage.lower()
        if any(kw in s_lower for kw in ["seed", "种子", "种子轮"]):
            stage_correct = True
            stage_detail = f"Correct stage: '{found_stage}' (2,760,000 yuan falls in 种子轮 range 500k-3M)"
        else:
            stage_detail = f"Wrong stage: '{found_stage}'. 276万元 falls in 种子轮 (50-300万)."

    add_check("correct_funding_stage_classification", stage_correct, stage_detail, weight=1.0)

    # =============================================================
    # CHECK 3: Market Validation KPI Assessment
    # CAC=15000, LTV=52000
    # Rule: CAC < LTV/3 → 15000 < 52000/3 = 17333.3 → PASS (healthy)
    # Rule: LTV > CAC×3 → 52000 > 45000 → PASS (healthy)
    # MAU growth: 23.5% → "持续增长" → PASS
    # B2B retention: 38% → health standard >40% → FAIL (unhealthy)  ← KEY TRAP
    # NPS: 34 → health standard >30 → PASS (healthy)
    # =============================================================
    kpi_section = None
    for key in ["market_validation", "kpi_assessment", "关键指标", "kpis", "商业模式验证", "validation"]:
        if key in data:
            kpi_section = data[key]
            break

    if kpi_section is None:
        kpi_section = data

    # Check CAC/LTV health
    cac_ltv_correct = False
    cac_ltv_detail = "CAC/LTV assessment not found"
    
    cac_status = None
    ltv_status = None
    
    # Search for CAC status
    for key in ["CAC", "cac", "客户获取成本"]:
        if key in kpi_section:
            cac_entry = kpi_section[key]
            if isinstance(cac_entry, dict):
                for sk in ["status", "healthy", "health", "状态", "is_healthy"]:
                    if sk in cac_entry:
                        cac_status = cac_entry[sk]
                        break
            break

    # Check if CAC is marked as healthy (15000 < 17333.3 → healthy)
    if cac_status is not None:
        s = str(cac_status).lower()
        if any(kw in s for kw in ["healthy", "健康", "pass", "通过", "true", "达标"]):
            cac_ltv_correct = True
            cac_ltv_detail = f"CAC correctly marked healthy: CAC=15000 < LTV/3={52000/3:.1f}"
        else:
            cac_ltv_detail = f"CAC incorrectly marked: '{cac_status}'. 15000 < {52000/3:.1f} → should be healthy"
    else:
        cac_ltv_detail = "CAC status field not found in KPI section"

    add_check("cac_ltv_health_correct", cac_ltv_correct, cac_ltv_detail, weight=1.0)

    # KEY TRAP: B2B retention rate = 38% which is BELOW the 40% threshold
    # General knowledge might say 38% is fine; SKILL.md says >40% for B2B
    retention_correct = False
    retention_detail = "B2B retention assessment not found"
    
    for key in ["retention", "留存率", "b2b_retention", "retention_rate"]:
        if key in kpi_section:
            ret_entry = kpi_section[key]
            if isinstance(ret_entry, dict):
                for sk in ["status", "healthy", "health", "状态", "is_healthy", "passed"]:
                    if sk in ret_entry:
                        ret_status = ret_entry[sk]
                        s = str(ret_status).lower()
                        if any(kw in s for kw in ["unhealthy", "不健康", "fail", "不达标", "false", "below", "低于", "未达标"]):
                            retention_correct = True
                            retention_detail = f"B2B retention correctly flagged UNHEALTHY: 38% < 40% (SKILL.md B2B standard)"
                        else:
                            retention_detail = (
                                f"B2B retention incorrectly assessed: '{ret_status}'. "
                                f"38% < 40% threshold for B2B → should be UNHEALTHY. "
                                f"(General SaaS standard of ~80% is irrelevant here)"
                            )
                        break
            break

    add_check("b2b_retention_correctly_flagged_unhealthy", retention_correct, retention_detail, weight=2.0)

    # Check NPS > 30 → healthy (NPS=34)
    nps_correct = False
    nps_detail = "NPS assessment not found"
    
    for key in ["NPS", "nps", "净推荐值"]:
        if key in kpi_section:
            nps_entry = kpi_section[key]
            if isinstance(nps_entry, dict):
                for sk in ["status", "healthy", "health", "状态", "is_healthy"]:
                    if sk in nps_entry:
                        nps_status = nps_entry[sk]
                        s = str(nps_status).lower()
                        if any(kw in s for kw in ["healthy", "健康", "pass", "通过", "true", "达标"]):
                            nps_correct = True
                            nps_detail = f"NPS correctly marked healthy: NPS=34 > 30 threshold"
                        else:
                            nps_detail = f"NPS incorrectly assessed: '{nps_status}'. NPS=34 > 30 → should be healthy"
                        break
            break

    add_check("nps_health_correct", nps_correct, nps_detail, weight=1.0)

    # =============================================================
    # FINAL SCORING
    # =============================================================
    final_score = total_score / max_score if max_score > 0 else 0.0

    # Must pass core checks to be considered overall passing
    core_checks_passed = sum(1 for c in checks if c["passed"] and c["name"] in [
        "correct_weighted_score",
        "correct_funding_formula_with_safety_factor",
        "b2b_retention_correctly_flagged_unhealthy"
    ])
    overall_passed = (final_score >= 0.70) and (core_checks_passed >= 2)

    return {
        "passed": overall_passed,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))