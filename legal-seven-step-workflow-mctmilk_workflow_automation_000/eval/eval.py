import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # Find the report file
    report_path = None
    target_path = Path(workspace_dir) / "cases" / "2024" / "civil" / "legal_analysis_report.md"
    
    if target_path.exists():
        report_path = target_path
    else:
        # Fallback: search broadly
        candidates = list(Path(workspace_dir).rglob("legal_analysis_report.md"))
        if candidates:
            report_path = candidates[0]
    
    # Check 0: File exists
    file_exists = report_path is not None and report_path.exists()
    checks.append({
        "name": "report_file_exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "legal_analysis_report.md not found anywhere in workspace"
    })
    
    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    content_lower = content.lower()
    
    # =====================================================================
    # CHECK 1: Seven-step workflow coverage
    # The report must cover all 7 steps
    # =====================================================================
    step_patterns = [
        (r'第[一1]步|结构化拆解|structural', "Step 1: 结构化拆解"),
        (r'第[二2]步|概念深挖|concept.*deep|深挖', "Step 2: 概念深挖"),
        (r'第[三3]步|体系定位|system.*map|关联网络', "Step 3: 体系定位"),
        (r'第[四4]步|证据映射|evidence.*map|要件.*事实.*证据', "Step 4: 证据映射"),
        (r'第[五5]步|攻防模拟|debate.*sim|攻击.*防御|对方律师', "Step 5: 攻防模拟"),
        (r'第[六6]步|类案验证|case.*valid|裁判分歧|高频败诉', "Step 6: 类案验证"),
        (r'第[七7]步|决策固化|decision.*tree|法条.*sop|sop', "Step 7: 决策固化"),
    ]
    
    step_results = []
    for pattern, name in step_patterns:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        step_results.append(found)
        checks.append({
            "name": f"workflow_step_present_{name}",
            "passed": found,
            "detail": f"'{name}' section found in report" if found else f"'{name}' section NOT found in report"
        })
    
    steps_coverage = sum(step_results) / len(step_results)
    
    # =====================================================================
    # CHECK 2: Seven-dimensional analysis table (Step 1 output)
    # Must have: 规范类型/适用主体/构成要件/法律效果/但书例外/关键概念
    # =====================================================================
    dimension_keywords = [
        ('规范类型', '规范类型 dimension'),
        ('适用主体', '适用主体 dimension'),
        ('构成要件', '构成要件 dimension'),
        ('法律效果', '法律效果 dimension'),
        ('但书|例外', '但书/例外 dimension'),
        ('关键概念', '关键概念 dimension'),
    ]
    
    dimension_results = []
    for pattern, desc in dimension_keywords:
        found = bool(re.search(pattern, content))
        dimension_results.append(found)
        checks.append({
            "name": f"seven_dim_table_{desc}",
            "passed": found,
            "detail": f"Dimension '{desc}' found" if found else f"Dimension '{desc}' MISSING from 七维度分析表"
        })
    
    dim_coverage = sum(dimension_results) / len(dimension_results)
    
    # =====================================================================
    # CHECK 3: Six-column evidence table (Step 4 - 要件-事实-证据六列表)
    # Must have evidence mapping structure
    # =====================================================================
    evidence_table_patterns = [
        r'六列表|六.*列|six.*col',
        r'要件.*事实.*证据|证据.*要件|要件.*证据',
        r'证明对象|证明标准|证明责任',
        r'证据.*清单|evidence.*list',
    ]
    
    evidence_table_found = any(bool(re.search(p, content, re.IGNORECASE)) for p in evidence_table_patterns)
    checks.append({
        "name": "evidence_six_column_table",
        "passed": evidence_table_found,
        "detail": "六列表 (six-column evidence table) found in Step 4" if evidence_table_found else "六列表 structure NOT found - Step 4 evidence mapping is missing or incomplete"
    })
    
    # Additional check: evidence table has actual evidence items
    evidence_items_patterns = [
        r'格式条款|预先拟定|重复使用',
        r'提示.*义务|说明.*义务',
        r'合同.*文本|协议.*文本|App.*界面|电子.*协议',
    ]
    evidence_items_found = sum(1 for p in evidence_items_patterns if bool(re.search(p, content)))
    evidence_content_rich = evidence_items_found >= 2
    checks.append({
        "name": "evidence_table_content_quality",
        "passed": evidence_content_rich,
        "detail": f"Evidence table references {evidence_items_found}/3 key evidence types for this case" if evidence_content_rich else "Evidence table lacks case-specific content"
    })
    
    # =====================================================================
    # CHECK 4: Attack-defense simulation (Step 5)
    # Must have attack list + defense strategies
    # =====================================================================
    attack_patterns = [
        r'攻击.*清单|攻击.*点|attack.*list',
        r'对方.*律师|opposing.*counsel|对方.*主张',
        r'防御.*策略|defense.*strat|应对.*方案',
    ]
    
    attack_results = [bool(re.search(p, content, re.IGNORECASE)) for p in attack_patterns]
    attack_defense_found = sum(attack_results) >= 2
    checks.append({
        "name": "attack_defense_simulation",
        "passed": attack_defense_found,
        "detail": f"Attack-defense simulation found ({sum(attack_results)}/3 patterns)" if attack_defense_found else "Step 5 攻防模拟 is incomplete - missing attack list or defense strategies"
    })
    
    # =====================================================================
    # CHECK 5: Iron Rule Two - Mandatory case validation notice
    # MUST explicitly mention 中国裁判文书网 AND 北大法宝
    # =====================================================================
    wenshu_found = bool(re.search(r'裁判文书网|wenshu', content, re.IGNORECASE))
    beida_found = bool(re.search(r'北大法宝|pkulaw', content, re.IGNORECASE))
    
    checks.append({
        "name": "iron_rule_2_wenshu_net",
        "passed": wenshu_found,
        "detail": "中国裁判文书网 cross-verification platform mentioned (Iron Rule 2)" if wenshu_found else "CRITICAL: 中国裁判文书网 NOT mentioned - Iron Rule 2 violation"
    })
    checks.append({
        "name": "iron_rule_2_pkulaw",
        "passed": beida_found,
        "detail": "北大法宝 cross-verification platform mentioned (Iron Rule 2)" if beida_found else "CRITICAL: 北大法宝 NOT mentioned - Iron Rule 2 violation"
    })
    
    iron_rule_2_passed = wenshu_found and beida_found
    
    # =====================================================================
    # CHECK 6: SOP Decision Tree (Step 7)
    # Must have 判断节点/证据要求/切换点
    # =====================================================================
    sop_components = [
        (r'判断节点|decision.*node|判断.*点', '判断节点'),
        (r'证据要求|evidence.*req|举证.*要求', '证据要求'),
        (r'切换点|transition.*point|转换.*点|切换', '切换点'),
    ]
    
    sop_results = []
    for pattern, name in sop_components:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        sop_results.append(found)
        checks.append({
            "name": f"sop_component_{name}",
            "passed": found,
            "detail": f"SOP component '{name}' found" if found else f"SOP component '{name}' MISSING from Step 7 决策固化"
        })
    
    sop_coverage = sum(sop_results) / len(sop_results)
    
    # =====================================================================
    # CHECK 7: Final deliverables checklist
    # All 7 items from the "最终交付物清单" should be present
    # =====================================================================
    deliverable_patterns = [
        (r'七维度.*拆解|结构.*拆解.*表', '七维度结构拆解表'),
        (r'概念.*深挖|关键.*概念.*报告', '关键概念深挖报告'),
        (r'关联网络|体系.*定位|法条.*关联', '法条关联网络图'),
        (r'证据.*作战|证据.*地图|六列表|要件.*事实.*证据', '证据作战地图（六列表）'),
        (r'攻防.*报告|防御.*策略|攻击.*清单', '攻防模拟报告'),
        (r'类案.*验证|裁判分歧|高频.*败诉', '类案验证报告'),
        (r'决策.*流程|sop|法条.*适用.*决策', '法条适用决策流程图（SOP）'),
    ]
    
    deliverable_results = []
    for pattern, name in deliverable_patterns:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        deliverable_results.append(found)
        checks.append({
            "name": f"deliverable_{name[:10]}",
            "passed": found,
            "detail": f"Deliverable '{name}' present" if found else f"Deliverable '{name}' MISSING from report"
        })
    
    deliverable_coverage = sum(deliverable_results) / len(deliverable_results)
    
    # =====================================================================
    # CHECK 8: Iron Rule acknowledgments at correct steps
    # Step 1 → 铁律一, Step 3 → 铁律三 (time sensitivity), Step 6 → 铁律二
    # =====================================================================
    iron_rule_mentions = bool(re.search(r'铁律|iron.*rule|四条.*律|副驾驶', content, re.IGNORECASE))
    checks.append({
        "name": "iron_rules_acknowledged",
        "passed": iron_rule_mentions,
        "detail": "Iron rules (铁律) acknowledged in report" if iron_rule_mentions else "Iron rules NOT mentioned - quality checkpoints missing"
    })
    
    time_sensitivity = bool(re.search(r'铁律三|时效性|训练数据|截止日期|新.*司法解释|2023.*解释', content))
    checks.append({
        "name": "iron_rule_3_time_sensitivity",
        "passed": time_sensitivity,
        "detail": "Iron Rule 3 (time sensitivity / new judicial interpretations) addressed" if time_sensitivity else "Iron Rule 3 NOT addressed - agent failed to flag 2023 judicial interpretation timeliness issue"
    })
    
    # =====================================================================
    # CHECK 9: Case-specific analysis (not generic)
    # Must reference the specific article and case facts
    # =====================================================================
    article_496 = bool(re.search(r'第?四百九十六条|第?496条|民法典.*496|496.*民法典', content))
    checks.append({
        "name": "article_496_referenced",
        "passed": article_496,
        "detail": "民法典第496条 specifically analyzed" if article_496 else "The specific article (民法典第496条) is not clearly referenced"
    })
    
    case_specific = bool(re.search(r'陈某|金融公司|金融科技|催收|逾期|个人信息|App.*协议|68页', content))
    checks.append({
        "name": "case_specific_facts_integrated",
        "passed": case_specific,
        "detail": "Case-specific facts (陈某/金融公司/催收 etc.) integrated into analysis" if case_specific else "Analysis appears generic - case-specific facts not integrated"
    })
    
    # =====================================================================
    # CHECK 10: Unverified case warning (the case note in the brief)
    # The brief explicitly flagged an unverified case number - must be handled
    # =====================================================================
    unverified_warning = bool(re.search(
        r'未.*核[验证]|核[验证].*未|待.*核[验证]|需.*核[验证]|未.*验证|12345.*未|案例.*真实性|真实性.*未',
        content
    ))
    checks.append({
        "name": "unverified_case_warning",
        "passed": unverified_warning,
        "detail": "Report explicitly flags the unverified case (京0491民初12345号) as requiring cross-verification" if unverified_warning else "CRITICAL: Report failed to flag the unverified case as per Iron Rule 2"
    })
    
    # =====================================================================
    # SCORING
    # =====================================================================
    all_checks = checks[1:]  # exclude file_exists from scoring
    
    # Weighted scoring
    critical_checks = [
        iron_rule_2_passed,                    # Iron Rule 2 (both platforms) - critical
        bool(re.search(r'判断节点', content)) and bool(re.search(r'切换点', content)),  # SOP completeness
        evidence_table_found,                  # Six-column table
        steps_coverage >= 6/7,                 # Most steps covered
    ]
    
    base_score = sum(c["passed"] for c in checks[1:]) / max(len(checks) - 1, 1)
    
    # Penalties for critical failures
    critical_penalty = sum(0.1 for c in critical_checks if not c)
    
    final_score = max(0.0, min(1.0, base_score - critical_penalty))
    
    # Overall pass: must hit 70% of checks AND pass both Iron Rule 2 checks AND have SOP
    overall_passed = (
        final_score >= 0.65 and
        iron_rule_2_passed and
        steps_coverage >= 5/7 and
        dim_coverage >= 4/6 and
        deliverable_coverage >= 5/7
    )
    
    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))