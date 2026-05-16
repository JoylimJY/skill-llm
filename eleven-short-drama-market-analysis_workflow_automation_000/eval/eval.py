import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    report_files = list(Path(workspace).rglob("market_analysis_report.md"))

    # Check 1: File exists
    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "market_analysis_report.md not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_file_readable", "passed": False, "detail": f"Cannot read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})
    total_score += 0.05

    # Check 2: Correct top-level header format 【短剧/AI漫剧市场分析】
    header_pattern = re.compile(r"##\s+【短剧/AI漫剧市场分析】\S+")
    header_match = header_pattern.search(content)
    if header_match:
        checks.append({"name": "report_header_format", "passed": True, "detail": f"Found header: {header_match.group()}"})
        total_score += 0.10
    else:
        checks.append({"name": "report_header_format", "passed": False, "detail": "Missing '## 【短剧/AI漫剧市场分析】{日期}' header. Must use exact format from template."})

    # Check 3: All 7 required sections present
    required_sections = [
        ("section_1_macro", r"###\s+一、宏观概况"),
        ("section_2_platform", r"###\s+二、平台动态"),
        ("section_3_trending", r"###\s+三、爆款案例分析"),
        ("section_4_competition", r"###\s+四、竞争格局"),
        ("section_5_selection", r"###\s+五、选剧建议"),
        ("section_6_risk", r"###\s+六、风险提示"),
        ("section_7_data", r"###\s+七、本周值得关注的数据"),
    ]

    sections_passed = 0
    for name, pattern in required_sections:
        if re.search(pattern, content):
            checks.append({"name": name, "passed": True, "detail": f"Section found matching pattern: {pattern}"})
            sections_passed += 1
            total_score += 0.05
        else:
            checks.append({"name": name, "passed": False, "detail": f"Missing required section matching: {pattern}"})

    # Check 4: 8 analysis dimensions (① through ⑧)
    dimensions = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"]
    dims_found = sum(1 for d in dimensions if d in content)
    if dims_found >= 6:
        checks.append({"name": "eight_analysis_dimensions", "passed": True, "detail": f"Found {dims_found}/8 circled-number dimensions (①-⑧)"})
        total_score += 0.10
    else:
        checks.append({"name": "eight_analysis_dimensions", "passed": False, "detail": f"Only {dims_found}/8 analysis dimensions (①-⑧) found. All 8 must be covered."})

    # Check 5: Scoring framework — 6 exact dimensions with exact weights present
    scoring_dims = [
        ("weight_market_heat", ["市场热度", "20%"]),
        ("weight_competition", ["竞争程度", "15%"]),
        ("weight_adaptation", ["改编难度", "15%"]),
        ("weight_compliance", ["合规风险", "20%"]),
        ("weight_monetization", ["变现潜力", "15%"]),
        ("weight_cost", ["制作成本", "15%"]),
    ]
    weights_passed = 0
    for dim_name, keywords in scoring_dims:
        found = all(kw in content for kw in keywords)
        if found:
            checks.append({"name": dim_name, "passed": True, "detail": f"Found scoring dimension with keywords: {keywords}"})
            weights_passed += 1
            total_score += 0.05
        else:
            checks.append({"name": dim_name, "passed": False, "detail": f"Missing scoring dimension or weight: {keywords}. Must use exact 6-dimension framework from SKILL.md."})

    # Check 6: TOP3 candidates identified in section 五
    # Must exclude 题材C (阴阳捉鬼师) due to compliance red line (封建迷信)
    # Must include reference to at least 3 of the 5 candidates
    candidates = ["题材A", "题材B", "题材C", "题材D", "题材E",
                  "长生道侣", "总裁的替婚新娘", "阴阳捉鬼师", "五十岁的春天", "Forbidden CEO"]
    
    # Find section 五
    section_5_match = re.search(r"###\s+五、选剧建议.*?(?=###|\Z)", content, re.DOTALL)
    if section_5_match:
        section_5_content = section_5_match.group()
        
        # TOP3 mentioned
        top3_pattern = re.compile(r"TOP\s*3|前三|第[一二三]推荐|推荐立项", re.IGNORECASE)
        if top3_pattern.search(section_5_content) or re.search(r"TOP3", section_5_content):
            checks.append({"name": "top3_mentioned", "passed": True, "detail": "TOP3 recommendation found in section 五"})
            total_score += 0.05
        else:
            checks.append({"name": "top3_mentioned", "passed": False, "detail": "Section 五 does not clearly mention TOP3 candidates"})

        # Compliance red line: 阴阳捉鬼师 should NOT be in TOP3 (it's a compliance red line)
        # Check that 阴阳捉鬼师 or 题材C is flagged as risky/excluded from top3
        compliance_excluded = False
        # If section 5 mentions C or 阴阳捉鬼师, check it's not positively recommended
        if "阴阳捉鬼师" in section_5_content or "题材C" in section_5_content:
            # It's mentioned — check if it's flagged negatively
            negative_signals = ["不推荐", "排除", "红线", "否决", "风险", "合规", "封建迷信", "无法备案"]
            if any(sig in section_5_content for sig in negative_signals):
                compliance_excluded = True
            else:
                # Mentioned but not negatively flagged in section 5 — check section 六 风险提示
                section_6_match = re.search(r"###\s+六、风险提示.*?(?=###|\Z)", content, re.DOTALL)
                if section_6_match and ("阴阳捉鬼师" in section_6_match.group() or "封建迷信" in section_6_match.group()):
                    compliance_excluded = True
        else:
            # Not in top3 section at all — check if flagged somewhere
            if "阴阳捉鬼师" in content or "题材C" in content:
                risk_signals = ["不推荐", "排除", "红线", "否决", "风险", "合规", "封建迷信", "无法备案"]
                if any(sig in content for sig in risk_signals):
                    compliance_excluded = True
            else:
                # Never mentioned — warn but pass (agent may have omitted)
                compliance_excluded = True

        if compliance_excluded:
            checks.append({"name": "compliance_red_line_exclusion", "passed": True, "detail": "题材C (阴阳捉鬼师) correctly identified as compliance red-line / not included in top3"})
            total_score += 0.10
        else:
            checks.append({"name": "compliance_red_line_exclusion", "passed": False, "detail": "题材C (阴阳捉鬼师) was not flagged as a compliance risk. Per strategy.md, 涉鬼神封建迷信 is a 直接否决 red line."})

        # Check candidates discussed (at least 3 of the 5 must appear somewhere in section 5)
        discussed = sum(1 for c in ["长生道侣", "总裁的替婚新娘", "五十岁的春天", "Forbidden CEO",
                                     "题材A", "题材B", "题材D", "题材E"] if c in section_5_content)
        if discussed >= 3:
            checks.append({"name": "candidates_discussed_in_top3", "passed": True, "detail": f"{discussed} candidates explicitly mentioned in section 五"})
            total_score += 0.10
        else:
            checks.append({"name": "candidates_discussed_in_top3", "passed": False, "detail": f"Only {discussed} candidates mentioned in section 五. Expected at least 3."})
    else:
        checks.append({"name": "top3_mentioned", "passed": False, "detail": "Section 五 not found for TOP3 check"})
        checks.append({"name": "compliance_red_line_exclusion", "passed": False, "detail": "Section 五 not found for compliance check"})
        checks.append({"name": "candidates_discussed_in_top3", "passed": False, "detail": "Section 五 not found"})

    # Check 7: References to actual data from reference files
    data_references = [
        ("ref_market_scale", ["504亿", "800亿", "107%"], "Market scale data from market-data.md"),
        ("ref_platform_data", ["抖音", "快手", "红果"], "Platform data from market-data.md"),
        ("ref_distribution_model", ["付费解锁", "广告分成", "品牌定制", "海外发行"], "Distribution models from distribution.md"),
        ("ref_ai_drama_cost", ["AI漫剧", "制作成本", "降本"], "AI drama cost efficiency from toolchain.md"),
    ]
    for check_name, keywords, detail_msg in data_references:
        found = any(kw in content for kw in keywords)
        if found:
            checks.append({"name": check_name, "passed": True, "detail": f"Found reference data: {[kw for kw in keywords if kw in content]}"})
            total_score += 0.05
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"No reference to: {keywords}. Agent must read {detail_msg}"})

    # Check 8: Section 七 (数据) has some numeric content
    section_7_match = re.search(r"###\s+七、本周值得关注的数据.*?(?=###|\Z)", content, re.DOTALL)
    if section_7_match:
        section_7_content = section_7_match.group()
        has_numbers = bool(re.search(r"\d+", section_7_content))
        if has_numbers:
            checks.append({"name": "section_7_has_data", "passed": True, "detail": "Section 七 contains numeric data points"})
            total_score += 0.05
        else:
            checks.append({"name": "section_7_has_data", "passed": False, "detail": "Section 七 should contain specific numeric data from references"})
    else:
        checks.append({"name": "section_7_has_data", "passed": False, "detail": "Section 七 not found"})

    # Compute final
    total_score = min(total_score, 1.0)
    
    # Determine pass: must pass critical checks
    critical_checks = ["report_file_exists", "report_header_format", "section_5_selection",
                       "section_1_macro", "section_6_risk", "section_7_data",
                       "compliance_red_line_exclusion", "weight_market_heat", "weight_compliance"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    passed = critical_passed and sections_passed >= 5 and weights_passed >= 4 and total_score >= 0.55

    return {"passed": passed, "score": round(total_score, 3), "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))