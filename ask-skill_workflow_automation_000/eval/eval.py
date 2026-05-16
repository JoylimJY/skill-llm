import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output file ---
    candidates = list(workspace.rglob("analysis_output.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "analysis_output.md not found anywhere in workspace"}]
        }

    output_file = candidates[0]
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    # ----------------------------------------------------------------
    # CHECK 1: Trigger word / header format
    # ----------------------------------------------------------------
    try:
        has_ask_header = bool(re.search(r'\*\*【ask\s*分析', content))
        checks.append({
            "name": "ask_framework_header",
            "passed": has_ask_header,
            "detail": "Must start with **【ask 分析 | ...】** header" if not has_ask_header else "Found **【ask 分析】** header"
        })
    except Exception as e:
        checks.append({"name": "ask_framework_header", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 2: Section 1 — 初始分析（龙虾视角）
    # ----------------------------------------------------------------
    try:
        has_section1 = bool(re.search(r'##\s*第1节[：:]\s*初始分析', content))
        has_lobster = bool(re.search(r'龙虾', content))
        passed = has_section1 and has_lobster
        checks.append({
            "name": "section1_initial_analysis",
            "passed": passed,
            "detail": f"Section1 header found: {has_section1}, 龙虾 mention found: {has_lobster}"
        })
    except Exception as e:
        checks.append({"name": "section1_initial_analysis", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 3: Section 2 — 批评者攻击 with required emoji markers
    # ----------------------------------------------------------------
    try:
        has_section2 = bool(re.search(r'##\s*第2节[：:]\s*批评者攻击', content))
        has_emoji_red = '🚨' in content
        has_emoji_chart = '📊' in content
        has_emoji_target = '🎯' in content
        has_critic_label = '【批评者质疑】' in content or '批评者质疑' in content
        passed = has_section2 and has_emoji_red and has_emoji_chart and has_emoji_target and has_critic_label
        checks.append({
            "name": "section2_critic_attack_with_emojis",
            "passed": passed,
            "detail": (f"Section2: {has_section2}, 🚨: {has_emoji_red}, 📊: {has_emoji_chart}, "
                       f"🎯: {has_emoji_target}, critic_label: {has_critic_label}")
        })
    except Exception as e:
        checks.append({"name": "section2_critic_attack_with_emojis", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 4: Section 3 — T1–T5 追问 structure with 龙虾回应
    # ----------------------------------------------------------------
    try:
        t_labels = []
        for i in range(1, 6):
            found = bool(re.search(rf'\*\*T{i}\s+', content))
            t_labels.append(found)
        
        has_all_t = all(t_labels)
        
        # Check specific T label types
        has_t1_clarify = bool(re.search(r'\*\*T1\s*澄清', content))
        has_t2_quantify = bool(re.search(r'\*\*T2\s*量化', content))
        has_t3_evidence = bool(re.search(r'\*\*T3\s*证据', content))
        has_t4_trigger = bool(re.search(r'\*\*T4\s*触发', content))
        has_t5_blind = bool(re.search(r'\*\*T5\s*盲点', content))
        
        # Count 龙虾回应 arrows
        lobster_responses = len(re.findall(r'→\s*龙虾回应', content))
        has_enough_responses = lobster_responses >= 5
        
        has_section3 = bool(re.search(r'##\s*第3节[：:]\s*小智追问', content))
        
        type_score = sum([has_t1_clarify, has_t2_quantify, has_t3_evidence, has_t4_trigger, has_t5_blind])
        passed = has_section3 and has_all_t and has_enough_responses and type_score >= 4
        checks.append({
            "name": "section3_t1_to_t5_with_lobster_responses",
            "passed": passed,
            "detail": (f"Section3: {has_section3}, T1-T5 present: {t_labels}, "
                       f"Type labels correct: {type_score}/5 (T1澄清:{has_t1_clarify} T2量化:{has_t2_quantify} "
                       f"T3证据:{has_t3_evidence} T4触发:{has_t4_trigger} T5盲点:{has_t5_blind}), "
                       f"龙虾回应 responses: {lobster_responses}/5 needed")
        })
    except Exception as e:
        checks.append({"name": "section3_t1_to_t5_with_lobster_responses", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 5: Section 4 — 情景树 table with required columns
    # ----------------------------------------------------------------
    try:
        has_section4 = bool(re.search(r'##\s*第4节[：:]\s*情景树', content))
        
        # Required table columns
        has_col_scenario = bool(re.search(r'情景', content))
        has_col_target = bool(re.search(r'目标价', content))
        has_col_prob = bool(re.search(r'概率', content))
        has_col_trigger = bool(re.search(r'触发条件', content))
        
        # Scenarios A/B/C
        has_scenario_a = bool(re.search(r'A[（(]看多[）)]|A.*看多|看多.*A', content))
        has_scenario_b = bool(re.search(r'B[（(]中性[）)]|B.*中性|中性.*B', content))
        has_scenario_c = bool(re.search(r'C[（(]看空[）)]|C.*看空|看空.*C', content))
        
        # Weighted target price line
        has_weighted = bool(re.search(r'概率加权目标价', content))
        
        passed = (has_section4 and has_col_target and has_col_prob and has_col_trigger 
                  and has_scenario_a and has_scenario_b and has_scenario_c and has_weighted)
        checks.append({
            "name": "section4_scenario_tree_table",
            "passed": passed,
            "detail": (f"Section4: {has_section4}, target col: {has_col_target}, prob col: {has_col_prob}, "
                       f"trigger col: {has_col_trigger}, A(bull): {has_scenario_a}, B(neutral): {has_scenario_b}, "
                       f"C(bear): {has_scenario_c}, weighted price: {has_weighted}")
        })
    except Exception as e:
        checks.append({"name": "section4_scenario_tree_table", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 6: Section 5 — 收敛结论 with 监测指标 table
    # ----------------------------------------------------------------
    try:
        has_section5 = bool(re.search(r'##\s*第5节[：:]\s*收敛结论', content))
        has_final_judgment = bool(re.search(r'\*\*最终判断\*\*', content))
        has_core_risk = bool(re.search(r'\*\*核心风险\*\*', content))
        has_monitor = bool(re.search(r'\*\*监测指标\*\*', content))
        
        # Table structure: 指标/当前值/警戒线/数据来源
        has_monitor_cols = (
            bool(re.search(r'当前值', content)) and
            bool(re.search(r'警戒线', content)) and
            bool(re.search(r'数据来源', content))
        )
        
        passed = has_section5 and has_final_judgment and has_core_risk and has_monitor and has_monitor_cols
        checks.append({
            "name": "section5_convergence_with_monitor_table",
            "passed": passed,
            "detail": (f"Section5: {has_section5}, 最终判断: {has_final_judgment}, "
                       f"核心风险: {has_core_risk}, 监测指标: {has_monitor}, "
                       f"table columns (当前值/警戒线/数据来源): {has_monitor_cols}")
        })
    except Exception as e:
        checks.append({"name": "section5_convergence_with_monitor_table", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 7: Convergence confidence score — 4-dimension /16 system
    # ----------------------------------------------------------------
    try:
        # Must have the 4 specific dimensions
        has_data_quality = bool(re.search(r'数据质量', content))
        has_logic_integrity = bool(re.search(r'逻辑完整性', content))
        has_critic_sufficiency = bool(re.search(r'批评充分性', content))
        has_scenario_coverage = bool(re.search(r'情景覆盖度', content))
        
        # Must have /16 total score
        has_total_16 = bool(re.search(r'/16', content))
        
        # Must have High/Medium/Low confidence label
        has_confidence_label = bool(re.search(r'[高中低]置信|高置信|中置信|低置信', content))
        
        # Must have 收敛置信度 header
        has_convergence_header = bool(re.search(r'收敛置信度', content))
        
        all_dimensions = has_data_quality and has_logic_integrity and has_critic_sufficiency and has_scenario_coverage
        
        passed = (has_convergence_header and all_dimensions and has_total_16 and has_confidence_label)
        checks.append({
            "name": "convergence_score_4dim_16pt_system",
            "passed": passed,
            "detail": (f"收敛置信度 header: {has_convergence_header}, "
                       f"数据质量: {has_data_quality}, 逻辑完整性: {has_logic_integrity}, "
                       f"批评充分性: {has_critic_sufficiency}, 情景覆盖度: {has_scenario_coverage}, "
                       f"/16 score: {has_total_16}, confidence label: {has_confidence_label}")
        })
    except Exception as e:
        checks.append({"name": "convergence_score_4dim_16pt_system", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 8: Source rating system ⭐⭐⭐ / ⭐⭐ / ⚠️
    # ----------------------------------------------------------------
    try:
        has_star_rating = bool(re.search(r'⭐', content))
        has_warning_symbol = '⚠️' in content
        passed = has_star_rating and has_warning_symbol
        checks.append({
            "name": "source_rating_system",
            "passed": passed,
            "detail": f"⭐ star ratings: {has_star_rating}, ⚠️ warning symbols: {has_warning_symbol}"
        })
    except Exception as e:
        checks.append({"name": "source_rating_system", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 9: Residual risk section
    # ----------------------------------------------------------------
    try:
        has_residual = bool(re.search(r'\*\*残差风险\*\*|残差风险', content))
        checks.append({
            "name": "residual_risk_section",
            "passed": has_residual,
            "detail": f"残差风险 section: {has_residual}"
        })
    except Exception as e:
        checks.append({"name": "residual_risk_section", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # CHECK 10: Quantified numbers in analysis (must have $ or % values)
    # ----------------------------------------------------------------
    try:
        price_patterns = re.findall(r'\$[\d,]+\.?\d*|[\d,]+\.?\d*\s*美元|[\d]+\.?\d*%', content)
        has_quantification = len(price_patterns) >= 5
        checks.append({
            "name": "quantification_with_numbers",
            "passed": has_quantification,
            "detail": f"Found {len(price_patterns)} quantified values (need >= 5): {price_patterns[:10]}"
        })
    except Exception as e:
        checks.append({"name": "quantification_with_numbers", "passed": False, "detail": str(e)})

    # ----------------------------------------------------------------
    # Scoring
    # ----------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    
    # Weight critical checks more heavily
    critical_checks = [
        "section3_t1_to_t5_with_lobster_responses",
        "section4_scenario_tree_table",
        "convergence_score_4dim_16pt_system",
    ]
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    
    score = (passed_checks / total_checks) * 0.7 + (critical_passed / len(critical_checks)) * 0.3
    overall_passed = passed_checks >= 8 and critical_passed >= 2

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))