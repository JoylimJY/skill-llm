import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    """Find car_comparison_report.md anywhere in workspace."""
    candidates = list(Path(workspace).rglob("car_comparison_report.md"))
    if candidates:
        return candidates[0]
    return None

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def main():
    workspace = sys.argv[1]
    checks = []
    
    report_path = find_report(workspace)
    
    if report_path is None:
        checks.append(check("report_file_exists", False, "car_comparison_report.md not found anywhere in workspace"))
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return
    
    checks.append(check("report_file_exists", True, f"Found at {report_path}"))
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Cannot read file: {e}"))
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return
    
    checks.append(check("report_readable", True, f"File readable, {len(content)} chars"))

    # =========================================================
    # CHECK 1: Required top-level sections (Step 4.1 structure)
    # =========================================================
    
    # 一句话总结
    has_summary = bool(re.search(r'##\s*一句话总结', content))
    checks.append(check(
        "section_yijuhua_summary",
        has_summary,
        "Must contain '## 一句话总结' section per Step 4.1 对比结论结构"
    ))
    
    # 参数对比表
    has_param_table = bool(re.search(r'##\s*参数对比表', content))
    checks.append(check(
        "section_param_table",
        has_param_table,
        "Must contain '## 参数对比表' section per Step 4.1"
    ))
    
    # 各维度胜出分析
    has_dimension_analysis = bool(re.search(r'##\s*各维度胜出分析', content))
    checks.append(check(
        "section_dimension_analysis",
        has_dimension_analysis,
        "Must contain '## 各维度胜出分析' section per Step 4.1"
    ))
    
    # 车主真实反馈
    has_owner_feedback = bool(re.search(r'##\s*车主真实反馈', content))
    checks.append(check(
        "section_owner_feedback",
        has_owner_feedback,
        "Must contain '## 车主真实反馈' section per Step 4.1"
    ))
    
    # 购买建议
    has_purchase_advice = bool(re.search(r'##\s*购买建议', content))
    checks.append(check(
        "section_purchase_advice",
        has_purchase_advice,
        "Must contain '## 购买建议' section per Step 4.1"
    ))

    # =========================================================
    # CHECK 2: Parameter table must contain ALL FIVE LAYERS
    # (Step 3.1 mandates: 基础信息层, 动力/续航层, 内饰/舒适层, 智驾层, 安全/空间)
    # =========================================================
    
    # 基础信息层 keywords in table
    has_jichu = bool(re.search(r'基础信息', content))
    checks.append(check(
        "param_layer_jichu_xinxi",
        has_jichu,
        "Parameter table must include 基础信息层 (basic info layer) per Step 3.1"
    ))
    
    # 动力/续航层
    has_dongli = bool(re.search(r'动力[\s/／]*续航|续航[\s/／]*动力|电池容量|CLTC续航', content))
    checks.append(check(
        "param_layer_dongli_xuhang",
        has_dongli,
        "Parameter table must include 动力/续航层 with fields like 电池容量, CLTC续航 per Step 3.1"
    ))
    
    # 内饰/舒适层
    has_neishi = bool(re.search(r'内饰[\s/／]*舒适|座椅|车机系统|中控屏', content))
    checks.append(check(
        "param_layer_neishi_shushi",
        has_neishi,
        "Parameter table must include 内饰/舒适层 with fields like 座椅, 中控屏 per Step 3.1"
    ))
    
    # 智驾层
    has_zhijia = bool(re.search(r'智驾|NOA|激光雷达|TOPS|自动驾驶', content))
    checks.append(check(
        "param_layer_zhijia",
        has_zhijia,
        "Parameter table must include 智驾层 with fields like NOA, 激光雷达, TOPS per Step 3.1"
    ))
    
    # 安全/空间
    has_anquan = bool(re.search(r'安全[\s/／]*空间|安全气囊|后备箱|气囊', content))
    checks.append(check(
        "param_layer_anquan_kongjian",
        has_anquan,
        "Parameter table must include 安全/空间 layer with fields like 安全气囊, 后备箱 per Step 3.1"
    ))

    # =========================================================
    # CHECK 3: Both car models present
    # =========================================================
    has_model3 = bool(re.search(r'Model\s*3|model\s*3|模型3|特斯拉', content, re.IGNORECASE))
    checks.append(check(
        "car_model3_present",
        has_model3,
        "Report must include Tesla Model 3 data"
    ))
    
    has_su7 = bool(re.search(r'SU7|su7|小米.*汽车|小米SU', content, re.IGNORECASE))
    checks.append(check(
        "car_su7_present",
        has_su7,
        "Report must include Xiaomi SU7 data"
    ))

    # =========================================================
    # CHECK 4: Dimension analysis has at least 3 specific dimensions
    # (Step 4.1 lists: 续航/能效, 智驾, 内饰/舒适, 性价比)
    # =========================================================
    dimension_hits = 0
    dimension_patterns = [
        r'续航[\s/／]*能效|能效[\s/／]*续航',
        r'智驾',
        r'内饰[\s/／]*舒适|舒适[\s/／]*内饰',
        r'性价比',
    ]
    found_dims = []
    for pat in dimension_patterns:
        # check in the 各维度胜出分析 section specifically
        dim_section_match = re.search(r'##\s*各维度胜出分析(.*?)(?=##|\Z)', content, re.DOTALL)
        if dim_section_match:
            section_text = dim_section_match.group(1)
            if re.search(pat, section_text):
                dimension_hits += 1
                found_dims.append(pat)
    
    checks.append(check(
        "dimension_analysis_coverage",
        dimension_hits >= 3,
        f"各维度胜出分析 must cover at least 3 of: 续航/能效, 智驾, 内饰/舒适, 性价比. Found {dimension_hits}: {found_dims}"
    ))

    # =========================================================
    # CHECK 5: 车主真实反馈 section structure per Step 3.2
    # Must have: 好评高频词, 投诉集中点, 代表性车主评论
    # =========================================================
    feedback_section = re.search(r'##\s*车主真实反馈(.*?)(?=##\s*购买建议|\Z)', content, re.DOTALL)
    
    if feedback_section:
        fb_text = feedback_section.group(1)
        has_hao_ping = bool(re.search(r'好评高频词', fb_text))
        has_tou_su = bool(re.search(r'投诉集中点', fb_text))
        has_daibiao = bool(re.search(r'代表性车主评论', fb_text))
        
        checks.append(check(
            "feedback_haoping_field",
            has_hao_ping,
            "车主真实反馈 must contain '好评高频词' field per Step 3.2 评论整合规范"
        ))
        checks.append(check(
            "feedback_tousu_field",
            has_tou_su,
            "车主真实反馈 must contain '投诉集中点' field per Step 3.2 评论整合规范"
        ))
        checks.append(check(
            "feedback_daibiaoxing_field",
            has_daibiao,
            "车主真实反馈 must contain '代表性车主评论' field per Step 3.2 评论整合规范"
        ))
    else:
        checks.append(check("feedback_haoping_field", False, "车主真实反馈 section not found for sub-checks"))
        checks.append(check("feedback_tousu_field", False, "车主真实反馈 section not found for sub-checks"))
        checks.append(check("feedback_daibiaoxing_field", False, "车主真实反馈 section not found for sub-checks"))

    # =========================================================
    # CHECK 6: Feedback section footer per Step 3.2
    # Must contain: 数据来源, 采集时间, 注：评论为用户主观表达
    # =========================================================
    has_shuju_laiyuan = bool(re.search(r'数据来源', content))
    checks.append(check(
        "footer_data_source",
        has_shuju_laiyuan,
        "Must include '数据来源' footer per Step 3.2 format"
    ))
    
    has_caiji_shijian = bool(re.search(r'采集时间', content))
    checks.append(check(
        "footer_collection_time",
        has_caiji_shijian,
        "Must include '采集时间' footer per Step 3.2 format"
    ))
    
    has_zhu_note = bool(re.search(r'注[：:]\s*评论为用户主观|评论为用户主观表达', content))
    checks.append(check(
        "footer_subjective_note",
        has_zhu_note,
        "Must include '注：评论为用户主观表达' disclaimer per Step 3.2 exact format"
    ))

    # =========================================================
    # CHECK 7: 购买建议 uses the "如果你更在意...选..." pattern (Step 4.1)
    # =========================================================
    advice_section = re.search(r'##\s*购买建议(.*?)(?=##|\Z|>\s*数据采集时间)', content, re.DOTALL)
    if advice_section:
        advice_text = advice_section.group(1)
        has_ruguoni = bool(re.search(r'如果你更在意.{1,30}选', advice_text, re.DOTALL))
        checks.append(check(
            "purchase_advice_pattern",
            has_ruguoni,
            "购买建议 must use the '如果你更在意[X]，选[车型]' pattern per Step 4.1 at least once"
        ))
    else:
        checks.append(check(
            "purchase_advice_pattern",
            False,
            "购买建议 section not found or malformed for pattern check"
        ))

    # =========================================================
    # CHECK 8: Overall data_collection_time footer on report (Step 4.1)
    # The final footer: > 数据采集时间：{日期} | 价格以官网最新为准
    # =========================================================
    has_final_footer = bool(re.search(r'数据采集时间.{1,50}价格以官网', content))
    checks.append(check(
        "final_footer_present",
        has_final_footer,
        "Report must end with '> 数据采集时间：{日期} | 价格以官网最新为准' per Step 4.1"
    ))

    # =========================================================
    # CHECK 9: Actual data from JSON files used
    # Check that specific numeric values from raw_data JSONs appear
    # =========================================================
    # Tesla Model 3 CLTC: 606 or 713
    has_tesla_range = bool(re.search(r'60[0-9]|71[0-9]', content))
    checks.append(check(
        "data_tesla_cltc_range",
        has_tesla_range,
        "Report must use actual Tesla Model 3 CLTC range data (606km or 713km) from raw_data files"
    ))
    
    # Xiaomi SU7 CLTC: 700, 830, or 800
    has_su7_range = bool(re.search(r'700|830|800', content))
    checks.append(check(
        "data_su7_cltc_range",
        has_su7_range,
        "Report must use actual Xiaomi SU7 CLTC range data (700/830/800km) from raw_data files"
    ))

    # =========================================================
    # CHECK 10: 维度胜出分析 includes a clear winner statement for each dim
    # (e.g., "XX胜出" pattern in the section)
    # =========================================================
    dim_section_match2 = re.search(r'##\s*各维度胜出分析(.*?)(?=##|\Z)', content, re.DOTALL)
    if dim_section_match2:
        dim_text = dim_section_match2.group(1)
        has_winner = bool(re.search(r'胜出', dim_text))
        checks.append(check(
            "dimension_has_winner",
            has_winner,
            "各维度胜出分析 must declare winners using 'XX胜出' per Step 4.1 template"
        ))
    else:
        checks.append(check(
            "dimension_has_winner",
            False,
            "各维度胜出分析 section not found"
        ))

    # =========================================================
    # SCORING
    # =========================================================
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total if total > 0 else 0.0
    
    # Must pass all structural checks to be considered passed
    # Critical checks that must all pass:
    critical = [
        "section_yijuhua_summary",
        "section_param_table",
        "section_dimension_analysis",
        "section_owner_feedback",
        "section_purchase_advice",
        "feedback_haoping_field",
        "feedback_tousu_field",
        "feedback_daibiaoxing_field",
        "footer_collection_time",
        "footer_subjective_note",
        "param_layer_zhijia",
        "param_layer_dongli_xuhang",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()