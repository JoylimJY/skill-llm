import sys
import json
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
    candidates = list(Path(workspace_dir).rglob("competition_guidance.json"))
    if not candidates:
        add_check("output_file_exists", False, "competition_guidance.json not found anywhere in workspace", weight=2.0)
        return {"passed": False, "score": 0.0, "checks": checks}
    
    target_file = candidates[0]
    add_check("output_file_exists", True, f"Found competition_guidance.json at {target_file}", weight=2.0)

    # --- Parse JSON ---
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        add_check("json_parseable", False, f"Failed to parse JSON: {e}", weight=2.0)
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("json_parseable", True, "JSON parsed successfully", weight=1.0)

    # Helper: search for project data
    def find_project_data(data, keywords_list):
        """Try to find a dict in data that matches a project by keywords."""
        # If data is a list, search each element
        if isinstance(data, list):
            for item in data:
                for kw in keywords_list:
                    text = json.dumps(item, ensure_ascii=False).lower()
                    if kw.lower() in text:
                        return item
        # If data is a dict, check top-level keys and values
        if isinstance(data, dict):
            for kw in keywords_list:
                text = json.dumps(data, ensure_ascii=False).lower()
                if kw.lower() in text:
                    # Try to find nested dict for this project
                    for v in data.values():
                        if isinstance(v, dict):
                            if kw.lower() in json.dumps(v, ensure_ascii=False).lower():
                                return v
                    # Return whole data if it's a flat structure with both projects
            return data
        return None

    full_text = json.dumps(data, ensure_ascii=False).lower()

    # ============================================================
    # PROJECT A: 智农云 → 高教主赛道-创业组
    # Expected scoring: 个人成长25, 项目创新30, 产业价值30, 团队协作15
    # PPT: 12-15 pages, includes 企业概况, 经营绩效, 财务预测, 创新成果
    # ============================================================

    # A1: Track identification - must identify 高教主赛道 and 创业组
    proj_a_data_text = ""
    # Search for project alpha context
    if "智农" in full_text or "alpha" in full_text or "saas" in full_text or "智农云" in full_text:
        proj_a_data_text = full_text  # Use full text for scoring checks

    track_a_passed = ("高教主赛道" in full_text or "高教" in full_text or "主赛道" in full_text) and \
                     ("创业组" in full_text)
    add_check(
        "project_alpha_track_identification",
        track_a_passed,
        "Must identify 高教主赛道-创业组 for 智农云 project" + (" ✓" if track_a_passed else " ✗"),
        weight=2.0
    )

    # A2: Exact scoring for 高教主赛道-创业组
    # 个人成长25, 项目创新30, 产业价值30, 团队协作15
    score_a_personal = "25" in full_text and ("个人成长" in full_text)
    score_a_innovation = "30" in full_text and ("项目创新" in full_text)
    score_a_industry = "30" in full_text and ("产业价值" in full_text)
    score_a_team = "15" in full_text and ("团队协作" in full_text)
    
    # All four must be present
    scoring_a_complete = score_a_personal and score_a_innovation and score_a_industry and score_a_team
    add_check(
        "project_alpha_scoring_criteria_personal_growth",
        score_a_personal,
        "高教主赛道-创业组: 个人成长=25分 must be present",
        weight=1.5
    )
    add_check(
        "project_alpha_scoring_criteria_innovation",
        score_a_innovation,
        "高教主赛道-创业组: 项目创新=30分 must be present",
        weight=1.5
    )
    add_check(
        "project_alpha_scoring_criteria_industry_value",
        score_a_industry,
        "高教主赛道-创业组: 产业价值=30分 must be present",
        weight=1.5
    )
    add_check(
        "project_alpha_scoring_criteria_teamwork",
        score_a_team,
        "高教主赛道-创业组: 团队协作=15分 must be present",
        weight=1.5
    )

    # A3: PPT structure for 创业组 - must include extra sections
    # Required extra sections: 企业概况, 经营绩效, 财务预测, 创新成果
    # Page count 12-15
    ppt_a_enterprise = "企业概况" in full_text
    ppt_a_performance = "经营绩效" in full_text
    ppt_a_finance = "财务预测" in full_text
    ppt_a_achievements = "创新成果" in full_text

    add_check(
        "project_alpha_ppt_enterprise_overview",
        ppt_a_enterprise,
        "创业组 PPT must include 企业概况 section",
        weight=1.0
    )
    add_check(
        "project_alpha_ppt_performance",
        ppt_a_performance,
        "创业组 PPT must include 经营绩效 section",
        weight=1.0
    )
    add_check(
        "project_alpha_ppt_financial_forecast",
        ppt_a_finance,
        "创业组 PPT must include 财务预测 section",
        weight=1.0
    )
    add_check(
        "project_alpha_ppt_innovation_achievements",
        ppt_a_achievements,
        "创业组 PPT must include 创新成果 section",
        weight=1.0
    )

    # A4: PPT page count 12-15 (should mention 12 or 15 in context of pages)
    import re
    page_count_mentions = re.findall(r'(1[2-5])\s*[页pP]|[页pP]\s*(1[2-5])', full_text)
    # Also check for patterns like "12-15" or "12~15"
    page_range_pattern = re.search(r'1[2-5]\s*[-~到至]\s*1[2-5]', full_text)
    ppt_a_pagecount = len(page_count_mentions) > 0 or page_range_pattern is not None
    add_check(
        "project_alpha_ppt_page_count_range",
        ppt_a_pagecount,
        "创业组 PPT page count should be in 12-15 range (看SKILL.md: 12-15页)",
        weight=1.0
    )

    # ============================================================
    # PROJECT B: 红心助农 → 青年红色筑梦之旅赛道-公益组
    # Expected scoring: 团队协作15, 创新性25, 实践性25, 带动就业15, 传承红色基因20
    # PPT: must include 传承红色基因 page, emphasize 社会价值, 公益属性
    # ============================================================

    # B1: Track identification - 青年红色筑梦之旅 + 公益组
    track_b_passed = ("青年红色筑梦之旅" in full_text or "红色筑梦" in full_text) and \
                     ("公益组" in full_text)
    add_check(
        "project_beta_track_identification",
        track_b_passed,
        "Must identify 青年红色筑梦之旅赛道-公益组 for 红心助农 project",
        weight=2.0
    )

    # B2: Exact scoring for 青年红色筑梦之旅
    # 团队协作15, 创新性25, 实践性25, 带动就业15, 传承红色基因20
    score_b_team = "15" in full_text and "团队协作" in full_text
    score_b_innovation = "25" in full_text and "创新性" in full_text
    score_b_practice = "25" in full_text and "实践性" in full_text
    score_b_employment = "15" in full_text and "带动就业" in full_text
    score_b_red_gene = "20" in full_text and "传承红色基因" in full_text

    add_check(
        "project_beta_scoring_team_cooperation",
        score_b_team,
        "青年红色筑梦之旅: 团队协作=15分 must be present",
        weight=1.5
    )
    add_check(
        "project_beta_scoring_innovation",
        score_b_innovation,
        "青年红色筑梦之旅: 创新性=25分 must be present",
        weight=1.5
    )
    add_check(
        "project_beta_scoring_practice",
        score_b_practice,
        "青年红色筑梦之旅: 实践性=25分 must be present",
        weight=1.5
    )
    add_check(
        "project_beta_scoring_employment_boost",
        score_b_employment,
        "青年红色筑梦之旅: 带动就业=15分 — this is a proprietary criterion not in standard guides",
        weight=2.0
    )
    add_check(
        "project_beta_scoring_red_gene",
        score_b_red_gene,
        "青年红色筑梦之旅: 传承红色基因=20分 — this is a unique proprietary criterion",
        weight=2.0
    )

    # B3: PPT for 青年红色筑梦之旅 - must include 传承红色基因 page
    ppt_b_red_heritage = "传承红色基因" in full_text
    ppt_b_social_value = "社会价值" in full_text or "社会影响" in full_text
    ppt_b_public_welfare = "公益" in full_text

    add_check(
        "project_beta_ppt_red_heritage_section",
        ppt_b_red_heritage,
        "青年红色筑梦之旅 PPT must include 传承红色基因 themed section (SKILL.md mandates this)",
        weight=2.0
    )
    add_check(
        "project_beta_ppt_social_value",
        ppt_b_social_value,
        "PPT for 红心助农 must emphasize 社会价值/社会影响",
        weight=1.0
    )
    add_check(
        "project_beta_ppt_public_welfare",
        ppt_b_public_welfare,
        "PPT for 红心助农 must reference 公益属性",
        weight=1.0
    )

    # ============================================================
    # CRITICAL: Verify that scoring is NOT confused between tracks
    # 高教主赛道-创意组 has 个人成长=30, but 创业组 has 个人成长=25
    # If the agent outputs 30 for project A's 个人成长, it failed (used wrong sub-group)
    # ============================================================
    
    # Check if incorrect score of 30 is NOT associated with 个人成长 for project A context
    # This is hard to check without structured parsing, so we do a heuristic:
    # If the data is properly structured per project, we can try to extract sub-sections
    
    try:
        # Try to find project A section and check its scores
        proj_a_section = None
        proj_b_section = None
        
        if isinstance(data, dict):
            for key, val in data.items():
                key_lower = key.lower()
                val_str = json.dumps(val, ensure_ascii=False).lower()
                if "智农" in key_lower or "alpha" in key_lower or ("智农" in val_str and "saas" in val_str):
                    proj_a_section = val
                if "红心" in key_lower or "beta" in key_lower or ("红心" in val_str and "公益" in val_str):
                    proj_b_section = val
        elif isinstance(data, list):
            for item in data:
                item_str = json.dumps(item, ensure_ascii=False).lower()
                if "智农" in item_str or "saas" in item_str:
                    proj_a_section = item
                if "红心" in item_str and "公益" in item_str:
                    proj_b_section = item

        if proj_a_section:
            proj_a_str = json.dumps(proj_a_section, ensure_ascii=False)
            # Check that 个人成长 is 25 (not 30) in proj A
            # Pattern: 个人成长 followed by 25 within reasonable proximity
            import re
            personal_growth_in_a = re.search(r'个人成长.{0,30}25|25.{0,30}个人成长', proj_a_str)
            personal_growth_wrong_in_a = re.search(r'个人成长.{0,30}30|30.{0,30}个人成长', proj_a_str)
            if personal_growth_in_a and not personal_growth_wrong_in_a:
                add_check(
                    "project_alpha_correct_personal_growth_score",
                    True,
                    "Correctly assigned 个人成长=25 (not 30) to 创业组 project A — critical differentiation",
                    weight=2.0
                )
            elif personal_growth_wrong_in_a and not personal_growth_in_a:
                add_check(
                    "project_alpha_correct_personal_growth_score",
                    False,
                    "ERROR: Used 30 for 个人成长 in 创业组 — this is the 创意组 score. Agent likely confused sub-groups.",
                    weight=2.0
                )
            else:
                add_check(
                    "project_alpha_correct_personal_growth_score",
                    bool(personal_growth_in_a),
                    f"个人成长 score assignment for project A: {'correct (25)' if personal_growth_in_a else 'unclear or missing'}",
                    weight=2.0
                )
        else:
            # Fallback: check globally that 创业组 context has 25 for 个人成长
            add_check(
                "project_alpha_correct_personal_growth_score",
                score_a_personal,
                "Could not isolate project A section; checking globally for 个人成长=25",
                weight=2.0
            )
    except Exception as e:
        add_check(
            "project_alpha_correct_personal_growth_score",
            False,
            f"Exception during cross-track score verification: {e}",
            weight=2.0
        )

    # ============================================================
    # FINAL SCORE COMPUTATION
    # ============================================================
    final_score = total_score / max_score if max_score > 0 else 0.0
    passed = final_score >= 0.70  # Must pass at least 70% of checks

    return {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))