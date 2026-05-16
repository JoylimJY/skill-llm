import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    
    # ── Find the two required output files ──────────────────────────────────
    canvas_files = list(Path(workspace).rglob("brand_canvas.md"))
    plan_files   = list(Path(workspace).rglob("brand_plan.md"))
    
    # --- brand_canvas.md checks ---
    canvas_ok = len(canvas_files) > 0
    checks.append(check("brand_canvas.md exists", canvas_ok,
                         f"Found: {canvas_files[0]}" if canvas_ok else "File not found anywhere in workspace"))
    
    canvas_text = ""
    if canvas_ok:
        try:
            canvas_text = canvas_files[0].read_text(encoding="utf-8")
        except Exception as e:
            checks.append(check("brand_canvas.md readable", False, str(e)))
            canvas_ok = False

    # C1: All 7 required sections of 个人品牌定位画布 must be present
    canvas_sections = [
        ("我是谁",        r"我是谁"),
        ("我的专业优势",  r"我的专业优势|专业优势"),
        ("我的目标受众",  r"我的目标受众|目标受众"),
        ("我能提供的价值", r"我能提供的价值|能提供的价值"),
        ("我的品牌个性",  r"我的品牌个性|品牌个性"),
        ("我的传播渠道",  r"我的传播渠道|传播渠道"),
        ("我的里程碑目标", r"我的里程碑目标|里程碑目标"),
    ]
    for section_name, pattern in canvas_sections:
        found = bool(re.search(pattern, canvas_text)) if canvas_text else False
        checks.append(check(f"canvas section: {section_name}", found,
                             f"Pattern '{pattern}' {'found' if found else 'NOT found'} in brand_canvas.md"))

    # C2: 个人特质 field populated with content (not blank)
    # Check that 姓名, 职称, 机构, 研究领域 under 我是谁 are filled
    identity_filled = bool(re.search(r"林志远|Zhiyuan Lin", canvas_text, re.IGNORECASE)) if canvas_text else False
    checks.append(check("canvas: 我是谁 section contains researcher name",
                         identity_filled,
                         "Researcher name (林志远) should appear in canvas identity section"))

    # C3: 品牌个性 must reference one of the 4 style types from SKILL.md
    style_types = ["严谨型", "创新型", "实践型", "思想型"]
    style_found = any(s in canvas_text for s in style_types) if canvas_text else False
    checks.append(check("canvas: 品牌个性 references one of 4 official style types (严谨型/创新型/实践型/思想型)",
                         style_found,
                         f"Found style types: {[s for s in style_types if s in canvas_text]}"))

    # C4: 里程碑目标 has short/medium/long-term breakdown (6个月, 1年/12个月, 3年)
    milestone_short  = bool(re.search(r"6个月|半年|短期", canvas_text)) if canvas_text else False
    milestone_mid    = bool(re.search(r"1年|一年|12个月|中期", canvas_text)) if canvas_text else False
    milestone_long   = bool(re.search(r"3年|三年|长期", canvas_text)) if canvas_text else False
    milestone_ok     = milestone_short and milestone_mid and milestone_long
    checks.append(check("canvas: 里程碑目标 has 3 time horizons (6月/1年/3年)",
                         milestone_ok,
                         f"short={milestone_short}, mid={milestone_mid}, long={milestone_long}"))

    # C5: 传播渠道 section mentions academic platforms (ResearchGate/Google Scholar/ORCID)
    academic_channels = bool(re.search(r"ResearchGate|Google Scholar|ORCID", canvas_text, re.IGNORECASE)) if canvas_text else False
    checks.append(check("canvas: 传播渠道 mentions academic platforms (ResearchGate/GS/ORCID)",
                         academic_channels,
                         "At least one academic channel platform should be listed"))

    # ── brand_plan.md checks ─────────────────────────────────────────────────
    plan_ok = len(plan_files) > 0
    checks.append(check("brand_plan.md exists", plan_ok,
                         f"Found: {plan_files[0]}" if plan_ok else "File not found anywhere in workspace"))

    plan_text = ""
    if plan_ok:
        try:
            plan_text = plan_files[0].read_text(encoding="utf-8")
        except Exception as e:
            checks.append(check("brand_plan.md readable", False, str(e)))
            plan_ok = False

    # P1: Must have all 6 sections from 输出规范
    plan_sections = [
        ("现状诊断",  r"现状诊断|品牌现状"),
        ("品牌定位",  r"品牌定位"),
        ("内容策略",  r"内容策略|内容体系"),
        ("渠道策略",  r"渠道策略|渠道运营"),
        ("行动计划",  r"行动计划|行动方案"),
        ("监测指标",  r"监测指标|效果监测"),
    ]
    for section_name, pattern in plan_sections:
        found = bool(re.search(pattern, plan_text)) if plan_text else False
        checks.append(check(f"plan section: {section_name}", found,
                             f"Pattern '{pattern}' {'found' if found else 'NOT found'} in brand_plan.md"))

    # P2: SWOT analysis must be present in 现状诊断
    swot_found = bool(re.search(r"SWOT|优势.*劣势|Strengths|Weaknesses|机会|威胁", plan_text, re.IGNORECASE)) if plan_text else False
    checks.append(check("plan: SWOT analysis present in 现状诊断",
                         swot_found,
                         "SWOT analysis is required in the 现状诊断 section"))

    # P3: 品牌定位 must address all 4 四要素: 专业领域, 目标受众, 价值主张, 个人风格
    four_elements = [
        ("专业领域", r"专业领域"),
        ("目标受众", r"目标受众"),
        ("价值主张", r"价值主张"),
        ("个人风格", r"个人风格"),
    ]
    for el_name, pattern in four_elements:
        found = bool(re.search(pattern, plan_text)) if plan_text else False
        checks.append(check(f"plan 品牌定位 四要素: {el_name}", found,
                             f"'{el_name}' {'found' if found else 'NOT found'} in brand_plan.md"))

    # P4: 内容策略 MUST follow exact content calendar frequencies from SKILL.md
    # - 每周: 1篇社交媒体内容
    # - 每月: 1篇深度文章/采访
    # - 每季度: 1次公开演讲
    # - 每年: 1份行业报告/白皮书
    freq_weekly    = bool(re.search(r"每周.*1篇|1篇.*每周|每周.*社交", plan_text)) if plan_text else False
    freq_monthly   = bool(re.search(r"每月.*1篇|1篇.*每月|每月.*深度|每月.*采访", plan_text)) if plan_text else False
    freq_quarterly = bool(re.search(r"每季度.*1次|1次.*每季度|每季度.*演讲", plan_text)) if plan_text else False
    freq_annual    = bool(re.search(r"每年.*1份|1份.*每年|每年.*报告|每年.*白皮书", plan_text)) if plan_text else False
    checks.append(check("plan: content calendar weekly frequency (每周1篇社交媒体)",
                         freq_weekly, f"Pattern match result: {freq_weekly}"))
    checks.append(check("plan: content calendar monthly frequency (每月1篇深度文章/采访)",
                         freq_monthly, f"Pattern match result: {freq_monthly}"))
    checks.append(check("plan: content calendar quarterly frequency (每季度1次演讲)",
                         freq_quarterly, f"Pattern match result: {freq_quarterly}"))
    checks.append(check("plan: content calendar annual frequency (每年1份报告/白皮书)",
                         freq_annual, f"Pattern match result: {freq_annual}"))

    # P5: Tiered channel strategy - Tier 1 must contain ResearchGate/GS/ORCID AND WeChat AND LinkedIn
    # Tier 2 must contain 知乎/头条 AND Twitter/X AND 行业媒体
    # Tier 3 must contain B站/视频号 AND 小红书 AND 播客
    tier1_academic = bool(re.search(r"Tier\s*1|第一层|核心渠道", plan_text, re.IGNORECASE)) if plan_text else False
    tier2_present  = bool(re.search(r"Tier\s*2|第二层|重要渠道", plan_text, re.IGNORECASE)) if plan_text else False
    tier3_present  = bool(re.search(r"Tier\s*3|第三层|辅助渠道", plan_text, re.IGNORECASE)) if plan_text else False
    checks.append(check("plan: Tier 1 (核心渠道) channel classification present",
                         tier1_academic,
                         f"Tier 1/核心渠道 heading {'found' if tier1_academic else 'NOT found'}"))
    checks.append(check("plan: Tier 2 (重要渠道) channel classification present",
                         tier2_present,
                         f"Tier 2/重要渠道 heading {'found' if tier2_present else 'NOT found'}"))
    checks.append(check("plan: Tier 3 (辅助渠道) channel classification present",
                         tier3_present,
                         f"Tier 3/辅助渠道 heading {'found' if tier3_present else 'NOT found'}"))

    # P6: Tier 1 must contain WeChat (微信公众号) AND LinkedIn - the SKILL.md is very specific
    wechat_in_plan = bool(re.search(r"微信公众号", plan_text)) if plan_text else False
    linkedin_in_plan = bool(re.search(r"LinkedIn", plan_text, re.IGNORECASE)) if plan_text else False
    checks.append(check("plan: 微信公众号 appears in channel strategy (required in Tier 1)",
                         wechat_in_plan, f"微信公众号 {'found' if wechat_in_plan else 'NOT found'}"))
    checks.append(check("plan: LinkedIn appears in channel strategy (required in Tier 1)",
                         linkedin_in_plan, f"LinkedIn {'found' if linkedin_in_plan else 'NOT found'}"))

    # P7: 行动计划 must have 3 time horizons matching the SKILL.md
    action_short  = bool(re.search(r"0-6个月|短期.*行动|6个月内", plan_text)) if plan_text else False
    action_mid    = bool(re.search(r"6-12个月|中期.*目标|12个月", plan_text)) if plan_text else False
    action_long   = bool(re.search(r"1-3年|长期.*愿景|3年", plan_text)) if plan_text else False
    checks.append(check("plan: 行动计划 has 3 time horizons (0-6月 / 6-12月 / 1-3年)",
                         action_short and action_mid and action_long,
                         f"short(0-6月)={action_short}, mid(6-12月)={action_mid}, long(1-3年)={action_long}"))

    # P8: 监测指标 must include all 4 categories from SKILL.md
    monitoring_categories = [
        ("学术指标", r"学术指标|论文数|引用数|h-index"),
        ("传播指标", r"传播指标|粉丝|阅读量|互动率"),
        ("产业指标", r"产业指标|合作邀约|咨询机会|演讲邀请"),
        ("品牌指标", r"品牌指标|媒体提及|行业排名|奖项"),
    ]
    for cat_name, pattern in monitoring_categories:
        found = bool(re.search(pattern, plan_text)) if plan_text else False
        checks.append(check(f"plan 监测指标 category: {cat_name}", found,
                             f"Pattern for {cat_name} {'found' if found else 'NOT found'}"))

    # P9: Plan must reference researcher-specific data (Joule paper, h-index 23, etc.)
    researcher_specific = bool(re.search(r"林志远|Joule|h-index.*23|23.*h-index|固态电解质|固态电池界面", plan_text)) if plan_text else False
    checks.append(check("plan: contains researcher-specific content (not generic template)",
                         researcher_specific,
                         "Plan must reference specific researcher data (name, papers, specialty)"))

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total        = len(checks)
    score        = round(passed_count / total, 4) if total > 0 else 0.0
    overall      = score >= 0.75  # must pass at least 75% of checks

    return {
        "passed": overall,
        "score":  score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result    = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))