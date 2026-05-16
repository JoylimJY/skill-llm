import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path):
    """Search for the output report file."""
    candidates = list(workspace.rglob("fund_analysis_report.txt"))
    if candidates:
        return candidates[0]
    return None

def load_report(workspace: Path):
    f = find_report(workspace)
    if f is None:
        return None, "fund_analysis_report.txt not found anywhere in workspace"
    try:
        content = f.read_text(encoding="utf-8")
        return content, None
    except Exception as e:
        return None, f"Error reading report: {e}"

def run_checks(workspace_path: str):
    workspace = Path(workspace_path)
    checks = []
    
    content, err = load_report(workspace)
    
    # Check 0: File existence
    checks.append({
        "name": "report_file_exists",
        "passed": content is not None,
        "detail": err if content is None else f"Found at: {find_report(workspace)}"
    })
    
    if content is None:
        # All remaining checks fail
        for name in [
            "header_box_drawing_characters",
            "fund_name_and_code_in_header",
            "section_one_news_overview",
            "news_impact_classification_used",
            "section_two_four_dimensions",
            "market_score_computed_correctly",
            "star_ratings_present",
            "section_three_fund_type_analysis",
            "stock_fund_weights_applied",
            "section_four_trend_prediction_table",
            "trend_table_three_time_horizons",
            "section_five_investment_recommendation",
            "position_recommendation_matrix_applied",
            "section_six_risk_points",
            "at_least_three_risk_points",
            "section_seven_disclaimer",
            "macro_dimension_analyzed",
            "industry_policy_dimension_analyzed",
            "fund_self_dimension_analyzed",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Report file missing"})
        total = sum(1 for c in checks if c["passed"])
        return {"passed": False, "score": total / len(checks), "checks": checks}
    
    # Check 1: Box-drawing header characters (╔═╗ style for sections 1 and 5)
    has_box_top = "╔" in content and "╗" in content
    has_box_bottom = "╚" in content and "╝" in content
    has_box_mid = "╠" in content or "║" in content
    checks.append({
        "name": "header_box_drawing_characters",
        "passed": has_box_top and has_box_bottom and has_box_mid,
        "detail": f"╔ present: {has_box_top}, ╚ present: {has_box_bottom}, ║ present: {has_box_mid}"
    })
    
    # Check 2: Fund name and code in header
    has_fund_name = "华夏新兴产业股票" in content
    has_fund_code = "003984" in content
    checks.append({
        "name": "fund_name_and_code_in_header",
        "passed": has_fund_name and has_fund_code,
        "detail": f"Fund name present: {has_fund_name}, Fund code present: {has_fund_code}"
    })
    
    # Check 3: Section one - News overview exists
    has_section_one = "新闻概览" in content or "【一" in content or "一、新闻" in content
    checks.append({
        "name": "section_one_news_overview",
        "passed": has_section_one,
        "detail": f"News overview section found: {has_section_one}"
    })
    
    # Check 4: News impact classification used (proprietary levels from SKILL.md)
    # Must use the specific terms from 新闻影响分级
    impact_terms = ["重大利好", "中度利好", "轻微利好", "中性", "轻微利空", "中度利空", "重大利空"]
    found_impact_terms = [t for t in impact_terms if t in content]
    checks.append({
        "name": "news_impact_classification_used",
        "passed": len(found_impact_terms) >= 2,
        "detail": f"Impact terms found: {found_impact_terms}"
    })
    
    # Check 5: Four dimensions section exists
    has_four_dims = ("四大维度" in content or "【二" in content or "二、四大" in content)
    macro_dim = "宏观面" in content or "宏观" in content
    market_dim = "市场面" in content or "市场" in content
    fund_dim = "基金自身" in content
    industry_dim = "行业政策" in content
    all_dims = macro_dim and market_dim and fund_dim and industry_dim
    checks.append({
        "name": "section_two_four_dimensions",
        "passed": has_four_dims and all_dims,
        "detail": f"四大维度section: {has_four_dims}, macro: {macro_dim}, market: {market_dim}, fund_self: {fund_dim}, industry: {industry_dim}"
    })
    
    # Check 6: Market environment score computed with the proprietary formula
    # Market score = 大盘趋势(40%) + 资金流向(30%) + 情绪(20%) + 板块(10%)
    # From data: trend=35*0.4=14, capital=25*0.3=7.5, sentiment=30*0.2=6, sector=40*0.1=4 => total=31.5 => ~32
    # This is in the "弱势" range (0-39). Check that the score or the label "弱势" appears.
    score_in_range = bool(re.search(r'[23][0-9][\s]*分', content)) or \
                     bool(re.search(r'评分[：:]\s*[23][0-9]', content)) or \
                     "弱势" in content
    checks.append({
        "name": "market_score_computed_correctly",
        "passed": score_in_range,
        "detail": f"Market score (expected ~32, category '弱势') or label found in report. Match: {score_in_range}"
    })
    
    # Check 7: Star ratings present (★ characters for dimension ratings)
    star_count = content.count("★")
    checks.append({
        "name": "star_ratings_present",
        "passed": star_count >= 4,
        "detail": f"Star ★ count in report: {star_count} (need >= 4)"
    })
    
    # Check 8: Fund type analysis section
    has_section_three = "【三" in content or "三、基金" in content or "基金类型分析" in content
    has_stock_type = "股票型" in content
    checks.append({
        "name": "section_three_fund_type_analysis",
        "passed": has_section_three and has_stock_type,
        "detail": f"Fund type section: {has_section_three}, stock type mentioned: {has_stock_type}"
    })
    
    # Check 9: Stock fund type PROPRIETARY WEIGHTS applied
    # 股票型: 行业政策(35%) + 市场情绪(30%) + 宏观(20%) + 基金自身(15%)
    weight_patterns = [
        r'35%', r'30%', r'20%', r'15%'
    ]
    weights_found = [bool(re.search(p, content)) for p in weight_patterns]
    # At least 3 of the 4 proprietary weights must be present
    checks.append({
        "name": "stock_fund_weights_applied",
        "passed": sum(weights_found) >= 3,
        "detail": f"Stock fund proprietary weights (35/30/20/15%) found: {weights_found}. Count: {sum(weights_found)}"
    })
    
    # Check 10: Trend prediction section exists
    has_section_four = "【四" in content or "走势预测" in content or "四、走势" in content
    checks.append({
        "name": "section_four_trend_prediction_table",
        "passed": has_section_four,
        "detail": f"Trend prediction section found: {has_section_four}"
    })
    
    # Check 11: Trend table has three time horizons
    short_term = "短期" in content and "1周" in content
    mid_term = "中期" in content and ("1-3" in content or "1～3" in content or "1个月" in content)
    long_term = "长期" in content and ("半年" in content or "6个月" in content)
    checks.append({
        "name": "trend_table_three_time_horizons",
        "passed": short_term and mid_term and long_term,
        "detail": f"Short-term(1周): {short_term}, Mid-term(1-3月): {mid_term}, Long-term(半年+): {long_term}"
    })
    
    # Check 12: Investment recommendation section
    has_section_five = "【五" in content or "投资建议" in content or "五、投资" in content
    rec_terms = ["买入", "持有", "减仓", "卖出", "观望"]
    found_recs = [t for t in rec_terms if t in content]
    checks.append({
        "name": "section_five_investment_recommendation",
        "passed": has_section_five and len(found_recs) >= 2,
        "detail": f"Investment section: {has_section_five}, recommendation terms found: {found_recs}"
    })
    
    # Check 13: Position recommendation matrix applied (仓位建议矩阵)
    # Market is "弱势下跌" + user is "稳健型" => should suggest 空仓 or very low position
    # Check for position terms from the matrix
    position_terms = ["满仓", "重仓", "半仓", "轻仓", "空仓"]
    found_positions = [t for t in position_terms if t in content]
    # Given the weak market + 稳健型 user, correct answer should be 空仓
    correct_position = "空仓" in content or "轻仓" in content  # both valid for weak market
    checks.append({
        "name": "position_recommendation_matrix_applied",
        "passed": len(found_positions) >= 1 and correct_position,
        "detail": f"Position terms found: {found_positions}, correct weak-market position (空仓/轻仓): {correct_position}"
    })
    
    # Check 14: Risk section exists
    has_section_six = "【六" in content or "风险提示" in content or "六、风险" in content
    checks.append({
        "name": "section_six_risk_points",
        "passed": has_section_six,
        "detail": f"Risk section found: {has_section_six}"
    })
    
    # Check 15: At least 3 specific risk points (numbered list or bullet points in risk section)
    # Look for numbered risks
    risk_numbers = re.findall(r'[123４５６][\.、．\s].*(?:风险|回撤|压力|不确定)', content)
    has_three_risks = len(risk_numbers) >= 3 or \
                      (content.count("风险") >= 4)  # mentions risk at least 4 times
    checks.append({
        "name": "at_least_three_risk_points",
        "passed": has_three_risks,
        "detail": f"Numbered risk items found: {len(risk_numbers)}, total '风险' mentions: {content.count('风险')}"
    })
    
    # Check 16: Disclaimer present
    has_disclaimer = "【七" in content or "免责声明" in content or "不构成投资建议" in content
    checks.append({
        "name": "section_seven_disclaimer",
        "passed": has_disclaimer,
        "detail": f"Disclaimer section found: {has_disclaimer}"
    })
    
    # Check 17: Macro dimension properly analyzed with specific data from inputs
    macro_data_used = ("CPI" in content or "PPI" in content) and \
                      ("美联储" in content or "降息" in content or "货币政策" in content)
    checks.append({
        "name": "macro_dimension_analyzed",
        "passed": macro_data_used,
        "detail": f"Macro indicators (CPI/PPI) found: {('CPI' in content or 'PPI' in content)}, Fed/monetary policy found: {('美联储' in content or '降息' in content or '货币政策' in content)}"
    })
    
    # Check 18: Industry policy dimension analyzed with specific news
    # Must mention the energy bureau policy and semiconductor policy
    industry_data_used = ("新能源" in content and ("300GW" in content or "装机" in content or "能源局" in content)) or \
                         ("半导体" in content and ("国产化" in content or "工信部" in content or "补贴" in content))
    checks.append({
        "name": "industry_policy_dimension_analyzed",
        "passed": industry_data_used,
        "detail": f"Industry-specific news data applied: {industry_data_used}"
    })
    
    # Check 19: Fund self dimension includes manager and holdings
    fund_self_analyzed = ("张磊" in content or "基金经理" in content) and \
                         ("宁德时代" in content or "重仓" in content or "持仓" in content)
    checks.append({
        "name": "fund_self_dimension_analyzed",
        "passed": fund_self_analyzed,
        "detail": f"Manager info present: {'张磊' in content or '基金经理' in content}, Holdings analyzed: {'宁德时代' in content or '重仓' in content}"
    })
    
    # Final scoring
    total_passed = sum(1 for c in checks if c["passed"])
    score = total_passed / len(checks)
    overall_passed = score >= 0.75  # Must pass at least 75% of checks
    
    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))