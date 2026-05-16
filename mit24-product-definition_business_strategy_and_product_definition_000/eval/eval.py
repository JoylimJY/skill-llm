import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Search for the product definition report file."""
    candidates = list(workspace.rglob("product_definition_report.json"))
    if not candidates:
        # Also accept Chinese-named or alternate names but penalize
        candidates = list(workspace.rglob("*产品定义*")) + list(workspace.rglob("*product_definition*"))
    return candidates[0] if candidates else None

def load_json_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def score_to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def check_string_contains_any(s, keywords):
    s_lower = s.lower()
    return any(kw.lower() in s_lower for kw in keywords)

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Find the report file ─────────────────────────────────────────────────
    report_path = find_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": f"Found at: {report_path}" if file_found else "product_definition_report.json not found"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Load JSON ────────────────────────────────────────────────────────────
    try:
        report = load_json_file(report_path)
        checks.append({"name": "report_is_valid_json", "passed": True, "detail": "Parsed successfully"})
    except Exception as e:
        checks.append({"name": "report_is_valid_json", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_str = json.dumps(report, ensure_ascii=False).lower()

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: STEP 11 - Pricing Framework
    # ════════════════════════════════════════════════════════════════════════

    # 1a. Must select from the 3 valid pricing methods (value-based recommended)
    pricing_section = None
    for key in report:
        if any(x in key.lower() for x in ["定价", "pricing", "price", "step11", "步骤11"]):
            pricing_section = report[key]
            break
    if pricing_section is None and isinstance(report, dict):
        # Try nested search
        for v in report.values():
            if isinstance(v, dict):
                for k2 in v:
                    if any(x in k2.lower() for x in ["定价", "pricing", "price"]):
                        pricing_section = v[k2]
                        break

    pricing_method_valid = check_string_contains_any(
        report_str,
        ["价值导向", "value-based", "value based", "价值为基础", "价值定价", "感知价值"]
    )
    checks.append({
        "name": "step11_pricing_method_selected",
        "passed": pricing_method_valid,
        "detail": "Must select and justify one of the 3 pricing methods; value-based (价值导向) strongly indicated"
    })

    # 1b. Must include a specific pricing strategy type (freemium/subscription/usage/one-time/tiered)
    pricing_strategy_valid = check_string_contains_any(
        report_str,
        ["订阅", "subscription", "freemium", "免费增值", "按用量", "阶梯", "tiered", "一次性"]
    )
    checks.append({
        "name": "step11_pricing_strategy_type",
        "passed": pricing_strategy_valid,
        "detail": "Must specify one of the 5 strategy types: freemium/订阅制/按用量/一次性/阶梯定价"
    })

    # 1c. Must include a price range
    price_numbers = re.findall(r'[\d,，]+(?:\.\d+)?(?:\s*(?:万|元|rmb|¥|￥))', report_str)
    has_price_range = len(price_numbers) >= 2
    checks.append({
        "name": "step11_price_range_given",
        "passed": has_price_range,
        "detail": f"Must provide a price range (found numeric price indicators: {price_numbers[:5]})"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: STEP 12 - CLV Calculation (PROPRIETARY TRAP)
    # Formula: CLV = 年合同金额 × 平均客户年限 × 毛利率
    # Input: 120000 × 4.5 × 0.72 = 388,800 RMB
    # CAC = 85,000 RMB
    # CLV/CAC = 388800 / 85000 ≈ 4.574 (must be > 3)
    # ════════════════════════════════════════════════════════════════════════

    # 2a. CLV value must be approximately correct (388,800 ± 5%)
    expected_clv = 120000 * 4.5 * 0.72  # 388,800
    clv_found = False
    clv_detail = f"Expected CLV ≈ {expected_clv:,.0f} RMB (120000 × 4.5 × 0.72)"
    
    # Search for numeric values close to expected CLV
    all_numbers = re.findall(r'[\d]+(?:[,，.][\d]+)*', report_str)
    for num_str in all_numbers:
        cleaned = num_str.replace(',', '').replace('，', '').replace(' ', '')
        try:
            val = float(cleaned)
            if abs(val - expected_clv) / expected_clv < 0.05:  # within 5%
                clv_found = True
                clv_detail = f"Found CLV value {val:,.0f} (expected {expected_clv:,.0f})"
                break
        except ValueError:
            continue
    
    checks.append({
        "name": "step12_clv_correct_value",
        "passed": clv_found,
        "detail": clv_detail
    })

    # 2b. CLV formula must use gross margin (毛利率) — not just revenue × years
    uses_gross_margin = check_string_contains_any(
        report_str,
        ["毛利", "gross margin", "利润率", "0.72", "72%", "72％"]
    )
    checks.append({
        "name": "step12_gross_margin_used_in_clv",
        "passed": uses_gross_margin,
        "detail": "CLV formula MUST include gross margin (毛利率=72%) per SKILL.md B2B formula"
    })

    # 2c. CLV/CAC ratio must be computed and labeled as healthy (> 3)
    # Expected: 388800 / 85000 ≈ 4.57
    expected_ratio = expected_clv / 85000
    ratio_found = False
    ratio_healthy_noted = False
    
    for num_str in all_numbers:
        cleaned = num_str.replace(',', '').replace('，', '')
        try:
            val = float(cleaned)
            if abs(val - expected_ratio) < 0.3:  # within 0.3 of ~4.57
                ratio_found = True
                break
        except ValueError:
            continue
    
    ratio_healthy_noted = check_string_contains_any(
        report_str,
        ["> 3", ">3", "大于3", "超过3", "健康", "healthy", "3倍"]
    )
    
    clv_cac_passed = ratio_found and ratio_healthy_noted
    checks.append({
        "name": "step12_clv_cac_ratio_evaluated",
        "passed": clv_cac_passed,
        "detail": f"Expected CLV/CAC ≈ {expected_ratio:.2f}; must also note > 3 health threshold. ratio_found={ratio_found}, healthy_noted={ratio_healthy_noted}"
    })

    # 2d. Payback period must be computed and evaluated against < 12 months
    # Payback: CAC / (monthly_revenue × gross_margin) = 85000 / (10000 × 0.72) = 85000/7200 ≈ 11.8 months
    expected_payback = 85000 / (10000 * 0.72)  # ≈ 11.81 months
    payback_found = False
    
    for num_str in all_numbers:
        cleaned = num_str.replace(',', '').replace('，', '')
        try:
            val = float(cleaned)
            if abs(val - expected_payback) < 1.5:  # within 1.5 months
                payback_found = True
                break
        except ValueError:
            continue
    
    payback_standard_noted = check_string_contains_any(
        report_str,
        ["12个月", "12 months", "< 12", "<12", "回收期", "payback"]
    )
    
    checks.append({
        "name": "step12_payback_period_computed",
        "passed": payback_found and payback_standard_noted,
        "detail": f"Expected payback ≈ {expected_payback:.1f} months; must reference < 12 month standard. found={payback_found}, standard_noted={payback_standard_noted}"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: STEP 13 - MVP Design
    # ════════════════════════════════════════════════════════════════════════

    # 3a. Must include Must-have vs Nice-to-have distinction
    must_have_distinction = check_string_contains_any(
        report_str,
        ["must-have", "must have", "必须有", "核心功能", "nice-to-have", "锦上添花", "可选"]
    )
    checks.append({
        "name": "step13_must_have_vs_nice_to_have",
        "passed": must_have_distinction,
        "detail": "MVP must explicitly distinguish Must-have vs Nice-to-have features"
    })

    # 3b. Must include at least one User Story in the correct format
    user_story_pattern = re.search(
        r'(作为|as\s+a|作为一个|as\s+an).*?(我希望|i\s+want|希望|want\s+to).*?(以便|so\s+that|为了|in\s+order)',
        report_str,
        re.IGNORECASE | re.DOTALL
    )
    checks.append({
        "name": "step13_user_story_format",
        "passed": user_story_pattern is not None,
        "detail": "Must include at least one User Story: 作为[角色]，我希望[功能]，以便[价值]"
    })

    # 3c. Must mention V1.0 or first version scope
    v1_scope = check_string_contains_any(
        report_str,
        ["v1.0", "v1", "第一版", "1.0", "first version", "版本一", "mvp", "最小可行"]
    )
    checks.append({
        "name": "step13_v1_scope_defined",
        "passed": v1_scope,
        "detail": "Must define first version (V1.0) feature scope"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 4: STEP 14 - Purchase Decision Matrix (PROPRIETARY TRAP)
    # Must cover all 6 exact dimensions from SKILL.md
    # ════════════════════════════════════════════════════════════════════════

    required_dimensions = [
        (["功能需求", "functional", "功能"], "功能需求"),
        (["性能", "performance", "速度", "精度", "稳定"], "性能指标"),
        (["价格", "price sensitivity", "价格敏感"], "价格敏感度"),
        (["品牌", "brand", "信任"], "品牌偏好"),
        (["服务", "service", "支持", "support", "培训", "实施"], "服务要求"),
        (["合规", "compliance", "认证", "标准"], "合规要求"),
    ]

    dimensions_found = 0
    dimension_details = []
    for keywords, dim_name in required_dimensions:
        found = check_string_contains_any(report_str, keywords)
        if found:
            dimensions_found += 1
        dimension_details.append(f"{dim_name}: {'✓' if found else '✗'}")

    checks.append({
        "name": "step14_all_6_dimensions_present",
        "passed": dimensions_found == 6,
        "detail": f"Found {dimensions_found}/6 required dimensions. " + ", ".join(dimension_details)
    })

    # 4b. Must have scoring (1-10 scale) for dimensions
    scoring_present = check_string_contains_any(
        report_str,
        ["1-10", "1到10", "权重", "weight", "评分", "score", "得分"]
    )
    checks.append({
        "name": "step14_scoring_scale_used",
        "passed": scoring_present,
        "detail": "Must use 1-10 scoring weights for each decision criterion"
    })

    # 4c. Must identify differential advantage point (竞品最低分 + 自己最高分)
    # From data: SupplyMind scores [9,8,7,4,8,7], 
    # SupplyWatch [5,4,8,6,5,6], RiskRadar [7,7,4,7,6,7], ChainGuard [4,5,9,5,4,5]
    # Average competitor min per dimension:
    # 功能需求: competitors min=4, SupplyMind=9 → DIFFERENTIAL ADVANTAGE
    # 性能: competitors min=4, SupplyMind=8
    # The differential advantage should be "功能需求" (functional requirements) dimension
    diff_advantage = check_string_contains_any(
        report_str,
        ["差异化", "差异点", "differential", "竞争优势", "advantage", "优势点", "最低.*最高", "我们.*高.*竞品.*低"]
    )
    checks.append({
        "name": "step14_differential_advantage_identified",
        "passed": diff_advantage,
        "detail": "Must identify the differential advantage point where competitors score lowest and SupplyMind scores highest"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 5: Overall Report Structure
    # ════════════════════════════════════════════════════════════════════════

    # Must contain all 4 required sections
    has_all_4_sections = all([
        check_string_contains_any(report_str, ["定价", "pricing", "price"]),
        check_string_contains_any(report_str, ["clv", "终身价值", "客户价值", "lifetime"]),
        check_string_contains_any(report_str, ["mvp", "最小可行", "产品方案", "功能清单"]),
        check_string_contains_any(report_str, ["购买决策", "决策标准", "purchase decision", "buying criteria"]),
    ])
    checks.append({
        "name": "report_has_all_4_sections",
        "passed": has_all_4_sections,
        "detail": "Report must contain all 4 sections: pricing, CLV, MVP, and purchase decision matrix"
    })

    # ════════════════════════════════════════════════════════════════════════
    # SCORING
    # ════════════════════════════════════════════════════════════════════════
    weights = {
        "report_file_exists": 0.05,
        "report_is_valid_json": 0.05,
        "step11_pricing_method_selected": 0.06,
        "step11_pricing_strategy_type": 0.05,
        "step11_price_range_given": 0.04,
        "step12_clv_correct_value": 0.12,
        "step12_gross_margin_used_in_clv": 0.10,
        "step12_clv_cac_ratio_evaluated": 0.10,
        "step12_payback_period_computed": 0.09,
        "step13_must_have_vs_nice_to_have": 0.05,
        "step13_user_story_format": 0.05,
        "step13_v1_scope_defined": 0.04,
        "step14_all_6_dimensions_present": 0.08,
        "step14_scoring_scale_used": 0.05,
        "step14_differential_advantage_identified": 0.05,
        "report_has_all_4_sections": 0.02,
    }

    for check in checks:
        if check["passed"] and check["name"] in weights:
            total_score += weights[check["name"]]

    passed = total_score >= 0.70 and all(
        c["passed"] for c in checks
        if c["name"] in [
            "report_file_exists",
            "report_is_valid_json",
            "step12_clv_correct_value",
            "step12_gross_margin_used_in_clv",
            "step14_all_6_dimensions_present",
        ]
    )

    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))