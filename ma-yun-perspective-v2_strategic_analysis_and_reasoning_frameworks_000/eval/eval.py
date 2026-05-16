import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
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
    target_file = None
    candidates = list(Path(workspace_dir).rglob("strategic_analysis.json"))
    
    if not candidates:
        add_check("file_exists", False, "strategic_analysis.json not found anywhere in workspace", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}
    
    target_file = candidates[0]
    add_check("file_exists", True, f"Found strategic_analysis.json at {target_file}", weight=1.0)

    # --- Load JSON ---
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        add_check("valid_json", True, "File is valid JSON", weight=1.0)
    except Exception as e:
        add_check("valid_json", False, f"Failed to parse JSON: {e}", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    # Convert entire JSON to a string for text-based checks
    full_text = json.dumps(data, ensure_ascii=False)
    full_text_lower = full_text.lower()

    # --- CHECK 1: All 8 Decision Heuristics Must Be Present ---
    # The 8 heuristics from SKILL.md (exact Chinese names)
    required_heuristics = [
        ("愿景检验", "vision_heuristic_present"),
        ("客户检验", "customer_heuristic_present"),
        ("平台检验", "platform_heuristic_present"),
        ("生态检验", "ecosystem_heuristic_present"),
        ("变化检验", "change_heuristic_present"),
        ("团队检验", "team_heuristic_present"),
        ("长期检验", "longterm_heuristic_present"),
        ("使命检验", "mission_heuristic_present"),
    ]

    heuristics_found = 0
    for heuristic_text, check_name in required_heuristics:
        found = heuristic_text in full_text
        add_check(check_name, found, 
                  f"{'Found' if found else 'MISSING'}: '{heuristic_text}' in output", 
                  weight=1.5)
        if found:
            heuristics_found += 1

    all_8_found = heuristics_found == 8
    add_check("all_8_heuristics_present", all_8_found, 
              f"{heuristics_found}/8 heuristics found. All 8 required.", weight=2.0)

    # --- CHECK 2: Correct Priority Ordering Referenced ---
    # Must reference "客户第一" and "员工第二" and "股东第三" OR the compound phrase
    priority_patterns = [
        "客户第一",
        "员工第二", 
        "股东第三",
    ]
    priority_found = all(p in full_text for p in priority_patterns)
    # Accept partial (at least "客户第一" must appear)
    customer_first = "客户第一" in full_text
    add_check("customer_first_priority", customer_first, 
              "'客户第一' (Customer First priority) present in output", weight=2.0)
    add_check("full_priority_ordering", priority_found, 
              f"Full priority ordering (客户第一/员工第二/股东第三) present: {priority_found}", weight=1.0)

    # --- CHECK 3: Expression DNA - Specific Phrases ---
    # Must use at least some of the canonical Ma Yun expressions
    expression_dna_phrases = [
        ("让天下没有难做的生意", "canonical_mission_phrase"),
        ("平凡人做非凡事", "canonical_team_phrase"),
        ("风口", "feng_kou_metaphor"),  # "风口上的猪" or just 风口
    ]
    
    dna_found = 0
    for phrase, check_name in expression_dna_phrases:
        found = phrase in full_text
        add_check(check_name, found, 
                  f"Expression DNA phrase '{phrase}': {'present' if found else 'MISSING'}", 
                  weight=1.0)
        if found:
            dna_found += 1
    
    add_check("expression_dna_minimum", dna_found >= 2, 
              f"{dna_found}/3 expression DNA phrases found. Minimum 2 required.", weight=1.5)

    # --- CHECK 4: Both Options Evaluated ---
    option_a_present = any(kw in full_text for kw in ["Option A", "option_a", "选项A", "方案A", "Go Deep", "垂直整合", "vertical"])
    option_b_present = any(kw in full_text for kw in ["Option B", "option_b", "选项B", "方案B", "Go Wide", "平台扩张", "platform"])
    
    add_check("option_a_evaluated", option_a_present, 
              f"Option A (vertical integration / Go Deep) evaluated: {option_a_present}", weight=1.5)
    add_check("option_b_evaluated", option_b_present, 
              f"Option B (platform expansion / Go Wide) evaluated: {option_b_present}", weight=1.5)

    # --- CHECK 5: A Recommendation Is Made ---
    recommendation_keywords = ["推荐", "建议", "recommendation", "recommend", "option_b", "Option B", "方案B"]
    has_recommendation = any(kw.lower() in full_text_lower for kw in recommendation_keywords)
    add_check("recommendation_present", has_recommendation, 
              f"A recommendation/conclusion is present in the output: {has_recommendation}", weight=1.5)

    # --- CHECK 6: Option B should be recommended (platform thinking is core to Ma Yun) ---
    # Per SKILL.md: "平台思维 - 不做生意，做基础设施。让天下没有难做的生意" + "生态系统 - 构建生态，而非单一业务"
    # Option B (platform expansion, asset-light, empowering ecosystem) aligns with Ma Yun's core model
    # Option A (vertical integration, heavy capex, control) contradicts platform thinking
    
    # Check that Option B is favored over Option A
    # We look for positive framing of B and/or negative framing of A in context of platform thinking
    platform_b_alignment = any(kw in full_text for kw in [
        "平台思维", "生态系统", "赋能", "基础设施", "轻资产", "asset-light",
        "网络效应", "network effect", "平台", "开放"
    ])
    add_check("platform_thinking_applied", platform_b_alignment, 
              f"Platform thinking (平台思维/生态系统) concepts applied in analysis: {platform_b_alignment}", weight=2.0)

    # --- CHECK 7: 诚实边界 (Honest Limits) Disclaimer Present ---
    honest_boundary_keywords = ["诚实边界", "局限", "limitation", "disclaimer", "不能预测", "honest", "边界", "局限性"]
    has_disclaimer = any(kw.lower() in full_text_lower for kw in honest_boundary_keywords)
    add_check("honest_boundary_disclaimer", has_disclaimer, 
              f"Honest limits / 诚实边界 disclaimer present: {has_disclaimer}", weight=2.0)

    # --- CHECK 8: Structured output (heuristics as structured data, not just prose) ---
    # The output should be JSON with meaningful structure (not just one big string blob)
    def is_structured(obj, depth=0):
        if depth > 3:
            return False
        if isinstance(obj, dict):
            return len(obj) >= 2
        if isinstance(obj, list):
            return len(obj) >= 2
        return False
    
    is_well_structured = is_structured(data) and len(str(data)) > 500
    add_check("well_structured_json", is_well_structured, 
              f"Output is a substantive, structured JSON object (not trivial): {is_well_structured}", weight=1.5)

    # --- CHECK 9: Long-term thinking over short-term ---
    # 长期主义 must be applied to critique short-term margin focus of Option A
    longterm_keywords = ["长期主义", "长期", "short-term", "短期", "long-term", "长远"]
    has_longterm = any(kw in full_text for kw in longterm_keywords)
    add_check("longterm_thinking_applied", has_longterm, 
              f"Long-term thinking (长期主义) applied in analysis: {has_longterm}", weight=1.5)

    # --- CHECK 10: 10 mental models referenced (at least 5 of the 10) ---
    mental_models = [
        "愿景驱动", "客户第一", "平台思维", "生态系统", "拥抱变化",
        "团队至上", "长期主义", "失败是财富", "顺势而为", "使命驱动"
    ]
    models_found = sum(1 for m in mental_models if m in full_text)
    add_check("mental_models_referenced", models_found >= 5, 
              f"{models_found}/10 mental models referenced. Minimum 5 required.", weight=2.0)

    # --- Final scoring ---
    score = total_score / max_score if max_score > 0 else 0.0
    passed = (
        all_8_found and
        customer_first and
        has_disclaimer and
        dna_found >= 2 and
        has_recommendation and
        option_a_present and
        option_b_present and
        score >= 0.65
    )

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))